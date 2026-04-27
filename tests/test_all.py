"""Комплексные тесты всего функционала приложения."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, SessionLocal
from models.price_list import BasePriceList
from models.counterparty import Counterparty, CounterpartyType
from models.glass import GlassType, GlassOption
from models.hardware import HardwareItem
from models.commercial_offer import CommercialOffer, OfferItem
from controllers.calculator_controller import CalculatorController
from controllers.price_list_controller import PriceListController
from controllers.counterparty_controller import CounterpartyController
from controllers.offer_controller import OfferController
from controllers.hardware_controller import HardwareController
from controllers.options_controller import OptionsController
from utils.validators import validate_dimensions
from utils.calculators import DoorCalculator, HatchCalculator, GateCalculator, TransomCalculator
from utils.calculators.base_calculator import CalculatorContext, PriceData


@pytest.fixture
def engine():
    """Создаёт тестовую БД в памяти."""
    e = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=e)
    return e


@pytest.fixture
def session(engine):
    """Создаёт сессию для тестов."""
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


@pytest.fixture
def base_price_list(session):
    """Создаёт базовый прайс для тестов."""
    pl = BasePriceList(name="Тестовый прайс")
    pl.doors_price_std_single = 15000.0
    pl.doors_price_per_m2_nonstd = 12000.0
    pl.doors_wide_markup = 2500.0
    pl.doors_double_std = 28000.0
    pl.hatch_std = 4500.0
    pl.hatch_wide_markup = 800.0
    pl.hatch_per_m2_nonstd = 9000.0
    pl.gate_per_m2 = 3800.0
    pl.gate_large_per_m2 = 4500.0
    pl.transom_per_m2 = 8500.0
    pl.transom_min = 4500.0
    pl.cutout_price = 800.0
    pl.deflector_per_m2 = 3200.0
    pl.trim_per_lm = 650.0
    pl.closer_price = 2500.0
    pl.hinge_price = 300.0
    pl.anti_theft_price = 450.0
    pl.gkl_price = 1200.0
    pl.mount_ear_price = 80.0
    session.add(pl)
    session.commit()
    return pl


@pytest.fixture
def prices(base_price_list):
    """Объект PriceData для тестов."""
    return PriceData(
        doors_std_single=15000.0,
        doors_per_m2_nonstd=12000.0,
        doors_wide_markup=2500.0,
        doors_double_std=28000.0,
        hatch_std=4500.0,
        hatch_wide_markup=800.0,
        hatch_per_m2_nonstd=9000.0,
        gate_per_m2=3800.0,
        gate_large_per_m2=4500.0,
        transom_per_m2=8500.0,
        transom_min=4500.0,
        cutout_price=800.0,
        deflector_per_m2=3200.0,
        trim_per_lm=650.0,
        closer_price=2500.0,
        hinge_price=300.0,
        anti_theft_price=450.0,
        gkl_price=1200.0,
        mount_ear_price=80.0
    )


class TestValidators:
    """Тесты валидаторов."""

    def test_door_standard_valid(self):
        """Стандартные размеры двери проходят валидацию."""
        valid, err = validate_dimensions("Дверь", 2100, 900)
        assert valid is True

    def test_door_too_small(self):
        """Дверь слишком маленькая."""
        valid, err = validate_dimensions("Дверь", 100, 500)
        assert valid is False

    def test_door_too_big(self):
        """Дверь слишком большая."""
        valid, err = validate_dimensions("Дверь", 2600, 2500)
        assert valid is False

    def test_hatch_dimensions(self):
        """Люк с валидными размерами."""
        valid, err = validate_dimensions("Люк", 800, 800)
        assert valid is True

    def test_gate_dimensions(self):
        """Ворота с валидными размерами."""
        valid, err = validate_dimensions("Ворота", 2500, 3000)
        assert valid is True
    
    def test_gate_too_big(self):
        """Ворота слишком большие."""
        valid, err = validate_dimensions("Ворота", 3001, 4000)
        assert valid is False


class TestDoorCalculator:
    """Тесты калькулятора дверей."""

    def test_standard_single(self, prices):
        """Стандартная одностворчатая дверь."""
        ctx = CalculatorContext(
            product_type="Дверь", subtype="Квартирная", height=2100, width=900,
            is_double_leaf=False, prices=prices
        )
        calc = DoorCalculator()
        result = calc.calculate(ctx)
        assert result == 15000.0

    def test_wide_single(self, prices):
        """Широкая одностворчатая дверь."""
        ctx = CalculatorContext(
            product_type="Дверь", subtype="Квартирная", height=2100, width=1050,
            is_double_leaf=False, prices=prices
        )
        calc = DoorCalculator()
        result = calc.calculate(ctx)
        assert result == 17500.0  # 15000 + 2500

    def test_standard_double(self, prices):
        """Стандартная двустворчатая дверь."""
        ctx = CalculatorContext(
            product_type="Дверь", subtype="Двустворчатая", height=2100, width=1200,
            is_double_leaf=True, prices=prices
        )
        calc = DoorCalculator()
        result = calc.calculate(ctx)
        assert result == 28000.0

    def test_markup(self, prices):
        """Наценка применяется."""
        ctx = CalculatorContext(
            product_type="Дверь", subtype="Квартирная", height=2100, width=900,
            is_double_leaf=False, prices=prices, markup_percent=10, markup_abs=500
        )
        calc = DoorCalculator()
        result = calc.calculate(ctx)
        expected = 15000 * 1.10 + 500
        assert result == expected


class TestHatchCalculator:
    """Тесты калькулятора люков."""

    def test_standard_hatch(self, prices):
        """Стандартный ревизионный люк."""
        ctx = CalculatorContext(
            product_type="Люк", subtype="Ревизионный", height=600, width=600,
            is_double_leaf=False, prices=prices
        )
        calc = HatchCalculator()
        result = calc.calculate(ctx)
        assert result == 4500.0  # Фикс. цена для <=0.4м²

    def test_large_hatch_per_m2(self, prices):
        """Большой люк считается по м²."""
        ctx = CalculatorContext(
            product_type="Люк", subtype="Ревизионный", height=1000, width=1000,
            is_double_leaf=False, prices=prices
        )
        calc = HatchCalculator()
        result = calc.calculate(ctx)
        area = 1.0  # 1000x1000 = 1м²
        assert result == 9000.0 * area


class TestGateCalculator:
    """Тесты калькулятора ворот."""

    def test_standard_gate(self, prices):
        """Стандартные ворота."""
        ctx = CalculatorContext(
            product_type="Ворота", subtype="Секционные", height=2500, width=2500,
            is_double_leaf=False, prices=prices
        )
        calc = GateCalculator()
        result = calc.calculate(ctx)
        area = 2.5 * 2.5  # 6.25м²
        assert result == 3800.0 * area


class TestPriceListController:
    """Тесты контроллера прайс-листов."""

    def test_create_base_price_list(self, session, base_price_list):
        """Создание базового прайса."""
        ctrl = PriceListController(session)
        base = ctrl.get_base_price_list()
        assert base is not None

    def test_get_personalized_lists(self, session, base_price_list):
        """Получение списка персонализированных прайсов."""
        ctrl = PriceListController(session)
        lists = ctrl.get_personalized_lists()
        assert isinstance(lists, list)

    def test_get_prices_for_calculation(self, session, base_price_list):
        """Получение цен для калькулятора."""
        ctrl = PriceListController(session)
        prices = ctrl.get_price_for_calculation(None)
        assert "cutout_price" in prices


class TestCounterpartyController:
    """Тесты контроллера контрагентов."""

    def test_create_counterparty(self, session, base_price_list):
        """Создание контрагента."""
        ctrl = CounterpartyController(session)
        cp = ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Тест ФЛ",
            inn=None,
            phone="+7 999 123-45-67",
            address="ул. Тестовая, д.1"
        )
        assert cp.name == "Тест ФЛ"
        assert cp.id is not None

    def test_get_all_counterparties(self, session, base_price_list):
        """Получение всех контрагентов."""
        ctrl = CounterpartyController(session)
        ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Контрагент 1",
            inn=None,
            phone="+7 111 111-11-11",
            address="Адрес 1"
        )
        ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Контрагент 2",
            inn=None,
            phone="+7 222 222-22-22",
            address="Адрес 2"
        )
        all_cp = ctrl.get_all()
        assert len(all_cp) >= 2

    def test_delete_used_counterparty(self, session, base_price_list):
        """Нельзя удалить контрагента с КП."""
        ctrl = CounterpartyController(session)
        cp = ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Тест для удаления",
            inn=None,
            phone="+7 999 999-99-99",
            address="Адрес удаления"
        )
        
        offer_ctrl = OfferController(session)
        offer_ctrl.create_offer(cp.id)
        
        result = ctrl.delete(cp.id)
        assert result["success"] is False
        assert "используется" in result["error"]


class TestOfferController:
    """Тесты контроллера КП."""

    def test_create_offer(self, session, base_price_list):
        """Создание коммерческого предложения."""
        cpa_ctrl = CounterpartyController(session)
        cp = cpa_ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Тест КП",
            inn=None,
            phone="+7 555 555-55-55",
            address="Адрес теста"
        )
        
        offer_ctrl = OfferController(session)
        offer = offer_ctrl.create_offer(cp.id)
        
        assert offer.number.startswith("КО-")
        assert offer.counterparty_id == cp.id
        assert offer.total_amount == 0.0

    def test_add_item_to_offer(self, session, base_price_list):
        """Добавление позиции в КП."""
        cpa_ctrl = CounterpartyController(session)
        cp = cpa_ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Тест позиции",
            inn=None,
            phone="+7 666 666-66-66",
            address="Адрес позиции"
        )
        
        offer_ctrl = OfferController(session)
        offer = offer_ctrl.create_offer(cp.id)
        
        item_data = {
            "product_type": "Дверь",
            "subtype": "Квартирная",
            "width": 900,
            "height": 2100,
            "quantity": 1,
            "base_price": 15000.0,
            "final_price": 15000.0,
            "markup_percent": 0,
            "markup_abs": 0,
            "options": {}
        }
        
        item = offer_ctrl.add_item_to_offer(offer.id, item_data)
        assert item.offer_id == offer.id
        assert item.final_price == 15000.0

    def test_recalculate_total(self, session, base_price_list):
        """Автопересчёт итога при добавлении позиции."""
        cpa_ctrl = CounterpartyController(session)
        cp = cpa_ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Тест пересчёта",
            inn=None,
            phone="+7 777 777-77-77",
            address="Адрес пересчёта"
        )
        
        offer_ctrl = OfferController(session)
        offer = offer_ctrl.create_offer(cp.id)
        
        offer_ctrl.add_item_to_offer(offer.id, {
            "product_type": "Дверь", "subtype": "Квартирная",
            "width": 900, "height": 2100, "quantity": 2,
            "base_price": 15000.0, "final_price": 15000.0,
            "markup_percent": 0, "markup_abs": 0, "options": {}
        })
        
        offer_ctrl.session.refresh(offer)
        assert offer.total_amount == 30000.0


class TestHardwareController:
    """Тесты контроллера фурнитуры."""

    def test_create_hardware(self, session, base_price_list):
        """Создание элемента фурнитуры."""
        ctrl = HardwareController(session)
        hw = ctrl.create(
            hw_type="Замок",
            name="Тестовый замок",
            price=5000.0,
            description="Описание",
            has_cylinder=True,
            price_list_id=base_price_list.id
        )
        assert hw.name == "Тестовый замок"
        assert hw.price == 5000.0

    def test_get_by_type(self, session, base_price_list):
        """Получение фурнитуры по типу."""
        ctrl = HardwareController(session)
        ctrl.create(
            hw_type="Замок", name="Замок 1", price=1000.0,
            price_list_id=base_price_list.id
        )
        ctrl.create(
            hw_type="Ручка", name="Ручка 1", price=500.0,
            price_list_id=base_price_list.id
        )
        
        locks = ctrl.get_by_type("Замок", base_price_list.id)
        assert len(locks) >= 1
        assert all(hw.type == "Замок" for hw in locks)


class TestOptionsController:
    """Тесты контроллера опций (стёкла)."""

    def test_create_glass_type(self, session, base_price_list):
        """Создание типа стекла."""
        ctrl = OptionsController(session)
        glass = ctrl.create_glass_type(
            name="Тестовое стекло",
            price_per_m2=2000.0,
            min_price=800.0,
            price_list_id=base_price_list.id
        )
        assert glass.name == "Тестовое стекло"
        assert glass.price_per_m2 == 2000.0

    def test_get_glass_types(self, session, base_price_list):
        """Получение списка типов стёкол."""
        ctrl = OptionsController(session)
        ctrl.create_glass_type(
            "Стекло 1", 1500.0, 500.0, base_price_list.id
        )
        
        glasses = ctrl.get_glass_types(base_price_list.id)
        assert len(glasses) >= 1

    def test_create_glass_option(self, session, base_price_list):
        """Создание опции стекла."""
        ctrl = OptionsController(session)
        glass = ctrl.create_glass_type(
            "Стекло для опций", 2000.0, 700.0, base_price_list.id
        )
        
        option = ctrl.create_glass_option(
            "Матировка", 500.0, 200.0, glass_type_id=glass.id
        )
        assert option.name == "Матировка"


class TestCalculatorController:
    """Тесты главного калькулятора."""

    def test_validate_and_calculate_door(self, session, base_price_list):
        """Полный расчёт двери."""
        ctrl = CalculatorController(session)
        config = {
            "product_type": "Дверь",
            "subtype": "Квартирная",
            "height": 2100,
            "width": 900,
            "is_double_leaf": False,
            "markup_percent": 0,
            "markup_abs": 0,
            "extra_options": {}
        }
        
        result = ctrl.validate_and_calculate(
            "Дверь", "Квартирная", 2100, 900,
            None, config, 0, 0, 1
        )
        
        assert result["success"] is True

    def test_validate_invalid_dimensions(self, session):
        """Ошибка при невалидных размерах."""
        ctrl = CalculatorController(session)
        config = {"extra_options": {}}
        
        result = ctrl.validate_and_calculate(
            "Дверь", "Квартирная", 100, 100,
            None, config, 0, 0, 1
        )
        
        assert result["success"] is False


class TestModels:
    """Тесты моделей."""

    def test_counterparty_required_fields(self, session):
        """Проверка обязательных полей контрагента."""
        cp = Counterparty(
            name="Полный тест",
            type=CounterpartyType.NATURAL,
            phone="+7 999 123-45-67",
            address="ул. Тестовая, 1"
        )
        session.add(cp)
        session.commit()
        
        assert cp.name == "Полный тест"
        assert cp.type == CounterpartyType.NATURAL

    def test_offer_item_creation(self, session, base_price_list):
        """Создание позиции КП."""
        cpa_ctrl = CounterpartyController(session)
        cp = cpa_ctrl.create(
            cp_type=CounterpartyType.NATURAL,
            name="Тест позиции",
            inn=None,
            phone="+7 999 999-99-99",
            address="Адрес"
        )
        offer_ctrl = OfferController(session)
        offer = offer_ctrl.create_offer(cp.id)
        
        item = OfferItem(
            offer_id=offer.id,
            position=1,
            product_type="Дверь",
            subtype="Квартирная",
            width=900,
            height=2100,
            quantity=1,
            base_price=15000.0,
            final_price=15000.0,
            markup_percent=0.0,
            markup_abs=0.0,
            options_="{}"
        )
        session.add(item)
        session.commit()
        
        assert item.markup_percent == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
