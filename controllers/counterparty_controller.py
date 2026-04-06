"""Контроллер управления контрагентами: CRUD, привязка прайс-листов."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.counterparty import Counterparty, CounterpartyType
from db.database import SessionLocal


class CounterpartyController:
    """
    Контроллер для работы с контрагентами.

    Отвечает за:
    - CRUD всех типов контрагентов
    - Валидацию уникальности ИНН/ОГРН
    - Привязку/отвязку прайс-листов
    - Проверку использования в КП перед удалением
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session or SessionLocal()
        self.repo = BaseRepository(self.session, Counterparty)

    def create(
            self,
            cp_type: CounterpartyType,
            name: str,
            inn: Optional[str],
            phone: str,
            address: str,
            email: Optional[str] = None,
            kpp: Optional[str] = None,
            ogrn: Optional[str] = None,
            price_list_id: Optional[int] = None
    ) -> Counterparty:
        """Создаёт нового контрагента с валидацией обязательных полей."""
        if cp_type == CounterpartyType.LEGAL and not (inn and kpp and ogrn):
            raise ValueError("Для ЮЛ обязательны ИНН, КПП, ОГРН")
        if cp_type == CounterpartyType.IP and not (inn and ogrn):
            raise ValueError("Для ИП обязательны ИНН и ОГРНИП")

        # Проверка уникальности ИНН
        if inn and self._inn_exists(inn):
            raise ValueError(f"Контрагент с ИНН {inn} уже существует")

        cp = Counterparty(
            type=cp_type,
            name=name,
            inn=inn,
            kpp=kpp,
            ogrn=ogrn,
            phone=phone,
            email=email,
            address=address,
            price_list_id=price_list_id
        )
        return self.repo.create(cp)

    def update(self, cp_id: int, data: Dict[str, Any]) -> Optional[Counterparty]:
        """Обновляет данные контрагента."""
        if "inn" in data and data["inn"]:
            existing = self._get_by_inn(data["inn"])
            if existing and existing.id != cp_id:
                raise ValueError(f"ИНН {data['inn']} уже занят")
        return self.repo.update(cp_id, data)

    def delete(self, cp_id: int) -> Dict[str, Any]:
        """
        Безопасное удаление контрагента.

        :return: Dict с ключами: success, error, offers_count
        """
        from models.commercial_offer import CommercialOffer
        cp = self.repo.get_by_id(cp_id)
        if not cp:
            return {"success": False, "error": "Контрагент не найден"}

        stmt = select(CommercialOffer).where(CommercialOffer.counterparty_id == cp_id)
        offers_count = len(self.session.execute(stmt).scalars().all())

        if offers_count > 0:
            return {
                "success": False,
                "error": f"Нельзя удалить: используется в {offers_count} коммерческих предложениях",
                "offers_count": offers_count
            }

        self.repo.delete(cp_id)
        return {"success": True, "offers_count": 0}

    def get_all(self) -> List[Counterparty]:
        """Возвращает всех контрагентов с подгруженным прайс-листом."""
        return self.session.query(Counterparty).all()

    def get_by_id(self, cp_id: int) -> Optional[Counterparty]:
        """Получает контрагента по ID."""
        return self.repo.get_by_id(cp_id)

    def search(self, query: str) -> List[Counterparty]:
        """Поиск контрагентов по имени, ИНН, телефону."""
        stmt = select(Counterparty).where(
            (Counterparty.name.ilike(f"%{query}%")) |
            (Counterparty.inn.ilike(f"%{query}%")) |
            (Counterparty.phone.ilike(f"%{query}%"))
        )
        return list(self.session.execute(stmt).scalars().all())

    def _inn_exists(self, inn: str) -> bool:
        """Проверяет существование контрагента с данным ИНН."""
        stmt = select(Counterparty.id).where(Counterparty.inn == inn)
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def _get_by_inn(self, inn: str) -> Optional[Counterparty]:
        """Получает контрагента по ИНН."""
        stmt = select(Counterparty).where(Counterparty.inn == inn)
        return self.session.execute(stmt).scalar_one_or_none()


def __enter__(self):
    return self


def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type:
        self.session.rollback()
    self.session.close()