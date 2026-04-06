"""Модели прайс-листов: базовый и персонализированные."""

from typing import Optional
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class TypePrice(Base):
    """Цены для конкретного типа изделия (подтип продукта)."""
    __tablename__ = "type_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    product_type: Mapped[str] = mapped_column(String(50))
    subtype: Mapped[str] = mapped_column(String(50))
    price_std_single: Mapped[float] = mapped_column(Float, default=0.0)
    price_double_std: Mapped[float] = mapped_column(Float, default=0.0)
    price_wide_markup: Mapped[float] = mapped_column(Float, default=0.0)
    price_per_m2_nonstd: Mapped[float] = mapped_column(Float, default=0.0)

    price_list = relationship("BasePriceList", back_populates="type_prices")


class BasePriceList(Base):
    """Базовый системный прайс-лист. Хранит эталонные цены и правила."""
    __tablename__ = "base_price_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Цены по умолчанию (если нет type-specific)
    doors_price_std_single: Mapped[float] = mapped_column(Float, default=0.0)
    doors_price_per_m2_nonstd: Mapped[float] = mapped_column(Float, default=0.0)
    doors_wide_markup: Mapped[float] = mapped_column(Float, default=0.0)
    doors_double_std: Mapped[float] = mapped_column(Float, default=0.0)
    hatch_std: Mapped[float] = mapped_column(Float, default=0.0)
    hatch_wide_markup: Mapped[float] = mapped_column(Float, default=0.0)
    hatch_per_m2_nonstd: Mapped[float] = mapped_column(Float, default=0.0)
    gate_per_m2: Mapped[float] = mapped_column(Float, default=0.0)
    gate_large_per_m2: Mapped[float] = mapped_column(Float, default=0.0)
    transom_per_m2: Mapped[float] = mapped_column(Float, default=0.0)
    transom_min: Mapped[float] = mapped_column(Float, default=0.0)
    cutout_price: Mapped[float] = mapped_column(Float, default=0.0)
    deflector_per_m2: Mapped[float] = mapped_column(Float, default=0.0)
    trim_per_lm: Mapped[float] = mapped_column(Float, default=0.0)
    closer_price: Mapped[float] = mapped_column(Float, default=0.0)
    hinge_price: Mapped[float] = mapped_column(Float, default=0.0)
    anti_theft_price: Mapped[float] = mapped_column(Float, default=0.0)
    gkl_price: Mapped[float] = mapped_column(Float, default=0.0)
    mount_ear_price: Mapped[float] = mapped_column(Float, default=0.0)

    # Связи
    type_prices = relationship("TypePrice", back_populates="price_list", cascade="all, delete-orphan")
    glass_types = relationship("GlassType", back_populates="price_list", cascade="all, delete-orphan")
    hardware = relationship("HardwareItem", back_populates="price_list", cascade="all, delete-orphan")
    presets = relationship("OptionPreset", back_populates="price_list")


class PersonalizedPriceList(Base):
    """Персонализированный прайс-лист. Копия базового с возможностью изменения."""
    __tablename__ = "personalized_price_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    base_price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    custom_doors_price_std_single: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    custom_doors_price_per_m2_nonstd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    custom_doors_wide_markup: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    custom_cutout_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    base_price_list = relationship("BasePriceList")


class CustomTypePrice(Base):
    """Переопределённые цены для типов в персонализированном прайсе."""
    __tablename__ = "custom_type_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("personalized_price_list.id"))
    product_type: Mapped[str] = mapped_column(String(50))
    subtype: Mapped[str] = mapped_column(String(50))
    price_std_single: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_double_std: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_wide_markup: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_per_m2_nonstd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    price_list = relationship("PersonalizedPriceList")