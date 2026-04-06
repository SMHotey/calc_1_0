"""Регистрация всех моделей для корректной работы SQLAlchemy Base.metadata."""

from models.price_list import BasePriceList, PersonalizedPriceList
from models.counterparty import Counterparty
from models.glass import GlassType, GlassOption
from models.hardware import HardwareItem
from models.commercial_offer import CommercialOffer, OfferItem
from models.option_preset import OptionPreset

__all__ = [
    "BasePriceList", "PersonalizedPriceList",
    "Counterparty",
    "GlassType", "GlassOption",
    "HardwareItem",
    "CommercialOffer", "OfferItem",
    "OptionPreset"
]