"""Модель банковских реквизитов контрагентов.

Содержит ORM-модель BankDetails для хранения банковских реквизитов контрагентов.
"""

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class BankDetails(Base):
    """Банковские реквизиты.

    Хранит банковские реквизиты контрагента: расчётный счёт, банк, БИК, корр. счёт.
    
    Attributes:
        id: уникальный идентификатор
        counterparty_id: ссылка на контрагента
        bank_name: название банка
        bik: БИК банка
        correspondent_account: корреспондентский счёт
        settlement_account: расчётный счёт
        is_default: является ли основным счётом
        notes: примечание
    
    Relationships:
        counterparty: связанный контрагент
    """
    __tablename__ = "bank_details"

    id: Mapped[int] = mapped_column(primary_key=True)
    counterparty_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparty.id"))
    bank_name: Mapped[str] = mapped_column(String(200))
    bik: Mapped[str] = mapped_column(String(9))  # 9 символов БИК
    correspondent_account: Mapped[str] = mapped_column(String(20))  # Корр. счёт
    settlement_account: Mapped[str] = mapped_column(String(20))  # Расчётный счёт
    is_default: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(String(200), nullable=True)

    counterparty = relationship("Counterparty", back_populates="bank_details")