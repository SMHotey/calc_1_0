"""РњРѕРґРµР»Рё РїСЂР°Р№СЃ-Р»РёСЃС‚РѕРІ: Р±Р°Р·РѕРІС‹Р№ Рё РїРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅС‹Рµ.

РЎРѕРґРµСЂР¶РёС‚ ORM-РјРѕРґРµР»Рё РґР»СЏ:
- TypePrice: С†РµРЅС‹ РїРѕ С‚РёРїР°Рј РїСЂРѕРґСѓРєС†РёРё (РґРІРµСЂРё, Р»СЋРєРё Рё С‚.Рґ.)
- BasePriceList: Р±Р°Р·РѕРІС‹Р№ СЃРёСЃС‚РµРјРЅС‹Р№ РїСЂР°Р№СЃ-Р»РёСЃС‚ СЃ СЌС‚Р°Р»РѕРЅРЅС‹РјРё С†РµРЅР°РјРё
- PersonalizedPriceList: РїРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅС‹Р№ РїСЂР°Р№СЃ-Р»РёСЃС‚ РґР»СЏ РєРѕРЅС‚СЂР°РіРµРЅС‚РѕРІ
- CustomTypePrice: РїРµСЂРµРѕРїСЂРµРґРµР»С‘РЅРЅС‹Рµ С†РµРЅС‹ РґР»СЏ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ РїРѕРґС‚РёРїР° РІ РїРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅРѕРј РїСЂР°Р№СЃРµ
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import String, Float, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class TypePrice(Base):
    """Р¦РµРЅС‹ РґР»СЏ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ С‚РёРїР° РёР·РґРµР»РёСЏ (РїРѕРґС‚РёРї РїСЂРѕРґСѓРєС‚Р°).
    
    РџРѕР·РІРѕР»СЏРµС‚ Р·Р°РґР°РІР°С‚СЊ СЂР°Р·РЅС‹Рµ С†РµРЅС‹ РґР»СЏ СЂР°Р·РЅС‹С… РїРѕРґС‚РёРїРѕРІ РїСЂРѕРґСѓРєС†РёРё
    (РЅР°РїСЂРёРјРµСЂ, "Р”РІРµСЂСЊ РўРµС…РЅРёС‡РµСЃРєР°СЏ" vs "Р”РІРµСЂСЊ EI 60").
    
    Attributes:
        id: СѓРЅРёРєР°Р»СЊРЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ
        price_list_id: СЃСЃС‹Р»РєР° РЅР° РїСЂР°Р№СЃ-Р»РёСЃС‚
        product_type: С‚РёРї РїСЂРѕРґСѓРєС†РёРё (Р”РІРµСЂСЊ, Р›СЋРє, Р’РѕСЂРѕС‚Р°, Р¤СЂР°РјСѓРіР°)
        subtype: РїРѕРґС‚РёРї (РўРµС…РЅРёС‡РµСЃРєР°СЏ, EI 60 Рё С‚.Рґ.)
        price_std_single: С†РµРЅР° РѕРґРЅРѕР»РёСЃС‚РѕРІРѕР№ СЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        price_double_std: С†РµРЅР° РґРІСѓСЃС‚РІРѕСЂС‡Р°С‚РѕР№ СЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        price_wide_markup: РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРѕРєРёР№ РїСЂРѕС‘Рј
        price_per_m2_nonstd: С†РµРЅР° Р·Р° РјВІ РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅРѕРіРѕ РёР·РґРµР»РёСЏ
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
    """Р‘Р°Р·РѕРІС‹Р№ СЃРёСЃС‚РµРјРЅС‹Р№ РїСЂР°Р№СЃ-Р»РёСЃС‚. РҐСЂР°РЅРёС‚ СЌС‚Р°Р»РѕРЅРЅС‹Рµ С†РµРЅС‹ Рё РїСЂР°РІРёР»Р°.
    
    РћСЃРЅРѕРІРЅРѕР№ СЃРїСЂР°РІРѕС‡РЅРёРє С†РµРЅ, РёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ РїСЂРё СЂР°СЃС‡С‘С‚Р°С….
    РЎРѕРґРµСЂР¶РёС‚ С†РµРЅС‹ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ РґР»СЏ РІСЃРµС… С‚РёРїРѕРІ РёР·РґРµР»РёР№ Рё РєРѕРјРїР»РµРєС‚СѓСЋС‰РёС….
    
    Attributes:
        id: СѓРЅРёРєР°Р»СЊРЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ
        name: РЅР°Р·РІР°РЅРёРµ РїСЂР°Р№СЃ-Р»РёСЃС‚Р°
        created_at: РґР°С‚Р° СЃРѕР·РґР°РЅРёСЏ
        updated_at: РґР°С‚Р° РїРѕСЃР»РµРґРЅРµРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ
        
    Р¦РµРЅС‹ РЅР° РґРІРµСЂРё:
        doors_price_std_single: С†РµРЅР° РѕРґРЅРѕР»РёСЃС‚РѕРІРѕР№ СЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        doors_price_per_m2_nonstd: С†РµРЅР° Р·Р° РјВІ РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        doors_wide_markup: РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРѕРєРёР№ РїСЂРѕС‘Рј
        doors_double_std: С†РµРЅР° РґРІСѓСЃС‚РІРѕСЂС‡Р°С‚РѕР№ СЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        
    Р¦РµРЅС‹ РЅР° Р»СЋРєРё:
        hatch_std: Р±Р°Р·РѕРІР°СЏ С†РµРЅР° Р»СЋРєР°
        hatch_wide_markup: РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРѕРєРёР№ РїСЂРѕС‘Рј
        hatch_per_m2_nonstd: С†РµРЅР° Р·Р° РјВІ РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅРѕРіРѕ Р»СЋРєР°
        
    Р¦РµРЅС‹ РЅР° РІРѕСЂРѕС‚Р°:
        gate_per_m2: С†РµРЅР° Р·Р° РјВІ СЃС‚Р°РЅРґР°СЂС‚РЅС‹С… РІРѕСЂРѕС‚
        gate_large_per_m2: С†РµРЅР° Р·Р° РјВІ Р±РѕР»СЊС€РёС… РІРѕСЂРѕС‚
        
    Р¦РµРЅС‹ РЅР° С„СЂР°РјСѓРіРё:
        transom_per_m2: С†РµРЅР° Р·Р° РјВІ С„СЂР°РјСѓРіРё
        transom_min: РјРёРЅРёРјР°Р»СЊРЅР°СЏ С†РµРЅР° С„СЂР°РјСѓРіРё
        
    Р¦РµРЅС‹ РЅР° РєРѕРјРїР»РµРєС‚СѓСЋС‰РёРµ:
        cutout_price: С†РµРЅР° Р·Р° РІС‹СЂРµР· (РїСЂРѕС‘Рј)
        deflector_per_m2: С†РµРЅР° РѕС‚Р±РѕР№РЅРѕР№ РїР»Р°СЃС‚РёРЅС‹ Р·Р° РјВІ
        trim_per_lm: С†РµРЅР° РґРѕР±РѕСЂР° Р·Р° Рї.Рј.
        closer_price: С†РµРЅР° РґРѕРІРѕРґС‡РёРєР°
        hinge_price: С†РµРЅР° РїРµС‚Р»Рё
        anti_theft_price: С†РµРЅР° РїСЂРѕС‚РёРІРѕСЃСЉС‘РјРЅРѕРіРѕ РјРµС…Р°РЅРёР·РјР°
        gkl_price: С†РµРЅР° Р“РљР› (РіРёРїСЃРѕРєР°СЂС‚РѕРЅ)
        mount_ear_price: С†РµРЅР° РјРѕРЅС‚Р°Р¶РЅРѕР№ СѓС€РєР°
    """
    __tablename__ = "base_price_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Р¦РµРЅС‹ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ (РµСЃР»Рё РЅРµС‚ type-specific)
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

    # Р¦РІРµС‚Р° Рё РїРѕРєСЂС‹С‚РёСЏ
    nonstd_color_markup_pct: Mapped[float] = mapped_column(Float, default=7.0)  # 7%
    diff_color_markup: Mapped[float] = mapped_column(Float, default=2000.0)
    moire_price: Mapped[float] = mapped_column(Float, default=2040.0)
    lacquer_per_m2: Mapped[float] = mapped_column(Float, default=1020.0)
    primer_single: Mapped[float] = mapped_column(Float, default=2550.0)
    primer_double: Mapped[float] = mapped_column(Float, default=5100.0)
    
    # Р’РµРЅС‚СЂРµС€РµС‚РєРё
    vent_grate_tech: Mapped[float] = mapped_column(Float, default=0.0)  # РўРµС…. РІРµРЅС‚СЂРµС€РµС‚РєР°
    vent_grate_pp: Mapped[float] = mapped_column(Float, default=0.0)

    # Уплотнитель
    seal_per_m2: Mapped[float] = mapped_column(Float, default=150.0)  # Цена за м.п.  # Рџ/Рї РІРµРЅС‚СЂРµС€РµС‚РєР°

    # РЎРІСЏР·Рё
    type_prices = relationship("TypePrice", back_populates="price_list", cascade="all, delete-orphan")
    glass_types = relationship("GlassType", back_populates="price_list", cascade="all, delete-orphan")
    vent_types = relationship("VentType", back_populates="price_list", cascade="all, delete-orphan")
    hardware = relationship("HardwareItem", back_populates="price_list", cascade="all, delete-orphan")
    closers = relationship("Closer", back_populates="price_list", cascade="all, delete-orphan")
    coordinators = relationship("Coordinator", back_populates="price_list", cascade="all, delete-orphan")


