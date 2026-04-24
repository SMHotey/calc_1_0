"""Калькулятор стоимости люков.

Содержит:
- HatchCalculator: расчёт стоимости люков (технических, ревизионных, EI 60)
"""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext


class HatchCalculator(BaseCalculator):
    """Логика расчёта люков.

    Рассчитывает стоимость люка на основе:
    - Размеров (высота, ширина)
    - Подтипа (Технический, EI 60, Ревизионный)
    - Площади изделия
    - Цен из прайс-листа

    Алгоритм (по п.6-10 требований):
    6) Одностворчатый люк стандартный: h=300-1000, w=300-1000 → цена за единицу
    7) Одностворчатый люк широкий: (h>1000 or w>1000) и оба <1100 → std + markup
    8) Одностворчатый люк нестандартный: (h>1100 or w>1100) и оба <1500 → per m², min = std+markup
    9) Люк ревизионный (однолистовой): area<=0.4 → fixed, else per m²
    10) Двухстворчатый люк:
        - h<=1000 and w<=1000 → std * 1.2
        - (h>1000 or w>1000) и оба <1100 → (std+markup) * 1.2
        - (h>1100 or w>1100) и оба <1500 → per m², min = (std+markup) * 1.2
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
        
        std = p.type_std_single if p.has_type_specific_price else p.hatch_std
        wide_markup = p.type_wide_markup if p.has_type_specific_price else p.hatch_wide_markup
        per_m2 = p.type_per_m2_nonstd if p.has_type_specific_price else p.hatch_per_m2_nonstd

        # === Ревизионный (п.9) ===
        if ctx.subtype == "Ревизионный":
            if area <= 0.4:
                return std
            return per_m2 * area

        # === Одностворчатый люк (п.6-8) ===
        if not ctx.is_double_leaf:
            # п.6: Стандартный: h=300-1000, w=300-1000
            if 300 <= h <= 1000 and 300 <= w <= 1000:
                return std
            # п.7: Широкий: (h>1000 or w>1000) и оба <1100
            if (h > 1000 or w > 1000) and h < 1100 and w < 1100:
                return std + wide_markup
            # п.8: Нестандартный: (h>1100 or w>1100) и оба <1500
            if (h > 1100 or w > 1100) and h < 1500 and w < 1500:
                calc_price = per_m2 * area
                # Min = std + wide_markup (п.7)
                return max(calc_price, std + wide_markup)
        
        # === Двухстворчатый люк (п.10) ===
        else:
            # h<=1000 and w<=1000 → std * 1.2
            if h <= 1000 and w <= 1000:
                return std * 1.2
            # (h>1000 or w>1000) и оба <1100 → (std+markup) * 1.2
            if (h > 1000 or w > 1000) and h < 1100 and w < 1100:
                return (std + wide_markup) * 1.2
            # (h>1100 or w>1100) и оба <1500 → per m², min = (std+markup) * 1.2
            if (h > 1100 or w > 1100) and h < 1500 and w < 1500:
                calc_price = per_m2 * area
                min_price = (std + wide_markup) * 1.2
                return max(calc_price, min_price)

        # По умолчанию - per m²
        return per_m2 * area