"""Debug: trace get_price_for_calculation()."""
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

# Create controllers
price_ctrl = PriceListController(session=session)
calc_ctrl = CalculatorController(session=session)

# Create personalized list
personal = price_ctrl.create_personalized(
    "Test Personalized",
    base_id=price_ctrl.get_base_price_list().id
)
print(f'Created personalized: id={personal.id}, base_price_list_id={personal.base_price_list_id}')

# Set custom price
personal.custom_doors_price_std_single = 25000.0
price_ctrl.session.commit()
print(f'Set custom price = 25000.0')

# Check get_price_list_by_id()
pl = price_ctrl.get_price_list_by_id(personal.id)
print(f'get_price_list_by_id({personal.id}): type={type(pl).__name__}, id={getattr(pl, "id", None)}')

# Now get prices
prices = price_ctrl.get_price_for_calculation(personal.id)
print(f'get_price_for_calculation({personal.id}): doors_price_std_single = {prices.get("doors_price_std_single")}')
print(f'Expected: 25000.0')