class PersonalizedPriceList(Base):
    """РџРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅС‹Р№ РїСЂР°Р№СЃ-Р»РёСЃС‚. РљРѕРїРёСЏ Р±Р°Р·РѕРІРѕРіРѕ СЃ РІРѕР·РјРѕР¶РЅРѕСЃС‚СЊСЋ РёР·РјРµРЅРµРЅРёСЏ.
    
    РЎРѕР·РґР°С‘С‚СЃСЏ РґР»СЏ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ РєРѕРЅС‚СЂР°РіРµРЅС‚Р°. РџРѕР·РІРѕР»СЏРµС‚ РїРµСЂРµРѕРїСЂРµРґРµР»РёС‚СЊ С‡Р°СЃС‚СЊ С†РµРЅ
    РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅРѕ Р±Р°Р·РѕРІРѕРіРѕ РїСЂР°Р№СЃ-Р»РёСЃС‚Р°. Р•СЃР»Рё С†РµРЅР° РЅРµ СѓРєР°Р·Р°РЅР° (NULL),
    РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ Р·РЅР°С‡РµРЅРёРµ РёР· Р±Р°Р·РѕРІРѕРіРѕ РїСЂР°Р№СЃР°.
    
    Attributes:
        id: СѓРЅРёРєР°Р»СЊРЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ
        name: РЅР°Р·РІР°РЅРёРµ РїРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅРѕРіРѕ РїСЂР°Р№СЃР°
        base_price_list_id: СЃСЃС‹Р»РєР° РЅР° Р±Р°Р·РѕРІС‹Р№ РїСЂР°Р№СЃ-Р»РёСЃС‚
        created_at: РґР°С‚Р° СЃРѕР·РґР°РЅРёСЏ
        updated_at: РґР°С‚Р° РїРѕСЃР»РµРґРЅРµРіРѕ РѕР±РЅРѕРІР»РµРЅРёСЏ
        
    РџРµСЂРµРѕРїСЂРµРґРµР»С‘РЅРЅС‹Рµ С†РµРЅС‹ (РјРѕРіСѓС‚ Р±С‹С‚СЊ NULL - С‚РѕРіРґР° Р±РµСЂС‘С‚СЃСЏ РёР· Р±Р°Р·РѕРІРѕРіРѕ):
        custom_doors_price_std_single: СЃРІРѕСЏ С†РµРЅР° РѕРґРЅРѕР»РёСЃС‚РѕРІРѕР№ РґРІРµСЂРё
        custom_doors_price_per_m2_nonstd: СЃРІРѕСЏ С†РµРЅР° РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        custom_doors_wide_markup: СЃРІРѕСЏ РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРёРЅСѓ
        custom_cutout_price: СЃРІРѕСЏ С†РµРЅР° РІС‹СЂРµР·Р°
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
    """РџРµСЂРµРѕРїСЂРµРґРµР»С‘РЅРЅС‹Рµ С†РµРЅС‹ РґР»СЏ С‚РёРїРѕРІ РІ РїРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅРѕРј РїСЂР°Р№СЃРµ.
    
    РџРѕР·РІРѕР»СЏРµС‚ Р·Р°РґР°С‚СЊ РёРЅРґРёРІРёРґСѓР°Р»СЊРЅС‹Рµ С†РµРЅС‹ РґР»СЏ РєРѕРЅРєСЂРµС‚РЅС‹С… РїРѕРґС‚РёРїРѕРІ РїСЂРѕРґСѓРєС†РёРё
    РІ СЂР°РјРєР°С… РїРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅРѕРіРѕ РїСЂР°Р№СЃ-Р»РёСЃС‚Р°.
    
    Attributes:
        id: СѓРЅРёРєР°Р»СЊРЅС‹Р№ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ
        price_list_id: СЃСЃС‹Р»РєР° РЅР° РїРµСЂСЃРѕРЅР°Р»РёР·РёСЂРѕРІР°РЅРЅС‹Р№ РїСЂР°Р№СЃ-Р»РёСЃС‚
        product_type: С‚РёРї РїСЂРѕРґСѓРєС†РёРё
        subtype: РїРѕРґС‚РёРї
        price_std_single: СЃРІРѕСЏ С†РµРЅР° РѕРґРЅРѕР»РёСЃС‚РѕРІРѕР№ (РјРѕР¶РµС‚ Р±С‹С‚СЊ NULL)
        price_double_std: СЃРІРѕСЏ С†РµРЅР° РґРІСѓСЃС‚РІРѕСЂС‡Р°С‚РѕР№ (РјРѕР¶РµС‚ Р±С‹С‚СЊ NULL)
        price_wide_markup: СЃРІРѕСЏ РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРёРЅСѓ (РјРѕР¶РµС‚ Р±С‹С‚СЊ NULL)
        price_per_m2_nonstd: СЃРІРѕСЏ С†РµРЅР° Р·Р° РјВІ (РјРѕР¶РµС‚ Р±С‹С‚СЊ NULL)
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
