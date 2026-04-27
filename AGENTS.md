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
- **New DB**: Delete and recreate `db/metalcalc.db` to pick up schema changes

## Architecture

- **MVC**: Models (SQLAlchemy) → Controllers → Views (PyQt6)
- **Calculator dispatch**: `CalculatorContext` + `CALC_MAP` → Door/Hatch/Gate/Transom/Glass calculators
- **Session**: Controllers auto-create via `SessionLocal()`; tests pass explicit sessions
- **Offer Options**: Reorganized from JSON to 7 separate tables:
  - `OfferItemGlass` (inline options_data JSON)
  - `OfferItemVent`, `OfferItemLock`, `OfferItemHandle`, `OfferItemCylinder`
  - `OfferItemCloser`, `OfferItemCoordinator`
- Each option table has `get_prices()` → `(base_price, current_price)` dual-price method
- Click-to-edit from КП table: click position → loads into calculator → edit → Save button appears → save to DB

## Model Registration (Critical)
`models/__init__.py` MUST import all model classes — without this, `Base.metadata` is incomplete and tables won't create. `db/database.py` imports models inside `init_db()` to avoid circular imports.

## Price Tables Short Names
Added to: `GlassOption`, `VentType`, `HardwareItem`, `Closer`, `Coordinator`:
- `short_name_kp`: for КП display
- `short_name_prod`: for production order

UI for short names in: `views/price_tab.py` dialogs and tables.

## Price Resolution
`PriceListController.get_price_for_calculation()` merges personalized prices over base; `None` falls through to base.

## Pre-existing Issues (Documented Failures)
- `tests/test_all.py::TestValidators::test_gate_too_big` — expects validation to fail but passes
- `tests/test_full_crud_cycle.py::TestFullCRUDCycle::test_8_full_cycle_integration` — extra item from shared fixture (11 vs 10)
- `db/` directory not a package (no `__init__.py`) — imports `db.database` work directly

## Modules (CRM)

### Deals (Сделки)
- **Model**: `models/deal.py` — Deal с workflow (черновик → КП → счёт → предоплата → оплата → завершена/отменена)
- **Controller**: `controllers/deal_controller.py` — CRUD, create_from_offer(), workflow methods
- **View**: `views/deals_tab.py` — DealsTab + DealDetailWidget (с документами внутри)
- **Dialog**: `views/dialogs/deal_dialog.py` — создание/редактирование сделки

### Documents (Документы)
- **Model**: `models/document.py` — Document с file_content (BLOB) и file_path
- **Controller**: `controllers/document_controller.py` — CRUD, загрузка файлов, export
- **View**: `views/documents_widget.py` — DocumentsWidget (используется в сделке и контрагенте)
- **Dialog**: `views/dialogs/document_dialog.py` — загрузка файла через file dialog
- **Supported formats**: PDF, XLSX, XLS, DOCX, DOC, JPEG

### Tab Integration
- **OffersTab** (КП): добавлена кнопка "Создать сделку" в контекстном меню
- **DealsTab** (Сделки): отдельная вкладка с фильтрами (контрагент, статус, даты)
- **CounterpartiesTab** (Контрагенты): сплиттер со списком и документами
