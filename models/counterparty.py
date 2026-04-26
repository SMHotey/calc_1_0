"""Модели контрагентов (ЮЛ, ИП, ФЛ).

Содержит ORM-модель Counterparty для хранения информации о контрагентах:
юридических лицах, индивидуальных предпринимателях и физических лицах.
"""

from sqlalchemy import String, Enum, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base
from constants import CounterpartyType


class Counterparty(Base):
    """Контрагент (клиент, поставщик, партнёр).
    
    Хранит информацию о юридических лицах, ИП и физических лицах.
    Каждый контрагент может быть привязан к персонализированному прайс-листу.
    
    Attributes:
        id: уникальный идентификатор
        type: тип контрагента (ЮЛ, ИП, ФЛ) из перечисления CounterpartyType
        name: наименование контрагента
        inn: ИНН (для ЮЛ - 10 цифр, для ИП - 12 цифр)
        kpp: КПП (только для ЮЛ, 9 цифр)
        ogrn: ОГРН/ОГРНИП
        address: юридический/физический адрес
        phone: контактный телефон
        email: контактный email (может быть пустым для ФЛ)
        price_list_id: ссылка на базовый прайс-лист (nullable - может быть не привязан)
        
    Relationships:
        price_list: связанный базовый прайс-лист
        offers: связанные коммерческие предложения
    """
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
    documents = relationship("Document", back_populates="counterparty", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="counterparty", cascade="all, delete-orphan")
    contact_persons = relationship("ContactPerson", back_populates="counterparty", cascade="all, delete-orphan")
    bank_details = relationship("BankDetails", back_populates="counterparty", cascade="all, delete-orphan")