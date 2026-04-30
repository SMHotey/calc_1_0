"""CRUD-операции и запросы к БД. Отделены от UI и бизнес-логики.

Содержит:
- BaseRepository - базовый класс с типовыми операциями (CRUD)
- Типизированные методы для работы с любой моделью
"""

from typing import TypeVar, Type, Sequence, Any, Optional
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from db.database import Base

# Типовая переменная для Generic-классов репозитория
# Ограничена снизу классом Base (все ORM-модели наследуют Base)
T = TypeVar("T", bound=Base)


class BaseRepository:
    """Базовый репозиторий с типовыми CRUD-операциями.
    
    Паттерн Repository: абстракция над доступом к данным.
    Позволяет унифицировать операции для всех моделей.
    
    Attributes:
        session: активная сессия БД
        model: класс модели для операций
    
    Example:
        repo = BaseRepository(session, User)
        user = repo.get_by_id(1)
        all_users = repo.get_all()
    """

    def __init__(self, session: Session, model: Type[T]) -> None:
        """Инициализация репозитория.
        
        Args:
            session: активная сессия SQLAlchemy
            model: класс модели (например, User, Product)
        """
        self.session = session
        self.model = model

    def get_by_id(self, obj_id: int) -> Optional[T]:
        """Получение объекта по ID.
        
        Args:
            obj_id: идентификатор объекта в БД
            
        Returns:
            Объект модели или None, если не найден
        """
        stmt = select(self.model).where(self.model.id == obj_id)
        return self.session.scalar(stmt)

    def get_all(self) -> Sequence[T]:
        """Получение всех записей данной модели.
        
        Returns:
            Список всех объектов модели
        """
        stmt = select(self.model)
        return self.session.scalars(stmt).all()

    def create(self, instance: T) -> T:
        """Создание новой записи в БД.
        
        Args:
            instance: объект модели для сохранения
            
        Returns:
            тот же объект с присвоенным ID
        """
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, obj_id: int, data: dict[str, Any]) -> Optional[T]:
        """Обновление записи по ID.
        
        Args:
            obj_id: идентификатор объекта
            data: словарь с полями для обновления
            
        Returns:
            Обновлённый объект или None, если не найден
        """
        try:
            # First, get the object to ensure it exists and is in session
            instance = self.get_by_id(obj_id)
            if not instance:
                return None
            
            # Update attributes directly (this is tracked by SQLAlchemy)
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            self.session.flush()
            return instance
        except Exception:
            self.session.rollback()
            raise

    def delete(self, obj_id: int) -> bool:
        """Удаление записи по ID.
        
        Args:
            obj_id: идентификатор объекта
            
        Returns:
            True если удалено, False если не найден
        """
        try:
            stmt = delete(self.model).where(self.model.id == obj_id)
            result = self.session.execute(stmt)
            self.session.flush()
            return result.rowcount > 0
        except Exception:
            self.session.rollback()
            raise