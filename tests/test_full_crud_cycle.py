"""Full CRUD cycle test: counterparty → contacts → price list → offer (10 items) → deal → documents."""

import pytest
from datetime import datetime
import os

# Import project modules
from db.database import SessionLocal, init_db, Base, engine
from constants import CounterpartyType, PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM, DealStatus

# Models
from models.counterparty import Counterparty
from models.contact_person import ContactPerson
from models.price_list import BasePriceList
from models.commercial_offer import CommercialOffer, OfferItem
from models.deal import Deal
from models.document import Document

# Controllers
from controllers.counterparty_controller import CounterpartyController
from controllers.offer_controller import OfferController
from controllers.deal_controller import DealController
from controllers.document_controller import DocumentController


# ---------- Fixtures ----------
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database schema once per test session."""
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a fresh database session for each test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def controllers(db_session):
    """Provide all controllers initialized with the same session."""
    return {
        "counterparty": CounterpartyController(db_session),
        "offer": OfferController(db_session),
        "deal": DealController(db_session),
        "document": DocumentController(db_session, storage_path="test_docs"),
    }


# ---------- Test Class ----------
class TestFullCRUDCycle:
    """Full cycle: counterparty → contacts → price list → offer → deal → documents."""

    def test_1_create_counterparty(self, db_session, controllers):
        """Create a legal entity counterparty."""
        cp_ctrl = controllers["counterparty"]

        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="Test Corp LLC",
            inn="7701234567",
            kpp="770101001",
            ogrn="1157701234567",
            address="Moscow, Test Street 1",
            phone="+7 (495) 111-22-33",
            email="test@testcorp.com"
        )

        assert cp.id is not None
        assert cp.name == "Test Corp LLC"
        assert cp.type == CounterpartyType.LEGAL
        assert cp.inn == "7701234567"

        # Verify in DB
        db_cp = db_session.get(Counterparty, cp.id)
        assert db_cp is not None
        assert len(db_cp.contact_persons) == 0

    def test_2_create_and_edit_contacts(self, db_session, controllers):
        """Create counterparty and manage its contact persons."""
        cp_ctrl = controllers["counterparty"]

        # Create counterparty
        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="Contact Test Corp",
            inn="7702345678",
            kpp="770201001",
            ogrn="1157702345678",
            address="Moscow, Contact Street 2",
            phone="+7 (495) 222-33-44"
        )

        # Add contact persons
        contact1 = ContactPerson(
            counterparty_id=cp.id,
            name="Ivan Petrov",
            position="Sales Manager",
            phone="+7 (916) 111-22-33",
            email="i.petrov@testcorp.com"
        )
        contact2 = ContactPerson(
            counterparty_id=cp.id,
            name="Maria Ivanova",
            position="Accountant",
            phone="+7 (916) 444-55-66",
            email="m.ivanova@testcorp.com"
        )
        db_session.add_all([contact1, contact2])
        db_session.commit()

        # Verify contacts created
        db_session.refresh(cp)
        assert len(cp.contact_persons) == 2

        # Edit first contact
        contact1.position = "Senior Sales Manager"
        contact1.phone = "+7 (916) 999-88-77"
        db_session.commit()

        updated = db_session.get(ContactPerson, contact1.id)
        assert updated.position == "Senior Sales Manager"
        assert updated.phone == "+7 (916) 999-88-77"

        # Delete second contact
        db_session.delete(contact2)
        db_session.commit()

        db_session.refresh(cp)
        assert len(cp.contact_persons) == 1

    def test_3_create_custom_price_list(self, db_session, controllers):
        """Create a custom price list for counterparty."""
        cp_ctrl = controllers["counterparty"]

        # Create counterparty
        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="PriceList Test Corp",
            inn="7703456789",
            kpp="770301001",
            ogrn="1157703456789",
            address="Moscow, Price Street 3",
            phone="+7 (495) 333-44-55"
        )

        # Get base price list (first one, created by init_db)
        base_pl = db_session.query(BasePriceList).first()
        assert base_pl is not None

        # Create custom price list
        custom_pl = BasePriceList(
            name="Custom Price List for PriceList Test Corp"
        )
        # Copy prices from base
        custom_pl.doors_price_std_single = base_pl.doors_price_std_single + 1000
        custom_pl.doors_price_per_m2_nonstd = base_pl.doors_price_per_m2_nonstd + 500
        custom_pl.doors_wide_markup = base_pl.doors_wide_markup
        custom_pl.doors_double_std = base_pl.doors_double_std
        custom_pl.hatch_std = base_pl.hatch_std
        custom_pl.hatch_wide_markup = base_pl.hatch_wide_markup
        custom_pl.hatch_per_m2_nonstd = base_pl.hatch_per_m2_nonstd
        custom_pl.gate_per_m2 = base_pl.gate_per_m2
        custom_pl.gate_large_per_m2 = base_pl.gate_large_per_m2
        custom_pl.transom_per_m2 = base_pl.transom_per_m2
        custom_pl.transom_min = base_pl.transom_min

        db_session.add(custom_pl)
        db_session.flush()

        # Link to counterparty
        cp.price_list_id = custom_pl.id
        db_session.commit()

        assert cp.price_list_id == custom_pl.id

    def test_4_create_offer_with_10_items(self, db_session, controllers):
        """Create commercial offer with 10 items of various configurations."""
        cp_ctrl = controllers["counterparty"]
        offer_ctrl = controllers["offer"]

        # Create counterparty
        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="Offer Test Corp",
            inn="7704567890",
            kpp="770401001",
            ogrn="1157704567890",
            address="Moscow, Offer Street 4",
            phone="+7 (495) 444-55-66"
        )

        # Create offer using controller
        offer = offer_ctrl.create_offer(
            counterparty_id=cp.id,
            number="OFFER-2024-001",
            notes="Test offer with 10 items"
        )

        assert offer.id is not None

        # Add 10 items with various configurations
        items_data = [
            # (product_type, subtype, height, width, quantity, base_price)
            (PRODUCT_DOOR, "Техническая", 2000, 900, 1, 15000.0),
            (PRODUCT_DOOR, "EI 60", 2100, 1000, 2, 22000.0),
            (PRODUCT_DOOR, "Квартирная", 2000, 900, 1, 18000.0),
            (PRODUCT_HATCH, "Технический", 800, 800, 1, 4500.0),
            (PRODUCT_HATCH, "Ревизионный", 600, 600, 1, 3500.0),
            (PRODUCT_HATCH, "EI 60", 1000, 1000, 1, 6500.0),
            (PRODUCT_GATE, "Технические", 2500, 3000, 1, 9500.0),
            (PRODUCT_GATE, "EI 60", 3000, 2000, 1, 12500.0),
            (PRODUCT_TRANSOM, "Техническая", 300, 500, 2, 4500.0),
            (PRODUCT_TRANSOM, "EI 60", 400, 800, 1, 11500.0),
        ]

        for idx, (ptype, subtype, h, w, qty, base_price) in enumerate(items_data, start=1):
            final_price = round((base_price + base_price * 0.10) * qty, 2)

            item_data = {
                "product_type": ptype,
                "subtype": subtype,
                "width": w,
                "height": h,
                "quantity": qty,
                "options": {},
                "base_price": base_price,
                "markup_percent": 10.0,
                "markup_abs": 0.0,
                "final_price": final_price
            }

            offer_ctrl.add_item_to_offer(offer.id, item_data)

        # Verify
        db_session.refresh(offer)
        assert len(offer.items) == 10
        assert offer.total_amount > 0

    def test_5_edit_offer(self, db_session, controllers):
        """Edit offer: change quantity, add new item, remove item."""
        cp_ctrl = controllers["counterparty"]
        offer_ctrl = controllers["offer"]

        # Create counterparty and offer
        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="Edit Offer Corp",
            inn="7705678901",
            kpp="770501001",
            ogrn="1157705678901",
            address="Moscow, Edit Street 5",
            phone="+7 (495) 555-66-77"
        )

        offer = offer_ctrl.create_offer(
            counterparty_id=cp.id,
            number="OFFER-2024-002"
        )

        # Add initial items
        item1_data = {
            "product_type": PRODUCT_DOOR,
            "subtype": "Техническая",
            "width": 900,
            "height": 2000,
            "quantity": 1,
            "options": {},
            "base_price": 15000.0,
            "markup_percent": 10.0,
            "markup_abs": 0.0,
            "final_price": 16500.0
        }
        item2_data = {
            "product_type": PRODUCT_HATCH,
            "subtype": "Технический",
            "width": 800,
            "height": 800,
            "quantity": 1,
            "options": {},
            "base_price": 4500.0,
            "markup_percent": 10.0,
            "markup_abs": 0.0,
            "final_price": 4950.0
        }

        offer_ctrl.add_item_to_offer(offer.id, item1_data)
        offer_ctrl.add_item_to_offer(offer.id, item2_data)

        # Edit: change quantity of item1
        item1 = offer.items[0]
        new_qty = 3
        new_final_price = round((item1.base_price + item1.base_price * 0.10) * new_qty, 2)
        offer_ctrl.update_item(item1.id, {"quantity": new_qty, "final_price": new_final_price})

        # Add new item (position will be assigned by controller)
        item3_data = {
            "product_type": PRODUCT_GATE,
            "subtype": "Технические",
            "width": 3000,
            "height": 2500,
            "quantity": 1,
            "options": {},
            "base_price": 9500.0,
            "markup_percent": 10.0,
            "markup_abs": 0.0,
            "final_price": 10450.0
        }
        offer_ctrl.add_item_to_offer(offer.id, item3_data)

        # Remove item2
        item2 = offer.items[1]  # After refresh, indices may change
        offer_ctrl.delete_item(item2.id)

        # Verify
        db_session.refresh(offer)
        assert len(offer.items) == 2
        assert offer.items[0].quantity == 3
        assert offer.total_amount > 21450.0  # Should be higher now

    def test_6_create_deal_from_offer(self, db_session, controllers):
        """Create deal from offer and update its status."""
        cp_ctrl = controllers["counterparty"]
        offer_ctrl = controllers["offer"]
        deal_ctrl = controllers["deal"]

        # Create counterparty and offer
        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="Deal Test Corp",
            inn="7706789012",
            kpp="770601001",
            ogrn="1157706789012",
            address="Moscow, Deal Street 6",
            phone="+7 (495) 666-77-88"
        )

        offer = offer_ctrl.create_offer(
            counterparty_id=cp.id,
            number="OFFER-2024-003"
        )

        # Add an item to offer
        item_data = {
            "product_type": PRODUCT_DOOR,
            "subtype": "Техническая",
            "width": 900,
            "height": 2000,
            "quantity": 1,
            "options": {},
            "base_price": 15000.0,
            "markup_percent": 10.0,
            "markup_abs": 0.0,
            "final_price": 16500.0
        }
        offer_ctrl.add_item_to_offer(offer.id, item_data)

        # Create deal from offer
        deal = deal_ctrl.create_from_offer(offer.id)

        assert deal.id is not None
        assert deal.commercial_offer_id == offer.id
        assert deal.counterparty_id == cp.id
        assert deal.status == DealStatus.DRAFT

        # Update deal status
        deal_ctrl.update_status(deal.id, DealStatus.OFFER_SENT)
        deal_ctrl.update(deal.id, {"comment": "Commercial offer sent to client"})

        updated_deal = db_session.get(Deal, deal.id)
        assert updated_deal.status == DealStatus.OFFER_SENT
        assert updated_deal.comment == "Commercial offer sent to client"

    def test_7_add_and_remove_documents(self, db_session, controllers):
        """Add and remove documents for deal."""
        cp_ctrl = controllers["counterparty"]
        deal_ctrl = controllers["deal"]
        doc_ctrl = controllers["document"]

        # Create counterparty and deal
        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="Document Test Corp",
            inn="7707890123",
            kpp="770701001",
            ogrn="1157707890123",
            address="Moscow, Document Street 7",
            phone="+7 (495) 777-88-99"
        )

        deal = deal_ctrl.create(
            number="D-001",
            counterparty_id=cp.id
        )

        # Create dummy files for testing
        os.makedirs("test_docs", exist_ok=True)

        # Add documents
        doc1_path = "test_docs/contract_test.pdf"
        with open(doc1_path, "wb") as f:
            f.write(b"Dummy PDF content")

        doc1 = doc_ctrl.create(
            name="Contract.pdf",
            file_path=doc1_path,
            counterparty_id=cp.id,
            deal_id=deal.id
        )

        doc2_path = "test_docs/spec_test.xlsx"
        with open(doc2_path, "wb") as f:
            f.write(b"Dummy XLSX content")

        doc2 = doc_ctrl.create(
            name="Specification.xlsx",
            file_path=doc2_path,
            counterparty_id=cp.id,
            deal_id=deal.id
        )

        doc3_path = "test_docs/invoice_test.pdf"
        with open(doc3_path, "wb") as f:
            f.write(b"Dummy Invoice content")

        doc3 = doc_ctrl.create(
            name="Invoice.pdf",
            file_path=doc3_path,
            counterparty_id=cp.id,
            deal_id=deal.id
        )

        assert len(deal.documents) == 3

        # Delete one document
        doc_ctrl.delete(doc2.id)

        db_session.refresh(deal)
        assert len(deal.documents) == 2

        # Verify remaining documents
        remaining_names = [d.name for d in deal.documents]
        assert "Contract.pdf" in remaining_names
        assert "Invoice.pdf" in remaining_names
        # Note: Specification.xlsx may still exist in DB if delete didn't cascade, but we deleted it via controller

    def test_8_full_cycle_integration(self, db_session, controllers):
        """Test full cycle: counterparty → contacts → price list → offer → deal → documents."""
        cp_ctrl = controllers["counterparty"]
        offer_ctrl = controllers["offer"]
        deal_ctrl = controllers["deal"]
        doc_ctrl = controllers["document"]

        # 1. Create counterparty
        cp = cp_ctrl.create(
            cp_type=CounterpartyType.LEGAL,
            name="Full Cycle Corp",
            inn="7708901234",
            kpp="770801001",
            ogrn="1157708901234",
            address="Moscow, Full Cycle Street 8",
            phone="+7 (495) 888-99-00",
            email="info@fullcycle.com"
        )

        # 2. Add contact persons
        contact1 = ContactPerson(
            counterparty_id=cp.id,
            name="Alexander Smirnov",
            position="Director",
            phone="+7 (916) 123-45-67",
            email="a.smirnov@fullcycle.com"
        )
        db_session.add(contact1)
        db_session.commit()

        # 3. Create custom price list
        base_pl = db_session.query(BasePriceList).first()
        custom_pl = BasePriceList(
            name="Full Cycle Custom Prices"
        )
        custom_pl.doors_price_std_single = base_pl.doors_price_std_single
        custom_pl.doors_price_per_m2_nonstd = base_pl.doors_price_per_m2_nonstd
        db_session.add(custom_pl)
        db_session.flush()

        cp.price_list_id = custom_pl.id
        db_session.flush()

        # 4. Create offer with 10 items
        offer = offer_ctrl.create_offer(
            counterparty_id=cp.id,
            number="OFFER-2024-FULL"
        )

        # Add 10 varied items with different configurations
        items_to_test = [
            # Door configurations
            {"ptype": PRODUCT_DOOR, "subtype": "Техническая", "h": 2000, "w": 900, "qty": 1, "opts": {}, "expected_price_factor": 1.0},
            {"ptype": PRODUCT_DOOR, "subtype": "EI 60", "h": 2100, "w": 1000, "qty": 2, "opts": {"closer_count": 1}, "expected_price_factor": 1.1},
            {"ptype": PRODUCT_DOOR, "subtype": "Квартирная", "h": 2000, "w": 900, "qty": 1, "opts": {"glass_items": []}, "expected_price_factor": 1.0},
            # Hatch configurations
            {"ptype": PRODUCT_HATCH, "subtype": "Технический", "h": 800, "w": 800, "qty": 1, "opts": {}, "expected_price_factor": 1.0},
            {"ptype": PRODUCT_HATCH, "subtype": "Ревизионный", "h": 600, "w": 600, "qty": 1, "opts": {}, "expected_price_factor": 1.0},
            {"ptype": PRODUCT_HATCH, "subtype": "EI 60", "h": 1000, "w": 1000, "qty": 1, "opts": {}, "expected_price_factor": 1.0},
            # Gate configurations
            {"ptype": PRODUCT_GATE, "subtype": "Технические", "h": 2500, "w": 3000, "qty": 1, "opts": {}, "expected_price_factor": 1.0},
            {"ptype": PRODUCT_GATE, "subtype": "EI 60", "h": 3000, "w": 2000, "qty": 1, "opts": {"large": True}, "expected_price_factor": 1.0},
            # Transom configurations
            {"ptype": PRODUCT_TRANSOM, "subtype": "Техническая", "h": 300, "w": 500, "qty": 2, "opts": {}, "expected_price_factor": 1.0},
            {"ptype": PRODUCT_TRANSOM, "subtype": "EI 60", "h": 400, "w": 800, "qty": 1, "opts": {"threshold_enabled": True}, "expected_price_factor": 1.0},
            # Mixed configuration
            {"ptype": PRODUCT_DOOR, "subtype": "Однолистовая", "h": 2200, "w": 1100, "qty": 1, "opts": {}, "expected_price_factor": 1.0},
        ]

        for idx, item_cfg in enumerate(items_to_test, start=1):
            h, w = item_cfg["h"], item_cfg["w"]
            qty = item_cfg["qty"]
            base_price = 10000.0 + idx * 1000  # Simple base price progression
            final_price = round((base_price + base_price * 0.10) * qty, 2)
            
            # Store expected factor for validation later
            item_cfg["expected_final_price"] = final_price

            item_data = {
                "product_type": item_cfg["ptype"],
                "subtype": item_cfg["subtype"],
                "height": h,
                "width": w,
                "quantity": qty,
                "options_": item_cfg["opts"],
                "base_price": base_price,
                "markup_percent": 10.0,
                "markup_abs": 0.0,
                "final_price": final_price
            }
            offer_ctrl.add_item_to_offer(offer.id, item_data)

        # Verify items were added
        db_session.refresh(offer)
        assert len(offer.items) == 10

        # Pre-calculate total expected
        expected_total = sum(item_cfg["expected_final_price"] for item_cfg in items_to_test)
        assert round(offer.total_amount, 2) == round(expected_total, 2)

        # 5. Create deal from offer
        deal = deal_ctrl.create_from_offer(offer.id)

        # Update deal status
        deal_ctrl.update_status(deal.id, DealStatus.OFFER_SENT)

        # 6. Add documents to deal
        os.makedirs("test_docs", exist_ok=True)
        doc_path = "test_docs/full_cycle_contract.pdf"
        with open(doc_path, "wb") as f:
            f.write(b"Full cycle contract content")

        doc = doc_ctrl.create(
            name="Full_Cycle_Contract.pdf",
            file_path=doc_path,
            counterparty_id=cp.id,
            deal_id=deal.id
        )

        # Final assertions
        assert cp.id is not None
        assert len(cp.contact_persons) == 1
        assert cp.price_list_id == custom_pl.id
        assert len(offer.items) == 10
        assert deal.commercial_offer_id == offer.id
        assert len(deal.documents) == 1

        # Verify relationships
        assert deal.counterparty == cp
        assert deal.commercial_offer == offer
        assert doc in deal.documents
