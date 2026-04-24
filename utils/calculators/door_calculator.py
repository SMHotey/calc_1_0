"""Калькулятор стоимости дверей.

Содержит:
- DoorCalculator: расчёт стоимости металлических дверей
"""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext


class DoorCalculator(BaseCalculator):
    """Реализует логику расчёта дверей: стандартная, широкая, нестандартная, двустворчатая.

    Рассчитывает стоимость двери на основе:
    - Размеров (высота, ширина)
    - Типа (однолистовая, двустворчатая)
    - Подтипа (Техническая, EI 60, Квартирная и т.д.)
    - Цен из прайс-листа (базовых или type-specific)

    Алгоритм (по п.1-5 требований):
    1) Одностворчатая стандартная: h=1500-2200, w=500-1000 → цена за единицу
    2) Одностворчатая широкая: h=1500-2200, w=1010-1100 → std + markup
    3) Одностворчатая нестандартная: h=1500-2490, w=500-1400, area<3.6, (h>2200 or w>1100) → per m², min = п.2
    4) Двухстворчатая стандартная: h=1500-2200, w=800-1300 → цена за единицу
    5) Двухстворчатая нестандартная: h=1500-2490, w=800-2390, area<3.6, (h>2200 or w>1300) → per m², min = п.4
    """

    def calculate_base(self, ctx: CalculatorContext) -> float:
        """Расчёт базовой стоимости двери без опций.

        Args:
            ctx: контекст расчёта с размерами, ценами, типом изделия

        Returns:
            Базовая стоимость двери в рублях
        """
        h, w = ctx.height, ctx.width
        area = (h / 1000.0) * (w / 1000.0)
        p = ctx.prices
        is_double = ctx.is_double_leaf
        
        std_single = p.type_std_single if p.has_type_specific_price else p.doors_std_single
        wide_markup = p.type_wide_markup if p.has_type_specific_price else p.doors_wide_markup
        double_std = p.type_double_std if p.has_type_specific_price else p.doors_double_std
        per_m2_nonstd = p.type_per_m2_nonstd if p.has_type_specific_price else p.doors_per_m2_nonstd

        # === Одностворчатые двери ===
        if not is_double:
            # п.1: Стандартная: h=1500-2200, w=500-1000
            if 1500 <= h <= 2200 and 500 <= w <= 1000:
                return std_single
            # п.2: Широкая: h=1500-2200, w=1010-1100
            if 1500 <= h <= 2200 and 1010 <= w <= 1100:
                return std_single + wide_markup
            # п.3: Нестандартная: h=1500-2490, w=500-1400, area<3.6, (h>2200 or w>1100)
            if 1500 <= h <= 2490 and 500 <= w <= 1400 and area < 3.6 and (h > 2200 or w > 1100):
                calc_price = per_m2_nonstd * area
                # Min = цена п.2 (стандартная + wideMarkup)
                return max(calc_price, std_single + wide_markup)
        # === Двухстворчатые двери ===
        else:
            # п.4: Стандартная: h=1500-2200, w=800-1300
            if 1500 <= h <= 2200 and 800 <= w <= 1300:
                return double_std
            # п.5: Нестандартная: h=1500-2490, w=800-2390, area<3.6, (h>2200 or w>1300)
            if 1500 <= h <= 2490 and 800 <= w <= 2390 and area < 3.6 and (h > 2200 or w > 1300):
                calc_price = per_m2_nonstd * area
                # Min = цена п.4 (двухстворчатая стандартная)
                return max(calc_price, double_std)

        # По умолчанию - нестандартная per m²
        return per_m2_nonstd * area