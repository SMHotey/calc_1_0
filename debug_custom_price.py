"""Debug: why custom price isn't used."""
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

# Check base price
base = price_ctrl.get_base_price_list()
print(f'Base price: doors_price_std_single = {base.doors_price_std_single}')

# Create personalized list
personal = price_ctrl.create_personalized(
    "Test Personalized",
    base_id=base.id
)
print(f'Created personalized list: id={personal.id}, name={personal.name}')

# Set custom price
personal.custom_doors_price_std_single = 25000.0
price_ctrl.session.commit()
print(f'Set custom_doors_price_std_single = 25000.0, committed')

# Check get_price_for_calculation
prices = price_ctrl.get_price_for_calculation(personal.id)
print(f'get_price_for_calculation(personal.id): doors_price_std_single = {prices.get("doors_price_std_single")}')

# Now calculate
result = calc_ctrl.validate_and_calculate(
    "Дверь", "Техническая",
    2000, 900, personal.id, {}
)
print(f'Calculation result: price_per_unit = {result.get("price_per_unit")}')
print(f'Expected: 25000.0')
