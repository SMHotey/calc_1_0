"""Регистрация всех моделей для корректной работы SQLAlchemy Base.metadata.

ВНИМАНИЕ: Этот файл КРИТИЧЕСКИ важен для работы приложения.
Без импорта всех моделей здесь, SQLAlchemy не "увидит" их таблицы при создании БД.
models/__init__.py должен импортировать ВСЕ модели, используемые в приложении.

Экспортируемые модели:
- BasePriceList, PersonalizedPriceList - прайс-листы
- Counterparty - контрагенты
- ContactPerson - контактные лица контрагентов
- GlassType, GlassOption - типы стёкол и их опции
- HardwareItem - фурнитура
- Closer - доводчики
- Coordinator - координаторы закрывания
- CommercialOffer, OfferItem - коммерческие предложения
- Deal - сделки
- ProductionOrder - заявки на производство
- Document - документы
"""

from models.price_list import BasePriceList, PersonalizedPriceList
from models.counterparty import Counterparty
from models.contact_person import ContactPerson
from models.bank_details import BankDetails
from models.glass import GlassType, GlassOption
from models.vent import VentType
from models.hardware import HardwareItem
from models.commercial_offer import CommercialOffer, OfferItem
from models.closer import Closer, Coordinator
from models.deal import Deal
from models.production_order import ProductionOrder
from models.document import Document

__all__ = [
    "BasePriceList", "PersonalizedPriceList",
    "Counterparty",
    "ContactPerson",
    "BankDetails",
    "GlassType", "GlassOption",
    "VentType",
    "HardwareItem",
    "Closer", "Coordinator",
    "CommercialOffer", "OfferItem",
    "Deal",
    "ProductionOrder",
    "Document"
]