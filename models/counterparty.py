"""Модели контрагентов (ЮЛ, ИП, ФЛ)."""

from sqlalchemy import String, Enum, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base
from constants import CounterpartyType


class Counterparty(Base):
    __tablename__ = "counterparty"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[CounterpartyType] = mapped_column(Enum(CounterpartyType))
    name: Mapped[str] = mapped_column(String(200))
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)
    kpp: Mapped[str | None] = mapped_column(String(9), nullable=True)
    ogrn: Mapped[str | None] = mapped_column(String(15), nullable=True)
    address: Mapped[str] = mapped_column(String(300))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)

    price_list_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("base_price_list.id"), nullable=True
    )
    price_list = relationship("BasePriceList", backref="assigned_counterparties")
    offers = relationship("CommercialOffer", back_populates="counterparty", cascade="all, delete-orphan")