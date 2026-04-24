"""Модель заявки на производство.

Содержит ORM-модель ProductionOrder для хранения заявок на производство.
"""

from sqlalchemy import DateTime, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base
from constants import ProductionOrderStatus
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON


class ProductionOrder(Base):
    """Заявка на производство.

    Создаётся на основе коммерческого предложения. Отслеживает статус
    производства изделия от черновика до отгрузки.

    Attributes:
        id: уникальный идентификатор
        commercial_offer_id: ссылка на коммерческое предложение
        deal_id: ссылка на сделку
        created_at: дата создания заявки
        updated_at: дата последнего редактирования
        changes: внесённые изменения (JSON)
        status: текущий статус заявки

    Relationships:
        commercial_offer: связанное коммерческое предложение
        deal: связанная сделка
    """
    __tablename__ = "production_order"

    id: Mapped[int] = mapped_column(primary_key=True)
    commercial_offer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("commercial_offer.id"), nullable=True
    )
    deal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    changes: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[ProductionOrderStatus] = mapped_column(
        Enum(ProductionOrderStatus), default=ProductionOrderStatus.DRAFT
    )

    commercial_offer = relationship("CommercialOffer", back_populates="production_orders")
    deal = relationship("Deal", back_populates="production_orders")