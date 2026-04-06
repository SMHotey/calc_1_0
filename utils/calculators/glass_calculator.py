"""Вспомогательный модуль для точного расчёта остекления (п.5.2)."""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class GlassCalcParams:
    height_mm: float
    width_mm: float
    type_price_m2: float
    type_min_price: float
    options_prices: List[Tuple[float, float]]  # (price_per_m2, min_price)
    double_sided: bool


class GlassCalculator:
    """Статический калькулятор стоимости остекления и его опций."""

    @staticmethod
    def calculate(params: GlassCalcParams) -> float:
        """
        Рассчитывает стоимость стекла согласно п.5.2 ТЗ.

        Формула:
        1. База = (цена_м2 * площадь), но >= мин_цена
        2. Если отношение сторон <= 1/5 -> *1.5
        3. + цена выреза
        4. Опции: (цена_м2_опции * площадь), >= мин_опции. Если 2 стороны -> *2, мин не удваивается.
        """
        area = (params.height_mm / 1000.0) * (params.width_mm / 1000.0)
        base_price = max(area * params.type_price_m2, params.type_min_price)

        # Проверка соотношения сторон
        ratio = params.height_mm / params.width_mm if params.width_mm > 0 else float('inf')
        if ratio <= 0.2 or ratio >= 5.0:
            base_price *= 1.5

        # Добавление опций
        options_total = 0.0
        for opt_price_m2, opt_min in params.options_prices:
            opt_val = area * opt_price_m2
            if params.double_sided:
                opt_val *= 2.0
            opt_val = max(opt_val, opt_min)
            options_total += opt_val

        return base_price + options_total