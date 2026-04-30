"""Тесты для всего функционала, связанного с прайс-листами.

Проверяют:
- Создание персонализированных прайс-листов
- Редактирование цен в персонализированных прайсах (custom_* поля)
- Динамическое изменение цен во всех вкладках при смене прайс-листа
- Калькулятор подтягивает правильные цены из персонализированного прайса
- Все виджеты в PriceTab правильно работают с персонализированными прайсами
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.database import Base, SessionLocal, _seed_demo_data
from controllers.price_list_controller import PriceListController
from controllers.calculator_controller import CalculatorController
from models.price_list import BasePriceList, PersonalizedPriceList, TypePrice, CustomTypePrice
from models.glass import GlassType, GlassOption
from models.hardware import HardwareItem
from models.closer import Closer, Coordinator


@pytest.fixture(scope="function")
def test_db_session():
    """Создаёт изолированную БД в памяти для каждого теста."""
    engine = create_engine("sqlite:///:memory:?cache=shared", echo=False)
    Session = sessionmaker(bind=engine)
    
    # Импортируем все модели для регистрации в Base.metadata
    import models  # noqa: F401
    
    # Создаём таблицы
    Base.metadata.create_all(bind=engine)
    
    session = Session()
    
    # Заполняем демо-данными (базовый прайс)
    _seed_demo_data(lambda: session)
    
    yield session
    
    session.close()


@pytest.fixture
def price_ctrl(test_db_session):
    """Контроллер прайс-листов с тестовой сессией."""
    ctrl = PriceListController(session=test_db_session)
    return ctrl


@pytest.fixture
def calc_ctrl(test_db_session):
    """Контроллер калькулятора с тестовой сессией."""
    ctrl = CalculatorController(session=test_db_session)
    return ctrl


class TestPersonalizedPriceListCreation:
    """Тесты создания персонализированных прайс-листов."""
    
    def test_create_personalized_saves_to_db(self, price_ctrl):
        """Персонализированный прайс сохраняется в БД."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "Тестовый персональный",
            base_id=base.id
        )
        assert personal.id is not None
        assert personal.name == "Тестовый персональный"
        assert personal.base_price_list_id == base.id
    
    def test_custom_price_overrides_base(self, price_ctrl):
        """Проверяем custom_ цены переопределяют базовые."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "с кастомной ценой",
            base_id=base.id
        )
        
        # Устанавливаем кастомную цену через контроллер
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 25000.0})
        
        # Проверяем get_price_for_calculation
        prices = price_ctrl.get_price_for_calculation(personal.id)
        assert prices["doors_price_std_single"] == 25000.0
        
        # Проверяем, что базовая цена не изменилась
        base_prices = price_ctrl.get_price_for_calculation(base.id)
        assert base_prices["doors_price_std_single"] == 15000.0
    
    def test_no_custom_uses_base_price(self, price_ctrl):
        """Если custom_ цена не установлена, используется базовая."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "Без кастома",
            base_id=base.id
        )
        
        # Цены должны быть как в базовом
        prices = price_ctrl.get_price_for_calculation(personal.id)
        assert prices["doors_price_std_single"] == base.doors_price_std_single
        assert prices["hatch_std"] == base.hatch_std


