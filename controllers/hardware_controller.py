"""Контроллер управления фурнитурой: CRUD, фильтрация по типам.

Содержит:
- HardwareController: контроллер для работы с дверной фурнитурой
- CRUD операции для замков, ручек, цилиндров, доводчиков
- Фильтрация по типу и прайс-листу
- Валидация связи «замок с цилиндром»
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.hardware import HardwareItem
from db.database import SessionLocal
from constants import HardwareType


class HardwareController:
    """Контроллер для работы с фурнитурой.

    Отвечает за:
    - CRUD замков, ручек, цилиндров, доводчиков
    - Фильтрацию по типу и прайс-листу
    - Валидацию связи «замок с цилиндром»
    - Группировку фурнитуры по типам

    Attributes:
        session: SQLAlchemy сессия для работы с БД
        repo: базовый репозиторий для CRUD операций
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """Инициализация контроллера.

        Args:
            session: опциональная сессия БД. Если не передана - создаётся новая.
        """
        self.session = session or SessionLocal()
        self.repo = BaseRepository(self.session, HardwareItem)

    def create(
            self,
            hw_type: str,
            name: str,
            price: float,
            price_list_id: int,
            description: Optional[str] = None,
            image_path: Optional[str] = None,
            has_cylinder: bool = False
    ) -> HardwareItem:
        """Создаёт новый элемент фурнитуры.

        Args:
            hw_type: тип фурнитуры (Замок, Ручка, Цилиндровый механизм, Доводчик)
            name: название/модель
            price: цена в рублях
            price_list_id: ID прайс-листа
            description: описание (опционально)
            image_path: путь к изображению (опционально)
            has_cylinder: требует ли замок цилиндра

        Returns:
            Созданный объект HardwareItem
        """
        item = HardwareItem(
            type=hw_type,
            name=name,
            price=price,
            description=description,
            image_path=image_path,
            has_cylinder=has_cylinder,
            price_list_id=price_list_id
        )
        return self.repo.create(item)

    def update(self, item_id: int, data: Dict[str, Any]) -> Optional[HardwareItem]:
        """Обновляет элемент фурнитуры.

        Args:
            item_id: ID элемента
            data: словарь с полями для обновления

        Returns:
            Обновлённый объект HardwareItem или None
        """
        return self.repo.update(item_id, data)

    def delete(self, item_id: int) -> bool:
        """Удаляет элемент фурнитуры.

        Args:
            item_id: ID элемента

        Returns:
            True если удаление успешно
        """
        return self.repo.delete(item_id)

    def get_by_id(self, item_id: int) -> Optional[HardwareItem]:
        """Получает элемент по ID.

        Args:
            item_id: ID элемента

        Returns:
            Объект HardwareItem или None
        """
        return self.repo.get_by_id(item_id)

    def get_by_type(self, hw_type: str, price_list_id: int) -> List[HardwareItem]:
        """Возвращает фурнитуру указанного типа для конкретного прайс-листа.

        Args:
            hw_type: тип фурнитуры
            price_list_id: ID прайс-листа

        Returns:
            Список элементов фурнитуры указанного типа
        """
        stmt = select(HardwareItem).where(
            HardwareItem.type == hw_type,
            HardwareItem.price_list_id == price_list_id
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_all_for_price_list(self, price_list_id: int) -> Dict[str, List[HardwareItem]]:
        """Группирует всю фурнитуру прайс-листа по типам.

        Args:
            price_list_id: ID прайс-листа

        Returns:
            Словарь: ключ = тип фурнитуры, значение = список элементов
        """
        stmt = select(HardwareItem).where(HardwareItem.price_list_id == price_list_id)
        items = self.session.execute(stmt).scalars().all()

        # Группировка по типам
        result = {t.value: [] for t in HardwareType}
        for item in items:
            if item.type in result:
                result[item.type].append(item)
        return result

    def get_cylinders_for_lock(self, lock_id: int) -> List[HardwareItem]:
        """Возвращает совместимые цилиндры для замка с флагом has_cylinder=True.

        Если замок не требует цилиндр (has_cylinder=False) - возвращает пустой список.

        Args:
            lock_id: ID замка

        Returns:
            Список цилиндровых механизмов, подходящих для замка
        """
        lock = self.get_by_id(lock_id)
        if not lock or not lock.has_cylinder:
            return []

        stmt = select(HardwareItem).where(
            HardwareItem.type == HardwareType.CYLINDER,
            HardwareItem.price_list_id == lock.price_list_id
        )
        return list(self.session.execute(stmt).scalars().all())

    def __enter__(self):
        """Контекстный менеджер - вход."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход (закрытие сессии)."""
        if exc_type:
            self.session.rollback()
        self.session.close()