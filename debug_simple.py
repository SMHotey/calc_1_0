"""Simple test: trace what get_price_for_calculation() returns."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, SessionLocal, _seed_demo_data
from controllers.price_list_controller import PriceListController

# Setup
engine = create_engine('sqlite:///:memory:?cache=shared')
Session = sessionmaker(bind=engine)
import models
Base.metadata.create_all(bind=engine)
session = Session()
_seed_demo_data(lambda: session)

# Create controller
price_ctrl = PriceListController(session=session)

# Create personalized
base = price_ctrl.get_base_price_list()
print(f'Base: id={base.id}, name={base.name}')

personal = price_ctrl.create_personalized("Test", base_id=base.id)
print(f'Personal: id={personal.id}, name={personal.name}')

# Update via controller
price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 25000.0})
print(f'After update: custom_doors_price_std_single={personal.custom_doors_price_std_single}')

# Now test get_price_for_calculation
print(f'\n--- get_price_for_calculation(personal.id) ---')
p1 = price_ctrl.get_price_for_calculation(personal.id)
print(f'Result: doors_price_std_single={p1["doors_price_std_single"]}')
print(f'Expected: 25000.0')

print(f'\n--- get_price_for_calculation(base.id) ---')
p2 = price_ctrl.get_price_for_calculation(base.id)
print(f'Result: doors_price_std_single={p2["doors_price_std_single"]}')
print(f'Expected: 15000.0')
