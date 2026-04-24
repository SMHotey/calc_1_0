"""Модели коммерческих предложений и их позиций.

Содержит ORM-модели для:
- CommercialOffer: коммерческое предложение (КП) для контрагента
- OfferItem: позиция в коммерческом предложении (конкретное изделие)
"""

from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON


class CommercialOffer(Base):
    """Коммерческое предложение (КП).
    
    Создаётся для конкретного контрагента. Содержит набор позиций (изделий)
    с рассчитанными ценами.
    
    Attributes:
        id: уникальный идентификатор
        number: номер КП (уникальный, например, "КП-2024-001")
        date: дата создания/выдачи КП
        total_amount: общая сумма КП
        notes: примечание/комментарий (может быть NULL)
        counterparty_id: ссылка на контрагента
        
    Relationships:
        counterparty: связанный контрагент
        items: позиции КП (удаляются каскадом при удалении КП)
    """
    __tablename__ = "commercial_offer"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    total_amount: Mapped[float]
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    counterparty_id: Mapped[int] = mapped_column(ForeignKey("counterparty.id"))
    counterparty = relationship("Counterparty", back_populates="offers")
    items = relationship("OfferItem", back_populates="offer", order_by="OfferItem.position",
                         cascade="all, delete-orphan")
    production_orders = relationship("ProductionOrder", back_populates="commercial_offer",
                            cascade="all, delete-orphan")
    deal = relationship("Deal", back_populates="commercial_offer", uselist=False)


class OfferItem(Base):
    """Позиция в коммерческом предложении.
    
    Представляет одно изделие (дверь, люк, ворота и т.д.) с размерами,
    опциями и рассчитанной ценой.
    
    Attributes:
        id: уникальный идентификатор
        position: порядковый номер позиции в КП
        product_type: тип изделия (Дверь, Люк, Ворота, Фрамуга)
        subtype: подтип (Техническая, EI 60 и т.д.)
        width: ширина в мм
        height: высота в мм
        quantity: количество изделий
        options_: JSON-объект с выбранными опциями (стекло, фурнитура и т.д.)
        base_price: базовая цена изделия
        markup_percent: наценка в процентах
        markup_abs: абсолютная наценка (в рублях)
        final_price: итоговая цена (база + наценки)
        offer_id: ссылка на родительское КП
        
    Relationships:
        offer: родительское коммерческое предложение
    """
    __tablename__ = "offer_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    position: Mapped[int]
    product_type: Mapped[str] = mapped_column(String(50))
    subtype: Mapped[str] = mapped_column(String(50))
    width: Mapped[float]
    height: Mapped[float]
    quantity: Mapped[int]
    options_: Mapped[dict] = mapped_column(JSON, default=dict)  # Сериализованные опции
    base_price: Mapped[float]
    markup_percent: Mapped[float]
    markup_abs: Mapped[float]
    final_price: Mapped[float]

    offer_id: Mapped[int] = mapped_column(ForeignKey("commercial_offer.id"))
    offer = relationship("CommercialOffer", back_populates="items")