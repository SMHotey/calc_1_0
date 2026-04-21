"""Модели наборов опций (пресетов).

Содержит ORM-модель OptionPreset для сохранения часто используемых
комбинаций опций (стекло, фурнитура, цвет и т.д.).
"""

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON
from db.database import Base


class OptionPreset(Base):
    """Набор опций (пресет).
    
    Позволяет сохранить часто используемую комбинацию опций для быстрого
    применения при расчёте изделия. Например, "Стандартная дверь EI 60"
    или "Элитная дверь с триплексом и доводчиком".
    
    Attributes:
        id: уникальный идентификатор
        name: название пресета
        data: JSON-объект с настройками (тип стекла, фурнитура, цвет RAL и т.д.)
        price_list_id: ссылка на прайс-лист
        
    Relationships:
        price_list: связанный базовый прайс-лист
        
    Пример data:
        {
            "glass_type": "Триплекс 8мм",
            "glass_option": "Пескоструй",
            "lock": "Cisa 15011",
            "closer": "DORMA TS93",
            "color": "8017"
        }
    """
    __tablename__ = "option_preset"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    price_list = relationship("BasePriceList", back_populates="presets")