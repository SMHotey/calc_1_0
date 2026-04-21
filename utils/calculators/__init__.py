"""Пакет модулей расчёта стоимости металлических изделий.

Содержит:
- BaseCalculator: базовый класс калькулятора
- CalculatorContext: контекст расчёта (входные данные)
- PriceData: структура с ценами для расчёта
- DoorCalculator: расчёт стоимости дверей
- HatchCalculator: расчёт стоимости люков
- GateCalculator: расчёт стоимости ворот
- TransomCalculator: расчёт стоимости фрамуг
"""

from utils.calculators.base_calculator import BaseCalculator, CalculatorContext, PriceData
from utils.calculators.door_calculator import DoorCalculator
from utils.calculators.hatch_calculator import HatchCalculator
from utils.calculators.gate_calculator import GateCalculator
from utils.calculators.transom_calculator import TransomCalculator

__all__ = [
    "BaseCalculator", "CalculatorContext", "PriceData",
    "DoorCalculator", "HatchCalculator", "GateCalculator", "TransomCalculator"
]