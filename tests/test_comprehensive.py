"""Comprehensive calculator test - all configurations and edge cases."""

import sys
sys.path.insert(0, '.')

from db.database import init_db
from controllers.calculator_controller import CalculatorController


def test_all_configurations():
    """Test all product types and configurations."""
    init_db()
    ctrl = CalculatorController()
    
    tests = [
        ("Door standard", "Door", "Technical", 2100, 900, {"is_double_leaf": False}, 0, 0, 1),
        ("Door double", "Door", "EI 60", 2100, 1200, {"is_double_leaf": True}, 0, 0, 1),
        ("Door RAL", "Door", "Technical", 2100, 900, {"is_double_leaf": False, "color_external": "5005"}, 0, 0, 1),
        ("Door metal 1.5", "Door", "Technical", 2100, 900, {"is_double_leaf": False, "metal_thickness": "1.5-1.5"}, 0, 0, 1),
        ("Hatch standard", "Hatch", "Technical", 2000, 800, {"is_double_leaf": False}, 0, 0, 1),
        ("Hatch double", "Hatch", "Technical", 2100, 1200, {"is_double_leaf": True}, 0, 0, 1),
        ("Gate standard", "Gate", "Gate", 3000, 4000, {}, 0, 0, 1),
        ("Gate large", "Gate", "Gate", 5000, 5000, {}, 0, 0, 1),
        ("Transom", "Transom", "Technical", 600, 900, {}, 0, 0, 1),
        ("Door threshold", "Door", "EI 60", 2100, 900, {"is_double_leaf": False, "threshold": True}, 0, 0, 1),
        ("Door closer", "Door", "EI 60", 2100, 900, {"is_double_leaf": False, "closers_count": 1}, 0, 0, 1),
        ("Door markup", "Door", "EI 60", 2100, 900, {"is_double_leaf": False}, 15, 1000, 2),
        ("Door min size", "Door", "Technical", 1800, 600, {"is_double_leaf": False}, 0, 0, 1),
        ("Door max size", "Door", "Technical", 2400, 1100, {"is_double_leaf": False}, 0, 0, 1),
        ("Gate nonstd", "Gate", "Gate", 3500, 4500, {}, 0, 0, 1),
    ]
    
    print("=== Calculator Tests ===")
    passed = 0
    failed = 0
    
    for name, ptype, subtype, h, w, opts, mp, ma, qty in tests:
        result = ctrl.validate_and_calculate(ptype, subtype, h, w, 1, opts, mp, ma, qty)
        if result.get("success"):
            print(f"OK {name}: {result['total_price']}")
            passed += 1
        else:
            print(f"FAIL {name}: {result.get('error')}")
            failed += 1
    
    # Test extras_breakdown
    print("\n=== extras_breakdown Test ===")
    result = ctrl.validate_and_calculate(
        "Door", "EI 60", 2100, 900, 1,
        {
            "is_double_leaf": False,
            "color_external": "5005",
            "metal_thickness": "1.5-1.5",
            "threshold": True,
            "extra_options": {"closer1": True}
        }, 10, 500, 1
    )
    
    if result.get("success"):
        details = result.get("details", {})
        extras = details.get("extras_breakdown", [])
        print(f"extras_breakdown ({len(extras)} items):")
        for item in extras:
            print(f"  - {item.get('name')}: {item.get('price')}")
        print(f"Total: {result['total_price']}")
        passed += 1
    else:
        print(f"FAIL extras_breakdown: {result.get('error')}")
        failed += 1
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    assert failed == 0, f"{failed} tests failed"
    print("\nAll tests passed!")
    return True


if __name__ == "__main__":
    test_all_configurations()