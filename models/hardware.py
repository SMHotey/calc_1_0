"""Модели фурнитуры (замки, ручки, цилиндры, доводчики).

Содержит ORM-модель HardwareItem для хранения информации о дверной фурнитуре:
замках, ручках, цилиндровых механизмах, доводчиках и т.д.
"""

from sqlalchemy import String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class HardwareItem(Base):
    """Элемент дверной фурнитуры.
    
    Хранит информацию о замках, ручках, цилиндрах, доводчиках и других комплектующих.
    
    Attributes:
        id: уникальный идентификатор
        type: тип фурнитуры (Замок, Ручка, Цилиндровый механизм, Доводчик)
        name: название/модель (например, "Cisa 15011", "DORMA TS93")
        price: цена в рублях
        description: описание товара (может быть NULL)
        image_path: путь к изображению (может быть NULL)
        has_cylinder: требует ли замок цилиндра (для типа "Замок")
        price_list_id: ссылка на прайс-лист
        
    Relationships:
        price_list: связанный базовый прайс-лист
    """
    __tablename__ = "hardware_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))  # lock, handle, cylinder
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float]
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    has_cylinder: Mapped[bool] = mapped_column(Boolean, default=False)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    price_list = relationship("BasePriceList", back_populates="hardware")