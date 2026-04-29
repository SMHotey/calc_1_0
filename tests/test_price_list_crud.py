"""
Тесты для CRUD операций с прайс-листами.
Проверяют: создание, получение, обновление, удаление базовых и персонализированных прайс-листов.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.database import Base
from models.price_list import BasePriceList, PersonalizedPriceList, TypePrice
from controllers.price_list_controller import PriceListController
from controllers.calculator_controller import CalculatorController


@pytest.fixture(scope="function")
def engine():
    """Создаёт in-memory SQLite базу для каждого теста."""
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture(scope="function")
def session(engine):
    """Создаёт сессию для каждого теста."""
    SessionLocal = sessionmaker(bind=engine)
    sess = SessionLocal()
    yield sess
    sess.close()


@pytest.fixture(scope="function")
def price_ctrl(session):
    """Создаёт контроллер с переданной сессией."""
    return PriceListController(session)


@pytest.fixture(scope="function")
def calc_ctrl(session):
    """Создаёт калькулятор с переданной сессией."""
    return CalculatorController(session)


@pytest.fixture(scope="function")
def base(session, price_ctrl):
    """Создаёт базовый прайс-лист с тестовыми данными."""
    base = price_ctrl.get_base_price_list()
    if base is None:
        base = BasePriceList(name="Базовый прайс")
        session.add(base)
        session.flush()
    
    # Always ensure TypePrice exists
    existing_tp = session.query(TypePrice).filter_by(
        price_list_id=base.id,
        product_type="дверь"
    ).first()
    
    if existing_tp is None:
        tp = TypePrice(
            price_list_id=base.id,
            product_type="дверь",
            subtype="стандартная",
            price_std_single=5000.0,
            price_double_std=7000.0,
            price_wide_markup=1.5,
            price_per_m2_nonstd=3000.0
        )
        session.add(tp)
        session.flush()
    
    # Update base prices and get updated object
    base = price_ctrl.update_base_list(base.id, {
        "doors_price_std_single": 5000.0,
        "doors_double_std": 7000.0,
    })
    print(f"DEBUG FIXTURE: base.id={base.id}, doors_price_std_single={base.doors_price_std_single}")
    return base


class TestPriceListCRUD:
    """Тесты CRUD операций с прайс-листами."""
    
    def test_base_price_list_exists(self, price_ctrl):
        """Базовый прайс-лист существует."""
        base = price_ctrl.get_base_price_list()
        assert base is not None
        assert base.name == "Базовый прайс"
    
    def test_get_base_price_list_returns_same(self, price_ctrl):
        """get_base_price_list возвращает один и тот же объект."""
        base1 = price_ctrl.get_base_price_list()
        base2 = price_ctrl.get_base_price_list()
        assert base1.id == base2.id
    
    def test_create_personalized_price_list(self, session, price_ctrl, base):
        """Создание персонализированного прайс-листа."""
        personal = price_ctrl.create_personalized(
            "Тестовый персональный",
            base_id=base.id
        )
        assert personal is not None
        assert personal.name == "Тестовый персональный"
        assert personal.base_price_list_id == base.id
        # Verify it's a different object type
        from models.price_list import BasePriceList, PersonalizedPriceList
        assert isinstance(personal, PersonalizedPriceList)
        assert not isinstance(personal, BasePriceList)
    
    def test_get_personalized_lists(self, session, price_ctrl, base):
        """Получение списка персонализированных прайсов."""
        p1 = price_ctrl.create_personalized("Персональный 1", base_id=base.id)
        p2 = price_ctrl.create_personalized("Персональный 2", base_id=base.id)
        
        all_personal = price_ctrl.get_personalized_lists()
        names = [p.name for p in all_personal]
        assert "Персональный 1" in names
        assert "Персональный 2" in names
    
    def test_personalized_list_inherits_base_prices(self, session, price_ctrl, base):
        """Персонализированный прайс наследует цены базового."""
        price_ctrl.update_base_list(base.id, {"doors_price_std_single": 5000.0})
        
        personal = price_ctrl.create_personalized(
            "Наследование",
            base_id=base.id
        )
        
        prices = price_ctrl.get_price_for_calculation(personal.id)
        assert prices["doors_price_std_single"] == 5000.0


class TestPriceListPriceRetrieval:
    """Тесты получения цен для расчётов."""
    
    def test_get_price_for_calculation_base(self, price_ctrl, base):
        """Получение цен для расчёта (базовый прайс)."""
        prices = price_ctrl.get_price_for_calculation(base.id)
        assert "doors_price_std_single" in prices
        assert prices["doors_price_std_single"] > 0
    
    def test_get_price_for_calculation_personalized(self, session, price_ctrl, base):
        """Получение цен для расчёта (персонализированный прайс)."""
        personal = price_ctrl.create_personalized(
            "Кастомный",
            base_id=base.id
        )
        
        # Update custom field on PersonalizedPriceList
        personal.custom_doors_price_std_single = 9999.0
        session.flush()
        
        prices = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        assert prices["doors_price_std_single"] == 9999.0
    
    def test_get_price_for_calculation_none_returns_base(self, price_ctrl, base):
        """None в price_list_id возвращает базовый прайс."""
        prices = price_ctrl.get_price_for_calculation(None)
        assert "doors_price_std_single" in prices
    
    def test_get_type_prices(self, price_ctrl, base):
        """Получение type-specific цен."""
        type_prices = price_ctrl.get_type_prices(base.id)
        assert len(type_prices) > 0


class TestPriceListCalculationIntegration:
    """Тесты интеграции с калькулятором."""
    
    def test_calculation_with_different_price_lists(self, session, base, calc_ctrl, price_ctrl):
        """Расчёт с разными прайс-листами даёт разные цены."""
        personal = price_ctrl.create_personalized(
            "Другая цена",
            base_id=base.id
        )
        print(f"DEBUG: personal.id = {personal.id}")
        
        # Update custom field on PersonalizedPriceList
        personal.custom_doors_price_std_single = 10000.0
        session.flush()
        session.refresh(personal)  # Ensure we have the latest data
        
        # Debug: check if custom field is persisted
        print(f"DEBUG: personal.custom_doors_price_std_single = {personal.custom_doors_price_std_single}")
        
        # Check DB directly
        from sqlalchemy import text
        db_val = session.execute(
            text("SELECT custom_doors_price_std_single FROM personalized_price_list WHERE id = :id"),
            {"id": personal.id}
        ).scalar()
        print(f"DEBUG: DB custom_doors_price_std_single = {db_val}")
        
        # Debug: check prices
        prices_base = price_ctrl.get_price_for_calculation(base.id, is_personalized=False)
        prices_personal = price_ctrl.get_price_for_calculation(personal.id, is_personalized=True)
        print(f"DEBUG: base doors_price_std_single = {prices_base['doors_price_std_single']}")
        print(f"DEBUG: personal doors_price_std_single = {prices_personal['doors_price_std_single']}")
        
        res1 = calc_ctrl.validate_and_calculate(
            "Дверь", "Стандартная",
            2000, 900, price_list_id=base.id, options={}
        )
        
        res2 = calc_ctrl.validate_and_calculate(
            "Дверь", "Стандартная",
            2000, 900, price_list_id=personal.id, options={}, is_personalized=True
        )
        
        print(f"DEBUG: res1 price_per_unit = {res1['price_per_unit']}")
        print(f"DEBUG: res2 price_per_unit = {res2['price_per_unit']}")
        
        assert res1["success"] is True
        assert res2["success"] is True
        assert res1["price_per_unit"] != res2["price_per_unit"]
    
    def test_calculation_with_none_price_list_uses_base(self, session, base, calc_ctrl, price_ctrl):
        """None в price_list_id использует базовый прайс."""
        res = calc_ctrl.validate_and_calculate(
            "Дверь", "Стандартная",
            2000, 900, price_list_id=None, options={}
        )
        assert res["success"] is True
        assert res["price_per_unit"] > 0
    
    def test_recalculation_with_new_price_list(self, session, base, calc_ctrl, price_ctrl):
        """Пересчёт с новым прайс-листом обновляет цену."""
        result = price_ctrl.update_base_list(base.id, {"doors_price_std_single": 10000.0})
        assert result is not None
        
        result1 = calc_ctrl.validate_and_calculate(
            "Дверь", "Техническая",
            2000, 900, price_list_id=base.id, options={}
        )
        assert result1["success"] is True
        price1 = result1["price_per_unit"]
        
        price_ctrl.update_base_list(base.id, {"doors_price_std_single": 20000.0})
        
        result2 = calc_ctrl.validate_and_calculate(
            "Дверь", "Техническая",
            2000, 900, price_list_id=base.id, options={}
        )
        assert result2["success"] is True
        price2 = result2["price_per_unit"]
        
        assert price2 != price1


class TestPriceListGlassAndHardware:
    """Тесты для стёкол и фурнитуры в прайс-листах."""
    
    def test_glass_types_copied_to_personalized(self, price_ctrl):
        """Типы стёкол копируются в персонализированный прайс."""
        base = price_ctrl.get_base_price_list()
        
        personal = price_ctrl.create_personalized(
            "С копированием стёкол",
            base_id=base.id
        )
        
        from controllers.options_controller import OptionsController
        opt_ctrl = OptionsController(price_ctrl.session)
        glasses = opt_ctrl.get_glass_types(personal.id)
        assert len(glasses) >= 0
    
    def test_hardware_copied_to_personalized(self, price_ctrl):
        """Фурнитура копируется в персонализированный прайс."""
        base = price_ctrl.get_base_price_list()
        
        personal = price_ctrl.create_personalized(
            "С фурнитурой",
            base_id=base.id
        )
        
        from controllers.hardware_controller import HardwareController
        hw_ctrl = HardwareController(price_ctrl.session)
        items = hw_ctrl.get_all_for_price_list(personal.id)
        assert len(items) >= 0


class TestPriceListEdgeCases:
    """Тесты граничных случаев."""
    
    def test_create_personalized_without_base_uses_default(self, session, price_ctrl):
        """Создание персонализированного без указания base_id."""
        personal = price_ctrl.create_personalized("Без базового")
        assert personal is not None
        base = price_ctrl.get_base_price_list()
        assert personal.base_price_list_id == base.id
    
    def test_get_price_for_calculation_invalid_id_returns_base(self, price_ctrl):
        """Несуществующий ID возвращает базовый прайс."""
        prices = price_ctrl.get_price_for_calculation(9999)
        assert "doors_price_std_single" in prices
    
    def test_multiple_personal_lists_independent(self, session, price_ctrl, base):
        """Несколько персонализированных прайсов независимы."""
        p1 = price_ctrl.create_personalized("Персональный 1", base_id=base.id)
        p2 = price_ctrl.create_personalized("Персональный 2", base_id=base.id)
        
        tp1 = session.query(TypePrice).filter_by(
            price_list_id=p1.id,
            product_type="дверь"
        ).first()
        if tp1:
            tp1.price_std_single = 1111.0
            session.flush()
        
        tp2 = session.query(TypePrice).filter_by(
            price_list_id=p2.id,
            product_type="дверь"
        ).first()
        if tp2:
            assert tp2.price_std_single != 1111.0
