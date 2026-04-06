"""Контроллер коммерческих предложений: CRUD, экспорт, drag&drop логика."""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from db.repositories import BaseRepository
from models.commercial_offer import CommercialOffer, OfferItem
from db.database import SessionLocal
from utils.report_generator import ReportGenerator
from utils.drag_drop import reorder_list
from datetime import datetime


class OfferController:
    """
    Контроллер для работы с коммерческими предложениями.

    Отвечает за:
    - CRUD предложений и их позиций
    - Генерацию PDF/HTML отчётов
    - Пересчёт итогов при изменении позиций
    - Сериализацию для Drag & Drop
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session or SessionLocal()
        self.offer_repo = BaseRepository(self.session, CommercialOffer)
        self.item_repo = BaseRepository(self.session, OfferItem)
        self.report_gen = ReportGenerator()

    def create_offer(
            self,
            counterparty_id: int,
            number: Optional[str] = None,
            notes: Optional[str] = None
    ) -> CommercialOffer:
        """Создаёт новое коммерческое предложение с авто-номером."""
        if not number:
            year_month = datetime.now().strftime("%y%m")
            stmt = select(func.max(CommercialOffer.number)).where(
                CommercialOffer.number.like(f"КО-{year_month}-%")
            )
            last = self.session.execute(stmt).scalar_one_or_none()
            next_num = 1 if not last else int(last.split("-")[-1]) + 1
            number = f"КО-{year_month}-{next_num:04d}"

        offer = CommercialOffer(
            number=number,
            counterparty_id=counterparty_id,
            total_amount=0.0,
            notes=notes
        )
        return self.offer_repo.create(offer)

    def add_item_to_offer(
            self,
            offer_id: int,
            item_data: Dict[str, Any]
    ) -> OfferItem:
        """Добавляет позицию в коммерческое предложение."""
        stmt = select(func.max(OfferItem.position)).where(OfferItem.offer_id == offer_id)
        next_pos = self.session.execute(stmt).scalar_one_or_none() or 0

        offer_item = OfferItem(
            offer_id=offer_id,
            position=next_pos + 1,
            product_type=item_data["product_type"],
            subtype=item_data["subtype"],
            width=item_data["width"],
            height=item_data["height"],
            quantity=item_data.get("quantity", 1),
            options_=item_data.get("options", {}),
            base_price=item_data["base_price"],
            markup_percent=item_data.get("markup_percent", 0),
            markup_abs=item_data.get("markup_abs", 0),
            final_price=item_data["final_price"]
        )
        created = self.item_repo.create(offer_item)
        self._recalculate_offer_total(offer_id)
        return created

    def update_item(self, item_id: int, data: Dict[str, Any]) -> Optional[OfferItem]:
        """Обновляет позицию и пересчитывает итог КП."""
        updated = self.item_repo.update(item_id, data)
        if updated:
            self._recalculate_offer_total(updated.offer_id)
        return updated

    def delete_item(self, item_id: int) -> bool:
        """Удаляет позицию и пересчитывает итог КП."""
        item = self.item_repo.get_by_id(item_id)
        if not item:
            return False
        offer_id = item.offer_id
        result = self.item_repo.delete(item_id)
        if result:
            self._recalculate_offer_total(offer_id)
        return result

    def reorder_items(self, offer_id: int, from_index: int, to_index: int) -> bool:
        """
        Меняет порядок позиций в предложении (для Drag & Drop).
        """
        stmt = select(OfferItem).where(OfferItem.offer_id == offer_id).order_by(OfferItem.position)
        items = self.session.execute(stmt).scalars().all()

        if not items or from_index >= len(items) or to_index >= len(items):
            return False

        reordered = reorder_list(
            [{"id": i.id, "position": i.position} for i in items],
            from_index, to_index
        )

        for item_data in reordered:
            self.session.execute(
                update(OfferItem)
                .where(OfferItem.id == item_data["id"])
                .values(position=item_data["position"])
            )
        self.session.flush()
        return True

    def get_offer_with_items(self, offer_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает предложение с детализацией позиций для UI."""
        offer = self.offer_repo.get_by_id(offer_id)
        if not offer:
            return None

        stmt = select(OfferItem).where(OfferItem.offer_id == offer_id).order_by(OfferItem.position)
        items = self.session.execute(stmt).scalars().all()

        return {
            "id": offer.id,
            "number": offer.number,
            "date": offer.date.strftime("%d.%m.%Y"),
            "cp_name": offer.counterparty.name,
            "cp_inn": offer.counterparty.inn,
            "notes": offer.notes,
            "total_amount": offer.total_amount,
            "items": [
                {
                    "id": it.id,
                    "position": it.position,
                    "product_type": it.product_type,
                    "subtype": it.subtype,
                    "width": it.width,
                    "height": it.height,
                    "quantity": it.quantity,
                    "options": it.options_,
                    "base_price": it.base_price,
                    "markup": f"{it.markup_percent}% + {it.markup_abs}₽",
                    "final_price": it.final_price
                }
                for it in items
            ]
        }

    def export_to_pdf(self, offer_id: int, output_path: str) -> str:
        """Генерирует PDF-файл коммерческого предложения."""
        offer_data = self.get_offer_with_items(offer_id)
        if not offer_data:
            raise ValueError(f"Предложение #{offer_id} не найдено")
        return self.report_gen.generate_pdf(offer_data, output_path)

    def export_to_html(self, offer_id: int) -> str:
        """Возвращает HTML-строку коммерческого предложения."""
        offer_data = self.get_offer_with_items(offer_id)
        if not offer_data:
            raise ValueError(f"Предложение #{offer_id} не найдено")
        return self.report_gen.generate_html(offer_data)

    def _recalculate_offer_total(self, offer_id: int) -> None:
        """Пересчитывает общую сумму предложения на основе позиций."""
        stmt = select(func.sum(OfferItem.final_price * OfferItem.quantity)).where(
            OfferItem.offer_id == offer_id
        )
        total = self.session.execute(stmt).scalar_one_or_none() or 0.0
        self.session.execute(
            update(CommercialOffer)
            .where(CommercialOffer.id == offer_id)
            .values(total_amount=total)
        )
        self.session.flush()

    def get_all_offers(self) -> List[Dict[str, Any]]:
        """Возвращает список всех предложений для отображения."""
        stmt = select(CommercialOffer).order_by(CommercialOffer.date.desc())
        offers = self.session.execute(stmt).scalars().all()
        return [
            {
                "id": o.id,
                "number": o.number,
                "date": o.date.strftime("%d.%m.%Y"),
                "counterparty": o.counterparty.name,
                "total": o.total_amount
            }
            for o in offers
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()
