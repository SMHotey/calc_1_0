"""Модели прайс-листов: базовый и персонализированные.

Содержит ORM-модели для:
- TypePrice: цены по типам продукции (двери, люки и т.д.)
- BasePriceList: базовый системный прайс-лист с эталонными ценами
- PersonalizedPriceList: персонализированный прайс-лист для контрагентов
- CustomTypePrice: предопределённые цены для конкретного подтипа в персонализированном прайсе
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class TypePrice(Base):
    """Цены для конкретного типа изделия (подтип продукта).
    
    Позволяет задавать разные цены для разных подтипов продукции
    (например, "Дверь Техническая" vs "Дверь EI 60").
    
    Attributes:
        id: уникальный идентификатор
        price_list_id: ссылка на прайс-лист
        product_type: тип продукции (Дверь, Люк, Ворота, Фрамуга)
        subtype: подтип (Техническая, EI 60 и т.д.)
        price_std_single: цена одностворчатой стандартной двери
        price_double_std: цена двухстворчатой стандартной двери
        price_wide_markup: наценка за широкий проём
        price_per_m2_nonstd: цена за м² нестандартного изделия
    """
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
    """Базовый системный прайс-лист. Хранит эталонные цены и правила.
    
    Основной справочник цен, используемый при расчёте.
    Содержит цены по умолчанию для всех типов изделий и комплектующих.
    
    Attributes:
        id: уникальный идентификатор
        name: название прайс-листа
        created_at: дата создания
        updated_at: дата последнего обновления
        
    Цены на двери:
        doors_price_std_single: цена одностворчатой стандартной двери
        doors_price_per_m2_nonstd: цена за м² нестандартной двери
        doors_wide_markup: наценка за широкий проём
        doors_double_std: цена двухстворчатой стандартной двери
        
    Цены на люки:
        hatch_std: базовая цена люка
        hatch_wide_markup: наценка за широкий проём
        hatch_per_m2_nonstd: цена за м² нестандартного люка
        
    Цены на ворота:
        gate_per_m2: цена за м² стандартных ворот
        gate_large_per_m2: цена за м² больших ворот
        
    Цены на фрамуги:
        transom_per_m2: цена за м² фрамуги
        transom_min: минимальная цена фрамуги
        
    Цены на комплектующие:
        cutout_price: цена за вырез (проём)
        deflector_per_m2: цена отбойной пластины за м²
        trim_per_lm: цена добора за п.м.
        closer_price: цена доводчика
        hinge_price: цена петли
        anti_theft_price: цена противосъёмного механизма
        gkl_price: цена ГКЛ (гипсокартон)
        mount_ear_price: цена монтажной ушки
    """
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
    threshold_price: Mapped[float] = mapped_column(Float, default=2500.0)

    # Цвета и покрытия
    nonstd_color_markup_pct: Mapped[float] = mapped_column(Float, default=7.0)  # 7%
    diff_color_markup: Mapped[float] = mapped_column(Float, default=2000.0)
    moire_price: Mapped[float] = mapped_column(Float, default=2040.0)
    lacquer_per_m2: Mapped[float] = mapped_column(Float, default=1020.0)
    primer_single: Mapped[float] = mapped_column(Float, default=2550.0)
    primer_double: Mapped[float] = mapped_column(Float, default=5100.0)
    
    # Вентрешётки
    vent_grate_tech: Mapped[float] = mapped_column(Float, default=0.0)  # Тех. вентрешётка
    vent_grate_pp: Mapped[float] = mapped_column(Float, default=0.0)

    # Уплотнитель
    seal_per_m2: Mapped[float] = mapped_column(Float, default=150.0)  # Цена за м.п.

    # Связи
    type_prices = relationship("TypePrice", back_populates="price_list", cascade="all, delete-orphan")
    glass_types = relationship("GlassType", back_populates="price_list", cascade="all, delete-orphan")
    vent_types = relationship("VentType", back_populates="price_list", cascade="all, delete-orphan")
    hardware = relationship("HardwareItem", back_populates="price_list", cascade="all, delete-orphan")
    closers = relationship("Closer", back_populates="price_list", cascade="all, delete-orphan")
    coordinators = relationship("Coordinator", back_populates="price_list", cascade="all, delete-orphan")


class PersonalizedPriceList(Base):
    """Персонализированный прайс-лист. Копия базового с возможностью изменения.
    
    Создаётся для конкретного контрагента. Позволяет переопределить часть цен
    от базового прайс-листа. Если цена не указана (NULL),
    используется значение из базового прайса.
    
    Attributes:
        id: уникальный идентификатор
        name: название персонализированного прайс-листа
        base_price_list_id: ссылка на базовый прайс-лист
        created_at: дата создания
        updated_at: дата последнего обновления
        
    Предопределённые цены (могут быть NULL - тогда берётся из базового):
        custom_doors_price_std_single: своя цена одностворчатой двери
        custom_doors_price_per_m2_nonstd: своя цена нестандартной двери
        custom_doors_wide_markup: своя наценка за ширину
        custom_cutout_price: своя цена выреза
    """
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
    """Предопределённые цены для типов в персонализированном прайсе.
    
    Позволяет задавать индивидуальные цены для конкретных подтипов продукции
    в рамках персонализированного прайс-листа.
    
    Attributes:
        id: уникальный идентификатор
        price_list_id: ссылка на персонализированный прайс-лист
        product_type: тип продукции
        subtype: подтип
        price_std_single: своя цена одностворчатой (может быть NULL)
        price_double_std: своя цена двухстворчатой (может быть NULL)
        price_wide_markup: своя наценка за ширину (может быть NULL)
        price_per_m2_nonstd: своя цена за м² (может быть NULL)
    """
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