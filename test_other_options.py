#!/usr/bin/env python3
"""Test script to verify that 'other' options (delivery, measurement, installation, bonus) 
are correctly added to the price calculation."""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.calculators.base_calculator import PriceData, CalculatorContext, BaseCalculator
from utils.calculators.door_calculator import DoorCalculator

def test_other_options():
    """Test that other options are correctly added to the price."""
    
    # Create a DoorCalculator instance
    calculator = DoorCalculator()
    
    # Create a PriceData object with base prices
    prices = PriceData(
        doors_std_single=10000.0,  # Base price for a standard door
        doors_per_m2_nonstd=8000.0,  # Price per m2 for non-standard
        doors_wide_markup=2000.0,  # Wide door markup
        doors_double_std=18000.0,  # Double door standard price
        # Other prices default to 0.0
    )
    
    # Create a CalculatorContext with some options including "other" options
    ctx = CalculatorContext(
        product_type="Дверь",
        subtype="Техническая",
        height=2000.0,  # 2000 mm
        width=800.0,    # 800 mm
        is_double_leaf=False,
        prices=prices,
        color_external=7035,
        color_internal=7035,
        metal_thickness="1.0-1.0",
        glass_items=[],
        closers_count=0,
        grilles=[],
        threshold_enabled=False,
        deflector_height_mm=0.0,
        deflector_double_side=False,
        trim_depth_mm=0.0,
        extra_options={
            # Standard options
            "is_double_leaf": False,
            # Other options that should be added directly to price
            "other": {
                "delivery": 1500.0,      # Delivery cost
                "measurement": 500.0,    # Measurement cost
                "installation": 3000.0,  # Installation cost
                "bonus": -1000.0         # Discount (negative bonus)
            }
        },
        markup_percent=0.0,  # No percentage markup for this test
        markup_abs=0.0,      # No absolute markup for this test
        hardware_items=[]    # No hardware for this test
    )
    
    # Calculate the price
    result = calculator.calculate(ctx)
    
    # Expected calculation:
    # Base price: Since height=2000, width=800 -> area=1.6 m2
    # This falls into standard range (h=1500-2200, w=500-1000) -> doors_std_single = 10000.0
    # Other options: 1500 + 500 + 3000 - 1000 = 4000.0
    # Total expected: 10000.0 + 4000.0 = 14000.0
    
    expected_base = 10000.0
    expected_other = 1500.0 + 500.0 + 3000.0 - 1000.0  # 4000.0
    expected_total = expected_base + expected_other
    
    print(f"Base price: {expected_base}")
    print(f"Other options: {expected_other}")
    print(f"Expected total: {expected_total}")
    print(f"Actual result: {result}")
    
    # Check if the result matches expected (within tolerance for floating point)
    if abs(result - expected_total) < 0.01:
        print("✅ TEST PASSED: Other options are correctly added to the price")
        return True
    else:
        print(f"❌ TEST FAILED: Expected {expected_total}, got {result}")
        return False

if __name__ == "__main__":
    success = test_other_options()
    sys.exit(0 if success else 1)