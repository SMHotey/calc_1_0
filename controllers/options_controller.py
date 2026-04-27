"""Контроллер управления опциями изделий: цвета, стёкла, металл, доп. опции.

Содержит:
- OptionsController: контроллер для работы с опциями изделий
- Управление типами стёкол и их опциями (матировка, плёнки и т.д.)
- Валидация цветов RAL
- Получение доступных толщин металла
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.glass import GlassType, GlassOption
from models.vent import VentType
from models.price_list import BasePriceList, PersonalizedPriceList
from db.database import SessionLocal
from constants import STANDARD_RAL


class OptionsController:
    """Контроллер для работы с опциями изделий.

    Отвечает за:
    - Управление типами стёкол и их опциями
    - Валидацию цветов RAL
    - Получение доступных опций для конфигуратора
    - Толщины металла в зависимости от типа изделия

    Attributes:
        session: SQLAlchemy сессия для работы с БД
        glass_repo: репозиторий для типов стёкол
        glass_opt_repo: репозиторий для опций стёкол
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """Инициализация контроллера.

        Args:
            session: опциональная сессия БД. Если не передана - создаётся новая.
        """
        self.session = session or SessionLocal()
        self.glass_repo = BaseRepository(self.session, GlassType)
        self.glass_opt_repo = BaseRepository(self.session, GlassOption)

    # === Стекла ===

    def create_glass_type(
            self,
            name: str,
            price_per_m2: float,
            min_price: float,
            price_list_id: int
    ) -> GlassType:
        """Добавляет новый тип стекла в прайс-лист.

        Args:
            name: название типа стекла
            price_per_m2: цена за м²
            min_price: минимальная цена
            price_list_id: ID прайс-листа

        Returns:
            Созданный объект GlassType
        """
        glass = GlassType(
            name=name,
            price_per_m2=price_per_m2,
            min_price=min_price,
            price_list_id=price_list_id
        )
        return self.glass_repo.create(glass)

    def update_glass_type(self, glass_id: int, data: Dict[str, Any]) -> Optional[GlassType]:
        """Обновляет параметры типа стекла.

        Args:
            glass_id: ID типа стекла
            data: словарь с полями для обновления

        Returns:
            Обновлённый объект GlassType или None
        """
        return self.glass_repo.update(glass_id, data)

    def delete_glass_type(self, glass_id: int) -> bool:
        """Удаляет тип стекла.

        При удалении типа стекла каскадно удаляются все связанные опции.

        Args:
            glass_id: ID типа стекла

        Returns:
            True если удаление успешно
        """
        return self.glass_repo.delete(glass_id)

    def get_glass_types(self, price_list_id: int) -> List[Dict[str, Any]]:
        """Возвращает список типов стёкол для выбора в конфигураторе.

        Args:
            price_list_id: ID прайс-листа

        Returns:
            Список словарей с данными типов стёкол и их опций
        """
        stmt = select(GlassType).where(GlassType.price_list_id == price_list_id)
        glasses = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": g.id,
                "name": g.name,
                "price_per_m2": g.price_per_m2,
                "min_price": g.min_price,
                "options": [
                    {"id": o.id, "name": o.name, "price_per_m2": o.price_per_m2, "min_price": o.min_price}
                    for o in g.options
                ]
            }
            for g in glasses
        ]

    def get_vent_types(self, price_list_id: int) -> List[Dict[str, Any]]:
        """Возвращает список типов вентиляционных решёток.

        Args:
            price_list_id: ID прайс-листа

        Returns:
            Список словарей с данными типов решёток
        """
        stmt = select(VentType).where(VentType.price_list_id == price_list_id)
        vents = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": v.id,
                "name": v.name,
                "price_per_m2": v.price_per_m2,
                "min_price": v.min_price,
            }
            for v in vents
        ]

    def create_glass_option(
            self,
            name: str,
            price_per_m2: float,
            min_price: float,
            glass_type_id: int | None = None
    ) -> GlassOption:
        """Добавляет опцию к стеклу или глобальную опцию.

        Если glass_type_id указан - опция привязана к конкретному типу стекла.
        Если glass_type_id = None - опция глобальная (доступна для всех стёкол).

        Args:
            name: название опции
            price_per_m2: цена за м²
            min_price: минимальная цена
            glass_type_id: ID типа стекла (None для глобальной опции)

        Returns:
            Созданный объект GlassOption
        """
        opt = GlassOption(
            name=name,
            price_per_m2=price_per_m2,
            min_price=min_price,
            glass_type_id=glass_type_id
        )
        return self.glass_opt_repo.create(opt)

    def update_glass_option(self, option_id: int, data: Dict[str, Any]) -> Optional[GlassOption]:
        """Обновляет параметры опции стекла.

        Args:
            option_id: ID опции
            data: словарь с полями для обновления

        Returns:
            Обновлённый объект GlassOption или None
        """
        return self.glass_opt_repo.update(option_id, data)

    def delete_glass_option(self, option_id: int) -> bool:
        """Удаляет опцию стекла.

        Args:
            option_id: ID опции

        Returns:
            True если удаление успешно
        """
        return self.glass_opt_repo.delete(option_id)

    def get_all_glass_options(self, price_list_id: int | None = None) -> List[Dict[str, Any]]:
        """Возвращает все глобальные опции стёкол (не привязанные к типу).

        Args:
            price_list_id: ID прайс-листа (используется для фильтрации, опционально)

        Returns:
            Список словарей с данными глобальных опций
        """
        stmt = select(GlassOption).where(GlassOption.glass_type_id.is_(None))
        if price_list_id:
            # Также получаем опции привязанные к стёклам текущего прайс-листа
            stmt = select(GlassOption).outerjoin(GlassType).where(
                (GlassOption.glass_type_id.is_(None)) |
                (GlassType.price_list_id == price_list_id)
            )
        options = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": o.id,
                "name": o.name,
                "price_per_m2": o.price_per_m2,
                "min_price": o.min_price,
                "is_global": o.glass_type_id is None
            }
            for o in options
        ]

    def get_global_glass_options(self) -> List[Dict[str, Any]]:
        """Возвращает только глобальные опции стёкол.

        Returns:
            Список словарей с данными глобальных опций
        """
        stmt = select(GlassOption).where(GlassOption.glass_type_id.is_(None))
        options = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": o.id,
                "name": o.name,
                "price_per_m2": o.price_per_m2,
                "min_price": o.min_price,
                "short_name_kp": o.short_name_kp,
                "short_name_prod": o.short_name_prod,
            }
            for o in options
        ]

    @staticmethod
    def validate_ral(color_value: int | str) -> tuple[bool, str]:
        """Проверяет, является ли цвет стандартным RAL из списка.

        Args:
            color_value: значение цвета (число или строка)

        Returns:
            Кортеж (валидность, тип):
            - (True, "standard") - стандартный цвет RAL
            - (False, "non_standard") - нестандартный цвет
        """
        if isinstance(color_value, int) and color_value in STANDARD_RAL:
            return True, "standard"
        if isinstance(color_value, str) and color_value.isdigit() and int(color_value) in STANDARD_RAL:
            return True, "standard"
        return False, "non_standard"

    @staticmethod
    def get_standard_ral_list() -> List[int]:
        """Возвращает список стандартных цветов RAL.

        Returns:
            Список кодов RAL
        """
        return STANDARD_RAL.copy()

    @staticmethod
    def get_available_thicknesses(is_apartment_or_single: bool) -> List[Dict[str, Any]]:
        """Возвращает доступные варианты толщины металла.

        В зависимости от типа изделия (квартирная/однолистовая или нет)
        доступны разные варианты толщины.

        Args:
            is_apartment_or_single: True для квартирных/однолистовых изделий

        Returns:
            Список словарей с вариантами толщины:
            - value: значение для сохранения
            - label: отображаемый текст
            - markup_pct: процент наценки за эту толщину
        """
        if is_apartment_or_single:
            # Односторонняя конструкция
            return [
                {"value": "1.0", "label": "1.0 мм (базовая)", "markup_pct": 0},
                {"value": "1.2", "label": "1.2 мм", "markup_pct": 5},
                {"value": "1.5", "label": "1.5 мм", "markup_pct": 12}
            ]
        # Двусторонняя конструкция (указывается для внешней и внутренней стороны)
        return [
            {"value": "1.0-1.0", "label": "1.0/1.0 мм (базовая)", "markup_pct": 0},
            {"value": "1.2-1.4", "label": "1.2/1.4 мм", "markup_pct": 5},
            {"value": "1.4-1.4", "label": "1.4/1.4 мм", "markup_pct": 8},
            {"value": "1.5-1.5", "label": "1.5/1.5 мм", "markup_pct": 12},
            {"value": "1.4-2.0", "label": "1.4/2.0 мм", "markup_pct": 15}
        ]
