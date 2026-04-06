"""Калькулятор стоимости фрамуг по правилам п.4.5."""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext


class TransomCalculator(BaseCalculator):
    """Мин. высота 200, ширина 400. Цена за м², но не менее минимума."""

    def calculate_base(self, ctx: CalculatorContext) -> float:
        area = (ctx.height / 1000.0) * (ctx.width / 1000.0)
        p = ctx.prices
        per_m2 = p.type_per_m2_nonstd if p.has_type_specific_price else p.transom_per_m2
        return max(area * per_m2, p.transom_min)