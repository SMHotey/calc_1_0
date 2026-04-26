"""Базовый контроллер с общей функциональностью для всех контроллеров."""

from typing import Optional, Type, Dict, Any, List, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from db.database import SessionLocal

# Generic type for model classes
T = TypeVar('T')


class BaseController:
    """Базовый класс для всех контроллеров с общей функциональностью.
    
    Содержит общие методы для:
    - Инициализации сессии и репозитория
    - Базовых CRUD операций
    - Обработки дат
    - Валидации данных
    """
    
    def __init__(self, model: Type[T], session: Optional[Session] = None) -> None:
        """Инициализация базового контроллера.
        
        Args:
            model: SQLAlchemy модель, с которой работает контроллер
            session: опциональная сессия БД. Если не передана - создаётся новая.
        """
        self.session = session or SessionLocal()
        self.repo = BaseRepository(self.session, model)
        self.model = model

    def get_by_id(self, id: int) -> Optional[T]:
        """Получает объект по ID.
        
        Args:
            id: идентификатор объекта
            
        Returns:
            Объект модели или None
        """
        return self.repo.get_by_id(id)

    def get_all(self) -> List[T]:
        """Возвращает все объекты.
        
        Returns:
            Список всех объектов модели
        """
        return self.repo.get_all()

    def create(self, **kwargs) -> Optional[T]:
        """Создаёт новый объект.
        
        Args:
            **kwargs: атрибуты объекта
            
        Returns:
            Созданный объект модели
        """
        return self.repo.create(self.model(**kwargs))

    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Обновляет объект по ID.
        
        Args:
            id: идентификатор объекта
            data: словарь с полями для обновления
            
        Returns:
            Обновлённый объект модели или None
        """
        return self.repo.update(id, data)

    def delete(self, id: int) -> bool:
        """Удаляет объект по ID.
        
        Args:
            id: идентификатор объекта
            
        Returns:
            True если удалено, False если не найден
        """
        return self.repo.delete(id)

    def _handle_date_field(self, data: Dict[str, Any], field_name: str) -> None:
        """Обрабатывает поле даты, преобразуя строку в datetime объект.
        
        Args:
            data: словарь с данными
            field_name: имя поля даты для обработки
        """
        if field_name in data and isinstance(data[field_name], str):
            try:
                from datetime import datetime
                data[field_name] = datetime.strptime(data[field_name], "%d.%m.%Y")
            except ValueError:
                data[field_name] = None

    def _handle_date_fields(self, data: Dict[str, Any], field_names: List[str]) -> None:
        """Обрабатывает несколько полей дат.
        
        Args:
            data: словарь с данными
            field_names: список имён полей дат для обработки
        """
        for field_name in field_names:
            self._handle_date_field(data, field_name)

    def _validate_unique_field(self, id: Optional[int], field_name: str, field_value: Any) -> bool:
        """Проверяет уникальность значения поля (кроме текущего объекта если указан id).
        
        Args:
            id: идентификатор текущего объекта (None для новых объектов)
            field_name: имя поля для проверки
            field_value: значение поля для проверки уникальности
            
        Returns:
            True если значение уникально, False если уже существует
        """
        stmt = select(self.model).where(getattr(self.model, field_name) == field_value)
        if id is not None:
            stmt = stmt.where(self.model.id != id)
        existing = self.session.execute(stmt).scalar_one_or_none()
        return existing is None