"""Базовый класс калькулятора и контекст расчётов.

Содержит:
- PriceData: структура данных с ценами из прайс-листа
- GlassItemData: данные для остекления (стекло + опции)
- CalculatorContext: контекст расчёта (все входные данные)
- BaseCalculator: абстрактный базовый класс для калькуляторов
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Protocol, Tuple
from abc import ABC, abstractmethod
from constants import STANDARD_RAL


@dataclass
class PriceData:
    """Типизированный объект с тарифами из прайс-листа.

    Содержит все цены, необходимые для расчёта стоимости изделия.
    Включает базовые цены и type-specific цены для конкретных подтипов.

    Атрибуты:
        - doors_std_single: цена однолистовой стандартной двери
        - doors_per_m2_nonstd: цена за м² нестандартной двери
        - doors_wide_markup: наценка за широкий проём двери
        - doors_double_std: цена двустворчатой стандартной двери
        - hatch_std: базовая цена люка
        - hatch_wide_markup: наценка за широкий проём люка
        - hatch_per_m2_nonstd: цена за м² нестандартного люка
        - gate_per_m2: цена за м² стандартных ворот
        - gate_large_per_m2: цена за м² больших ворот
        - transom_per_m2: цена за м² фрамуги
        - transom_min: минимальная цена фрамуги
        - type_std_single: type-specific цена однолистовой
        - type_double_std: type-specific цена двустворчатой
        - type_wide_markup: type-specific наценка за ширину
        - type_per_m2_nonstd: type-specific цена за м²
        - has_type_specific_price: есть ли специфичные цены для типа
        - cutout_price: цена за вырез (проём)
        - deflector_per_m2: цена отбойной пластины за м²
        - trim_per_lm: цена добора за п.м.
        - closer_price: цена доводчика
        - hinge_price: цена петли
        - anti_theft_price: цена противосъёмного механизма
        - gkl_price: цена ГКЛ
        - mount_ear_price: цена монтажной ушка
        - nonstd_color_markup_pct: наценка за нестандартный цвет (5%)
        - diff_color_markup: наценка за разные цвета сторон
        - moire_lacquer_primer_per_m2: цены мореной краски/грунта
        - custom_options: пользовательские опции
    """
    # Базовые цены изделий (по умолчанию)
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

    # Type-specific цены (для конкретного подтипа изделия)
    type_std_single: float = 0.0
    type_double_std: float = 0.0
    type_wide_markup: float = 0.0
    type_per_m2_nonstd: float = 0.0
    has_type_specific_price: bool = False

    # Опции
    cutout_price: float = 0.0
    deflector_per_m2: float = 0.0
    trim_per_lm: float = 0.0
    closer_price: float = 0.0
    hinge_price: float = 0.0
    anti_theft_price: float = 0.0
    gkl_price: float = 0.0
    mount_ear_price: float = 0.0
    threshold_price: float = 0.0
    nonstd_color_markup_pct: float = 7.0  # 7% от базовой стоимости (без опций)
    diff_color_markup: float = 2000.0  # За разные цвета сторон
    
    # Покрытия (Муар, Лак, Грунт)
    moire_price: float = 2040.0  # Фиксированная за изделие
    lacquer_per_m2: float = 1020.0  # За м²
    primer_single: float = 2550.0  # За 1 створку
    primer_double: float = 5100.0  # За 2 створки
    
    moire_lacquer_primer_per_m2: Dict[str, float] = field(default_factory=dict)
    custom_options: Dict[str, float] = field(default_factory=dict)


@dataclass
class GlassItemData:
    """Данные для одного элемента остекления.

    Атрибуты:
        - type_id: ID типа стекла
        - height: высота стекла в мм
        - width: ширина стекла в мм
        - options: список ID выбранных опций стекла
        - double_sided_options: опции на обеих сторонах
        - options_price_m2: цена за м² для расчёта опций
        - min_price: минимальная цена
        - opt_prices_mins: цены и мин. цены для каждой опции
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
    Контекст расчёта изделия. Заполняется контроллером из UI и БД.
    Не зависит от фреймворков и ORM.
    """
    product_type: str
    subtype: str
    height: float
    width: float
    is_double_leaf: bool
    prices: PriceData

    # Опции
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

    # Фурнитура (цены за шт)
    hardware_items: List[float] = field(default_factory=list)


class BaseCalculator(ABC):
    """Абстрактный базовый класс для всех калькуляторов изделий."""

    @abstractmethod
    def calculate_base(self, ctx: CalculatorContext) -> float:
        """Расчёт базовой стоимости изделия (без опций и наценок)."""
        ...

    def calculate(self, ctx: CalculatorContext) -> float:
        """
        Полный расчёт стоимости с учётом всех опций, фурнитуры и наценок.

        :param ctx: Контекст расчёта
        :return: Итоговая цена за единицу
        """
        area_m2 = (ctx.height / 1000.0) * (ctx.width / 1000.0)
        base_price = self.calculate_base(ctx)

        # 5.1 Цвет
        price = self._apply_color_options(ctx, base_price, area_m2)

        # 5.3 Металл
        price = self._apply_metal_thickness(price, ctx.metal_thickness)

        # 5.2 Остекление
        for glass in ctx.glass_items:
            price += self._calculate_glass_cost(glass, ctx)

        # 5.5 Решётки
        for gr in ctx.grilles:
            g_area = (gr['h'] / 1000) * (gr['w'] / 1000)
            gr_price = max(g_area * gr.get('price_per_m2', 0), gr.get('min_price', 0))
            gr_price += ctx.prices.cutout_price
            price += gr_price

        # 5.4 Доводчики
        price += ctx.closers_count * ctx.prices.closer_price

        # 5.6 Порог
        if ctx.threshold_enabled:
            count = 2 if ctx.is_double_leaf else 1
            price += ctx.prices.threshold_price * count

        # 5.7 Отбойная
        if ctx.deflector_height_mm > 0:
            d_area = (ctx.width / 1000.0) * (ctx.deflector_height_mm / 1000.0)
            plate_price = d_area * ctx.prices.deflector_per_m2
            if ctx.deflector_double_side:
                plate_price *= 2
            price += plate_price

        # 5.8 Доборы
        if ctx.trim_depth_mm > 0:
            lin_meters = (2 * ctx.height + ctx.width) / 1000.0
            trim_price = lin_meters * ctx.prices.trim_per_lm
            if ctx.trim_depth_mm > 150:
                trim_price *= (ctx.trim_depth_mm / 150.0)
            price += trim_price

        # 5.9 Стандартные опции
        price += self._apply_standard_extras(ctx)

        # Фурнитура
        price += sum(ctx.hardware_items)

        # Пользовательские опции (5.10)
        for opt_name, opt_count in ctx.extra_options.get("custom", {}).items():
            unit_price = ctx.prices.custom_options.get(opt_name, 0.0)
            price += unit_price * opt_count

        # Наценка
        markup_val = (price * ctx.markup_percent / 100.0) + ctx.markup_abs
        return price + markup_val

    def _apply_color_options(self, ctx: CalculatorContext, base: float, area: float) -> float:
        """Расчёт цветовых опций.
        
        Логика:
        - 7% от базовой стоимости (только base, без опций) за нестандартный цвет
        - +2000 если цвета разные, но оба стандартные
        - +7% + 2000 если один или оба нестандартные
        - Если оба нестандартные: только +7% (один раз), не 14%
        """
        price = base
        is_apartment_or_single = "Квартирная" in ctx.subtype or "Однолистовая" in ctx.subtype
        
        ext_color = str(ctx.color_external)
        int_color = str(ctx.color_internal)
        
        # Стандартные цвета из БД или константы
        std_colors = ctx.prices.standard_colors if hasattr(ctx.prices, 'standard_colors') else STANDARD_RAL
        ext_std = ext_color in std_colors
        int_std = int_color in std_colors
        
        # Нестандартный цвет = +7% от базовой стоимости
        has_nonstd = not ext_std or not int_std
        if has_nonstd:
            # % рассчитывается от базовой стоимости (без опций)
            color_surcharge = base * (ctx.prices.nonstd_color_markup_pct / 100.0)
            price += color_surcharge
        
        # Разные цвета = +2000 (фиксированная наценка)
        if not is_apartment_or_single and ext_color != int_color:
            price += ctx.prices.diff_color_markup
        
        # Покрытия (Муар, Лак, Грунт)
        # Муар - фиксированная цена за изделие
        if ctx.extra_options.get("coating_moire"):
            price += ctx.prices.moire_price
        
        # Лак - за м²
        if ctx.extra_options.get("coating_lacquer"):
            price += area * ctx.prices.lacquer_per_m2
        
        # Грунт - за створку
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
        """Расчёт стоимости одного стекла и его опций."""
        g_area = (glass.height / 1000.0) * (glass.width / 1000.0)

        # Базовая цена стекла
        base_glass = max(g_area * glass.options_price_m2, glass.min_price)

        # Штраф за узкое/высокое стекло (отношение h/w <= 1:5)
        # "При соотношении высоты и ширины стекла менее или равно 1 к 5 наценка составляет 50%"
        ratio = glass.height / glass.width if glass.width > 0 else float('inf')
        if ratio <= 0.2:  # h/w <= 1/5
            base_glass *= 1.5

        # Вырез
        base_glass += calc_ctx.prices.cutout_price

        # Опции стекла
        for opt_price_m2, opt_min_price in glass.opt_prices_mins:
            opt_cost = g_area * opt_price_m2
            if glass.double_sided_options:
                opt_cost *= 2
                # Минимальная стоимость НЕ удваивается
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
            # Только для одностворчатых
            if not ctx.is_double_leaf:
                price += ctx.prices.gkl_price

        # Mount ears: always charge based on provided count (may be 0)
        ears_count = int(extras.get("mount_ears_count") or 0)
        if ears_count > 0:
            price += ctx.prices.mount_ear_price * ears_count

        return price
