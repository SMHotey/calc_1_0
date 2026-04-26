"""Контроллер для управления пресетами (наборами опций)."""
from typing import Optional
from sqlalchemy.orm import Session
from models.preset import Preset
from controllers.base_controller import BaseController


class PresetController(BaseController):
    """Контроллер для работы с пресетами.

    Позволяет создавать, получать, обновлять и удалять пресеты,
    а также применять их к конфигурациям изделий.
    """

    def __init__(self, session: Optional[Session] = None):
        """Инициализация контроллера пресетов.

        Args:
            session: опциональная сессия БД. Если не передана - создаётся новая.
        """
        super().__init__(Preset, session)

    def create_preset(self, name: str, price_list_id: int, options_data: dict) -> Preset:
        """Создаёт новый пресет с заданными опциями.

        Args:
            name: название пресета
            price_list_id: ID прайс-листа, к которому относится пресет
            options_data: словарь с опциями (например, {"color": "RAL 7035", "metal": "1.5-1.5"})

        Returns:
            Созданный объект пресета
        """
        import json
        preset = self.create(
            name=name,
            price_list_id=price_list_id,
            options_data=json.dumps(options_data, ensure_ascii=False)
        )
        return preset

    def apply_preset(self, preset_id: int, current_dict: dict) -> dict:
        """Применяет пресет к текущей конфигурации.

        Args:
            preset_id: ID пресета для применения
            current_dict: текущая конфигурация изделия (словарь с параметрами)

        Returns:
            Новый словарь конфигурации с применёнными опциями из пресета
        """
        preset = self.get_by_id(preset_id)
        if not preset:
            return current_dict

        options = preset.get_options_dict()
        # Создаём копию текущего словаря, чтобы не изменять исходный
        result = current_dict.copy()
        # Применяем опции из пресета, перезаписывая существующие значения
        for key, value in options.items():
            result[key] = value
        return result