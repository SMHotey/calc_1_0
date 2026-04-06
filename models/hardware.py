"""Модели фурнитуры (замки, ручки, цилиндры)."""

from sqlalchemy import String, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class HardwareItem(Base):
    __tablename__ = "hardware_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50))  # lock, handle, cylinder
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[float]
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    has_cylinder: Mapped[bool] = mapped_column(Boolean, default=False)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    price_list = relationship("BasePriceList", back_populates="hardware")