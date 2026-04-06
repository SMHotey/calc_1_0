"""CRUD-операции и запросы к БД. Отделены от UI и бизнес-логики."""

from typing import TypeVar, Type, Sequence, Any, Optional
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from db.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository:
    """Базовый репозиторий с типовыми CRUD-операциями."""

    def __init__(self, session: Session, model: Type[T]) -> None:
        self.session = session
        self.model = model

    def get_by_id(self, obj_id: int) -> Optional[T]:
        """Получение объекта по ID."""
        stmt = select(self.model).where(self.model.id == obj_id)
        return self.session.scalar(stmt)

    def get_all(self) -> Sequence[T]:
        """Получение всех записей."""
        stmt = select(self.model)
        return self.session.scalars(stmt).all()

    def create(self, instance: T) -> T:
        """Создание новой записи."""
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, obj_id: int, data: dict[str, Any]) -> Optional[T]:
        """Обновление записи по ID."""
        stmt = update(self.model).where(self.model.id == obj_id).values(**data)
        self.session.execute(stmt)
        return self.get_by_id(obj_id)

    def delete(self, obj_id: int) -> bool:
        """Удаление записи по ID."""
        stmt = delete(self.model).where(self.model.id == obj_id)
        result = self.session.execute(stmt)
        self.session.flush()
        return result.rowcount > 0