# Check what calculator returns vs what's saved in DB
from controllers.calculator_controller import CalculatorController

calc = CalculatorController()

# Test with simple door - NO options
result1 = calc.validate_and_calculate(
    product_type='Дверь',
    subtype='Техническая',
    height=2100,
    width=1000,
    price_list_id=1,
    options={'is_double_leaf': False},
    markup_percent=0,
    markup_abs=0,
    quantity=1
)

print("=== Calculator with NO options ===")
print(f"price_per_unit (base): {result1.get('price_per_unit')}")
print(f"total_price: {result1.get('total_price')}")
details = result1.get('details', {})
print(f"details['base_price']: {details.get('base_price')}")
print(f"details['final']: {details.get('final')}")
print(f"extras_breakdown: {details.get('extras_breakdown')}")

# Test WITH hardware
result2 = calc.validate_and_calculate(
    product_type='Дверь',
    subtype='Техническая',
    height=2100,
    width=1000,
    price_list_id=1,
    options={'is_double_leaf': False, 'hardware_ids': [1]},  # Add lock
    markup_percent=0,
    markup_abs=0,
    quantity=1
)

print("\n=== Calculator WITH hardware (lock) ===")
print(f"price_per_unit (base): {result2.get('price_per_unit')}")
print(f"total_price: {result2.get('total_price')}")
details2 = result2.get('details', {})
print(f"details['base_price']: {details2.get('base_price')}")
print(f"details['final']: {details2.get('final')}")
print(f"extras_breakdown: {details2.get('extras_breakdown')}")

print("\n=== THE PROBLEM ===")
print(f"details['base_price'] = {details2.get('base_price')} (price WITHOUT options)")
print(f"details['final'] = {details2.get('final')} (price WITH options)")
print(f"result['price_per_unit'] = {result2.get('price_per_unit')} (same as final)")
print("")
print("In the saved data, we store 'base_price' = price_per_unit = final price!")
print("But in the dialog, we should show base_price WITHOUT options!")