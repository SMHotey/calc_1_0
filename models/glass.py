"""Модели типов стёкол и их опций.

Содержит ORM-модели для:
- GlassType: типы стёкол (армированное, закалённое, триплекс и т.д.)
- GlassOption: дополнительные опции для стёкол (матировка, плёнки и т.д.)
"""

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class GlassType(Base):
    """Тип стекла для остекления дверей/люков.
    
    Представляет различные виды стёкол с их характеристиками и ценами.
    
    Attributes:
        id: уникальный идентификатор
        name: название типа стекла (например, "Армированное 4мм")
        price_per_m2: цена за квадратный метр
        min_price: минимальная цена (если площадь маленькая)
        price_list_id: ссылка на прайс-лист
        
    Relationships:
        price_list: связанный базовый прайс-лист
        options: дополнительные опции для этого типа стекла
    """
    __tablename__ = "glass_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price_per_m2: Mapped[float]
    min_price: Mapped[float]
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    price_list = relationship("BasePriceList", back_populates="glass_types")
    options = relationship("GlassOption", back_populates="glass_type", cascade="all, delete-orphan")


class GlassOption(Base):
    """Дополнительная опция для стекла (матировка, плёнка, пескоструй и т.д.).
    
    Опции могут быть как привязаны к конкретному типу стекла, так и глобальными
    (glass_type_id = None) - для использования со всеми типами стёкол.
    
    Attributes:
        id: уникальный идентификатор
        name: название опции (например, "Матировка", "Пескоструй")
        price_per_m2: цена за квадратный метр
        min_price: минимальная цена
        glass_type_id: ссылка на тип стекла (nullable для глобальных опций)
        
    Relationships:
        glass_type: связанный тип стекла (если привязана)
    """
    __tablename__ = "glass_option"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price_per_m2: Mapped[float]
    min_price: Mapped[float]
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    glass_type_id: Mapped[int | None] = mapped_column(ForeignKey("glass_type.id"), nullable=True)
    glass_type = relationship("GlassType", back_populates="options")