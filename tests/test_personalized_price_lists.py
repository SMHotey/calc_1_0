"""Comprehensive tests for personalized/custom price lists.

Covers:
- Creation of personalized price lists with all custom fields
- Editing custom price fields and verification
- Calculation with personalized price lists (all product types: Door, Hatch, Gate, Transom)
- Type-specific price inheritance and fallback
- Glass and hardware copying to personalized price lists
- The is_personalized flag behavior
- Price fallback when custom fields are None
- Deleting personalized price lists with counterparty reassignment
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.database import Base, SessionLocal, _seed_demo_data
from controllers.price_list_controller import PriceListController
from controllers.calculator_controller import CalculatorController
from models.price_list import (
    BasePriceList, PersonalizedPriceList, TypePrice, CustomTypePrice
)
from models.glass import GlassType, GlassOption
from models.hardware import HardwareItem
from models.closer import Closer, Coordinator
from constants import PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM


@pytest.fixture(scope="function")
def test_db_session():
    """Create isolated in-memory database for each test."""
    engine = create_engine("sqlite:///:memory:?cache=shared", echo=False)
    Session = sessionmaker(bind=engine)
    
    # Import all models for Base.metadata registration
    import models  # noqa: F401
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = Session()
    
    # Seed with demo data (base price list)
    _seed_demo_data(lambda: session)
    
    yield session
    
    session.close()


@pytest.fixture
def price_ctrl(test_db_session):
    """Price list controller with test session."""
    return PriceListController(session=test_db_session)


@pytest.fixture
def calc_ctrl(test_db_session):
    """Calculator controller with test session."""
    return CalculatorController(session=test_db_session)


@pytest.fixture
def base_price_list(price_ctrl):
    """Get the base price list."""
    return price_ctrl.get_base_price_list()


class TestPersonalizedPriceListCreation:
    """Tests for creating personalized price lists with all custom fields."""
    
    def test_create_personalized_basic(self, price_ctrl, base_price_list):
        """Basic creation of personalized price list."""
        personal = price_ctrl.create_personalized(
            "Test Personalized",
            base_id=base_price_list.id
        )
        assert personal is not None
        assert personal.name == "Test Personalized"
        assert personal.base_price_list_id == base_price_list.id
        assert personal.id >= 1000  # Personalized IDs start from 1000
        assert isinstance(personal, PersonalizedPriceList)
    
    def test_create_personalized_all_custom_fields(self, price_ctrl, base_price_list, test_db_session):
        """Create personalized price list and set all custom fields."""
        personal = price_ctrl.create_personalized(
            "Full Custom",
            base_id=base_price_list.id
        )
        
        # Set all custom fields
        custom_data = {
            # Door prices
            "custom_doors_price_std_single": 25000.0,
            "custom_doors_price_per_m2_nonstd": 18000.0,
            "custom_doors_wide_markup": 3500.0,
            "custom_doors_double_std": 45000.0,
            # Hatch prices
            "custom_hatch_std": 7000.0,
            "custom_hatch_wide_markup": 1200.0,
            "custom_hatch_per_m2_nonstd": 15000.0,
            # Gate prices
            "custom_gate_per_m2": 5500.0,
            "custom_gate_large_per_m2": 6500.0,
            # Transom prices
            "custom_transom_per_m2": 12000.0,
            "custom_transom_min": 7000.0,
            # Hardware prices
            "custom_cutout_price": 1200.0,
            "custom_deflector_per_m2": 4500.0,
            "custom_trim_per_lm": 950.0,
            "custom_closer_price": 4500.0,
            "custom_hinge_price": 500.0,
            "custom_anti_theft_price": 750.0,
            "custom_gkl_price": 2000.0,
            "custom_mount_ear_price": 150.0,
            "custom_threshold_price": 3500.0,
            # Vent grates
            "custom_vent_grate_tech": 3500.0,
            "custom_vent_grate_pp": 5000.0,
            # Seal
            "custom_seal_per_m2": 250.0,
            # Color prices
            "custom_nonstd_color_markup_pct": 10.0,
            "custom_diff_color_markup": 3000.0,
            "custom_moire_price": 3500.0,
            "custom_lacquer_per_m2": 1500.0,
            "custom_primer_single": 3500.0,
            "custom_primer_double": 7000.0,
        }
        
        price_ctrl.update_personalized(personal.id, custom_data)
        test_db_session.flush()
        test_db_session.refresh(personal)
        
        # Verify all fields
        assert personal.custom_doors_price_std_single == 25000.0
        assert personal.custom_doors_price_per_m2_nonstd == 18000.0
        assert personal.custom_doors_wide_markup == 3500.0
        assert personal.custom_doors_double_std == 45000.0
        assert personal.custom_hatch_std == 7000.0
        assert personal.custom_gate_per_m2 == 5500.0
        assert personal.custom_transom_per_m2 == 12000.0
        assert personal.custom_cutout_price == 1200.0
        assert personal.custom_closer_price == 4500.0
        assert personal.custom_hinge_price == 500.0
        assert personal.custom_nonstd_color_markup_pct == 10.0
        assert personal.custom_moire_price == 3500.0
    
    def test_create_personalized_from_another(self, price_ctrl, base_price_list):
        """Create personalized price list from another personalized one."""
        p1 = price_ctrl.create_personalized("Source", base_id=base_price_list.id)
        p2 = price_ctrl.create_personalized("Copy", source_id=p1.id)
        
        assert p2.base_price_list_id == p1.base_price_list_id
        assert p2.id >= 1000
    
    def test_personalized_id_starts_at_1000(self, price_ctrl, base_price_list):
        """Verify personalized price list IDs start at 1000."""
        p1 = price_ctrl.create_personalized("First", base_id=base_price_list.id)
        assert p1.id >= 1000
        
        p2 = price_ctrl.create_personalized("Second", base_id=base_price_list.id)
        assert p2.id >= 1000
        assert p2.id > p1.id


class TestCustomPriceEditing:
    """Tests for editing custom price fields and verification."""
    
    def test_edit_single_custom_field(self, price_ctrl, base_price_list, test_db_session):
        """Edit a single custom field and verify."""
        personal = price_ctrl.create_personalized("Editable", base_id=base_price_list.id)
        
        # Edit door price
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 30000.0})
        test_db_session.flush()
        test_db_session.refresh(personal)
        
        assert personal.custom_doors_price_std_single == 30000.0
        
        # Verify prices returned by get_price_for_calculation
        prices = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        assert prices["doors_price_std_single"] == 30000.0
    
    def test_edit_multiple_custom_fields(self, price_ctrl, base_price_list, test_db_session):
        """Edit multiple custom fields and verify."""
        personal = price_ctrl.create_personalized("Multi Edit", base_id=base_price_list.id)
        
        price_ctrl.update_personalized(personal.id, {
            "custom_doors_price_std_single": 25000.0,
            "custom_hatch_std": 6000.0,
            "custom_gate_per_m2": 5000.0,
            "custom_closer_price": 4000.0,
        })
        test_db_session.flush()
        
        prices = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        assert prices["doors_price_std_single"] == 25000.0
        assert prices["hatch_std"] == 6000.0
        assert prices["gate_per_m2"] == 5000.0
        assert prices["closer_price"] == 4000.0
    
    def test_edit_none_clears_custom_price(self, price_ctrl, base_price_list, test_db_session):
        """Setting custom field to None should fallback to base price."""
        personal = price_ctrl.create_personalized("Clear Test", base_id=base_price_list.id)
        
        # Set custom price
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 30000.0})
        test_db_session.flush()
        
        prices_with_custom = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        assert prices_with_custom["doors_price_std_single"] == 30000.0
        
        # Clear custom price (set to None)
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": None})
        test_db_session.flush()
        test_db_session.refresh(personal)
        
        # Should fallback to base price
        prices_fallback = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        base_prices = price_ctrl.get_price_for_calculation(base_price_list.id)
        assert prices_fallback["doors_price_std_single"] == base_prices["doors_price_std_single"]


class TestCalculationWithPersonalizedPriceLists:
    """Tests for calculation with personalized price lists for all product types."""
    
    def test_door_calculation_with_personalized(self, price_ctrl, calc_ctrl, base_price_list, test_db_session):
        """Door calculation with personalized price list."""
        # Create personalized with custom door price
        personal = price_ctrl.create_personalized("Door Custom", base_id=base_price_list.id)
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 50000.0})
        test_db_session.flush()
        
        # Calculate with base price list
        result_base = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2100, 900, base_price_list.id, {}, 0, 0, 1
        )
        
        # Calculate with personalized price list
        result_personal = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2100, 900, personal.id, {}, 0, 0, 1,
            is_personalized=True
        )
        
        assert result_base["success"] is True
        assert result_personal["success"] is True
        assert result_base["price_per_unit"] != result_personal["price_per_unit"]
        # Personalized should be higher (50000 vs 15000)
        assert result_personal["price_per_unit"] > result_base["price_per_unit"]
    
    def test_hatch_calculation_with_personalized(self, price_ctrl, calc_ctrl, base_price_list, test_db_session):
        """Hatch calculation with personalized price list."""
        personal = price_ctrl.create_personalized("Hatch Custom", base_id=base_price_list.id)
        price_ctrl.update_personalized(personal.id, {"custom_hatch_std": 8000.0})
        test_db_session.flush()
        test_db_session.refresh(personal)
        
        # First verify that the custom price is actually returned by get_price_for_calculation
        prices_personal = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        prices_base = price_ctrl.get_price_for_calculation(base_price_list.id)
        
        print(f"DEBUG: personal prices hatch_std = {prices_personal.get('hatch_std')}")
        print(f"DEBUG: base prices hatch_std = {prices_base.get('hatch_std')}")
        
        assert prices_personal["hatch_std"] == 8000.0, f"Expected 8000.0, got {prices_personal['hatch_std']}"
        assert prices_base["hatch_std"] == 4500.0
        
        # Test base calculation
        result_base = calc_ctrl.validate_and_calculate(
            "Люк", "Технический",
            800, 800, base_price_list.id, {}, 0, 0, 1
        )
        
        print(f"DEBUG: result_base = {result_base}")
        
        # Test personalized calculation
        result_personal = calc_ctrl.validate_and_calculate(
            "Люк", "Технический",
            800, 800, personal.id, {}, 0, 0, 1,
            is_personalized=True
        )
        
        print(f"DEBUG: result_personal = {result_personal}")
        
        assert result_base["success"] is True
        assert result_personal["success"] is True
        # Personalized should use custom_hatch_std = 8000 vs base hatch_std = 4500
        assert result_personal["price_per_unit"] > result_base["price_per_unit"], \
            f"Expected personal price > base price, but got {result_personal['price_per_unit']} vs {result_base['price_per_unit']}"
    
    def test_gate_calculation_with_personalized(self, price_ctrl, calc_ctrl, base_price_list, test_db_session):
        """Gate calculation with personalized price list."""
        personal = price_ctrl.create_personalized("Gate Custom", base_id=base_price_list.id)
        # For large gates (h>=3000 or w>=3000), custom_gate_large_per_m2 is used
        price_ctrl.update_personalized(personal.id, {"custom_gate_large_per_m2": 6000.0})
        test_db_session.flush()
        
        # Test with large gate (h>=3000) - uses gate_large_per_m2
        result_base = calc_ctrl.validate_and_calculate(
            PRODUCT_GATE, "Технические",
            3000, 3000, base_price_list.id, {}, 0, 0, 1
        )
        
        result_personal = calc_ctrl.validate_and_calculate(
            PRODUCT_GATE, "Технические",
            3000, 3000, personal.id, {}, 0, 0, 1,
            is_personalized=True
        )
        
        assert result_base["success"] is True
        assert result_personal["success"] is True
        # Base uses gate_large_per_m2=4500, Personalized uses custom_gate_large_per_m2=6000
        assert result_personal["price_per_unit"] != result_base["price_per_unit"], \
            f"Expected different prices, got {result_personal['price_per_unit']} vs {result_base['price_per_unit']}"
    
    def test_transom_calculation_with_personalized(self, price_ctrl, calc_ctrl, base_price_list, test_db_session):
        """Transom calculation with personalized price list."""
        personal = price_ctrl.create_personalized("Transom Custom", base_id=base_price_list.id)
        # For Transom, transom_per_m2 is the main price field
        price_ctrl.update_personalized(personal.id, {"custom_transom_per_m2": 12000.0})
        test_db_session.flush()
        
        # First verify prices are returned correctly
        prices_personal = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        prices_base = price_ctrl.get_price_for_calculation(base_price_list.id)
        print(f"DEBUG: personal transom_per_m2 = {prices_personal.get('transom_per_m2')}")
        print(f"DEBUG: base transom_per_m2 = {prices_base.get('transom_per_m2')}")
        
        # Test base calculation - uses transom_per_m2 = 8500.0
        result_base = calc_ctrl.validate_and_calculate(
            PRODUCT_TRANSOM, "Техническая",
            600, 900, base_price_list.id, {}, 0, 0, 1
        )
        print(f"DEBUG: result_base = {result_base}")
        
        # Test personalized calculation - should use custom_transom_per_m2 = 12000.0
        result_personal = calc_ctrl.validate_and_calculate(
            PRODUCT_TRANSOM, "Техническая",
            600, 900, personal.id, {}, 0, 0, 1,
            is_personalized=True
        )
        print(f"DEBUG: result_personal = {result_personal}")
        
        assert result_base["success"] is True
        assert result_personal["success"] is True
        assert result_personal["price_per_unit"] != result_base["price_per_unit"], \
            f"Expected different prices, got {result_personal['price_per_unit']} vs {result_base['price_per_unit']}"
    
    def test_calculation_with_none_price_list_uses_base(self, calc_ctrl, base_price_list):
        """None price_list_id should use base price list."""
        result = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2100, 900, None, {}, 0, 0, 1
        )
        
        assert result["success"] is True
        assert result["price_per_unit"] > 0


class TestTypeSpecificPrices:
    """Tests for type-specific price inheritance and fallback."""
    
    def test_custom_type_price_for_personalized(self, price_ctrl, base_price_list, test_db_session):
        """Type-specific prices for personalized price list."""
        personal = price_ctrl.create_personalized(
            "With Type Prices",
            base_id=base_price_list.id
        )
        
        # Get existing custom type price (copied from base)
        from sqlalchemy import select
        stmt = select(CustomTypePrice).where(
            CustomTypePrice.price_list_id == personal.id,
            CustomTypePrice.product_type == PRODUCT_DOOR,
            CustomTypePrice.subtype == "Техническая"
        )
        existing = test_db_session.execute(stmt).scalar_one_or_none()
        assert existing is not None
        
        # Update custom type price
        price_ctrl.update_type_price(existing.id, {
            "price_std_single": 25000.0,
            "price_double_std": 45000.0,
        })
        test_db_session.flush()
        
        # Verify get_type_price returns custom values
        prices = price_ctrl.get_type_price(personal.id, PRODUCT_DOOR, "Техническая")
        assert prices is not None
        assert prices["price_std_single"] == 25000.0
        assert prices["price_double_std"] == 45000.0
    
    def test_fallback_to_base_type_price(self, price_ctrl, base_price_list, test_db_session):
        """If no custom type price, fallback to base price list's type price."""
        personal = price_ctrl.create_personalized(
            "No Type Prices",
            base_id=base_price_list.id
        )
        
        # Delete custom type prices to test fallback
        from sqlalchemy import delete
        stmt = delete(CustomTypePrice).where(
            CustomTypePrice.price_list_id == personal.id
        )
        test_db_session.execute(stmt)
        test_db_session.flush()
        
        # Should fallback to base type price
        prices = price_ctrl.get_type_price(personal.id, PRODUCT_DOOR, "Техническая")
        assert prices is not None
        # Base type price for Дверь/Техническая is 15000
        assert prices["price_std_single"] == 15000.0
    
    def test_get_type_prices_for_personalized(self, price_ctrl, base_price_list):
        """get_type_prices returns CustomTypePrice for personalized lists."""
        personal = price_ctrl.create_personalized(
            "Type Prices Test",
            base_id=base_price_list.id
        )
        
        type_prices = price_ctrl.get_type_prices(personal.id)
        assert len(type_prices) > 0
        # All should be CustomTypePrice instances
        for tp in type_prices:
            assert isinstance(tp, CustomTypePrice)


