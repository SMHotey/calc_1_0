"""Модель документов.

Содержит ORM-модель Document для хранения документов (PDF, JPEG, DOCX, XLSX).
Документы хранятся в двух форматах: путь к файлу на диске и содержимое в БД.
"""

from sqlalchemy import String, DateTime, Integer, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base
from datetime import datetime


class Document(Base):
    """Документ.

    Хранит информацию о документах, привязанных к сделке или контрагенту.
    Поддерживает PDF, JPEG, DOCX, XLSX файлы.
    Документы хранятся в двух местах: путь к файлу на диске + содержимое в БД (BLOB).

    Attributes:
        id: уникальный идентификатор
        counterparty_id: ссылка на контрагента (nullable)
        deal_id: ссылка на сделку (nullable)
        file_path: путь к файлу на диске
        file_content: бинарное содержимое файла (BLOB) для хранения в БД
        document_date: дата документа
        name: наименование документа
        file_type: тип файла (pdf, jpeg, docx, xlsx, xls, doc)

    Relationships:
        counterparty: связанный контрагент
        deal: связанная сделка
    """
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    counterparty_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("counterparty.id"), nullable=True
    )
    deal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deal.id"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(String(500))
    file_content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    document_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    name: Mapped[str] = mapped_column(String(200))
    file_type: Mapped[str] = mapped_column(String(10), default="pdf")

    counterparty = relationship("Counterparty", back_populates="documents")
    deal = relationship("Deal", back_populates="documents")