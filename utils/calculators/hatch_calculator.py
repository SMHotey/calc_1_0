"""Калькулятор стоимости люков по правилам п.4.3.

Содержит:
- HatchCalculator: расчёт стоимости люков (технических, ревизионных, EI 60)
"""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext


class HatchCalculator(BaseCalculator):
    """Логика расчёта люков: стандартный, широкий, нестандартный, ревизионный, двустворчатый.

    Рассчитывает стоимость люка на основе:
    - Размеров (высота, ширина)
    - Подтипа (Технический, EI 60, Ревизионный)
    - Площади изделия
    - Цен из прайс-листа

    Особенности:
    - Ревизионные люки имеют ограничение по площади (0.4 м²)
    - При превышении - переход на расчёт по м²
    """

    def calculate_base(self, ctx: CalculatorContext) -> float:
        """Расчёт базовой стоимости люка без опций.

        Args:
            ctx: контекст расчёта с размерами, ценами, типом изделия

        Returns:
            Базовая стоимость люка в рублях
        """
        h, w = ctx.height, ctx.width
        area = (h / 1000.0) * (w / 1000.0)
        p = ctx.prices
        
        std_single = p.type_std_single if p.has_type_specific_price else p.hatch_std
        wide_markup = p.type_wide_markup if p.has_type_specific_price else p.hatch_wide_markup
        per_m2 = p.type_per_m2_nonstd if p.has_type_specific_price else p.hatch_per_m2_nonstd

        if ctx.subtype == "Ревизионный":
            return std_single if area <= 0.4 else round(per_m2 * area, 2)

        if not ctx.is_double_leaf:
            if 300 <= h <= 1000 and 300 <= w <= 1000:
                return std_single
            if (h > 1000 or w > 1000) and h < 1100 and w < 1100:
                return std_single + wide_markup
            if (h > 1100 or w > 1100) and h < 1500 and w < 1500:
                wide_price = std_single + wide_markup
                return max(per_m2 * area, wide_price)
        else:
            if h <= 1000 and w <= 1000:
                return std_single * 1.2
            if (h > 1000 or w > 1000) and h < 1100 and w < 1100:
                return (std_single + wide_markup) * 1.2
            if (h > 1100 or w > 1100) and h < 1500 and w < 1500:
                min_price = (std_single + wide_markup) * 1.2
                return max(per_m2 * area, min_price)

        return per_m2 * area