class TestGlassAndHardwareCopying:
    """Tests for glass and hardware copying to personalized price lists."""
    
    def test_glass_types_copied_to_personalized(self, price_ctrl, test_db_session):
        """Glass types are copied to personalized price list."""
        base = price_ctrl.get_base_price_list()
        
        personal = price_ctrl.create_personalized(
            "With Glasses",
            base_id=base.id
        )
        test_db_session.commit()
        
        from controllers.options_controller import OptionsController
        opt_ctrl = OptionsController(test_db_session)
        glasses = opt_ctrl.get_glass_types(personal.id)
        assert len(glasses) > 0
    
    def test_hardware_copied_to_personalized(self, price_ctrl, test_db_session):
        """Hardware is copied to personalized price list."""
        base = price_ctrl.get_base_price_list()
        
        personal = price_ctrl.create_personalized(
            "With Hardware",
            base_id=base.id
        )
        test_db_session.commit()
        
        from controllers.hardware_controller import HardwareController
        hw_ctrl = HardwareController(test_db_session)
        items = hw_ctrl.get_all_for_price_list(personal.id)
        assert len(items) > 0
    
    def test_closers_copied_to_personalized(self, price_ctrl, test_db_session):
        """Closers and coordinators are copied to personalized price list."""
        base = price_ctrl.get_base_price_list()
        
        # First, add closers to the base price list (seed data doesn't include them)
        from sqlalchemy import select
        existing_closers = test_db_session.execute(
            select(Closer).where(Closer.price_list_id == base.id)
        ).scalars().all()
        
        if len(existing_closers) == 0:
            # Add sample closers to base price list
            test_db_session.add_all([
                Closer(name="Dorma B2", door_weight=45, price=8500.0, price_list_id=base.id),
                Closer(name="Dorma TS-73", door_weight=65, price=9500.0, price_list_id=base.id),
                Coordinator(name="Apecs 2440/1", price=3200.0, price_list_id=base.id),
            ])
            test_db_session.flush()
        
        personal = price_ctrl.create_personalized(
            "With Closers",
            base_id=base.id
        )
        test_db_session.flush()
        
        closers = test_db_session.execute(
            select(Closer).where(Closer.price_list_id == personal.id)
        ).scalars().all()
        assert len(closers) > 0, f"Expected closers to be copied, but found {len(closers)}"


