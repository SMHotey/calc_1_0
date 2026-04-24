"""Модель контактных лиц.

Содержит ORM-модель ContactPerson для хранения контактных лиц контрагентов.
"""

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class ContactPerson(Base):
    """Контактное лицо.

    Представляет контактное лицо контрагента с ФИО, должностью, телефоном, email.
    
    Attributes:
        id: уникальный идентификатор
        counterparty_id: ссылка на контрагента
        name: ФИО контактного лица
        position: должность (может быть NULL)
        phone: телефон (может быть NULL)
        email: email (может быть NULL)
    
    Relationships:
        counterparty: связанный контрагент
    """
    __tablename__ = "contact_person"

    id: Mapped[int] = mapped_column(primary_key=True)
    counterparty_id: Mapped[int] = mapped_column(Integer, ForeignKey("counterparty.id"))
    name: Mapped[str] = mapped_column(String(200))
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)

    counterparty = relationship("Counterparty", back_populates="contact_persons")