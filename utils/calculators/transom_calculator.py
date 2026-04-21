"""Калькулятор стоимости фрамуг по правилам п.4.5.

Содержит:
- TransomCalculator: расчёт стоимости фрамуг
"""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext


class TransomCalculator(BaseCalculator):
    """Мин. высота 200, ширина 400. Цена за м², но не менее минимума.

    Рассчитывает стоимость фрамуги на основе:
    - Площади изделия (высота × ширина / 1_000_000)
    - Подтипа (Техническая, EI 60)
    - Цены за м² из прайс-листа

    Особенности:
    - Минимальная высота: 200 мм
    - Минимальная ширина: 400 мм
    - Расчёт по площади, но с ограничением минимальной цены
    - Если площадь слишком мала - применяется минимальная цена
    """

    def calculate_base(self, ctx: CalculatorContext) -> float:
        """Расчёт базовой стоимости фрамуги без опций.

        Args:
            ctx: контекст расчёта с размерами, ценами, типом изделия

        Returns:
            Базовая стоимость фрамуги в рублях
        """
        area = (ctx.height / 1000.0) * (ctx.width / 1000.0)
        p = ctx.prices
        per_m2 = p.type_per_m2_nonstd if p.has_type_specific_price else p.transom_per_m2
        return max(area * per_m2, p.transom_min)