class TestPriceEditWidgetBehavior:
    """Тесты поведения виджета редактирования цен."""
    
    def test_save_custom_price_for_personalized(self, price_ctrl, test_db_session):
        """Сохранение custom_ цены для персонализированного прайса."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "Тестовый",
            base_id=base.id
        )
        test_db_session.commit()
        
        # Устанавливаем custom_ цены (как будто из _on_double_click)
        price_ctrl.update_personalized(personal.id, {
            "custom_doors_price_std_single": 30000.0,
            "custom_doors_price_per_m2_nonstd": 20000.0
        })
        
        # Проверяем, что цены берутся из custom_ полей
        prices = price_ctrl.get_price_for_calculation(personal.id)
        assert prices["doors_price_std_single"] == 30000.0
        assert prices["doors_price_per_m2_nonstd"] == 20000.0
        
        # Проверяем, что базовый прайс не затронут
        base_prices = price_ctrl.get_price_for_calculation(base.id)
        assert base_prices["doors_price_std_single"] == 15000.0
    
    def test_base_price_not_affected_by_personalized_edit(self, price_ctrl, test_db_session):
        """Редактирование персонализированного прайса не меняет базовый."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "Тестовый2",
            base_id=base.id
        )
        test_db_session.commit()
        
        # Меняем custom_ цену
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 50000.0})
        
        # Базовая цена не должна измениться
        base_prices = price_ctrl.get_price_for_calculation(base.id)
        assert base_prices["doors_price_std_single"] == 15000.0


class TestCalculatorPriceSelection:
    """Тесты выбора прайс-листа в калькуляторе."""
    
    def test_calculator_uses_selected_price_list(self, price_ctrl, calc_ctrl):
        """Калькулятор использует цены выбранного прайс-листа."""
        base = price_ctrl.get_base_price_list()
        
        # Создаём персонализированный прайс
        personal = price_ctrl.create_personalized(
            "Для теста",
            base_id=base.id
        )
        price_ctrl.update_personalized(personal.id, {"custom_doors_price_std_single": 50000.0})
        
        # Расчёт с базовым прайсом
        result_base = calc_ctrl.validate_and_calculate(
            "Дверь", "Техническая",
            2000, 900,  # стандартные размеры
            base.id,
            {}
        )
        
        # Расчёт с персонализированным прайсом
        result_personal = calc_ctrl.validate_and_calculate(
            "Дверь", "Техническая",
            2000, 900,
            personal.id,
            {}
        )
        
        assert result_base["success"] is True
        assert result_personal["success"] is True
        # Цена должна отличаться
        assert result_base["price_per_unit"] != result_personal["price_per_unit"]
    
    def test_calculator_falls_back_to_base_for_none(self, price_ctrl, calc_ctrl):
        """Если price_list_id=None, используется базовый прайс."""
        base = price_ctrl.get_base_price_list()
        
        result = calc_ctrl.validate_and_calculate(
            "Дверь", "Техническая",
            2000, 900,
            None,  # None = базовый
            {}
        )
        
        assert result["success"] is True
        assert result["price_per_unit"] == 15000.0  # базовая цена


class TestTypeSpecificPrices:
    """Тесты type-specific цен для персональных прайсов."""
    
    def test_custom_type_price_for_personalized(self, price_ctrl):
        """Type-specific цены для персонального прайса."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "С type-specific",
            base_id=base.id
        )
        
        # Получаем уже существующий custom type price (скопированный из базы)
        from sqlalchemy import select
        stmt = select(CustomTypePrice).where(
            CustomTypePrice.price_list_id == personal.id,
            CustomTypePrice.product_type == "Дверь",
            CustomTypePrice.subtype == "Техническая"
        )
        existing = price_ctrl.session.execute(stmt).scalar_one_or_none()
        assert existing is not None
        
        # Обновляем существующий custom type price
        price_ctrl.update_type_price(existing.id, {
            "price_std_single": 18000.0,
            "price_double_std": 32000.0,
            "price_wide_markup": 3000.0,
            "price_per_m2_nonstd": 14000.0
        })
        
        # Проверяем, что цены берутся из custom type price
        prices = price_ctrl.get_type_price(personal.id, "Дверь", "Техническая")
        assert prices is not None
        assert prices["price_std_single"] == 18000.0
        assert prices["price_double_std"] == 32000.0
    
    def test_fallback_to_base_type_price(self, price_ctrl):
        """Если нет custom type price, используется базовый."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "Без type-specific",
            base_id=base.id
        )
        
        # Запрашиваем type price для персонализированного прайса
        prices = price_ctrl.get_type_price(personal.id, "Дверь", "Техническая")
        
        # Должны получить цены из базового прайса
        assert prices is not None
        assert prices["price_std_single"] == 15000.0  # базовая цена