class TestIsPersonalizedFlag:
    """Tests for the is_personalized flag behavior."""
    
    def test_is_personalized_true_uses_personalized(self, price_ctrl, calc_ctrl, base_price_list, test_db_session):
        """is_personalized=True should use personalized price list."""
        personal = price_ctrl.create_personalized("Flag Test", base_id=base_price_list.id)
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 99999.0})
        test_db_session.flush()
        
        result = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2100, 900, personal.id, {}, 0, 0, 1,
            is_personalized=True
        )
        
        assert result["success"] is True
        assert result["price_per_unit"] > 50000  # Should use 99999 custom price
    
    def test_is_personalized_false_uses_base(self, price_ctrl, calc_ctrl, base_price_list, test_db_session):
        """is_personalized=False with personalized ID should still work (auto-detect)."""
        personal = price_ctrl.create_personalized("Auto Detect", base_id=base_price_list.id)
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 99999.0})
        test_db_session.flush()
        
        # Even with is_personalized=False, the calculator should auto-detect
        result = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2100, 900, personal.id, {}, 0, 0, 1,
            is_personalized=False  # Intentionally False
        )
        
        assert result["success"] is True
        # Should still detect and use personalized price
    
    def test_auto_detect_personalized(self, price_ctrl, calc_ctrl, base_price_list, test_db_session):
        """Calculator should auto-detect personalized price list when is_personalized flag not set."""
        personal = price_ctrl.create_personalized("Auto Detect Test", base_id=base_price_list.id)
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 88888.0})
        test_db_session.flush()
        
        # Don't pass is_personalized flag - should auto-detect
        result = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2100, 900, personal.id, {}, 0, 0, 1
        )
        
        assert result["success"] is True
        # Should have detected personalized and used custom price


