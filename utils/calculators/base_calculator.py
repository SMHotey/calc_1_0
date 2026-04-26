"""Р‘Р°Р·РѕРІС‹Р№ РєР»Р°СЃСЃ РєР°Р»СЊРєСѓР»СЏС‚РѕСЂР° Рё РєРѕРЅС‚РµРєСЃС‚ СЂР°СЃС‡С‘С‚РѕРІ.

РЎРѕРґРµСЂР¶РёС‚:
- PriceData: СЃС‚СЂСѓРєС‚СѓСЂР° РґР°РЅРЅС‹С… СЃ С†РµРЅР°РјРё РёР· РїСЂР°Р№СЃ-Р»РёСЃС‚Р°
- GlassItemData: РґР°РЅРЅС‹Рµ РґР»СЏ РѕСЃС‚РµРєР»РµРЅРёСЏ (СЃС‚РµРєР»Рѕ + РѕРїС†РёРё)
- CalculatorContext: РєРѕРЅС‚РµРєСЃС‚ СЂР°СЃС‡С‘С‚Р° (РІСЃРµ РІС…РѕРґРЅС‹Рµ РґР°РЅРЅС‹Рµ)
- BaseCalculator: Р°Р±СЃС‚СЂР°РєС‚РЅС‹Р№ Р±Р°Р·РѕРІС‹Р№ РєР»Р°СЃСЃ РґР»СЏ РєР°Р»СЊРєСѓР»СЏС‚РѕСЂРѕРІ
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Protocol, Tuple
from abc import ABC, abstractmethod
from constants import STANDARD_RAL
import logging
logger = logging.getLogger(__name__)


@dataclass
class PriceData:
    """РўРёРїРёР·РёСЂРѕРІР°РЅРЅС‹Р№ РѕР±СЉРµРєС‚ СЃ С‚Р°СЂРёС„Р°РјРё РёР· РїСЂР°Р№СЃ-Р»РёСЃС‚Р°.

    РЎРѕРґРµСЂР¶РёС‚ РІСЃРµ С†РµРЅС‹, РЅРµРѕР±С…РѕРґРёРјС‹Рµ РґР»СЏ СЂР°СЃС‡С‘С‚Р° СЃС‚РѕРёРјРѕСЃС‚Рё РёР·РґРµР»РёСЏ.
    Р’РєР»СЋС‡Р°РµС‚ Р±Р°Р·РѕРІС‹Рµ С†РµРЅС‹ Рё type-specific С†РµРЅС‹ РґР»СЏ РєРѕРЅРєСЂРµС‚РЅС‹С… РїРѕРґС‚РёРїРѕРІ.

    РђС‚СЂРёР±СѓС‚С‹:
        - doors_std_single: С†РµРЅР° РѕРґРЅРѕР»РёСЃС‚РѕРІРѕР№ СЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        - doors_per_m2_nonstd: С†РµРЅР° Р·Р° РјВІ РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        - doors_wide_markup: РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРѕРєРёР№ РїСЂРѕС‘Рј РґРІРµСЂРё
        - doors_double_std: С†РµРЅР° РґРІСѓСЃС‚РІРѕСЂС‡Р°С‚РѕР№ СЃС‚Р°РЅРґР°СЂС‚РЅРѕР№ РґРІРµСЂРё
        - hatch_std: Р±Р°Р·РѕРІР°СЏ С†РµРЅР° Р»СЋРєР°
        - hatch_wide_markup: РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРѕРєРёР№ РїСЂРѕС‘Рј Р»СЋРєР°
        - hatch_per_m2_nonstd: С†РµРЅР° Р·Р° РјВІ РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅРѕРіРѕ Р»СЋРєР°
        - gate_per_m2: С†РµРЅР° Р·Р° РјВІ СЃС‚Р°РЅРґР°СЂС‚РЅС‹С… РІРѕСЂРѕС‚
        - gate_large_per_m2: С†РµРЅР° Р·Р° РјВІ Р±РѕР»СЊС€РёС… РІРѕСЂРѕС‚
        - transom_per_m2: С†РµРЅР° Р·Р° РјВІ С„СЂР°РјСѓРіРё
        - transom_min: РјРёРЅРёРјР°Р»СЊРЅР°СЏ С†РµРЅР° С„СЂР°РјСѓРіРё
        - type_std_single: type-specific С†РµРЅР° РѕРґРЅРѕР»РёСЃС‚РѕРІРѕР№
        - type_double_std: type-specific С†РµРЅР° РґРІСѓСЃС‚РІРѕСЂС‡Р°С‚РѕР№
        - type_wide_markup: type-specific РЅР°С†РµРЅРєР° Р·Р° С€РёСЂРёРЅСѓ
        - type_per_m2_nonstd: type-specific С†РµРЅР° Р·Р° РјВІ
        - has_type_specific_price: РµСЃС‚СЊ Р»Рё СЃРїРµС†РёС„РёС‡РЅС‹Рµ С†РµРЅС‹ РґР»СЏ С‚РёРїР°
        - cutout_price: С†РµРЅР° Р·Р° РІС‹СЂРµР· (РїСЂРѕС‘Рј)
        - deflector_per_m2: С†РµРЅР° РѕС‚Р±РѕР№РЅРѕР№ РїР»Р°СЃС‚РёРЅС‹ Р·Р° РјВІ
        - trim_per_lm: С†РµРЅР° РґРѕР±РѕСЂР° Р·Р° Рї.Рј.
        - closer_price: С†РµРЅР° РґРѕРІРѕРґС‡РёРєР°
        - hinge_price: С†РµРЅР° РїРµС‚Р»Рё
        - anti_theft_price: С†РµРЅР° РїСЂРѕС‚РёРІРѕСЃСЉС‘РјРЅРѕРіРѕ РјРµС…Р°РЅРёР·РјР°
        - gkl_price: С†РµРЅР° Р“РљР›
        - mount_ear_price: С†РµРЅР° РјРѕРЅС‚Р°Р¶РЅРѕР№ СѓС€РєР°
        - nonstd_color_markup_pct: РЅР°С†РµРЅРєР° Р·Р° РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅС‹Р№ С†РІРµС‚ (5%)
        - diff_color_markup: РЅР°С†РµРЅРєР° Р·Р° СЂР°Р·РЅС‹Рµ С†РІРµС‚Р° СЃС‚РѕСЂРѕРЅ
        - moire_lacquer_primer_per_m2: С†РµРЅС‹ РјРѕСЂРµРЅРѕР№ РєСЂР°СЃРєРё/РіСЂСѓРЅС‚Р°
        - custom_options: РїРѕР»СЊР·РѕРІР°С‚РµР»СЊСЃРєРёРµ РѕРїС†РёРё
    """
    # Р‘Р°Р·РѕРІС‹Рµ С†РµРЅС‹ РёР·РґРµР»РёР№ (РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ)
    doors_std_single: float = 0.0
    doors_per_m2_nonstd: float = 0.0
    doors_wide_markup: float = 0.0
    doors_double_std: float = 0.0
    hatch_std: float = 0.0
    hatch_wide_markup: float = 0.0
    hatch_per_m2_nonstd: float = 0.0
    gate_per_m2: float = 0.0
    gate_large_per_m2: float = 0.0
    transom_per_m2: float = 0.0
    transom_min: float = 0.0

    # Type-specific С†РµРЅС‹ (РґР»СЏ РєРѕРЅРєСЂРµС‚РЅРѕРіРѕ РїРѕРґС‚РёРїР° РёР·РґРµР»РёСЏ)
    type_std_single: float = 0.0
    type_double_std: float = 0.0
    type_wide_markup: float = 0.0
    type_per_m2_nonstd: float = 0.0
    has_type_specific_price: bool = False

    # РћРїС†РёРё
    cutout_price: float = 0.0
    deflector_per_m2: float = 0.0
    trim_per_lm: float = 0.0
    closer_price: float = 0.0
    hinge_price: float = 0.0
    anti_theft_price: float = 0.0
    gkl_price: float = 0.0
    mount_ear_price: float = 0.0
    threshold_price: float = 0.0
    nonstd_color_markup_pct: float = 7.0  # 7% РѕС‚ Р±Р°Р·РѕРІРѕР№ СЃС‚РѕРёРјРѕСЃС‚Рё (Р±РµР· РѕРїС†РёР№)
    diff_color_markup: float = 2000.0  # Р—Р° СЂР°Р·РЅС‹Рµ С†РІРµС‚Р° СЃС‚РѕСЂРѕРЅ
    
    # РџРѕРєСЂС‹С‚РёСЏ (РњСѓР°СЂ, Р›Р°Рє, Р“СЂСѓРЅС‚)
    moire_price: float = 2040.0  # Р¤РёРєСЃРёСЂРѕРІР°РЅРЅР°СЏ Р·Р° РёР·РґРµР»РёРµ
    lacquer_per_m2: float = 1020.0  # Р—Р° РјВІ
    primer_single: float = 2550.0  # Р—Р° 1 СЃС‚РІРѕСЂРєСѓ
    primer_double: float = 5100.0  # Р—Р° 2 СЃС‚РІРѕСЂРєРё
    
    moire_lacquer_primer_per_m2: Dict[str, float] = field(default_factory=dict)

    # Уплотнитель
    seal_per_m2: float = 150.0  # Цена за м.п.
    custom_options: Dict[str, float] = field(default_factory=dict)


@dataclass
class GlassItemData:
    """Р”Р°РЅРЅС‹Рµ РґР»СЏ РѕРґРЅРѕРіРѕ СЌР»РµРјРµРЅС‚Р° РѕСЃС‚РµРєР»РµРЅРёСЏ.

    РђС‚СЂРёР±СѓС‚С‹:
        - type_id: ID С‚РёРїР° СЃС‚РµРєР»Р°
        - height: РІС‹СЃРѕС‚Р° СЃС‚РµРєР»Р° РІ РјРј
        - width: С€РёСЂРёРЅР° СЃС‚РµРєР»Р° РІ РјРј
        - options: СЃРїРёСЃРѕРє ID РІС‹Р±СЂР°РЅРЅС‹С… РѕРїС†РёР№ СЃС‚РµРєР»Р°
        - double_sided_options: РѕРїС†РёРё РЅР° РѕР±РµРёС… СЃС‚РѕСЂРѕРЅР°С…
        - options_price_m2: С†РµРЅР° Р·Р° РјВІ РґР»СЏ СЂР°СЃС‡С‘С‚Р° РѕРїС†РёР№
        - min_price: РјРёРЅРёРјР°Р»СЊРЅР°СЏ С†РµРЅР°
        - opt_prices_mins: С†РµРЅС‹ Рё РјРёРЅ. С†РµРЅС‹ РґР»СЏ РєР°Р¶РґРѕР№ РѕРїС†РёРё
    """
    type_id: int
    height: float
    width: float
    options: List[int]
    double_sided_options: bool = False
    options_price_m2: float = 0.0
    min_price: float = 0.0
    opt_prices_mins: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class CalculatorContext:
    """
    РљРѕРЅС‚РµРєСЃС‚ СЂР°СЃС‡С‘С‚Р° РёР·РґРµР»РёСЏ. Р—Р°РїРѕР»РЅСЏРµС‚СЃСЏ РєРѕРЅС‚СЂРѕР»Р»РµСЂРѕРј РёР· UI Рё Р‘Р”.
    РќРµ Р·Р°РІРёСЃРёС‚ РѕС‚ С„СЂРµР№РјРІРѕСЂРєРѕРІ Рё ORM.
    """
    product_type: str
    subtype: str
    height: float
    width: float
    is_double_leaf: bool
    prices: PriceData

    # РћРїС†РёРё
    color_external: int | str = 7035
    color_internal: int | str = 7035
    metal_thickness: str = "1.0-1.0"
    glass_items: List[GlassItemData] = field(default_factory=list)
    closers_count: int = 0
    grilles: List[Dict[str, Any]] = field(default_factory=list)  # {'h', 'w', 'type', 'price_per_m2', 'min_price'}
    threshold_enabled: bool = False
    deflector_height_mm: float = 0.0
    deflector_double_side: bool = False
    trim_depth_mm: float = 0.0
    extra_options: Dict[str, Any] = field(default_factory=dict)  # hinges, anti_theft, gkl, mount_ears
    markup_percent: float = 0.0
    markup_abs: float = 0.0

    # Р¤СѓСЂРЅРёС‚СѓСЂР° (С†РµРЅС‹ Р·Р° С€С‚)
    hardware_items: List[float] = field(default_factory=list)

    # Уплотнитель
    seal_enabled: bool = False  # Включен уплотнитель


class BaseCalculator(ABC):
    """РђР±СЃС‚СЂР°РєС‚РЅС‹Р№ Р±Р°Р·РѕРІС‹Р№ РєР»Р°СЃСЃ РґР»СЏ РІСЃРµС… РєР°Р»СЊРєСѓР»СЏС‚РѕСЂРѕРІ РёР·РґРµР»РёР№."""

    @abstractmethod
    def calculate_base(self, ctx: CalculatorContext) -> float:
        """Р Р°СЃС‡С‘С‚ Р±Р°Р·РѕРІРѕР№ СЃС‚РѕРёРјРѕСЃС‚Рё РёР·РґРµР»РёСЏ (Р±РµР· РѕРїС†РёР№ Рё РЅР°С†РµРЅРѕРє)."""
        ...

    def calculate(self, ctx: CalculatorContext) -> float:
        """
        РџРѕР»РЅС‹Р№ СЂР°СЃС‡С‘С‚ СЃС‚РѕРёРјРѕСЃС‚Рё СЃ СѓС‡С‘С‚РѕРј РІСЃРµС… РѕРїС†РёР№, С„СѓСЂРЅРёС‚СѓСЂС‹ Рё РЅР°С†РµРЅРѕРє.

        :param ctx: РљРѕРЅС‚РµРєСЃС‚ СЂР°СЃС‡С‘С‚Р°
        :return: РС‚РѕРіРѕРІР°СЏ С†РµРЅР° Р·Р° РµРґРёРЅРёС†Сѓ
        """
        area_m2 = (ctx.height / 1000.0) * (ctx.width / 1000.0)
        base_price = self.calculate_base(ctx)

        # 5.1 Р¦РІРµС‚
        price = self._apply_color_options(ctx, base_price, area_m2)

        # 5.3 РњРµС‚Р°Р»Р»
        price = self._apply_metal_thickness(price, ctx.metal_thickness)

        # 5.2 РћСЃС‚РµРєР»РµРЅРёРµ
        for glass in ctx.glass_items:
            price += self._calculate_glass_cost(glass, ctx)

        # 5.5 Вентиляционные решётки
        logger.info(f"calculate: grilles count={len(ctx.grilles)}")
        for gr in ctx.grilles:
            g_area = (gr['h'] / 1000) * (gr['w'] / 1000)
            gr_price = max(g_area * gr.get('price_per_m2', 0), gr.get('min_price', 0))
            gr_price += ctx.prices.cutout_price
            logger.info(f"calculate: grille h={gr['h']}, w={gr['w']}, area={g_area:.3f}, price_per_m2={gr.get('price_per_m2', 0)}, min_price={gr.get('min_price', 0)}, cutout={ctx.prices.cutout_price}, total={gr_price}")
            price += gr_price

        # 5.4 Р”РѕРІРѕРґС‡РёРєРё
        price += ctx.closers_count * ctx.prices.closer_price

        # 5.6 РџРѕСЂРѕРі
        if ctx.threshold_enabled:
            count = 2 if ctx.is_double_leaf else 1
            price += ctx.prices.threshold_price * count

        # 5.7 РћС‚Р±РѕР№РЅР°СЏ
        if ctx.deflector_height_mm > 0:
            d_area = (ctx.width / 1000.0) * (ctx.deflector_height_mm / 1000.0)
            plate_price = d_area * ctx.prices.deflector_per_m2
            if ctx.deflector_double_side:
                plate_price *= 2
            price += plate_price

        # 5.8 Р”РѕР±РѕСЂС‹
        if ctx.trim_depth_mm > 0:
            lin_meters = (2 * ctx.height + ctx.width) / 1000.0
            trim_price = lin_meters * ctx.prices.trim_per_lm
            if ctx.trim_depth_mm > 150:
                trim_price *= (ctx.trim_depth_mm / 150.0)
            price += trim_price

        # 5.9 РЎС‚Р°РЅРґР°СЂС‚РЅС‹Рµ РѕРїС†РёРё
        price += self._apply_standard_extras(ctx)

        # Р¤СѓСЂРЅРёС‚СѓСЂР°
        price += sum(ctx.hardware_items)

        # Уплотнитель (5.11) - рассчитывается по периметру
        if ctx.seal_enabled:
            # Периметр в метрах: 2*(высота + ширина)
            perimeter_m = 2 * (ctx.height + ctx.width) / 1000.0
            # Для двустворчатых - умножаем на 2
            if ctx.is_double_leaf:
                perimeter_m *= 2
            price += perimeter_m * ctx.prices.seal_per_m2

        # РџРѕР»СЊР·РѕРІР°С‚РµР»СЊСЃРєРёРµ РѕРїС†РёРё (5.10)
        for opt_name, opt_count in ctx.extra_options.get("custom", {}).items():
            unit_price = ctx.prices.custom_options.get(opt_name, 0.0)
            price += unit_price * opt_count

        # Р”СЂСѓРіРёРµ С„РёРєСЃРёСЂРѕРІР°РЅРЅС‹Рµ РѕРїС†РёРё (РґРѕСЃС‚Р°РІРєР°, Р·Р°РјРµСЂ, СѓСЃС‚Р°РЅРѕРІРєР°, Р±РѕРЅСѓСЃ)
        other_options = ctx.extra_options.get("other", {})
        price += other_options.get("delivery", 0.0)
        price += other_options.get("measurement", 0.0)
        price += other_options.get("installation", 0.0)
        price += other_options.get("bonus", 0.0)

        # РќР°С†РµРЅРєР°
        markup_val = (price * ctx.markup_percent / 100.0) + ctx.markup_abs
        return price + markup_val

    def _apply_color_options(self, ctx: CalculatorContext, base: float, area: float) -> float:
        """Р Р°СЃС‡С‘С‚ С†РІРµС‚РѕРІС‹С… РѕРїС†РёР№.
        
        Р›РѕРіРёРєР°:
        - 7% РѕС‚ Р±Р°Р·РѕРІРѕР№ СЃС‚РѕРёРјРѕСЃС‚Рё (С‚РѕР»СЊРєРѕ base, Р±РµР· РѕРїС†РёР№) Р·Р° РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅС‹Р№ С†РІРµС‚
        - +2000 РµСЃР»Рё С†РІРµС‚Р° СЂР°Р·РЅС‹Рµ, РЅРѕ РѕР±Р° СЃС‚Р°РЅРґР°СЂС‚РЅС‹Рµ
        - +7% + 2000 РµСЃР»Рё РѕРґРёРЅ РёР»Рё РѕР±Р° РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅС‹Рµ
        - Р•СЃР»Рё РѕР±Р° РЅРµСЃС‚Р°РЅРґР°СЂС‚РЅС‹Рµ: С‚РѕР»СЊРєРѕ +7% (РѕРґРёРЅ СЂР°Р·), РЅРµ 14%
        """
        price = base
        is_apartment_or_single = "РљРІР°СЂС‚РёСЂРЅР°СЏ" in ctx.subtype or "РћРґРЅРѕР»РёСЃС‚РѕРІР°СЏ" in ctx.subtype
        
        ext_color = str(ctx.color_external)
        int_color = str(ctx.color_internal)
        
        # РЎС‚Р°РЅРґР°СЂС‚РЅС‹Рµ С†РІРµС‚Р° РёР· Р‘Р” РёР»Рё РєРѕРЅСЃС‚Р°РЅС‚С‹
        std_colors = ctx.prices.standard_colors if hasattr(ctx.prices, 'standard_colors') else STANDARD_RAL
        ext_std = ext_color in std_colors
        int_std = int_color in std_colors
        
        # РќРµСЃС‚Р°РЅРґР°СЂС‚РЅС‹Р№ С†РІРµС‚ = +7% РѕС‚ Р±Р°Р·РѕРІРѕР№ СЃС‚РѕРёРјРѕСЃС‚Рё
        has_nonstd = not ext_std or not int_std
        if has_nonstd:
            # % СЂР°СЃСЃС‡РёС‚С‹РІР°РµС‚СЃСЏ РѕС‚ Р±Р°Р·РѕРІРѕР№ СЃС‚РѕРёРјРѕСЃС‚Рё (Р±РµР· РѕРїС†РёР№)
            color_surcharge = base * (ctx.prices.nonstd_color_markup_pct / 100.0)
            price += color_surcharge
        
        # Р Р°Р·РЅС‹Рµ С†РІРµС‚Р° = +2000 (С„РёРєСЃРёСЂРѕРІР°РЅРЅР°СЏ РЅР°С†РµРЅРєР°)
        if not is_apartment_or_single and ext_color != int_color:
            price += ctx.prices.diff_color_markup
        
        # РџРѕРєСЂС‹С‚РёСЏ (РњСѓР°СЂ, Р›Р°Рє, Р“СЂСѓРЅС‚)
        # РњСѓР°СЂ - С„РёРєСЃРёСЂРѕРІР°РЅРЅР°СЏ С†РµРЅР° Р·Р° РёР·РґРµР»РёРµ
        if ctx.extra_options.get("coating_moire"):
            price += ctx.prices.moire_price
        
        # Р›Р°Рє - Р·Р° РјВІ
        if ctx.extra_options.get("coating_lacquer"):
            price += area * ctx.prices.lacquer_per_m2
        
        # Р“СЂСѓРЅС‚ - Р·Р° СЃС‚РІРѕСЂРєСѓ
        if ctx.extra_options.get("coating_primer"):
            if ctx.is_double_leaf:
                price += ctx.prices.primer_double
            else:
                price += ctx.prices.primer_single
        
        return price

    def _apply_metal_thickness(self, price: float, metal_thickness: str) -> float:
        thickness_multipliers = {
            "1.2-1.4": 1.05,
            "1.4-1.4": 1.08,
            "1.5-1.5": 1.12,
            "1.4-2.0": 1.15
        }
        return price * thickness_multipliers.get(metal_thickness, 1.0)

    def _calculate_glass_cost(self, glass: GlassItemData, calc_ctx: CalculatorContext) -> float:
        """Р Р°СЃС‡С‘С‚ СЃС‚РѕРёРјРѕСЃС‚Рё РѕРґРЅРѕРіРѕ СЃС‚РµРєР»Р° Рё РµРіРѕ РѕРїС†РёР№."""
        g_area = (glass.height / 1000.0) * (glass.width / 1000.0)

        # Р‘Р°Р·РѕРІР°СЏ С†РµРЅР° СЃС‚РµРєР»Р°
        base_glass = max(g_area * glass.options_price_m2, glass.min_price)

        # РЁС‚СЂР°С„ Р·Р° СѓР·РєРѕРµ/РІС‹СЃРѕРєРѕРµ СЃС‚РµРєР»Рѕ (РѕС‚РЅРѕС€РµРЅРёРµ h/w <= 1:5)
        # "РџСЂРё СЃРѕРѕС‚РЅРѕС€РµРЅРёРё РІС‹СЃРѕС‚С‹ Рё С€РёСЂРёРЅС‹ СЃС‚РµРєР»Р° РјРµРЅРµРµ РёР»Рё СЂР°РІРЅРѕ 1 Рє 5 РЅР°С†РµРЅРєР° СЃРѕСЃС‚Р°РІР»СЏРµС‚ 50%"
        ratio = glass.height / glass.width if glass.width > 0 else float('inf')
        if ratio <= 0.2:  # h/w <= 1/5
            base_glass *= 1.5

        # Р’С‹СЂРµР·
        base_glass += calc_ctx.prices.cutout_price

        # РћРїС†РёРё СЃС‚РµРєР»Р°
        for opt_price_m2, opt_min_price in glass.opt_prices_mins:
            opt_cost = g_area * opt_price_m2
            if glass.double_sided_options:
                opt_cost *= 2
                # РњРёРЅРёРјР°Р»СЊРЅР°СЏ СЃС‚РѕРёРјРѕСЃС‚СЊ РќР• СѓРґРІР°РёРІР°РµС‚СЃСЏ
            opt_cost = max(opt_cost, opt_min_price)
            base_glass += opt_cost

        return base_glass

    def _apply_standard_extras(self, ctx: CalculatorContext) -> float:
        price = 0.0
        extras = ctx.extra_options

        # Hinges: new counts-based logic (active/passive leaves)
        # UI provides hinge_count_active, hinge_count_passive, hinge_default_active, hinge_default_passive
        hinge_count_active = int(extras.get("hinge_count_active") or 0)
        hinge_count_passive = int(extras.get("hinge_count_passive") or 0)
        hinge_default_active = int(extras.get("hinge_default_active") or 0)
        hinge_default_passive = int(extras.get("hinge_default_passive") or 0)

        if ctx.is_double_leaf:
            extra_active = max(0, hinge_count_active - hinge_default_active)
            extra_passive = max(0, hinge_count_passive - hinge_default_passive)
            hinges_to_charge = extra_active + extra_passive
        else:
            # Single leaf: only active leaf counts
            hinges_to_charge = max(0, hinge_count_active - hinge_default_active)

        if hinges_to_charge:
            price += ctx.prices.hinge_price * hinges_to_charge

        # Anti-theft pins: keep boolean behaviour (unchanged) - charge per leaf
        if extras.get("anti_theft_pins"):
            count = 2 if ctx.is_double_leaf else 1
            price += ctx.prices.anti_theft_price * count

        if extras.get("gkl"):
            # РўРѕР»СЊРєРѕ РґР»СЏ РѕРґРЅРѕСЃС‚РІРѕСЂС‡Р°С‚С‹С…
            if not ctx.is_double_leaf:
                price += ctx.prices.gkl_price

        # Mount ears: always charge based on provided count (may be 0)
        ears_count = int(extras.get("mount_ears_count") or 0)
        if ears_count > 0:
            price += ctx.prices.mount_ear_price * ears_count

        return price



