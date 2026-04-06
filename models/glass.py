"""Модели типов стёкол и их опций."""

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class GlassType(Base):
    __tablename__ = "glass_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price_per_m2: Mapped[float]
    min_price: Mapped[float]
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    price_list = relationship("BasePriceList", back_populates="glass_types")
    options = relationship("GlassOption", back_populates="glass_type", cascade="all, delete-orphan")


class GlassOption(Base):
    __tablename__ = "glass_option"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price_per_m2: Mapped[float]
    min_price: Mapped[float]
    glass_type_id: Mapped[int] = mapped_column(ForeignKey("glass_type.id"))
    glass_type = relationship("GlassType", back_populates="options")