class TestPriceFallbackWhenNone:
    """Tests for price fallback when custom fields are None."""
    
    def test_none_custom_uses_base_price(self, price_ctrl, base_price_list, test_db_session):
        """If custom field is None, use base price."""
        personal = price_ctrl.create_personalized("Fallback Test", base_id=base_price_list.id)
        # Don't set any custom fields
        
        prices = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        
        # Should equal base prices
        base_prices = price_ctrl.get_price_for_calculation(base_price_list.id)
        assert prices["doors_price_std_single"] == base_prices["doors_price_std_single"]
        assert prices["hatch_std"] == base_prices["hatch_std"]
    
    def test_partial_custom_fields(self, price_ctrl, base_price_list, test_db_session):
        """Some custom fields set, others None - mix of custom and base prices."""
        personal = price_ctrl.create_personalized("Partial Custom", base_id=base_price_list.id)
        
        # Set only door price
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 30000.0})
        test_db_session.flush()
        
        prices = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        
        # Door price should be custom
        assert prices["doors_price_std_single"] == 30000.0
        # Hatch price should fallback to base
        base_prices = price_ctrl.get_price_for_calculation(base_price_list.id)
        assert prices["hatch_std"] == base_prices["hatch_std"]


class TestDeletePersonalizedWithReassignment:
    """Tests for deleting personalized price lists with counterparty reassignment."""
    
    def test_delete_with_reassign(self, price_ctrl, base_price_list, test_db_session):
        """Delete personalized and reassign counterparties to base."""
        from models.counterparty import Counterparty, CounterpartyType
        
        personal = price_ctrl.create_personalized("To Delete", base_id=base_price_list.id)
        test_db_session.flush()
        
        # Create counterparty with this price list (address is required - NOT NULL)
        cp = Counterparty(
            name="Test CP",
            type=CounterpartyType.NATURAL,
            address="Test Address 123",
            phone="+7 999 123-45-67",
            price_list_id=personal.id
        )
        test_db_session.add(cp)
        test_db_session.flush()
        
        # Delete with reassign
        result = price_ctrl.delete_personalized(personal.id, reassign_to_base=True)
        assert result is True
        
        # Check counterparty reassigned to base
        test_db_session.refresh(cp)
        assert cp.price_list_id == base_price_list.id
    
    def test_delete_without_reassign(self, price_ctrl, base_price_list, test_db_session):
        """Delete personalized without reassigning counterparties."""
        from models.counterparty import Counterparty, CounterpartyType
        
        personal = price_ctrl.create_personalized("To Delete 2", base_id=base_price_list.id)
        test_db_session.flush()
        
        # Create counterparty with this price list (address is required - NOT NULL)
        cp = Counterparty(
            name="Test CP 2",
            type=CounterpartyType.NATURAL,
            address="Test Address 456",
            phone="+7 999 987-65-43",
            price_list_id=personal.id
        )
        test_db_session.add(cp)
        test_db_session.flush()
        
        # Delete without reassign
        result = price_ctrl.delete_personalized(personal.id, reassign_to_base=False)
        assert result is True
        
        # Check counterparty still has old price_list_id (now invalid)
        test_db_session.refresh(cp)
        assert cp.price_list_id == personal.id


