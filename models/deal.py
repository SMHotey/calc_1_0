"""Модель сделки.

Содержит ORM-модель Deal для хранения информации о коммерческих сделках
с полным workflow (от черновика до завершения/отмены).
"""

from sqlalchemy import String, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base
from datetime import datetime
from constants import DealStatus


class Deal(Base):
    """Сделка.

    Хранит информацию о коммерческой сделке с контрагентом.
    Поддерживает полный workflow: черновик -> отправлено КП -> выставлен счёт ->
    предоплата -> полная оплата -> завершена/отменена.

    Attributes:
        id: уникальный идентификатор
        number: номер сделки
        commercial_offer_id: ссылка на КП (nullable)
        counterparty_id: ссылка на контрагента
        created_at: дата создания сделки
        completed_at: дата завершения сделки (может быть NULL)
        status: статус сделки из перечисления DealStatus

        # Workflow: Счёт
        invoice_number: номер счёта (nullable)
        invoice_date: дата счёта (nullable)
        invoice_amount: сумма счёта (nullable)

        # Workflow: Предоплата
        prepayment_date: дата предоплаты (nullable)
        prepayment_amount: сумма предоплаты (nullable)

        # Workflow: Полная оплата
        full_payment_date: дата полной оплаты (nullable)

        # Workflow: Завершение
        completion_date: дата завершения сделки (nullable)

        # Workflow: Отмена
        cancellation_date: дата отмены сделки (nullable)
        cancellation_reason: причина отмены (nullable)

        comment: комментарий/примечание (может быть NULL)

    Relationships:
        production_orders: связанные заявки на производство
        documents: связанные документы
        commercial_offer: связанное коммерческое предложение
        counterparty: связанный контрагент
    """
    __tablename__ = "deal"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(50), unique=True)
    commercial_offer_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("commercial_offer.id"), nullable=True
    )
    counterparty_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparty.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[DealStatus] = mapped_column(default=DealStatus.DRAFT)

    # Счёт
    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    invoice_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Предоплата
    prepayment_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    prepayment_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Полная оплата
    full_payment_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Завершение
    completion_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Отмена
    cancellation_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)

    production_orders = relationship("ProductionOrder", back_populates="deal", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="deal", cascade="all, delete-orphan")
    commercial_offer = relationship("CommercialOffer", back_populates="deal")
    counterparty = relationship("Counterparty", back_populates="deals")