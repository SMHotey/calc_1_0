"""Контроллер наборов опций (пресетов): сохранение и применение конфигураций."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.option_preset import OptionPreset
from db.database import SessionLocal


class PresetController:
    """
    Контроллер для работы с наборами опций (пресетами).

    Отвечает за:
    - Сохранение текущей конфигурации опций под именем
    - Применение пресета к изделию (замена опций)
    - CRUD пресетов в рамках прайс-листа
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session or SessionLocal()
        self.repo = BaseRepository(self.session, OptionPreset)

    def create_preset(
            self,
            name: str,
            price_list_id: int,
            options_data: Dict[str, Any]
    ) -> OptionPreset:
        """
        Создаёт новый пресет с сериализованными опциями.
        """
        preset = OptionPreset(
            name=name,
            data=options_data,
            price_list_id=price_list_id
        )
        return self.repo.create(preset)

    def apply_preset(self, preset_id: int, current_options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Применяет пресет к текущим опциям изделия.
        """
        preset = self.repo.get_by_id(preset_id)
        if not preset:
            raise ValueError("Пресет не найден")

        preserved = {
            "product_type": current_options.get("product_type"),
            "subtype": current_options.get("subtype"),
            "height": current_options.get("height"),
            "width": current_options.get("width"),
            "quantity": current_options.get("quantity", 1)
        }
        return {**preset.data, **preserved}

    def get_presets_for_price_list(self, price_list_id: int) -> List[Dict[str, Any]]:
        """Возвращает список пресетов для выбора."""
        stmt = select(OptionPreset).where(OptionPreset.price_list_id == price_list_id)
        presets = self.session.execute(stmt).scalars().all()
        return [{"id": p.id, "name": p.name} for p in presets]

    def update_preset(self, preset_id: int, data: Dict[str, Any]) -> Optional[OptionPreset]:
        """Обновляет название или данные пресета."""
        return self.repo.update(preset_id, data)

    def delete_preset(self, preset_id: int) -> bool:
        """Удаляет пресет."""
        return self.repo.delete(preset_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()
