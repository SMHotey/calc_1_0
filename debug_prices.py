from db.database import SessionLocal, init_db
from models.price_list import BasePriceList, PersonalizedPriceList
from sqlalchemy import select
import os

# Fresh DB
if os.path.exists('db/metalcalc.db'):
    os.remove('db/metalcalc.db')
init_db()

session = SessionLocal()

# Check IDs
bases = session.execute(select(BasePriceList)).scalars().all()
print('Base:', [(b.id, b.name) for b in bases])

from controllers.price_list_controller import PriceListController
ctrl = PriceListController(session)

# Create personalized
personal = ctrl.create_personalized('Test', base_id=bases[0].id)
print(f'Personal: id={personal.id}, base_price_list_id={personal.base_price_list_id}')

# Update custom price
ctrl.update_personalized(personal.id, {'custom_doors_price_std_single': 50000.0})
print(f'After update: custom_doors_price_std_single={personal.custom_doors_price_std_single}')

# Get prices for calculation
prices = ctrl.get_price_for_calculation(personal.id)
print(f'Prices for personal.id={personal.id}: doors_price_std_single={prices["doors_price_std_single"]}')

# Get prices for base
base_prices = ctrl.get_price_for_calculation(bases[0].id)
print(f'Prices for base.id={bases[0].id}: doors_price_std_single={base_prices["doors_price_std_single"]}')

session.close()
