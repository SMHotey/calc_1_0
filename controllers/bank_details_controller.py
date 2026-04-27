"""Контроллер банковских реквизитов: CRUD.

Содержит:
- BankDetailsController: контроллер для работы с банковскими реквизитами контрагентов
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from db.repositories import BaseRepository
from models.bank_details import BankDetails
from db.database import SessionLocal
from .base_controller import BaseController


class BankDetailsController(BaseController):
    """Контроллер для работы с банковскими реквизитами.

    Отвечает за CRUD операции с банковскими реквизитами контрагентов.

    Attributes:
        session: SQLAlchemy сессия для работы с БД
        repo: репозиторий для операций с BankDetails
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """Инициализация контроллера.

        Args:
            session: опциональная сессия БД. Если не передана - создаётся новая.
        """
        super().__init__(BankDetails, session)

    def create(
            self,
            counterparty_id: int,
            bank_name: str,
            bik: str,
            correspondent_account: str,
            settlement_account: str,
            is_default: bool = False,
            notes: Optional[str] = None
    ) -> BankDetails:
        """Создаёт новые банковские реквизиты.

        Args:
            counterparty_id: ID контрагента
            bank_name: название банка
            bik: БИК банка
            correspondent_account: корреспондентский счёт
            settlement_account: расчётный счёт
            is_default: является ли основным
            notes: примечание

        Returns:
            Созданный объект BankDetails
        """
        # Если выбран как default - сбрасываем у других
        if is_default:
            self._reset_defaults(counterparty_id)

        bank_details = BankDetails(
            counterparty_id=counterparty_id,
            bank_name=bank_name,
            bik=bik,
            correspondent_account=correspondent_account,
            settlement_account=settlement_account,
            is_default=is_default,
            notes=notes
        )
        return self.repo.create(bank_details)

    def get_by_counterparty(self, counterparty_id: int) -> List[BankDetails]:
        """Возвращает все банковские реквизиты контрагента.

        Args:
            counterparty_id: ID контрагента

        Returns:
            Список BankDetails
        """
        from sqlalchemy import select
        stmt = select(BankDetails).where(
            BankDetails.counterparty_id == counterparty_id
        ).order_by(BankDetails.is_default.desc())
        return list(self.session.execute(stmt).scalars().all())

    def get_by_id(self, bank_details_id: int) -> Optional[BankDetails]:
        """Возвращает банковские реквизиты по ID.

        Args:
            bank_details_id: ID реквизитов

        Returns:
            BankDetails или None
        """
        return self.repo.get_by_id(bank_details_id)

    def update(self, bank_details_id: int, data: Dict[str, Any]) -> Optional[BankDetails]:
        """Обновляет банковские реквизиты.

        Args:
            bank_details_id: ID реквизитов
            data: словарь с полями для обновления

        Returns:
            Обновлённый объект BankDetails или None
        """
        # Если устанавливаем как default - сбрасываем у других
        if data.get("is_default"):
            bank_details = self.repo.get_by_id(bank_details_id)
            if bank_details:
                self._reset_defaults(bank_details.counterparty_id)

        return self.repo.update(bank_details_id, data)

    def delete(self, bank_details_id: int) -> bool:
        """Удаляет банковские реквизиты.

        Args:
            bank_details_id: ID реквизитов

        Returns:
            True если удаление успешно
        """
        return self.repo.delete(bank_details_id)

    def _reset_defaults(self, counterparty_id: int) -> None:
        """Сбрасывает флаг is_default для всех реквизитов контрагента.

        Args:
            counterparty_id: ID контрагента
        """
        from sqlalchemy import update
        self.session.execute(
            update(BankDetails)
            .where(BankDetails.counterparty_id == counterparty_id)
            .values(is_default=False)
        )
        self.session.flush()

    def __enter__(self):
        """Контекстный менеджер - вход."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход (закрытие сессии)."""
        if exc_type:
            self.session.rollback()
        self.session.close()