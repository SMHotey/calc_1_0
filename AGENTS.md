# AGENTS.md — МеталлоКальк PRO

## Quick Start

```powershell
# Run app (from project root)
python main.py

# Run tests
pytest tests/ -v
```

## Project Structure

```
├── main.py              # Entry point — initializes DB, logging, UI
├── constants.py         # App-wide constants, product types, enums
├── requirements.txt    # Dependencies (PyQt6, SQLAlchemy, reportlab, pytest)
│
├── db/
│   └── database.py      # SQLite setup, session factory, demo data seeding
│
├── models/              # SQLAlchemy ORM models
├── controllers/         # Business logic layer
├── views/              # PyQt6 UI (tabs, dialogs)
│   └── dialogs/         # Modal dialogs
│
├── utils/
│   ├── calculators/    # Price calculation per product type
│   ├── validators.py   # Dimension validation
│   └── report_generator.py
│
├── resources/
│   └── styles.qss      # Qt stylesheet (custom theme)
│
└── tests/               # pytest test suite
```

## Architecture Notes

- **MVC pattern**: Controllers hold business logic, Views are PyQt6 widgets, Models are SQLAlchemy
- **Entry point**: `main.py` → `init_db()` → `MainWindow` with 5 tabs (Calculator, Offers, Prices, Counterparties, Presets)
- **DB auto-init**: First run creates `db/metalcalc.db` and seeds demo data. No migrations.
- **Logging**: Writes to `logs/app_runtime.log` (UTF-8). SQLAlchemy logs suppressed (level WARNING).

## Important Patterns

- **Controller pattern**: Each major view has a corresponding controller (e.g., `CalculatorController`)
- **Session management**: Controllers receive `Session` via constructor, commit on success, rollback on exception
- **Calculators**: Strategy pattern via `CalculatorContext` + concrete calculators (`DoorCalculator`, `HatchCalculator`, etc.)
- **No type hints on public API**: Models and controllers use basic typing, but some internal code lacks annotations
- **Russian-language UI**: All strings, error messages, and UI labels are in Russian

## Key Commands

| Task | Command |
|------|---------|
| Run app | `python main.py` |
| Run all tests | `pytest tests/ -v` |
| Run specific test | `pytest tests/test_all.py::TestDoorCalculator -v` |
| Re-create DB | Delete `db/metalcalc.db` and run `python main.py` |

## Testing

- Uses `sqlite:///:memory:` for tests (isolated in-memory DB)
- Tests import from `db.database`, `controllers.*`, `utils.calculators`, `utils.validators`
- Test session created via `sessionmaker` bound to in-memory engine

## Gotchas

- **Unicode filenames**: README file is `README_ДЛЯ_МЕНЕДЖЕРОВ.md` (Cyrillic)
- **DB path is relative**: `db/database.py` uses `os.path.dirname(__file__)` to locate `metalcalc.db`
- **QSS stylesheet fallback**: If `resources/styles.qss` not found, app runs with default Qt theme and logs warning
- **No alembic/migrations**: Schema changes require DB deletion and re-seed
- **PyQt6 requires display**: Headless testing with `pytest-qt` works, but app won't run in environments without display

## Style / Conventions

- Python 3.10+ type hints (`from __future__ import annotations` not used)
- SQLAlchemy 2.0 with `future=True` (legacy mode disabled)
- PyQt6 signals/slots via decorators or explicit connect
- No formatter/linter configured — follow existing code style (PEP8-ish, 4-space indent)