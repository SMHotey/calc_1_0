#!/usr/bin/env python
"""Test why personalized price isn't being used in calculator."""
from db.database import SessionLocal, init_db
from controllers.price_list_controller import PriceListController
from controllers.calculator_controller import CalculatorController
from sqlalchemy import select
from models.price_list import BasePriceList
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
print(f'Base: id={base.id}, doors_price_std_single={base.doors_price_std_single}')

# Create personalized
personal = price_ctrl.create_personalized('Test', base_id=base.id)
print(f'Personal: id={personal.id}, base_price_list_id={personal.base_price_list_id}')

# Update custom price
price_ctrl.update_personalized(personal.id, {'custom_doors_price_std_single': 50000.0})
print(f'Updated custom_doors_price_std_single to 50000')

# Test validate_and_calculate with base
result_base = calc_ctrl.validate_and_calculate(
    'Дверь', 'Техническая',
    2000, 900,
    base.id,
    {}
)
print(f'Base result: price_per_unit={result_base.get("price_per_unit")}')

# Test with personalized - WITHOUT is_personalized flag
result_personal = calc_ctrl.validate_and_calculate(
    'Дверь', 'Техническая',
    2000, 900,
    personal.id,
    {}
)
print(f'Personal result (no flag): price_per_unit={result_personal.get("price_per_unit")}')

session.close()
