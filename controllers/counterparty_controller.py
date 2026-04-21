"""Контроллер управления контрагентами: CRUD, привязка прайс-листов.

Содержит:
- CounterpartyController: контроллер для работы с контрагентами
- Валидация ИНН/КПП/ОГРН в зависимости от типа
- Проверка использования в КП перед удалением
- Поиск контрагентов по различным полям
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.repositories import BaseRepository
from models.counterparty import Counterparty, CounterpartyType
from db.database import SessionLocal


class CounterpartyController:
    """Контроллер для работы с контрагентами.

    Отвечает за:
    - CRUD всех типов контрагентов (ЮЛ, ИП, ФЛ)
    - Валидацию уникальности ИНН/ОГРН
    - Привязку/отвязку прайс-листов
    - Проверку использования в КП перед удалением
    - Поиск по имени, ИНН, телефону

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
        """Создаёт нового контрагента с валидацией обязательных полей.

        Args:
            cp_type: тип контрагента (юридическое лицо, ИП, физическое лицо)
            name: наименование контрагента
            inn: ИНН (обязателен для ЮЛ и ИП)
            phone: контактный телефон
            address: адрес
            email: email (опционально)
            kpp: КПП (обязателен для ЮЛ)
            ogrn: ОГРН/ОГРНИП (обязателен для ЮЛ и ИП)
            price_list_id: ID прайс-листа для привязки

        Returns:
            Созданный объект Counterparty

        Raises:
            ValueError: при нарушении бизнес-правил (недостающие данные, дубликат ИНН)
        """
        # Валидация обязательных полей по типу контрагента
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
        """Обновляет данные контрагента.

        Args:
            cp_id: ID контрагента
            data: словарь с полями для обновления

        Returns:
            Обновлённый объект Counterparty или None, если не найден
        """
        if "inn" in data and data["inn"]:
            existing = self._get_by_inn(data["inn"])
            if existing and existing.id != cp_id:
                raise ValueError(f"ИНН {data['inn']} уже занят")
        return self.repo.update(cp_id, data)

    def delete(self, cp_id: int) -> Dict[str, Any]:
        """Безопасное удаление контрагента.

        Проверяет, что контрагент не используется в коммерческих предложениях.
        Если используется - удаление блокируется.

        Args:
            cp_id: ID контрагента

        Returns:
            Dict с ключами:
            - success: True/False
            - error: сообщение об ошибке (если success=False)
            - offers_count: количество связанных КП (если нельзя удалить)
        """
        from models.commercial_offer import CommercialOffer
        cp = self.repo.get_by_id(cp_id)
        if not cp:
            return {"success": False, "error": "Контрагент не найден"}

        # Проверка использования в КП
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
        """Возвращает всех контрагентов.

        Returns:
            Список всех контрагентов из БД
        """
        return self.session.query(Counterparty).all()

    def get_by_id(self, cp_id: int) -> Optional[Counterparty]:
        """Получает контрагента по ID.

        Args:
            cp_id: ID контрагента

        Returns:
            Объект Counterparty или None
        """
        return self.repo.get_by_id(cp_id)

    def search(self, query: str) -> List[Counterparty]:
        """Поиск контрагентов по имени, ИНН, телефону.

        Args:
            query: поисковая строка (частичное совпадение)

        Returns:
            Список найденных контрагентов
        """
        stmt = select(Counterparty).where(
            (Counterparty.name.ilike(f"%{query}%")) |
            (Counterparty.inn.ilike(f"%{query}%")) |
            (Counterparty.phone.ilike(f"%{query}%"))
        )
        return list(self.session.execute(stmt).scalars().all())

    def _inn_exists(self, inn: str) -> bool:
        """Проверяет существование контрагента с данным ИНН.

        Args:
            inn: ИНН для проверки

        Returns:
            True если контрагент с таким ИНН уже существует
        """
        stmt = select(Counterparty.id).where(Counterparty.inn == inn)
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def _get_by_inn(self, inn: str) -> Optional[Counterparty]:
        """Получает контрагента по ИНН.

        Args:
            inn: ИНН для поиска

        Returns:
            Объект Counterparty или None
        """
        stmt = select(Counterparty).where(Counterparty.inn == inn)
        return self.session.execute(stmt).scalar_one_or_none()
