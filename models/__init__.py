"""Регистрация всех моделей для корректной работы SQLAlchemy Base.metadata.

ВНИМАНИЕ: Этот файл КРИТИЧЕСКИ важен для работы приложения.
Без импорта всех моделей здесь, SQLAlchemy не "увидит" их таблицы при создании БД.
models/__init__.py должен импортировать ВСЕ модели, используемые в приложении.

Экспортируемые модели:
- BasePriceList, PersonalizedPriceList - прайс-листы
- Counterparty - контрагенты
- GlassType, GlassOption - типы стёкол и их опции
- HardwareItem - фурнитура
- Closer - доводчики
- Coordinator - координаторы закрывания
- CommercialOffer, OfferItem - коммерческие предложения
- OptionPreset - наборы опций
"""

from models.price_list import BasePriceList, PersonalizedPriceList
from models.counterparty import Counterparty
from models.glass import GlassType, GlassOption
from models.hardware import HardwareItem
from models.commercial_offer import CommercialOffer, OfferItem
from models.option_preset import OptionPreset
from models.closer import Closer, Coordinator

__all__ = [
    "BasePriceList", "PersonalizedPriceList",
    "Counterparty",
    "GlassType", "GlassOption",
    "HardwareItem",
    "Closer", "Coordinator",
    "CommercialOffer", "OfferItem",
    "OptionPreset"
]