from db.database import SessionLocal, init_db
from controllers.price_list_controller import PriceListController
from controllers.calculator_controller import CalculatorController
import os

# Fresh DB
if os.path.exists('db/metalcalc.db'):
    os.remove('db/metalcalc.db')
init_db()

session = SessionLocal()

# Create controllers
price_ctrl = PriceListController(session)
calc_ctrl = CalculatorController(session)

# Get base
base = price_ctrl.get_base_price_list()
print(f'Base: id={base.id}')

# Create personalized
personal = price_ctrl.create_personalized('Test', base_id=base.id)
print(f'Personal: id={personal.id}')

# Update custom price
price_ctrl.update_personalized(personal.id, {'custom_doors_price_std_single': 50000.0})

# Check what get_price_for_calculation returns
prices = price_ctrl.get_price_for_calculation(personal.id)
print(f'Prices from get_price_for_calculation:')
print(f'  doors_price_std_single={prices.get("doors_price_std_single")}')
print(f'  type(prices)={type(prices)}')

# Now test validate_and_calculate with personalized
result = calc_ctrl.validate_and_calculate(
    'Дверь', 'Техническая',
    2000, 900,
    personal.id,
    {}
)
print(f'Result: price_per_unit={result.get("price_per_unit")}')

session.close()
