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

    Алгоритм:
    1. Определяет категорию изделия (стандартная/широкая/нестандартная)
    2. Применяет соответствующую формулу расчёта
    3. Добавляет стоимость опций (стекло, фурнитура, доводчик и т.д.)
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

        if not is_double:
            if 1500 <= h <= 2200 and 500 <= w <= 1000:
                return std_single
            if 1500 <= h <= 2200 and 1010 <= w <= 1100:
                return std_single + wide_markup
            if 1500 <= h <= 2490 and 500 <= w <= 1400 and area < 3.6 and (h > 2200 or w > 1100):
                calc_price = per_m2_nonstd * area
                return max(calc_price, std_single + wide_markup)
        else:
            if 1500 <= h <= 2200 and 800 <= w <= 1300:
                return double_std
            if 1500 <= h <= 2490 and 800 <= w <= 2390 and area < 3.6 and (h > 2200 or w > 1300):
                calc_price = per_m2_nonstd * area
                return max(calc_price, double_std)

        return per_m2_nonstd * area