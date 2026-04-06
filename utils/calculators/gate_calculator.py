"""Калькулятор стоимости ворот по правилам п.4.4."""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext


class GateCalculator(BaseCalculator):
    """Ворота всегда двустворчатые. Расчёт по площади с учётом габаритов."""

    def calculate_base(self, ctx: CalculatorContext) -> float:
        h, w = ctx.height, ctx.width
        area = (h / 1000.0) * (w / 1000.0)
        p = ctx.prices
        
        per_m2 = p.type_per_m2_nonstd if p.has_type_specific_price else p.gate_per_m2

        is_standard = (area > 3.6 or h > 2490) and h < 3000 and w < 3000
        if is_standard:
            return per_m2 * area

        is_large = area > 3.6 and (h >= 3000 or w >= 3000)
        if is_large:
            return p.gate_large_per_m2 * area

        return per_m2 * area