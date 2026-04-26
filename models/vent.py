"""Модели типов вентиляционных решёток.

Содержит ORM-модели для:
- VentType: типы вентиляционных решёток (техническая, противопожарная и т.д.)
"""

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class VentType(Base):
    """Тип вентиляционной решётки для дверей/люков.
    
    Представляет различные виды вент.решёток с их характеристиками и ценами.
    
    Attributes:
        id: уникальный идентификатор
        name: название типа решётки (например, "Техническая", "Противопожарная")
        price_per_m2: цена за квадратный метр
        min_price: минимальная цена (если площадь маленькая)
        price_list_id: ссылка на прайс-лист
        
    Relationships:
        price_list: связанный базовый прайс-лист
    """
    __tablename__ = "vent_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price_per_m2: Mapped[float]
    min_price: Mapped[float]
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    price_list = relationship("BasePriceList", back_populates="vent_types")