"""Additional tests for Gate, Transom, Glass calculators and BaseCalculator options integration."""

import pytest
from utils.calculators.base_calculator import CalculatorContext, PriceData, GlassItemData
from utils.calculators.gate_calculator import GateCalculator
from utils.calculators.transom_calculator import TransomCalculator
from utils.calculators.glass_calculator import GlassCalculator, GlassCalcParams
from utils.calculators.door_calculator import DoorCalculator
from utils.calculators.hatch_calculator import HatchCalculator
from utils.validators import validate_dimensions
from constants import PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM

# ----- Fixtures -----

@pytest.fixture
def base_prices() -> PriceData:
    p = PriceData()
    p.doors_std_single = 15000.0
    p.doors_wide_markup = 2500.0
    p.doors_per_m2_nonstd = 11000.0
    p.doors_double_std = 28000.0
    p.hatch_std = 4000.0
    p.hatch_wide_markup = 800.0
    p.hatch_per_m2_nonstd = 9000.0
    p.gate_per_m2 = 3500.0
    p.gate_large_per_m2 = 4200.0
    p.transom_per_m2 = 8000.0
    p.transom_min = 4500.0
    p.cutout_price = 800.0
    p.deflector_per_m2 = 3200.0
    p.trim_per_lm = 650.0
    p.closer_price = 2500.0
    p.hinge_price = 300.0
    p.anti_theft_price = 450.0
    p.gkl_price = 1200.0
    p.mount_ear_price = 80.0
    p.threshold_price = 2000.0
    return p

# ----- Helper factory -----

def make_ctx(prod: str, subtype: str, h: float, w: float, is_double: bool, prices: PriceData, **kwargs) -> CalculatorContext:
    return CalculatorContext(product_type=prod, subtype=subtype, height=h, width=w,
                             is_double_leaf=is_double, prices=prices, **kwargs)

# ----- GateCalculator tests -----

class TestGateCalculator:
    def test_normal_gate_label_default_single(self, base_prices: PriceData):
        # area = 3.0 (3000x1000), h>2490 but <3000 and w<3000 -> per m2
        ctx = make_ctx(PRODUCT_GATE, "Технические", 3000, 1000, False, base_prices)
        expected_price = base_prices.gate_per_m2 * 3.0
        assert GateCalculator().calculate(ctx) == expected_price

    def test_large_gate_label_higher_dimensions(self, base_prices: PriceData):
        # area = (3000/1000)*(1700/1000) = 5.1, h>=3000 so large_per_m2
        ctx = make_ctx(PRODUCT_GATE, "�����������", 3000, 1700, False, base_prices)
        area = (ctx.height / 1000.0) * (ctx.width / 1000.0)
        expected_price = base_prices.gate_large_per_m2 * area
        assert GateCalculator().calculate(ctx) == expected_price

    def test_small_gate_below_threshold(self, base_prices: PriceData):
        # area = 2.5 (2500x1000), h<2490 so small uses per m2 price
        ctx = make_ctx(PRODUCT_GATE, "Технические", 2000, 1000, False, base_prices)
        expected_price = base_prices.gate_per_m2 * 2.0
        assert abs(GateCalculator().calculate(ctx) - expected_price) < 0.01

# ----- TransomCalculator tests -----

class TestTransomBoundary:
    def test_minimum_size_acceptable(self, base_prices: PriceData):
        # min height 200, min width 400
        ctx = make_ctx(PRODUCT_TRANSOM, "Техническая", 200, 400, False, base_prices)
        # area = 0.08, price should be 0.08*8000 = 640, but min 4500 applied
        assert TransomCalculator().calculate(ctx) == 4500.0

    def test_below_min_height(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_TRANSOM, "Техническая", 150, 400, False, base_prices)
        valid, msg = validate_dimensions(PRODUCT_TRANSOM, 150, 400)
        assert not valid

    def test_below_min_width(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_TRANSOM, "Техническая", 300, 350, False, base_prices)
        valid, msg = validate_dimensions(PRODUCT_TRANSOM, 300, 350)
        assert not valid