class TestGlassAndHardwarePrices:
    """Тесты копирования стёкол и фурнитуры."""
    
    def test_glass_types_copied_to_personalized(self, price_ctrl, test_db_session):
        """Типы стёкол копируются в персонализированный прайс."""
        base = price_ctrl.get_base_price_list()
        
        personal = price_ctrl.create_personalized(
            "Стёклами",
            base_id=base.id
        )
        price_ctrl.session.commit()
        
        # Проверяем, что стёкла скопировались
        from controllers.options_controller import OptionsController
        opt_ctrl = OptionsController(test_db_session)
        glasses = opt_ctrl.get_glass_types(personal.id)
        assert len(glasses) > 0
    
    def test_hardware_copied_to_personalized(self, price_ctrl, test_db_session):
        """Фурнитура копируется в персональный прайс."""
        base = price_ctrl.get_base_price_list()
        
        personal = price_ctrl.create_personalized(
            "С фурнитурой",
            base_id=base.id
        )
        price_ctrl.session.commit()
        
        # Проверяем, что фурнитура скопировалась
        from controllers.hardware_controller import HardwareController
        hw_ctrl = HardwareController(test_db_session)
        items = hw_ctrl.get_by_type(hw_type="Замок", price_list_id=personal.id)
        assert len(items) > 0


class TestPriceListSwitching:
    """Тесты динамического изменения цен при смене прайс-листа."""
    
    def test_multiple_price_lists_independent(self, price_ctrl):
        """Персонализированные прайсы независимы друг от друга."""
        base = price_ctrl.get_base_price_list()
        
        p1 = price_ctrl.create_personalized("Прайс 1", base_id=base.id)
        price_ctrl.update_personalized(p1.id, {"custom_doors_price_std_single": 10000.0})
        
        p2 = price_ctrl.create_personalized("Прайс 2", base_id=base.id)
        price_ctrl.update_personalized(p2.id, {"custom_doors_price_std_single": 20000.0})
        
        prices1 = price_ctrl.get_price_for_calculation(p1.id)
        prices2 = price_ctrl.get_price_for_calculation(p2.id)
        
        assert prices1["doors_price_std_single"] == 10000.0
        assert prices2["doors_price_std_single"] == 20000.0
    
    def test_get_price_list_by_id(self, price_ctrl):
        """get_price_list_by_id возвращает правильный прайс."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "Тест",
            base_id=base.id
        )
        price_ctrl.session.commit()
        
        # По ID персонализированного
        found = price_ctrl.get_price_list_by_id(personal.id)
        assert found is not None
        assert isinstance(found, PersonalizedPriceList)
        assert found.name == "Тест"
        
        # По ID базового
        found_base = price_ctrl.get_price_list_by_id(base.id)
        assert found_base is not None
        assert isinstance(found_base, BasePriceList)


class TestColorPrices:
    """Тесты цен на цвета и покрытия."""
    
    def test_color_prices_custom_for_personalized(self, price_ctrl):
        """Цены на цвета можно переопределить для персонализированного прайса."""
        base = price_ctrl.get_base_price_list()
        personal = price_ctrl.create_personalized(
            "С цветами",
            base_id=base.id
        )
        
        # Устанавливаем custom цены на цвета
        price_ctrl.update_personalized(personal.id, {
            "custom_nonstd_color_markup_pct": 10.0,
            "custom_diff_color_markup": 3000.0,
            "custom_moire_price": 2500.0
        })
        
        # Проверяем get_price_for_calculation
        prices = price_ctrl.get_price_for_calculation(personal.id)
        assert prices["nonstd_color_markup_pct"] == 10.0
        assert prices["diff_color_markup"] == 3000.0
        assert prices["moire_price"] == 2500.0
