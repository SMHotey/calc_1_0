"""Контроллер управления опциями изделий: цвета, стёкла, металл, доп. опции."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.glass import GlassType, GlassOption
from models.price_list import BasePriceList, PersonalizedPriceList
from db.database import SessionLocal
from constants import STANDARD_RAL


class OptionsController:
    """
    Контроллер для работы с опциями изделий.

    Отвечает за:
    - Управление типами стёкол и их опциями (п.5.2)
    - Валидацию цветов RAL
    - Получение доступных опций для конфигуратора
    """

    def __init__(self, session: Optional[Session] = None) -> None:
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
        """Добавляет новый тип стекла в прайс-лист."""
        glass = GlassType(
            name=name,
            price_per_m2=price_per_m2,
            min_price=min_price,
            price_list_id=price_list_id
        )
        return self.glass_repo.create(glass)

    def update_glass_type(self, glass_id: int, data: Dict[str, Any]) -> Optional[GlassType]:
        """Обновляет параметры типа стекла."""
        return self.glass_repo.update(glass_id, data)

    def delete_glass_type(self, glass_id: int) -> bool:
        """Удаляет тип стекла (каскадно удалятся опции)."""
        return self.glass_repo.delete(glass_id)

    def get_glass_types(self, price_list_id: int) -> List[Dict[str, Any]]:
        """Возвращает список типов стёкол для выбора."""
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

    def create_glass_option(
            self,
            glass_type_id: int,
            name: str,
            price_per_m2: float,
            min_price: float
    ) -> GlassOption:
        """Добавляет опцию к конкретному типу стекла."""
        opt = GlassOption(
            name=name,
            price_per_m2=price_per_m2,
            min_price=min_price,
            glass_type_id=glass_type_id
        )
        return self.glass_opt_repo.create(opt)

    @staticmethod
    def validate_ral(color_value: int | str) -> tuple[bool, str]:
        """Проверяет, является ли цвет стандартным RAL из списка."""
        if isinstance(color_value, int) and color_value in STANDARD_RAL:
            return True, "standard"
        if isinstance(color_value, str) and color_value.isdigit() and int(color_value) in STANDARD_RAL:
            return True, "standard"
        return False, "non_standard"

    @staticmethod
    def get_standard_ral_list() -> List[int]:
        """Возвращает список стандартных цветов RAL."""
        return STANDARD_RAL.copy()

    @staticmethod
    def get_available_thicknesses(is_apartment_or_single: bool) -> List[Dict[str, Any]]:
        """
        Возвращает доступные варианты толщины металла.

        :param is_apartment_or_single: Для квартирных/однолистовых — одна толщина
        """
        if is_apartment_or_single:
            return [
                {"value": "1.0", "label": "1.0 мм (базовая)", "markup_pct": 0},
                {"value": "1.2", "label": "1.2 мм", "markup_pct": 5},
                {"value": "1.5", "label": "1.5 мм", "markup_pct": 12}
            ]
        return [
            {"value": "1.0-1.0", "label": "1.0/1.0 мм (базовая)", "markup_pct": 0},
            {"value": "1.2-1.4", "label": "1.2/1.4 мм", "markup_pct": 5},
            {"value": "1.4-1.4", "label": "1.4/1.4 мм", "markup_pct": 8},
            {"value": "1.5-1.5", "label": "1.5/1.5 мм", "markup_pct": 12},
            {"value": "1.4-2.0", "label": "1.4/2.0 мм", "markup_pct": 15}
        ]


def __enter__(self):
    return self


def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type:
        self.session.rollback()
    self.session.close()