"""Контроллер управления прайс-листами: CRUD, копирование, привязка контрагентов."""

import logging
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, text
from db.repositories import BaseRepository
from models.price_list import BasePriceList, PersonalizedPriceList, TypePrice, CustomTypePrice
from models.counterparty import Counterparty
from db.database import SessionLocal

logger = logging.getLogger(__name__)


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
    
    def get_base_price_list(self) -> Optional[BasePriceList]:
        """Возвращает единственный системный базовый прайс-лист."""
        base = self.base_repo.get_all()
        if not base:
            # Create base price list if it doesn't exist
            new_base = BasePriceList(name="Базовый прайс")
            self.session.add(new_base)
            self.session.flush()
            return new_base
        return base[0]
    
    def get_personalized_lists(self) -> List[PersonalizedPriceList]:
        """Возвращает все активные персонализированные прайс-листы."""
        return self.personal_repo.get_all()
    
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
            if source:
                source_base_id = source.base_price_list_id
            else:
                source_base_id = None
        elif base_id:
            source_base_id = base_id
        else:
            base = self.get_base_price_list()
            source_base_id = base.id
        
        if not source_base_id:
            raise ValueError("Исходный прайс-лист не найден.")
        
        # Create new personalized price list
        new_pl = self.personal_repo.create(
            PersonalizedPriceList(
                name=name,
                base_price_list_id=source_base_id,
                # Initialize custom fields to None
                custom_doors_price_std_single=None,
                custom_doors_price_per_m2_nonstd=None,
                custom_doors_wide_markup=None,
                custom_doors_double_std=None,
                custom_hatch_std=None,
                custom_hatch_wide_markup=None,
                custom_hatch_per_m2_nonstd=None,
                custom_gate_per_m2=None,
                custom_gate_large_per_m2=None,
                custom_transom_per_m2=None,
                custom_transom_min=None,
                custom_cutout_price=None,
                custom_deflector_per_m2=None,
                custom_trim_per_lm=None,
                custom_closer_price=None,
                custom_hinge_price=None,
                custom_anti_theft_price=None,
                custom_gkl_price=None,
                custom_mount_ear_price=None,
                custom_threshold_price=None,
                custom_vent_grate_tech=None,
                custom_vent_grate_pp=None,
                custom_seal_per_m2=None,
                custom_nonstd_color_markup_pct=None,
                custom_diff_color_markup=None,
                custom_moire_price=None,
                custom_lacquer_per_m2=None,
                custom_primer_single=None,
                custom_primer_double=None
            )
        )
        
        # Copy all data from base price list
        self._copy_type_prices(source_base_id, new_pl.id)
        self._copy_glass_types(source_base_id, new_pl.id)
        self._copy_hardware(source_base_id, new_pl.id)
        self._copy_closers(source_base_id, new_pl.id)
        
        self.session.commit()
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
        
        glasses = self.session.execute(
            select(GlassType).where(GlassType.price_list_id == from_price_list_id)
        ).scalars().all()
        
        glass_map = {}
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
    
    def get_price_list_by_id(
        self, 
        price_list_id: int, 
        prefer_type: str = "auto"
    ) -> Optional[BasePriceList | PersonalizedPriceList]:
        """Возвращает прайс по ID (базовый или персонализированный)."""
        if prefer_type == "base":
            base_by_id = self.base_repo.get_by_id(price_list_id)
            if base_by_id:
                return base_by_id
            if prefer_type != "auto":
                return None
        elif prefer_type == "personalized":
            pl = self.personal_repo.get_by_id(price_list_id)
            if pl:
                return pl
            if prefer_type != "auto":
                return None
        
        # Auto mode: try both
        if price_list_id >= 1000:
            # Likely personalized
            pl = self.personal_repo.get_by_id(price_list_id)
            if pl:
                return pl
            base_by_id = self.base_repo.get_by_id(price_list_id)
            if base_by_id:
                return base_by_id
        else:
            # Likely base
            base_by_id = self.base_repo.get_by_id(price_list_id)
            if base_by_id:
                return base_by_id
            pl = self.personal_repo.get_by_id(price_list_id)
            if pl:
                return pl
        
        # Not found in either table
        return None

    def update_personalized(self, pl_id: int, data: Dict[str, Any]) -> Optional[PersonalizedPriceList]:
        """Обновляет поля персонализированного прайс-листа."""
        return self.personal_repo.update(pl_id, data)
    
    def update_base_list(self, pl_id: int, data: Dict[str, Any]) -> Optional[BasePriceList]:
        """Обновляет поля базового прайс-листа."""
        return self.base_repo.update(pl_id, data)
    
    def delete_personalized(self, pl_id: int, reassign_to_base: bool = True) -> bool:
        """
        Удаляет персонализированный прайс-лист.
        
        :param pl_id: ID удаляемого прайса
        :param reassign_to_base: Если True, контрагенты переназначаются на базовый прайс
        :return: True если удаление успешно
        """
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
    
    def get_price_for_calculation(self, price_list_id: Optional[int], is_personalized: bool = False) -> Dict[str, float]:
        """
        Возвращает словарь цен для калькулятора, разрешая наследование из базового прайса.
        
        :param price_list_id: ID прайса (None = базовый)
        :param is_personalized: True если ID относится к персонализированному прайсу
        :return: Dict с ключами цен для PriceData
        """
        # Step 1: None -> базовый
        if price_list_id is None:
            base = self.get_base_price_list()
            logger.info(f"get_price_for_calculation: Using BASE (None)")
            return self._extract_prices(base)
        
        # Step 2: Get price list by ID
        logger.info(f"get_price_for_calculation: Looking up ID={price_list_id}, is_personalized={is_personalized}")
        
        if is_personalized:
            price_list = self.personal_repo.get_by_id(price_list_id)
            if not price_list:
                price_list = self.base_repo.get_by_id(price_list_id)
        else:
            price_list = self.base_repo.get_by_id(price_list_id)
            if not price_list:
                price_list = self.personal_repo.get_by_id(price_list_id)
        
        if price_list is None:
            # Not found, fallback to base
            logger.warning(f"get_price_for_calculation: FALLBACK to BASE (ID={price_list_id} not found)")
            return self._extract_prices(self.get_base_price_list())
        
        # Step 3: Check if it's personalized
        from models.price_list import PersonalizedPriceList
        logger.info(f"get_price_for_calculation: Got price_list type={type(price_list).__name__}, id={getattr(price_list, 'id', None)}")
        
        if isinstance(price_list, PersonalizedPriceList):
            logger.info(f"get_price_for_calculation: Using PERSONALIZED (ID={price_list_id}, name={price_list.name})")
            # Get base prices from the referenced base
            base_obj = self.base_repo.get_by_id(price_list.base_price_list_id)
            if not base_obj:
                base_obj = self.get_base_price_list()
            base_prices = self._extract_prices(base_obj)
            
            # Get personalized custom overrides
            custom_fields = self._get_custom_fields(price_list)
            logger.info(f"get_price_for_calculation: custom_fields keys: {list(custom_fields.keys())}")
            logger.info(f"get_price_for_calculation: custom_doors_price_std_single = {custom_fields.get('doors_price_std_single')}")
            
            # Merge: base + custom overrides (only override if value is not None)
            result = dict(base_prices)
            for k, v in custom_fields.items():
                if v is not None:
                    result[k] = v
                    logger.info(f"get_price_for_calculation: Overriding {k} = {v}")
            return result
        else:
            # It's a base price list
            logger.info(f"get_price_for_calculation: Using BASE (ID={price_list_id})")
            return self._extract_prices(price_list)
    
    def _extract_prices(self, pl: BasePriceList | PersonalizedPriceList) -> Dict[str, Optional[float]]:
        """Извлекает числовые поля цен из модели в словарь."""
        fields = [
            # Door prices
            "doors_price_std_single", "doors_price_per_m2_nonstd", "doors_wide_markup",
            "doors_double_std",
            # Hatch prices
            "hatch_std", "hatch_wide_markup", "hatch_per_m2_nonstd",
            # Gate prices
            "gate_per_m2", "gate_large_per_m2",
            # Transom prices
            "transom_per_m2", "transom_min",
            # Hardware prices
            "cutout_price", "deflector_per_m2", "trim_per_lm",
            "closer_price", "hinge_price", "anti_theft_price", "gkl_price", "mount_ear_price",
            "threshold_price",
            # Vent grates
            "vent_grate_tech", "vent_grate_pp",
            # Seal
            "seal_per_m2",
            # Color prices
            "nonstd_color_markup_pct", "diff_color_markup", "moire_price",
            "lacquer_per_m2", "primer_single", "primer_double"
        ]
        result = {}
        for f in fields:
            val = getattr(pl, f, None)
            result[f] = val
        return result
    
    def _get_custom_fields(self, personal: PersonalizedPriceList) -> Dict[str, Optional[float]]:
        """Возвращает словарь custom_ полей для персонализированного прайса."""
        return {
            # Doors
            "doors_price_std_single": personal.custom_doors_price_std_single,
            "doors_price_per_m2_nonstd": personal.custom_doors_price_per_m2_nonstd,
            "doors_wide_markup": personal.custom_doors_wide_markup,
            "doors_double_std": personal.custom_doors_double_std,
            # Hatches
            "hatch_std": personal.custom_hatch_std,
            "hatch_wide_markup": personal.custom_hatch_wide_markup,
            "hatch_per_m2_nonstd": personal.custom_hatch_per_m2_nonstd,
            # Gates
            "gate_per_m2": personal.custom_gate_per_m2,
            "gate_large_per_m2": personal.custom_gate_large_per_m2,
            # Transoms
            "transom_per_m2": personal.custom_transom_per_m2,
            "transom_min": personal.custom_transom_min,
            # Hardware
            "cutout_price": personal.custom_cutout_price,
            "deflector_per_m2": personal.custom_deflector_per_m2,
            "trim_per_lm": personal.custom_trim_per_lm,
            "closer_price": personal.custom_closer_price,
            "hinge_price": personal.custom_hinge_price,
            "anti_theft_price": personal.custom_anti_theft_price,
            "gkl_price": personal.custom_gkl_price,
            "mount_ear_price": personal.custom_mount_ear_price,
            "threshold_price": personal.custom_threshold_price,
            # Vent grates
            "vent_grate_tech": personal.custom_vent_grate_tech,
            "vent_grate_pp": personal.custom_vent_grate_pp,
            # Seal
            "seal_per_m2": personal.custom_seal_per_m2,
            # Color prices
            "nonstd_color_markup_pct": personal.custom_nonstd_color_markup_pct,
            "diff_color_markup": personal.custom_diff_color_markup,
            "moire_price": personal.custom_moire_price,
            "lacquer_per_m2": personal.custom_lacquer_per_m2,
            "primer_single": personal.custom_primer_single,
            "primer_double": personal.custom_primer_double
        }
    
    def get_type_prices(self, price_list_id: int) -> List[Union[TypePrice, CustomTypePrice]]:
        """Возвращает все type-specific цены для прайс-листа.
        
        Для персонализированных прайс-листов читает из CustomTypePrice.
        Для базового прайс-листа читает из TypePrice.
        Сортирует по product_type, subtype для стабильного порядка.
        """
        # Check if it's a personalized price list
        personal = self.personal_repo.get_by_id(price_list_id)
        if personal:
            # Query CustomTypePrice for personalized price lists
            stmt = select(CustomTypePrice).where(CustomTypePrice.price_list_id == price_list_id
                ).order_by(CustomTypePrice.product_type, CustomTypePrice.subtype)
            return list(self.session.execute(stmt).scalars().all())
        else:
            # Query TypePrice for base price list
            stmt = select(TypePrice).where(TypePrice.price_list_id == price_list_id
                ).order_by(TypePrice.product_type, TypePrice.subtype)
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
    ) -> Union[TypePrice, CustomTypePrice]:
        """Создаёт type-specific цену для типа изделия.
        
        Для персонализированных прайс-листов создаёт CustomTypePrice.
        Для базового прайс-листа создаёт TypePrice.
        """
        # Check if it's a personalized price list
        personal = self.personal_repo.get_by_id(price_list_id)
        if personal:
            # Create CustomTypePrice for personalized price lists
            tp = CustomTypePrice(
                price_list_id=price_list_id,
                product_type=product_type,
                subtype=subtype,
                price_std_single=price_std_single,
                price_double_std=price_double_std,
                price_wide_markup=price_wide_markup,
                price_per_m2_nonstd=price_per_m2_nonstd
            )
        else:
            # Create TypePrice for base price list
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
        self.session.commit()
        return tp
    
    def update_type_price(self, tp_id: int, data: Dict[str, Any], price_list_id: Optional[int] = None) -> Optional[Union[TypePrice, CustomTypePrice]]:
        """Обновляет type-specific цену.
        
        Сначала ищет в CustomTypePrice (для персонализированных прайс-листів),
        затем в TypePrice (для базового прайса-листа).
        Если передан price_list_id, проверяет, что запись принадлежит именно этому прайс-листу.
        """
        # First, try to find in CustomTypePrice (personalized price lists)
        stmt = select(CustomTypePrice).where(CustomTypePrice.id == tp_id)
        tp = self.session.execute(stmt).scalar_one_or_none()
        
        # Дополнительная проверка: если передан price_list_id, убеждаемся что запись ему принадлежит
        if tp and price_list_id and tp.price_list_id != price_list_id:
            tp = None  # ID совпал, но это запись от другого прайс-листа
        
        if not tp:
            # Not found in CustomTypePrice, try TypePrice (base price list)
            stmt = select(TypePrice).where(TypePrice.id == tp_id)
            tp = self.session.execute(stmt).scalar_one_or_none()
            
            # Для TypePrice тоже проверяем принадлежность к прайс-листу
            if tp and price_list_id and tp.price_list_id != price_list_id:
                tp = None
        
        if tp:
            for key, value in data.items():
                setattr(tp, key, value)
            self.session.flush()
            self.session.commit()
        return tp
    
    def delete_type_price(self, tp_id: int) -> bool:
        """Удаляет type-specific цену.
        
        Сначала ищет в CustomTypePrice (для персонализированных прайс-листов),
        затем в TypePrice (для базового прайс-листа).
        """
        # First, try to find in CustomTypePrice (personalized price lists)
        stmt = select(CustomTypePrice).where(CustomTypePrice.id == tp_id)
        tp = self.session.execute(stmt).scalar_one_or_none()
        
        if not tp:
            # Not found in CustomTypePrice, try TypePrice (base price list)
            stmt = select(TypePrice).where(TypePrice.id == tp_id)
            tp = self.session.execute(stmt).scalar_one_or_none()
        
        if tp:
            self.session.delete(tp)
            self.session.flush()
            self.session.commit()
            return True
        return False