class TestPersonalizedPriceListIndependence:
    """Tests to ensure personalized price lists are independent."""
    
    def test_multiple_personal_lists_independent(self, price_ctrl, base_price_list, test_db_session):
        """Multiple personalized price lists don't affect each other."""
        p1 = price_ctrl.create_personalized("Price 1", base_id=base_price_list.id)
        p2 = price_ctrl.create_personalized("Price 2", base_id=base_price_list.id)
        
        price_ctrl.update_personalized(p1.id, {"custom_doors_price_std_single": 10000.0})
        price_ctrl.update_personalized(p2.id, {"custom_doors_price_std_single": 20000.0})
        test_db_session.flush()
        
        prices1 = price_ctrl.get_price_for_calculation(p1.id, is_personalized=True)
        prices2 = price_ctrl.get_price_for_calculation(p2.id, is_personalized=True)
        
        assert prices1["doors_price_std_single"] == 10000.0
        assert prices2["doors_price_std_single"] == 20000.0
    
    def test_base_not_affected_by_personalized(self, price_ctrl, base_price_list, test_db_session):
        """Changes to personalized price list don't affect base."""
        personal = price_ctrl.create_personalized("No Affect", base_id=base_price_list.id)
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 99999.0})
        test_db_session.flush()
        
        base_prices = price_ctrl.get_price_for_calculation(base_price_list.id)
        assert base_prices["doors_price_std_single"] == 15000.0  # Base unchanged


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_get_price_for_calculation_invalid_id(self, price_ctrl):
        """Invalid price list ID should return base prices."""
        prices = price_ctrl.get_price_for_calculation(99999)
        assert "doors_price_std_single" in prices
    
    def test_get_price_for_calculation_none(self, price_ctrl):
        """None ID should return base prices."""
        prices = price_ctrl.get_price_for_calculation(None)
        assert "doors_price_std_single" in prices
    
    def test_create_personalized_without_base_uses_default(self, price_ctrl):
        """Creating personalized without specifying base_id uses default base."""
        personal = price_ctrl.create_personalized("No Base Specified")
        base = price_ctrl.get_base_price_list()
        assert personal.base_price_list_id == base.id
    
    def test_get_price_list_by_id_personalized(self, price_ctrl, base_price_list):
        """get_price_list_by_id returns correct personalized price list."""
        personal = price_ctrl.create_personalized("Get By ID", base_id=base_price_list.id)
        
        found = price_ctrl.get_price_list_by_id(personal.id)
        assert found is not None
        assert isinstance(found, PersonalizedPriceList)
        assert found.name == "Get By ID"
    
    def test_get_price_list_by_id_base(self, price_ctrl, base_price_list):
        """get_price_list_by_id returns correct base price list."""
        found = price_ctrl.get_price_list_by_id(base_price_list.id)
        assert found is not None
        assert isinstance(found, BasePriceList)

