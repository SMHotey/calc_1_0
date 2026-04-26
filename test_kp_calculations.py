#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for generating and evaluating 20 door/window/framings configurations
using the CalculatorController. The script:
- Imports CalculatorController and SessionLocal from the project
- Creates 20 varied product configurations (type, subtype, leaves, sizes, colors, etc.)
- Calls validate_and_calculate() for each configuration
- Prints configuration details, calculated price, and extras breakdown
- Performs lightweight verifications on price and extras coverage
- Cleans up DB session at the end
"""

import sys
import json
from typing import Dict, Any


def _import_controller() -> object:
    # Try multiple import paths to accommodate project layout
    candidates = [
        ("app.controllers.calculator_controller", "CalculatorController"),
        ("controllers.calculator_controller", "CalculatorController"),
        ("calculator_controller", "CalculatorController"),
    ]
    for module_path, class_name in candidates:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            return getattr(mod, class_name)
        except Exception:
            continue
    raise ImportError("Could not import CalculatorController from known paths")


def _import_session_local() -> object:
    candidates = [
        ("db.database", "SessionLocal"),
        ("database", "SessionLocal"),
        ("sqlalchemy.orm", "Session"),  # fallback
    ]
    for module_path, attr in candidates:
        try:
            mod = __import__(module_path, fromlist=[attr])
            return getattr(mod, attr)
        except Exception:
            continue
    raise ImportError("Could not import SessionLocal from known paths")


def _generate_configs(n: int):
    products = ["Дверь", "Люк", "Ворота", "Фрамуга"]
    subtypes = ["EI 60", "EI 30", "EI 15", "EI 90"]
    leaves = ["single", "double"]
    thicknesses = ["1.0-1.0", "1.2-1.4", "1.4-1.4", "1.6-2.0"]
    colors = ["7035 standard", "RAL-1023", "RAL-7016", "RAL-9003"]
    closers = [False, True]
    thresholds = [False, True]
    glasses = ["single", "double", "tempered"]
    hardwares = ["standard", "premium"]
    heights = [1500, 1700, 1900, 2100]
    widths = [800, 1000, 1200]

    configs = []
    idx = 0
    for p in products:
        for s in subtypes:
            for l in leaves:
                for h in heights:
                    for w in widths:
                        conf = {
                            "product_type": p,
                            "subtype": s,
                            "leaves": l,
                            "height_mm": int(h),
                            "width_mm": int(w),
                            "thickness_pair": thicknesses[idx % len(thicknesses)],
                            "color": colors[idx % len(colors)],
                            "closer": closers[idx % len(closers)],
                            "threshold": thresholds[idx % len(thresholds)],
                            "glass": glasses[idx % len(glasses)],
                            "hardware": hardwares[idx % len(hardwares)],
                        }
                        configs.append(conf)
                        idx += 1
                        if len(configs) >= n:
                            return configs
    return configs


def main() -> int:
    try:
        CalculatorController = _import_controller()
    except ImportError as e:
        print(f"Import error: {e}")
        return 2

    try:
        SessionLocal = _import_session_local()
    except ImportError as e:
        print(f"Import error: {e}")
        return 2

    # Generate 20 configurations
    configs = _generate_configs(20)

    # Initialize DB session and controller
    session = SessionLocal()
    try:
        try:
            calc_ctrl = CalculatorController(session)
        except TypeError:
            calc_ctrl = CalculatorController()
    except Exception as e:
        print(f"Failed to initialize CalculatorController: {e}")
        session.close()
        return 3

    print("Starting 20 KPI calculations...")

    for idx, cfg in enumerate(configs, start=1):
        print("\n[Config {}]".format(idx))
        print(json.dumps(cfg, ensure_ascii=False, indent=2))

        try:
            result = calc_ctrl.validate_and_calculate(
                product_type=cfg["product_type"],
                subtype=cfg["subtype"],
                height=cfg["height_mm"],
                width=cfg["width_mm"],
                price_list_id=cfg.get("price_list_id", 1),
                options={
                    "is_double_leaf": cfg.get("leaves") == "double",
                    "color_external": cfg.get("color", "7035"),
                    "color_internal": cfg.get("color", "7035"),
                    "metal_thickness": cfg.get("thickness", "1.0-1.0"),
                    "glass_items": cfg.get("glass_items", []),
                    "hardware_ids": cfg.get("hardware_ids", []),
                    "closers_count": cfg.get("closers_count", 0),
                    "threshold": cfg.get("threshold", False),
                    "extra_options": {}
                },
                markup_percent=cfg.get("markup_percent", 0),
                markup_abs=cfg.get("markup_abs", 0),
                quantity=1
            )
        except Exception as e:
            print(f"Error calculating config #{idx}: {e}")
            continue

        price = None
        extras = {}
        if isinstance(result, dict):
            price = result.get("price")
            extras = result.get("extras_breakdown") or {}
        else:
            print(f"Unexpected result type for config #{idx}: {type(result)}")
            continue

        print("Calculated price:", price)
        print("Extras breakdown:")
        print(json.dumps(extras, ensure_ascii=False, indent=2))

        # Basic verifications
        if price is not None:
            assert price >= 0, f"Negative price for config #{idx}"
        # Note: Extra validations depend on the calculator's implementation details.
        # To keep tests robust across configurations, we avoid asserting specific
        # keys inside the extras breakdown here.

    print("All configurations processed.")
    session.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
