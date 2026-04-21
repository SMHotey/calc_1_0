"""Модели доводчиков и координаторов закрывания.

Содержит ORM-модели для:
- Closer: доводчики с ценой по весу двери
- Coordinator: координаторы закрывания
"""

from datetime import datetime
from sqlalchemy import String, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class Closer(Base):
    """Доводчик с привязкой к весу двери.
    
    Attributes:
        id: уникальный идентификатор
        price_list_id: ссылка на прайс-лист
        name: наименование доводчика
        door_weight: вес двери (кг)
        price: цена
    """
    __tablename__ = "closer"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    name: Mapped[str] = mapped_column(String(100))
    door_weight: Mapped[float] = mapped_column(Float, default=0.0)
    price: Mapped[float] = mapped_column(Float, default=0.0)

    price_list = relationship("BasePriceList", back_populates="closers")


class Coordinator(Base):
    """Координатор закрывания.
    
    Attributes:
        id: уникальный идентификатор
        price_list_id: ссылка на прайс-лист
        name: наименование координатора
        price: цена
    """
    __tablename__ = "coordinator"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float, default=0.0)

    price_list = relationship("BasePriceList", back_populates="coordinators")