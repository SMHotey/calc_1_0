"""Контроллер управления сделками: CRUD, workflow, связь с КП.

Содержит:
- DealController: контроллер для работы со сделками
- Валидация статусов и workflow
- Создание сделки на основании КП
- Фильтрация по контрагенту, статусу, датам
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from db.repositories import BaseRepository
from models.deal import Deal
from models.commercial_offer import CommercialOffer
from models.counterparty import Counterparty
from db.database import SessionLocal
from constants import DealStatus
from datetime import datetime


class DealController:
    """Контроллер для рабо��ы со сделками.

    Отвечает за:
    - CRUD сделок
    - Создание сделки на основании КП
    - Workflow сделки (счёт, предоплата, оплата, завершение/отмена)
    - Фильтрацию по контрагенту, статусу, датам

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
        self.repo = BaseRepository(self.session, Deal)

    def create_from_offer(self, offer_id: int, counterparty_id: Optional[int] = None) -> Deal:
        """Создаёт новую сделку на основании коммерческого предложения.

        Args:
            offer_id: ID коммерческого предложения
            counterparty_id: ID контрагента (если None - возьмётся из КП)

        Returns:
            Созданный объект Deal

        Raises:
            ValueError: если КП не найдено или сделка на его основе уже существует
        """
        offer = self.session.get(CommercialOffer, offer_id)
        if not offer:
            raise ValueError("Коммерческое предложение не найдено")

        # Проверяем, что сделка на основе этого КП ещё не создана
        existing = self.session.execute(
            select(Deal).where(Deal.commercial_offer_id == offer_id)
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Сделка на основе этого КП уже существует")

        # Генерируем номер сделки
        deal_number = self._generate_deal_number()

        deal = Deal(
            number=deal_number,
            commercial_offer_id=offer_id,
            counterparty_id=counterparty_id or offer.counterparty_id,
            status=DealStatus.DRAFT
        )
        return self.repo.create(deal)

    def create(
            self,
            number: str,
            counterparty_id: int,
            commercial_offer_id: Optional[int] = None,
            comment: Optional[str] = None
    ) -> Deal:
        """Создаёт новую сделку.

        Args:
            number: номер сделки (должен быть уникальным)
            counterparty_id: ID контрагента
            commercial_offer_id: ID КП (опционально)
            comment: комментарий (опционально)

        Returns:
            Созданный объект Deal

        Raises:
            ValueError: при нарушении бизнес-правил
        """
        # Проверка уникальности номера
        if self._number_exists(number):
            raise ValueError(f"Сделка с номером {number} уже существует")

        deal = Deal(
            number=number,
            counterparty_id=counterparty_id,
            commercial_offer_id=commercial_offer_id,
            comment=comment,
            status=DealStatus.DRAFT
        )
        return self.repo.create(deal)

    def update(self, deal_id: int, data: Dict[str, Any]) -> Optional[Deal]:
        """Обновляет данные сделки.

        Args:
            deal_id: ID сделки
            data: словарь с полями для обновления

        Returns:
            Обновлённый объект Deal или None, если не найден
        """
        if "number" in data and data["number"]:
            existing = self._get_by_number(data["number"])
            if existing and existing.id != deal_id:
                raise ValueError(f"Номер сделки {data['number']} уже занят")

        # Обработка дат
        for date_field in ["invoice_date", "prepayment_date", "full_payment_date",
                           "completion_date", "cancellation_date"]:
            if date_field in data and isinstance(data[date_field], str):
                try:
                    data[date_field] = datetime.strptime(data[date_field], "%d.%m.%Y")
                except ValueError:
                    data[date_field] = None

        return self.repo.update(deal_id, data)

    def update_status(self, deal_id: int, status: DealStatus) -> Optional[Deal]:
        """Обновляет статус сделки.

        Args:
            deal_id: ID сделки
            status: новый статус

        Returns:
            Обновлённый объект Deal или None
        """
        return self.repo.update(deal_id, {"status": status})

    def set_invoice(self, deal_id: int, invoice_number: str, invoice_date: datetime,
                    invoice_amount: float) -> Optional[Deal]:
        """Выставляет счёт по сделке.

        Args:
            deal_id: ID сделки
            invoice_number: номер счёта
            invoice_date: дата счёта
            invoice_amount: сумма счёта

        Returns:
            Обновлённый объект Deal
        """
        data = {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "invoice_amount": invoice_amount,
            "status": DealStatus.INVOICE_ISSUED
        }
        return self.repo.update(deal_id, data)

    def set_prepayment(self, deal_id: int, prepayment_date: datetime,
                       prepayment_amount: float) -> Optional[Deal]:
        """Регистрирует предоплату по сделке.

        Args:
            deal_id: ID сделки
            prepayment_date: дата предоплаты
            prepayment_amount: сумма предоплаты

        Returns:
            Обновлённый объект Deal
        """
        data = {
            "prepayment_date": prepayment_date,
            "prepayment_amount": prepayment_amount,
            "status": DealStatus.PREPAYMENT
        }
        return self.repo.update(deal_id, data)

    def set_full_payment(self, deal_id: int, full_payment_date: datetime) -> Optional[Deal]:
        """Регистрирует полную оплату по сделке.

        Args:
            deal_id: ID сделки
            full_payment_date: дата полной оплаты

        Returns:
            Обновлённый объект Deal
        """
        data = {
            "full_payment_date": full_payment_date,
            "status": DealStatus.FULL_PAYMENT
        }
        return self.repo.update(deal_id, data)

    def complete(self, deal_id: int) -> Optional[Deal]:
        """Завершает сделку.

        Args:
            deal_id: ID сделки

        Returns:
            Обновлённый объект Deal
        """
        from datetime import datetime
        data = {
            "status": DealStatus.COMPLETED,
            "completion_date": datetime.now(),
            "completed_at": datetime.now()
        }
        return self.repo.update(deal_id, data)

    def cancel(self, deal_id: int, reason: str) -> Optional[Deal]:
        """Отменяет сделку.

        Args:
            deal_id: ID сделки
            reason: причина отмены

        Returns:
            Обновлённый объект Deal
        """
        from datetime import datetime
        data = {
            "status": DealStatus.CANCELLED,
            "cancellation_date": datetime.now(),
            "cancellation_reason": reason,
            "completed_at": datetime.now()
        }
        return self.repo.update(deal_id, data)

    def delete(self, deal_id: int) -> bool:
        """Удаляет сделку.

        Args:
            deal_id: ID сделки

        Returns:
            True если удалено, False если не найден
        """
        return self.repo.delete(deal_id)

    def get_by_id(self, deal_id: int) -> Optional[Deal]:
        """Получает сделку по ID.

        Args:
            deal_id: ID сделки

        Returns:
            Объект Deal или None
        """
        return self.repo.get_by_id(deal_id)

    def get_all(self) -> List[Deal]:
        """Возвращает все сделки.

        Returns:
            Список всех сделок из БД
        """
        return self.session.query(Deal).all()

    def get_by_counterparty(self, counterparty_id: int) -> List[Deal]:
        """Получает все сделки контрагента.

        Args:
            counterparty_id: ID контрагента

        Returns:
            Список сделок контрагента
        """
        return list(self.session.execute(
            select(Deal).where(Deal.counterparty_id == counterparty_id)
        ).scalars().all())

    def search(
            self,
            query: Optional[str] = None,
            counterparty_id: Optional[int] = None,
            status: Optional[DealStatus] = None,
            date_from: Optional[datetime] = None,
            date_to: Optional[datetime] = None
    ) -> List[Deal]:
        """Поиск и фильтрация сделок.

        Args:
            query: поисковая строка (по номеру сделки)
            counterparty_id: фильтр по контрагенту
            status: фильтр по статусу
            date_from: фильтр по дате создания (от)
            date_to: фильтр по дате создания (до)

        Returns:
            Список найденных сделок
        """
        conditions = []

        if query:
            conditions.append(Deal.number.ilike(f"%{query}%"))

        if counterparty_id:
            conditions.append(Deal.counterparty_id == counterparty_id)

        if status:
            conditions.append(Deal.status == status)

        if date_from:
            conditions.append(Deal.created_at >= date_from)

        if date_to:
            conditions.append(Deal.created_at <= date_to)

        if conditions:
            stmt = select(Deal).where(and_(*conditions))
        else:
            stmt = select(Deal)

        return list(self.session.execute(stmt).scalars().all())

    def _generate_deal_number(self) -> str:
        """Генерирует уникальный номер сделки.

        Returns:
            Уникальный номер в формате "С-ГГГГ-ММММ-NNNN"
        """
        from datetime import datetime
        year = datetime.now().year
        prefix = f"С-{year}-"

        # Находим максимальный номер с таким префиксом
        stmt = select(Deal).where(Deal.number.like(f"{prefix}%"))
        existing = self.session.execute(stmt).scalars().all()

        if not existing:
            return f"{prefix}0001"

        max_num = 0
        for deal in existing:
            try:
                num = int(deal.number.split("-")[-1])
                if num > max_num:
                    max_num = num
            except (ValueError, IndexError):
                continue

        return f"{prefix}{max_num + 1:04d}"

    def _number_exists(self, number: str) -> bool:
        """Проверяет существование сделки с данным номером.

        Args:
            number: номер для проверки

        Returns:
            True если сделка с таким номером уже существует
        """
        stmt = select(Deal.id).where(Deal.number == number)
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def _get_by_number(self, number: str) -> Optional[Deal]:
        """Получает сделку по номеру.

        Args:
            number: номер сделки

        Returns:
            Объект Deal или None
        """
        stmt = select(Deal).where(Deal.number == number)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_deal_with_details(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """Получает сделку с детальной информацией.

        Args:
            deal_id: ID сделки

        Returns:
            Словарь с данными сделки или None
        """
        deal = self.repo.get_by_id(deal_id)
        if not deal:
            return None

        counterparty = self.session.get(Counterparty, deal.counterparty_id)

        result = {
            "id": deal.id,
            "number": deal.number,
            "status": deal.status.value if deal.status else None,
            "created_at": deal.created_at.strftime("%d.%m.%Y") if deal.created_at else None,
            "completed_at": deal.completed_at.strftime("%d.%m.%Y") if deal.completed_at else None,
            "comment": deal.comment,
            "counterparty_id": deal.counterparty_id,
            "counterparty_name": counterparty.name if counterparty else None,
            "commercial_offer_id": deal.commercial_offer_id,
            "invoice_number": deal.invoice_number,
            "invoice_date": deal.invoice_date.strftime("%d.%m.%Y") if deal.invoice_date else None,
            "invoice_amount": float(deal.invoice_amount) if deal.invoice_amount else None,
            "prepayment_date": deal.prepayment_date.strftime("%d.%m.%Y") if deal.prepayment_date else None,
            "prepayment_amount": float(deal.prepayment_amount) if deal.prepayment_amount else None,
            "full_payment_date": deal.full_payment_date.strftime("%d.%m.%Y") if deal.full_payment_date else None,
            "completion_date": deal.completion_date.strftime("%d.%m.%Y") if deal.completion_date else None,
            "cancellation_date": deal.cancellation_date.strftime("%d.%m.%Y") if deal.cancellation_date else None,
            "cancellation_reason": deal.cancellation_reason,
        }
        return result