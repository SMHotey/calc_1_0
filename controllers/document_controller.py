"""Контроллер управления документами: CRUD, загрузка, хранение.

Содержит:
- DocumentController: контроллер для работы с документами
- Загрузка файлов через диалог и сохранение в БД + на диск
- Фильтрация по владельцу (контрагент/сделка)
"""

from typing import Optional, List, Dict, Any
import os
import shutil
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from db.repositories import BaseRepository
from models.document import Document
from db.database import SessionLocal
from constants import DOCUMENT_FILE_TYPES
from datetime import datetime


class DocumentController:
    """Контроллер для работы с документами.

    Отвечает за:
    - CRUD документов
    - Загрузку файлов (сохранение в БД и на диск)
    - Фильтрацию по контрагенту/сделке
    - Экспорт документа на диск

    Attributes:
        session: SQLAlchemy сессия для работы с БД
        repo: базовый репозиторий для CRUD операций
        storage_path: путь для хранения файлов на диске
    """

    def __init__(self, session: Optional[Session] = None,
                 storage_path: Optional[str] = None) -> None:
        """Инициализация контроллера.

        Args:
            session: опциональная сессия БД. Если не передана - создаётся новая.
            storage_path: путь для хранения файлов на диске
        """
        self.session = session or SessionLocal()
        self.repo = BaseRepository(self.session, Document)

        # Папка для хранения файлов
        if storage_path:
            self.storage_path = storage_path
        else:
            # По умолчанию - в папке docs рядом с проектом
            self.storage_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "docs"
            )

        # Создаём папку если не существует
        os.makedirs(self.storage_path, exist_ok=True)

    def create(
            self,
            name: str,
            file_path: str,
            counterparty_id: Optional[int] = None,
            deal_id: Optional[int] = None,
            document_date: Optional[datetime] = None,
            save_to_disk: bool = True
    ) -> Document:
        """Создаёт новый документ с загрузкой файла.

        Args:
            name: наименование документа
            file_path: путь к файлу на диске
            counterparty_id: ID контрагента (если привязан к контрагенту)
            deal_id: ID сделки (если привязан к сделке)
            document_date: дата документа (по умолчанию - текущая)
            save_to_disk: сохранять ли копию на диск

        Returns:
            Созданный объект Document

        Raises:
            ValueError: если файл не найден или неверный формат
            ValueError: если не указан ни counterparty_id, ни deal_id
        """
        if not counterparty_id and not deal_id:
            raise ValueError("Документ должен быть привязан к контрагенту или сделке")

        # Проверяем существование файла
        if not os.path.exists(file_path):
            raise ValueError(f"Файл не найден: {file_path}")

        # Определяем тип файла
        file_ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        file_type = file_ext if file_ext in DOCUMENT_FILE_TYPES else "pdf"

        # Читаем содержимое файла
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Определяем путь для сохранения на диске
        disk_path = ""
        if save_to_disk:
            # Генерируем уникальное имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            disk_path = os.path.join(
                self.storage_path,
                f"{timestamp}_{base_name}.{file_type}"
            )
            # Копируем файл
            shutil.copy2(file_path, disk_path)

        document = Document(
            name=name,
            file_path=disk_path or file_path,
            file_content=file_content,
            file_type=file_type,
            counterparty_id=counterparty_id,
            deal_id=deal_id,
            document_date=document_date or datetime.now()
        )

        return self.repo.create(document)

    def create_from_content(
            self,
            name: str,
            file_content: bytes,
            file_type: str,
            counterparty_id: Optional[int] = None,
            deal_id: Optional[int] = None,
            document_date: Optional[datetime] = None
    ) -> Document:
        """Создаёт документ из бинарного содержимого (без загрузки с диска).

        Args:
            name: наименование документа
            file_content: бинарное содержимое файла
            file_type: тип файла (pdf, xlsx, docx и т.д.)
            counterparty_id: ID контрагента
            deal_id: ID сделки
            document_date: дата документа

        Returns:
            Созданный объект Document
        """
        if not counterparty_id and not deal_id:
            raise ValueError("Документ должен быть привязан к контрагенту или сделке")

        # Сохраняем на диск
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        disk_path = os.path.join(
            self.storage_path,
            f"{timestamp}_{name}.{file_type}"
        )

        try:
            with open(disk_path, "wb") as f:
                f.write(file_content)
        except Exception:
            disk_path = ""  # Если не удалось сохранить

        document = Document(
            name=name,
            file_path=disk_path,
            file_content=file_content,
            file_type=file_type,
            counterparty_id=counterparty_id,
            deal_id=deal_id,
            document_date=document_date or datetime.now()
        )

        return self.repo.create(document)

    def update(self, doc_id: int, data: Dict[str, Any]) -> Optional[Document]:
        """Обновляет данные документа.

        Args:
            doc_id: ID документа
            data: словарь с полями для обновления

        Returns:
            Обновлённый объект Document или None
        """
        # Обработка даты
        if "document_date" in data and isinstance(data["document_date"], str):
            try:
                data["document_date"] = datetime.strptime(data["document_date"], "%d.%m.%Y")
            except ValueError:
                data["document_date"] = None

        return self.repo.update(doc_id, data)

    def delete(self, doc_id: int, delete_file: bool = True) -> bool:
        """Удаляет документ.

        Args:
            doc_id: ID документа
            delete_file: удалять ли файл с диска

        Returns:
            True если удалено
        """
        doc = self.repo.get_by_id(doc_id)
        if doc and delete_file and doc.file_path and os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except OSError:
                pass  # Игнорируем ошибки удаления файла

        return self.repo.delete(doc_id)

    def get_by_id(self, doc_id: int) -> Optional[Document]:
        """Получает документ по ID.

        Args:
            doc_id: ID документа

        Returns:
            Объект Document или None
        """
        return self.repo.get_by_id(doc_id)

    def get_all(self) -> List[Document]:
        """Возвращает все документы.

        Returns:
            Список всех документов
        """
        return self.repo.get_all()

    def get_by_counterparty(self, counterparty_id: int) -> List[Document]:
        """Получает все документы контрагента.

        Args:
            counterparty_id: ID контрагента

        Returns:
            Список документов контрагента
        """
        return list(self.session.execute(
            select(Document).where(Document.counterparty_id == counterparty_id)
        ).scalars().all())

    def get_by_deal(self, deal_id: int) -> List[Document]:
        """Получает все документы сделки.

        Args:
            deal_id: ID сделки

        Returns:
            Список документов сделки
        """
        return list(self.session.execute(
            select(Document).where(Document.deal_id == deal_id)
        ).scalars().all())

    def get_documents_for_owner(
            self,
            counterparty_id: Optional[int] = None,
            deal_id: Optional[int] = None
    ) -> List[Document]:
        """Получает документы для владельца (контрагент или сделка).

        Args:
            counterparty_id: ID контрагента
            deal_id: ID сделки

        Returns:
            Список документов
        """
        conditions = []

        if counterparty_id:
            conditions.append(Document.counterparty_id == counterparty_id)
        if deal_id:
            conditions.append(Document.deal_id == deal_id)

        if not conditions:
            return []

        stmt = select(Document).where(and_(*conditions))
        return list(self.session.execute(stmt).scalars().all())

    def export_to_disk(self, doc_id: int, destination_path: str) -> bool:
        """Экспортирует документ на диск.

        Args:
            doc_id: ID документа
            destination_path: путь для сохранения

        Returns:
            True если успешно
        """
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            return False

        # Сначала пробуем взять из БД
        if doc.file_content:
            with open(destination_path, "wb") as f:
                f.write(doc.file_content)
            return True

        # Если нет в БД - пробуем с диска
        if doc.file_path and os.path.exists(doc.file_path):
            shutil.copy2(doc.file_path, destination_path)
            return True

        return False

    def get_document_info(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о документе.

        Args:
            doc_id: ID документа

        Returns:
            Словарь с информацией о документе
        """
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            return None

        return {
            "id": doc.id,
            "name": doc.name,
            "file_type": doc.file_type,
            "file_path": doc.file_path,
            "document_date": doc.document_date.strftime("%d.%m.%Y") if doc.document_date else None,
            "counterparty_id": doc.counterparty_id,
            "deal_id": doc.deal_id,
            "has_content": doc.file_content is not None
        }