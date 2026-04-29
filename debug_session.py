"""Debug script to trace session issues."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, SessionLocal, _seed_demo_data
from controllers.price_list_controller import PriceListController
from controllers.calculator_controller import CalculatorController

# Setup
engine = create_engine('sqlite:///:memory:?cache=shared')
Session = sessionmaker(bind=engine)
import models  # Register models
Base.metadata.create_all(bind=engine)
session = Session()
_seed_demo_data(lambda: session)

# Test
price_ctrl = PriceListController(session=session)
calc_ctrl = CalculatorController(session=session)

base = price_ctrl.get_base_price_list()
print(f'Before: base.doors_price_std_single = {base.doors_price_std_single}')

base.doors_price_std_single = 10000.0
session.flush()
print(f'After flush: base.doors_price_std_single = {base.doors_price_std_single}')

# Now calculate
result = calc_ctrl.validate_and_calculate(
    "Дверь", "Техническая",
    2000, 900, base.id, {}
)
print(f'Calculation result: price_per_unit = {result.get("price_per_unit")}')
print(f'Expected: 10000.0')
