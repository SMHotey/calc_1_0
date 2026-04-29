# AGENTS.md — МеталлоКальк PRO v2.0

## Quick Commands
```
python main.py                                      # Run app
pytest tests/test_calculators.py -v                  # Unit tests
pytest tests/test_calculators_additional.py -v        # Extended calculator tests
pytest tests/test_all.py -v                           # Full integration suite
pytest tests/test_full_crud_cycle.py -v              # CRM/deal lifecycle tests
```

## Entry Point
`main.py` → `init_db()` (create DB if missing + seed) → `QApplication` → `MainWindow` (5 tabs: Калькулятор, КП, Прайс, Контрагенты, Сделки)

## DB
- SQLite at `db/metalcalc.db`, auto-created on first run via `init_db()`
- **No migrations** — delete `db/metalcalc.db` to pick up schema changes
- `models/__init__.py` MUST import all model classes — without this, `Base.metadata` is incomplete and tables won't create
- `db/database.py` imports models inside `init_db()` to avoid circular imports
- `db/` **is** a package (has `__init__.py`)

## Units & Calculations
- Input: millimeters (mm)
- Area formula: `(height / 1000.0) * (width / 1000.0)` — gives m² as float
- Found in: `utils/calculators/base_calculator.py`, `door_calculator.py`, `hatch_calculator.py`, `glass_calculator.py`

## Architecture
- **MVC**: Models (SQLAlchemy, `models/`) → Controllers (`controllers/`) → Views (PyQt6, `views/`)
- **Calculator dispatch**: `CalculatorController.CALC_MAP` maps product type → calculator class (Door/Hatch/Gate/Transom)
  - `CalculatorContext` + `PriceData` in `utils/calculators/` hold calculation inputs
  - Strategy pattern: `DoorCalculator`, `HatchCalculator`, `GateCalculator`, `TransomCalculator`
- **Session handling**: Controllers auto-create via `SessionLocal()`; tests pass explicit sessions
- **Price resolution**: `PriceListController.get_price_for_calculation()` merges personalized prices over base; `None` falls through to base

## Offer Options (7 tables)
Each has `get_prices()` → `(base_price, current_price)`:
- `OfferItemGlass` (inline `options_data` JSON), `OfferItemVent`, `OfferItemLock`, `OfferItemHandle`, `OfferItemCylinder`, `OfferItemCloser`, `OfferItemCoordinator`

## Price Tables Short Names
On `GlassOption`, `VentType`, `HardwareItem`, `Closer`, `Coordinator`:
- `short_name_kp`: for КП display
- `short_name_prod`: for production order
- UI in `views/price_tab.py`

## CRM Modules
- **Deals** (`models/deal.py`, `controllers/deal_controller.py`, `views/deals_tab.py`) — workflow: черновик → КП → счёт → предоплата → оплата → завершена/отменена
- **Documents** (`models/document.py`, `controllers/document_controller.py`, `views/documents_widget.py`) — BLOB storage, supports PDF/XLSX/XLS/DOCX/DOC/JPEG
- **Tab integration**: OffersTab has "Создать сделку" context menu; DealsTab has filters; CounterpartiesTab has splitter with documents

## Click-to-Edit (КП table)
Click position → loads into calculator → edit → "Сохранить" button appears → saves to DB

## Display Requirement
PyQt6 crashes without a display. In CI/headless: `xvfb-run -a pytest tests/` or set `QT_QPA_PLATFORM=offscreen`.

## Dependencies (requirements.txt)
PyQt6==6.6.1, SQLAlchemy==2.0.32, reportlab==4.0.9, Jinja2==3.1.3, pytest==7.4.4, pytest-qt==4.2.0

## Pre-existing Test Issues
- `tests/test_all.py::TestValidators::test_gate_too_big` — expects validation to fail but passes (test bug)
- `tests/test_full_crud_cycle.py::TestFullCRUDCycle::test_8_full_cycle_integration` — extra item from shared fixture (11 vs 10)

## Not Present
No pyproject.toml, setup.py, Makefile, .flake8, pytest.ini, .pre-commit-config.yaml, CI workflows, CLAUDE.md, .cursorrules, or opencode.json.
