"""Контроллер для управления доводчиками и координаторами закрывания."""

from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.closer import Closer, Coordinator


class CloserController:
    """Контроллер для управления доводчиками и координаторами закрывания."""
    
    def __init__(self, session: Session = None):
        self._session = session
    
    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = SessionLocal()
        return self._session
    
    def set_session(self, session: Session) -> None:
        """Установить внешнюю сессию для совместного использования."""
        self._session = session
        
    def close(self):
        if self._session is not None and self._session != SessionLocal():
            self._session.close()
    
    # Доводчики
    def get_closers(self, price_list_id: int) -> list[Closer]:
        """Получить все доводчики для прайс-листа."""
        return self.session.query(Closer).filter(
            Closer.price_list_id == price_list_id
        ).order_by(Closer.door_weight).all()
    
    def get_closer_by_id(self, closer_id: int) -> Closer | None:
        """Получить доводчик по ID."""
        return self.session.query(Closer).filter(Closer.id == closer_id).first()
    
    def create_closer(self, price_list_id: int, name: str, door_weight: float, price: float) -> Closer:
        """Создать новый доводчик."""
        closer = Closer(
            price_list_id=price_list_id,
            name=name,
            door_weight=door_weight,
            price=price
        )
        self.session.add(closer)
        self.session.commit()
        self.session.refresh(closer)
        return closer
    
    def update_closer(self, closer_id: int, name: str = None, door_weight: float = None, price: float = None) -> Closer | None:
        """Обновить доводчик."""
        closer = self.get_closer_by_id(closer_id)
        if closer is None:
            return None
        if name is not None:
            closer.name = name
        if door_weight is not None:
            closer.door_weight = door_weight
        if price is not None:
            closer.price = price
        self.session.commit()
        self.session.refresh(closer)
        return closer
    
    def delete_closer(self, closer_id: int) -> bool:
        """Удалить доводчик."""
        closer = self.get_closer_by_id(closer_id)
        if closer is None:
            return False
        self.session.delete(closer)
        self.session.commit()
        return True
    
    # Координаторы
    def get_coordinators(self, price_list_id: int) -> list[Coordinator]:
        """Получить все координаторы для прайс-листа."""
        return self.session.query(Coordinator).filter(
            Coordinator.price_list_id == price_list_id
        ).all()
    
    def get_coordinator_by_id(self, coord_id: int) -> Coordinator | None:
        """Получить координатор по ID."""
        return self.session.query(Coordinator).filter(Coordinator.id == coord_id).first()
    
    def create_coordinator(self, price_list_id: int, name: str, price: float) -> Coordinator:
        """Создать новый координатор."""
        coordinator = Coordinator(
            price_list_id=price_list_id,
            name=name,
            price=price
        )
        self.session.add(coordinator)
        self.session.commit()
        self.session.refresh(coordinator)
        return coordinator
    
    def update_coordinator(self, coord_id: int, name: str = None, price: float = None) -> Coordinator | None:
        """Обновить координатор."""
        coordinator = self.get_coordinator_by_id(coord_id)
        if coordinator is None:
            return None
        if name is not None:
            coordinator.name = name
        if price is not None:
            coordinator.price = price
        self.session.commit()
        self.session.refresh(coordinator)
        return coordinator
    
    def delete_coordinator(self, coord_id: int) -> bool:
        """Удалить координатор."""
        coordinator = self.get_coordinator_by_id(coord_id)
        if coordinator is None:
            return False
        self.session.delete(coordinator)
        self.session.commit()
        return True