"""Контроллер управления контактными лицами: CRUD.

Содержит:
- ContactPersonController: контроллер для работы с контактными лицами
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.contact_person import ContactPerson
from db.database import SessionLocal


class ContactPersonController:
    """Контроллер для работы с контактными лицами.

    Attributes:
        session: SQLAlchemy сессия для работы с БД
        repo: базовый репозиторий для CRUD операций
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """Инициализация контроллера."""
        self.session = session or SessionLocal()
        self.repo = BaseRepository(self.session, ContactPerson)

    def create(
            self,
            name: str,
            counterparty_id: int,
            position: Optional[str] = None,
            phone: Optional[str] = None,
            email: Optional[str] = None
    ) -> ContactPerson:
        """Создаёт новое контактное лицо."""
        person = ContactPerson(
            name=name,
            counterparty_id=counterparty_id,
            position=position,
            phone=phone,
            email=email
        )
        return self.repo.create(person)

    def update(self, person_id: int, data: dict) -> Optional[ContactPerson]:
        """Обновляет данные контактного лица."""
        return self.repo.update(person_id, data)

    def delete(self, person_id: int) -> bool:
        """Удаляет контактное лицо."""
        return self.repo.delete(person_id)

    def get_by_id(self, person_id: int) -> Optional[ContactPerson]:
        """Получает контактное лицо по ID."""
        return self.repo.get_by_id(person_id)

    def get_by_counterparty(self, counterparty_id: int) -> List[ContactPerson]:
        """Получает все контактные лица контрагента."""
        stmt = select(ContactPerson).where(
            ContactPerson.counterparty_id == counterparty_id
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_all(self) -> List[ContactPerson]:
        """Возвращает все контактные лица."""
        return self.repo.get_all()