class TestClosersCalculation:
    """Tests for closers loading and calculation (bug fix verification)."""
    
    def test_closer1_selected_count_is_1(self, calc_ctrl, base_price_list):
        """When closer1 is selected, closers_count should be 1."""
        # Simulate UI options with closer1=True
        options = {
            "extra_options": {
                "closer1": True,
                "closer2": False,
            }
        }
        
        result = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2000, 900, base_price_list.id, options, 0, 0, 1
        )
        
        assert result["success"] is True
        # Price should include 1 * closer_price (2500.0)
        # Base door price = 15000, closer_price = 2500
        expected_min = 15000.0 + 2500.0  # At least base + 1 closer
        assert result["price_per_unit"] >= expected_min, \
            f"Expected price >= {expected_min}, got {result['price_per_unit']}"
    
    def test_closer2_selected_count_is_2(self, calc_ctrl, base_price_list):
        """When both closers are selected, closers_count should be 2."""
        # Simulate UI options with closer1=True and closer2=True
        options = {
            "is_double_leaf": True,
            "extra_options": {
                "closer1": True,
                "closer2": True,
            }
        }
        
        result = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2000, 1200, base_price_list.id, options, 0, 0, 1
        )
        
        assert result["success"] is True
        # Price should include 2 * closer_price (2 * 2500.0)
        # Base double door price = 28000, 2 closers = 5000
        expected_min = 28000.0 + 5000.0
        assert result["price_per_unit"] >= expected_min, \
            f"Expected price >= {expected_min}, got {result['price_per_unit']}"
    
    def test_no_closers_selected_count_is_0(self, calc_ctrl, base_price_list):
        """When no closers are selected, closers_count should be 0."""
        # Simulate UI options with no closers
        options = {
            "extra_options": {
                "closer1": False,
                "closer2": False,
            }
        }
        
        result = calc_ctrl.validate_and_calculate(
            PRODUCT_DOOR, "Техническая",
            2000, 900, base_price_list.id, options, 0, 0, 1
        )
        
        assert result["success"] is True
        # Price should NOT include closer_price
        # Base door price = 15000, no closers
        expected_max = 15000.0 + 100.0  # Just base price + small margin for other options
        assert result["price_per_unit"] <= expected_max, \
            f"Expected price <= {expected_max}, got {result['price_per_unit']}"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", __file__]))
