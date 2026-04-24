"""Калькулятор стоимости ворот.

Содержит:
- GateCalculator: расчёт стоимости ворот
"""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext


class GateCalculator(BaseCalculator):
    """Ворота - расчёт по площади с учётом габаритов.

    Рассчитывает стоимость ворот на основе:
    - Площади изделия (высота × ширина / 1_000_000)
    - Подтипа (Технические, EI 60, Однолистовые)
    - Цены за м² из прайс-листа

    Алгоритм (по п.11-12 требований):
    11) Стандартные: area>3.6 или h>2490, но h<3000 и w<3000 → per m²
    12) Большие: area>3.6 и (h>=3000 или w>=3000) → larger per m²
    """

    def calculate_base(self, ctx: CalculatorContext) -> float:
        """Расчёт базовой стоимости ворот без опций.

        Args:
            ctx: контекст расчёта с размерами, ценами, типом изделия

        Returns:
            Базовая стоимость ворот в рублях
        """
        h, w = ctx.height, ctx.width
        area = (h / 1000.0) * (w / 1000.0)
        p = ctx.prices
        
        per_m2 = p.type_per_m2_nonstd if p.has_type_specific_price else p.gate_per_m2
        large_per_m2 = p.gate_large_per_m2

        # п.11: Стандартные = area > 3.6 или h > 2490, но h < 3000 и w < 3000
        if (area > 3.6 or h > 2490) and h < 3000 and w < 3000:
            return per_m2 * area

        # п.12: Большие = area > 3.6 и (h >= 3000 или w >= 3000)
        if area > 3.6 and (h >= 3000 or w >= 3000):
            return large_per_m2 * area

        # Малые - по умолчанию стандартная цена
        return per_m2 * area