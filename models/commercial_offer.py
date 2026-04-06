"""Модели коммерческих предложений и их позиций."""

from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON


class CommercialOffer(Base):
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


class OfferItem(Base):
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