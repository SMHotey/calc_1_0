"""Глобальные константы и конфигурация приложения."""

from enum import Enum

APP_NAME: str = "МеталлоКальк PRO"
APP_VERSION: str = "2.0.0"
LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# --- UI Strings ---
TAB_CALCULATOR: str = "Калькулятор"
TAB_OFFERS: str = "Коммерческие предложения"
TAB_PRICES: str = "Прайс-листы"
TAB_COUNTERPARTIES: str = "Контрагенты"
TAB_PRESETS: str = "Наборы опций"

BTN_ADD: str = "Добавить"
BTN_EDIT: str = "Редактировать"
BTN_DELETE: str = "Удалить"
BTN_SAVE: str = "Сохранить"
BTN_CANCEL: str = "Отмена"
BTN_EXPORT_PDF: str = "Экспорт PDF"
BTN_EXPORT_HTML: str = "Экспорт HTML"

MSG_CONFIRM_DELETE: str = "Удалить '{name}'? При удалении прайс-листа связанные контрагенты будут привязаны к базовому."
ERR_DIMENSIONS: str = "Недопустимые размеры для данного типа изделия."
ERR_NO_COUNTERPARTY: str = "Для сохранения КП выберите контрагента."
ERR_PRICE_LINK: str = "К контрагенту не привязан прайс-лист."

# --- Продукция ---
PRODUCT_DOOR: str = "Дверь"
PRODUCT_HATCH: str = "Люк"
PRODUCT_GATE: str = "Ворота"
PRODUCT_TRANSOM: str = "Фрамуга"

PRODUCT_TYPES: dict[str, list[str]] = {
    PRODUCT_DOOR: ["Техническая", "EI 60", "EIS 60", "EIWS 60", "Квартирная", "Однолистовая"],
    PRODUCT_HATCH: ["Технический", "EI 60", "Ревизионный"],
    PRODUCT_GATE: ["Технические", "EI 60", "Однолистовые"],
    PRODUCT_TRANSOM: ["Техническая", "EI 60"]
}

STANDARD_RAL: list[str] = ["7035", "7040", "8017", "3003", "5005", "9016", "9005"]

# --- Типы контрагентов ---
class CounterpartyType(str, Enum):
    LEGAL = "Юридическое лицо"
    IP = "Индивидуальный предприниматель"
    NATURAL = "Физическое лицо"

# --- Типы фурнитуры ---
class HardwareType(str, Enum):
    LOCK = "Замок"
    HANDLE = "Ручка"
    CYLINDER = "Цилиндровый механизм"
    CLOSER = "Доводчик"