# ----- GlassCalculator tests -----

class TestGlassCalculatorOptions:
    def test_standard_glass_no_angle_penalty(self, base_prices: PriceData):
        params = GlassCalcParams(height_mm=1000, width_mm=2000,
                                type_price_m2=2500.0, type_min_price=500.0,
                                options_prices=[], double_sided=False)
        # area = 2.0, base=5000 > 500 => 5000
        assert GlassCalculator.calculate(params) == 5000.0

    def test_aspect_ratio_penalty(self, base_prices: PriceData):
        params = GlassCalcParams(height_mm=200, width_mm=1000,
                                type_price_m2=2000.0, type_min_price=500.0,
                                options_prices=[], double_sided=False)
        # area = 0.2, base=400 < 500 => 500, *1.5 => 750
        assert GlassCalculator.calculate(params) == 750.0

    def test_double_sided_options_min_not_doubled(self, base_prices: PriceData):
        params = GlassCalcParams(height_mm=500, width_mm=500,
                                type_price_m2=2000.0, type_min_price=1000.0,
                                options_prices=[(100.0, 200.0)], double_sided=True)
        # base=1000, option=50*2=100 < 200 => 200, total 1200
        assert GlassCalculator.calculate(params) == 1200.0

# ----- BaseCalculator options integration -----

class TestBaseOptionsIntegration:
    def test_hinge_and_anti_theft_price(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices,
                       extra_options={
                           "hinge_count_active": 3,
                           "hinge_default_active": 1,
                           "anti_theft_pins": True
                       })
        # hinge: 3 active - 1 default = 2 * hinge_price(300) = 600
        # anti theft: 1 leaf * 450 = 450
        # base 15000
        expected = 15000 + 600 + 450
        assert DoorCalculator().calculate(ctx) == expected

    def test_mount_ears_col_count(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices,
                       extra_options={
                           "mount_ears_count": 4
                       })
        expected = 15000 + 4 * base_prices.mount_ear_price
        assert DoorCalculator().calculate(ctx) == expected

    def test_threshold_price_double_leaf(self, base_prices: PriceData):
        # Test that threshold price is applied for double-leaf doors
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, True, base_prices,
                       threshold_enabled=True)
        # Base price for double standard door + 2 * threshold_price
        expected = base_prices.doors_double_std + base_prices.threshold_price * 2
        assert DoorCalculator().calculate(ctx) == expected

    def test_deflector_price_single_side(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices,
                       deflector_height_mm=200, deflector_double_side=False)
        # deflector area = width 0.9 * 0.2 = 0.18
        deflector_cost = 0.18 * base_prices.deflector_per_m2
        expected = 15000 + deflector_cost
        assert abs(DoorCalculator().calculate(ctx) - expected) < 1e-6

    def test_deflector_price_double_side(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices,
                       deflector_height_mm=200, deflector_double_side=True)
        deflector_cost = 0.18 * base_prices.deflector_per_m2 * 2
        expected = 15000 + deflector_cost
        assert abs(DoorCalculator().calculate(ctx) - expected) < 1e-6

    def test_trim_price_multipliers(self, base_prices: PriceData):
        # trim depth > 150
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices,
                       trim_depth_mm=200)
        lin_meters = (2 * 2000 + 900) / 1000
        trim_price = lin_meters * base_prices.trim_per_lm * (200/150)
        expected = 15000 + trim_price
        assert abs(DoorCalculator().calculate(ctx) - expected) < 1e-6

    def test_custom_options_price(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices,
                       extra_options={
                           "custom": {"special_boost": 2}
                       })
        # price per custom option a = 0 if not defined in custom_options
        base_prices.custom_options["special_boost"] = 500.0
        expected = 15000 + 2 * 500.0
        assert DoorCalculator().calculate(ctx) == expected

# ----- Full suite run command (for verification) -----

# Run all tests now to verify
if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))
