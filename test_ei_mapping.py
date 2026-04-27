"""Test EI price mapping."""
from controllers.calculator_controller import CalculatorController

ctrl = CalculatorController()

# Тест: EI-60 - должен использовать цены как EIS-60
r = ctrl.validate_and_calculate("Дверь", "EI 60", 2000, 900, None, {}, 0, 0, 1)
print(f"EI 60: {r['price_per_unit']}")

# Тест: EIWS-60 - должен использовать цены как EIS-60  
r = ctrl.validate_and_calculate("Дверь", "EIWS 60", 2000, 900, None, {}, 0, 0, 1)
print(f"EIWS 60: {r['price_per_unit']}")

# Тест: EIS-60 - оригинальная цена
r = ctrl.validate_and_calculate("Дверь", "EIS 60", 2000, 900, None, {}, 0, 0, 1)
print(f"EIS 60: {r['price_per_unit']}")