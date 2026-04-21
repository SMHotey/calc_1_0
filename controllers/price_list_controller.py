"""Контроллер управления прайс-листами: CRUD, копирование, привязка контрагентов."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from db.repositories import BaseRepository
from models.price_list import BasePriceList, PersonalizedPriceList, TypePrice, CustomTypePrice
from models.counterparty import Counterparty
from db.database import SessionLocal


class PriceListController:
    """
    Контроллер для работы с прайс-листами.

    Отвечает за:
    - CRUD базового и персонализированных прайсов
    - Копирование базового прайса в персонализированный
    - Удаление с переназначением контрагентов
    - Получение актуальных цен для расчётов (включая type-specific)
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session or SessionLocal()
        self.base_repo = BaseRepository(self.session, BasePriceList)
        self.personal_repo = BaseRepository(self.session, PersonalizedPriceList)
        self.cp_repo = BaseRepository(self.session, Counterparty)

    def get_base_price_list(self) -> BasePriceList:
        """Возвращает единственный системный базовый прайс-лист."""
        base = self.base_repo.get_all()
        if not base:
            raise RuntimeError("Базовый прайс-лист не найден в БД.")
        return base[0]

    def get_personalized_lists(self) -> List[PersonalizedPriceList]:
        """Возвращает все активные персонализированные прайс-листы."""
        return self.personal_repo.get_all()

    def get_price_list_by_id(self, price_list_id: int) -> Optional[BasePriceList | PersonalizedPriceList]:
        """Возвращает прайс по ID (базовый или персонализированный)."""
        # Сначала пробуем персональный
        pl = self.personal_repo.get_by_id(price_list_id)
        if pl:
            return pl
        # Потом базовый
        return self.base_repo.get_by_id(price_list_id)

    def create_personalized(
            self,
            name: str,
            base_id: Optional[int] = None,
            source_id: Optional[int] = None
    ) -> PersonalizedPriceList:
        """
        Создаёт персонализированный прайс-лист на основе базового или существующего.

        :param name: Название нового прайса
        :param base_id: ID базового прайса для копирования (по умолчанию - системный)
        :param source_id: ID персонализированного прайса для копирования (приоритет над base_id)
        :return: Созданный объект PersonalizedPriceList
        """
        if source_id:
            source = self.personal_repo.get_by_id(source_id)
        elif base_id:
            source = self.base_repo.get_by_id(base_id)
        else:
            source = self.get_base_price_list()

        if not source:
            raise ValueError("Исходный прайс-лист не найден.")

        # For new personalized list, start with None (meaning "use base price")
        new_pl = self.personal_repo.create(
            PersonalizedPriceList(
                name=name,
                base_price_list_id=source.id if isinstance(source, BasePriceList) else source.base_price_list_id,
                custom_doors_price_std_single=None,
                custom_doors_price_per_m2_nonstd=None,
                custom_doors_wide_markup=None,
                custom_cutout_price=None
            )
        )
        
        # Copy all data from base price list
        from_id = source.id if isinstance(source, BasePriceList) else source.base_price_list_id
        self._copy_type_prices(from_id, new_pl.id)
        self._copy_glass_types(from_id, new_pl.id)
        self._copy_hardware(from_id, new_pl.id)
        self._copy_closers(from_id, new_pl.id)
        
        return new_pl

    def _copy_type_prices(self, from_price_list_id: int, to_price_list_id: int) -> None:
        """Копирует type-specific цены из одного прайса в другой."""
        base_prices = self.session.execute(
            select(TypePrice).where(TypePrice.price_list_id == from_price_list_id)
        ).scalars().all()
        
        for bp in base_prices:
            custom = CustomTypePrice(
                price_list_id=to_price_list_id,
                product_type=bp.product_type,
                subtype=bp.subtype,
                price_std_single=bp.price_std_single,
                price_double_std=bp.price_double_std,
                price_wide_markup=bp.price_wide_markup,
                price_per_m2_nonstd=bp.price_per_m2_nonstd
            )
            self.session.add(custom)
        self.session.flush()
    
    def _copy_glass_types(self, from_price_list_id: int, to_price_list_id: int) -> None:
        """Копирует типы стёкол и их опции."""
        from models.glass import GlassType, GlassOption
        
        # Copy glass types
        glasses = self.session.execute(
            select(GlassType).where(GlassType.price_list_id == from_price_list_id)
        ).scalars().all()
        
        glass_map = {}  # old_id -> new_glass
        for g in glasses:
            new_glass = GlassType(
                name=g.name,
                price_per_m2=g.price_per_m2,
                min_price=g.min_price,
                price_list_id=to_price_list_id
            )
            self.session.add(new_glass)
            self.session.flush()
            glass_map[g.id] = new_glass
        
        # Copy glass options
        options = self.session.execute(
            select(GlassOption).where(GlassOption.glass_type_id.in_([g.id for g in glasses]))
        ).scalars().all()
        
        for opt in options:
            new_opt = GlassOption(
                name=opt.name,
                price_per_m2=opt.price_per_m2,
                min_price=opt.min_price,
                glass_type_id=glass_map.get(opt.glass_type_id).id if opt.glass_type_id else None
            )
            self.session.add(new_opt)
        self.session.flush()
    
    def _copy_hardware(self, from_price_list_id: int, to_price_list_id: int) -> None:
        """Копирует фурнитуру."""
        from models.hardware import HardwareItem
        
        items = self.session.execute(
            select(HardwareItem).where(HardwareItem.price_list_id == from_price_list_id)
        ).scalars().all()
        
        for item in items:
            new_item = HardwareItem(
                type=item.type,
                name=item.name,
                price=item.price,
                description=item.description,
                has_cylinder=item.has_cylinder,
                price_list_id=to_price_list_id
            )
            self.session.add(new_item)
        self.session.flush()
    
    def _copy_closers(self, from_price_list_id: int, to_price_list_id: int) -> None:
        """Копирует доводчики и координаторы."""
        from models.closer import Closer, Coordinator
        
        closers = self.session.execute(
            select(Closer).where(Closer.price_list_id == from_price_list_id)
        ).scalars().all()
        
        for c in closers:
            new_c = Closer(
                name=c.name,
                door_weight=c.door_weight,
                price=c.price,
                price_list_id=to_price_list_id
            )
            self.session.add(new_c)
        
        coordinators = self.session.execute(
            select(Coordinator).where(Coordinator.price_list_id == from_price_list_id)
        ).scalars().all()
        
        for c in coordinators:
            new_c = Coordinator(
                name=c.name,
                price=c.price,
                price_list_id=to_price_list_id
            )
            self.session.add(new_c)
        
        self.session.flush()

    def get_type_price(
            self, 
            price_list_id: Optional[int],
            product_type: str,
            subtype: str
    ) -> Optional[Dict[str, float]]:
        """
        Возвращает type-specific цены для конкретного типа изделия.
        Проверяет персонализированный прайс, затем базовый.
        
        :return: Dict с keys: price_std_single, price_double_std, price_wide_markup, price_per_m2_nonstd
        """
        if not price_list_id:
            base = self.get_base_price_list()
            price_list_id = base.id
            return self._get_type_price_from_base(base.id, product_type, subtype)
        
        personal = self.personal_repo.get_by_id(price_list_id)
        if not personal:
            base = self.get_base_price_list()
            return self._get_type_price_from_base(base.id, product_type, subtype)
        
        custom = self.session.execute(
            select(CustomTypePrice).where(
                and_(
                    CustomTypePrice.price_list_id == price_list_id,
                    CustomTypePrice.product_type == product_type,
                    CustomTypePrice.subtype == subtype
                )
            )
        ).scalar_one_or_none()
        
        if custom and (custom.price_std_single is not None or custom.price_double_std is not None):
            return {
                "price_std_single": custom.price_std_single or 0,
                "price_double_std": custom.price_double_std or 0,
                "price_wide_markup": custom.price_wide_markup or 0,
                "price_per_m2_nonstd": custom.price_per_m2_nonstd or 0
            }
        
        base = self.base_repo.get_by_id(personal.base_price_list_id)
        return self._get_type_price_from_base(base.id if base else 1, product_type, subtype)

    def _get_type_price_from_base(self, base_id: int, product_type: str, subtype: str) -> Optional[Dict[str, float]]:
        """Получает type-specific цены из базового прайса."""
        tp = self.session.execute(
            select(TypePrice).where(
                and_(
                    TypePrice.price_list_id == base_id,
                    TypePrice.product_type == product_type,
                    TypePrice.subtype == subtype
                )
            )
        ).scalar_one_or_none()
        
        if tp:
            return {
                "price_std_single": tp.price_std_single,
                "price_double_std": tp.price_double_std,
                "price_wide_markup": tp.price_wide_markup,
                "price_per_m2_nonstd": tp.price_per_m2_nonstd
            }
        return None

    def update_personalized(self, pl_id: int, data: Dict[str, Any]) -> Optional[PersonalizedPriceList]:
        """Обновляет поля персонализированного прайс-листа."""
        return self.personal_repo.update(pl_id, data)

    def delete_personalized(self, pl_id: int, reassign_to_base: bool = True) -> bool:
        """
        Удаляет персонализированный прайс-лист.

        :param pl_id: ID удаляемого прайса
        :param reassign_to_base: Если True, контрагенты переназначаются на базовый прайс
        :return: True если удаление успешно
        """
        from models.counterparty import Counterparty
        pl = self.personal_repo.get_by_id(pl_id)
        if not pl:
            return False

        if reassign_to_base:
            base = self.get_base_price_list()
            stmt = select(Counterparty).where(Counterparty.price_list_id == pl_id)
            counterparts = self.session.execute(stmt).scalars().all()
            for cp in counterparts:
                cp.price_list_id = base.id
            self.session.flush()

        return self.personal_repo.delete(pl_id)

    def get_price_for_calculation(self, price_list_id: Optional[int]) -> Dict[str, float]:
        """
        Возвращает словарь цен для калькулятора, разрешая наследование из базового прайса.

        :param price_list_id: ID прайса (None = базовый)
        :return: Dict с ключами цен для PriceData
        """
        if not price_list_id:
            base = self.get_base_price_list()
            return self._extract_prices(base, is_base=True)
        
        # Check if it's a personalized price list first, then base
        # Note: They use separate ID spaces, so we must check both
        personal = self.personal_repo.get_by_id(price_list_id)
        if personal:
            # Get base prices from the referenced base
            base_obj = self.base_repo.get_by_id(personal.base_price_list_id)
            if not base_obj:
                base_obj = self.get_base_price_list()
            base_prices = self._extract_prices(base_obj, is_base=True)
            
            # Get personalized custom overrides
            custom_fields = {
                "doors_price_std_single": personal.custom_doors_price_std_single,
                "doors_price_per_m2_nonstd": personal.custom_doors_price_per_m2_nonstd,
                "doors_wide_markup": personal.custom_doors_wide_markup,
                "cutout_price": personal.custom_cutout_price,
            }
            
            # Merge: base + custom overrides (only override if value is not None)
            result = dict(base_prices)
            for k, v in custom_fields.items():
                if v is not None:
                    result[k] = v
            return result
        
        # Try base
        base = self.base_repo.get_by_id(price_list_id)
        if base:
            return self._extract_prices(base, is_base=True)

        # Fallback to system base
        return self._extract_prices(self.get_base_price_list(), is_base=True)

    def _extract_prices(self, pl: BasePriceList | PersonalizedPriceList, is_base: bool) -> Dict[str, Optional[float]]:
        """Извлекает числовые поля цен из модели в словарь."""
        fields = [
            "doors_price_std_single", "doors_price_per_m2_nonstd", "doors_wide_markup",
            "doors_double_std", "hatch_std", "hatch_wide_markup", "hatch_per_m2_nonstd",
            "gate_per_m2", "gate_large_per_m2", "transom_per_m2", "transom_min",
            "cutout_price", "deflector_per_m2", "trim_per_lm",
            "closer_price", "hinge_price", "anti_theft_price", "gkl_price", "mount_ear_price",
            "threshold_price", "vent_grate_tech", "vent_grate_pp"
        ]
        result = {}
        for f in fields:
            val = getattr(pl, f, None)
            result[f] = val
        return result

    def update_base(self, base: BasePriceList) -> BasePriceList:
        """Обновляет базовый прайс-лист."""
        self.session.flush()
        return base

    # === Type Prices (type-specific pricing) ===

    def get_type_prices(self, price_list_id: int) -> List[TypePrice]:
        """Возвращает все type-specific цены для прайс-листа."""
        stmt = select(TypePrice).where(TypePrice.price_list_id == price_list_id)
        return list(self.session.execute(stmt).scalars().all())

    def create_type_price(
            self,
            price_list_id: int,
            product_type: str,
            subtype: str,
            price_std_single: float = 0,
            price_double_std: float = 0,
            price_wide_markup: float = 0,
            price_per_m2_nonstd: float = 0
    ) -> TypePrice:
        """Создаёт type-specific цену для типа изделия."""
        tp = TypePrice(
            price_list_id=price_list_id,
            product_type=product_type,
            subtype=subtype,
            price_std_single=price_std_single,
            price_double_std=price_double_std,
            price_wide_markup=price_wide_markup,
            price_per_m2_nonstd=price_per_m2_nonstd
        )
        self.session.add(tp)
        self.session.flush()
        return tp

    def update_type_price(self, tp_id: int, data: Dict[str, Any]) -> Optional[TypePrice]:
        """Обновляет type-specific цену."""
        stmt = select(TypePrice).where(TypePrice.id == tp_id)
        tp = self.session.execute(stmt).scalar_one_or_none()
        if tp:
            for key, value in data.items():
                setattr(tp, key, value)
            self.session.flush()
        return tp

    def delete_type_price(self, tp_id: int) -> bool:
        """Удаляет type-specific цену."""
        stmt = select(TypePrice).where(TypePrice.id == tp_id)
        tp = self.session.execute(stmt).scalar_one_or_none()
        if tp:
            self.session.delete(tp)
            self.session.flush()
            return True
        return False

