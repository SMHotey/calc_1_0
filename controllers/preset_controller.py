"""Контроллер наборов опций (пресетов): сохранение и применение конфигураций.

Содержит:
- PresetController: контроллер для работы с наборами опций (пресетами)
- Сохранение текущей конфигурации опций под именем
- Применение пресета к изделию (замена опций)
- CRUD пресетов в рамках прайс-листа
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.option_preset import OptionPreset
from db.database import SessionLocal


class PresetController:
    """Контроллер для работы с наборами опций (пресетами).

    Отвечает за:
    - Сохранение текущей конфигурации опций под именем
    - Применение пресета к изделию (замена опций)
    - CRUD пресетов в рамках прайс-листа
    - Создание часто используемых конфигураций

    Attributes:
        session: SQLAlchemy сессия для работы с БД
        repo: базовый репозиторий для CRUD операций
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """Инициализация контроллера.

        Args:
            session: опциональная сессия БД. Если не передана - создаётся новая.
        """
        self.session = session or SessionLocal()
        self.repo = BaseRepository(self.session, OptionPreset)

    def create_preset(
            self,
            name: str,
            price_list_id: int,
            options_data: Dict[str, Any]
    ) -> OptionPreset:
        """Создаёт новый пресет с сериализованными опциями.

        Пресет сохраняет полную конфигурацию изделия: тип стекла, фурнитуру,
        цвет, толщину металла и другие опции.

        Args:
            name: название пресета
            price_list_id: ID прайс-листа
            options_data: словарь с опциями изделия (JSON)

        Returns:
            Созданный объект OptionPreset

        Example options_data:
            {
                "glass_type": "Триплекс 8мм",
                "lock": "Cisa 15011",
                "closer": "DORMA TS93",
                "color_external": 8017,
                "color_internal": 7035,
                "metal_thickness": "1.2-1.4"
            }
        """
        preset = OptionPreset(
            name=name,
            data=options_data,
            price_list_id=price_list_id
        )
        return self.repo.create(preset)

    def apply_preset(self, preset_id: int, current_options: Dict[str, Any]) -> Dict[str, Any]:
        """Применяет пресет к текущим опциям изделия.

        Основные параметры изделия (тип, подтип, размеры, количество) сохраняются,
        остальные опции заменяются из пресета.

        Args:
            preset_id: ID пресета
            current_options: текущие опции изделия

        Returns:
            Объединённый словарь (базовые параметры + опции из пресета)

        Raises:
            ValueError: если пресет не найден
        """
        preset = self.repo.get_by_id(preset_id)
        if not preset:
            raise ValueError("Пресет не найден")

        # Сохраняем базовые параметры изделия
        preserved = {
            "product_type": current_options.get("product_type"),
            "subtype": current_options.get("subtype"),
            "height": current_options.get("height"),
            "width": current_options.get("width"),
            "quantity": current_options.get("quantity", 1)
        }
        # Накладываем опции пресета поверху
        return {**preset.data, **preserved}

    def get_presets_for_price_list(self, price_list_id: int) -> List[Dict[str, Any]]:
        """Возвращает список пресетов для выбора в UI.

        Args:
            price_list_id: ID прайс-листа

        Returns:
            Список словарей с id и name пресетов
        """
        stmt = select(OptionPreset).where(OptionPreset.price_list_id == price_list_id)
        presets = self.session.execute(stmt).scalars().all()
        return [{"id": p.id, "name": p.name} for p in presets]

    def update_preset(self, preset_id: int, data: Dict[str, Any]) -> Optional[OptionPreset]:
        """Обновляет название или данные пресета.

        Args:
            preset_id: ID пресета
            data: словарь с полями для обновления (name и/или data)

        Returns:
            Обновлённый объект OptionPreset или None
        """
        return self.repo.update(preset_id, data)

    def delete_preset(self, preset_id: int) -> bool:
        """Удаляет пресет.

        Args:
            preset_id: ID пресета

        Returns:
            True если удаление успешно
        """
        return self.repo.delete(preset_id)

    def __enter__(self):
        """Контекстный менеджер - вход."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход (закрытие сессии)."""
        if exc_type:
            self.session.rollback()
        self.session.close()
