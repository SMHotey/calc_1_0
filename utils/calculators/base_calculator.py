"""Базовый класс калькулятора и контекст расчётов."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Protocol, Tuple
from abc import ABC, abstractmethod
from constants import STANDARD_RAL


@dataclass
class PriceData:
    """Типизированный объект с тарифами из прайс-листа."""
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
    nonstd_color_markup_pct: float = 0.05  # 5%
    diff_color_markup: float = 1500.0
    moire_lacquer_primer_per_m2: Dict[str, float] = field(default_factory=dict)
    custom_options: Dict[str, float] = field(default_factory=dict)


@dataclass
class GlassItemData:
    """Данные для одного элемента остекления."""
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
            price += 2500.0 * count  # Значение берётся из prices в реале, здесь заглушка-константа по ТЗ

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
        price = base
        is_apartment_or_single = "Квартирная" in ctx.subtype or "Однолистовая" in ctx.subtype

        ext_color = str(ctx.color_external)
        int_color = str(ctx.color_internal)
        ext_std = ext_color in STANDARD_RAL
        int_std = int_color in STANDARD_RAL
        if not ext_std or not int_std:
            price *= (1.0 + ctx.prices.nonstd_color_markup_pct)

        if not is_apartment_or_single and ext_color != int_color:
            price += ctx.prices.diff_color_markup

        for opt_key, p_m2 in ctx.prices.moire_lacquer_primer_per_m2.items():
            if ctx.extra_options.get(f"coating_{opt_key}"):
                price += area * p_m2

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

        # Штраф за узкое/высокое стекло (отношение <= 1/5)
        ratio = glass.height / glass.width if glass.width > 0 else float('inf')
        if ratio <= 0.2 or ratio >= 5.0:
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

        if extras.get("extra_hinge"):
            count = 2 if ctx.is_double_leaf else 1
            price += ctx.prices.hinge_price * count

        if extras.get("anti_theft_pins"):
            count = 2 if ctx.is_double_leaf else 1
            price += ctx.prices.anti_theft_price * count

        if extras.get("gkl"):
            # Только для одностворчатых
            if not ctx.is_double_leaf:
                price += ctx.prices.gkl_price

        ears_count = extras.get("mount_ears", 0)
        if ears_count in (4, 6, 8):
            price += ctx.prices.mount_ear_price * ears_count

        return price