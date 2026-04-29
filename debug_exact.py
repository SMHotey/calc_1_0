"""Debug: mimic exact test logic."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, SessionLocal, _seed_demo_data
from controllers.price_list_controller import PriceListController 
from controllers.calculator_controller import CalculatorController

# Setup
engine = create_engine('sqlite:///:memory:?cache=shared')
Session = sessionmaker(bind=engine)
import models
Base.metadata.create_all(bind=engine)
session = Session()
_seed_demo_data(lambda: session)

# Create controllers with SAME session
price_ctrl = PriceListController(session=session)
calc_ctrl = CalculatorController(session=session)

# Mimic test_get_price_for_calculation_personalized
base = price_ctrl.get_base_price_list()
print(f'Base: id={base.id}, name={base.name}')

personal = price_ctrl.create_personalized(
    "С кастомной ценой",
    base_id=base.id
)
print(f'Personalized: id={personal.id}, name={personal.name}')

# Set custom price via update (like the test does)
price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 25000.0})
print(f'After update: custom_doors_price_std_single={personal.custom_doors_price_std_single}')

# Now get prices
prices = price_ctrl.get_price_for_calculation(personal.id)
print(f'get_price_for_calculation(personal.id): doors_price_std_single = {prices.get("doors_price_std_single")}')
print(f'Expected: 25000.0')

# Also check base
base_prices = price_ctrl.get_price_for_calculation(base.id)
print(f'get_price_for_calculation(base.id): doors_price_std_single = {base_prices.get("doors_price_std_single")}')
print(f'Expected: 15000.0')
