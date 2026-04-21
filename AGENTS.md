# AGENTS.md — МеталлоКальк PRO v2.0

## Quick Commands
```
python main.py           # Run app
pytest tests/ -v         # All tests
pytest tests/test_calculators.py -v    # Unit tests only
pytest tests/test_all.py -v           # Integration tests
```

## Key Facts

- **Entry**: `main.py` → `init_db()` → QApplication → MainWindow
- **DB**: SQLite (`db/metalcalc.db`), auto-created on first run
- **Schema changes**: Delete `db/metalcalc.db` — no migrations
- **Unit**: millimeters (mm) — area = (h × w) / 1_000_000
- **Display required**: PyQt6 crashes without X11/display; use `xvfb-run` in CI

## Architecture

- **MVC**: Models (SQLAlchemy) → Controllers → Views (PyQt6)
- **Calculator dispatch**: `CalculatorContext` + `CALC_MAP` → Door/Hatch/Gate/Transom/Glass calculators
- **Session**: Controllers auto-create via `SessionLocal()`; tests pass explicit sessions

## Model Registration (Critical)
`models/__init__.py` MUST import all model classes — without this, `Base.metadata` is incomplete and tables won't create. `db/database.py` imports models inside `init_db()` to avoid circular imports.

## Price Resolution
`PriceListController.get_price_for_calculation()` merges personalized prices over base; `None` falls through to base.

## Pre-existing Issues
- `tests/test_all.py::TestValidators::test_gate_too_big` — fails (validation logic may need review)
- `db/` directory not a package (no `__init__.py`) — imports `db.database` work directly
