"""Модульные тесты калькуляторов стоимости. Строго проверяют формулы из п.4 и п.5 ТЗ."""

import pytest
from utils.calculators.base_calculator import CalculatorContext, PriceData, GlassItemData
from utils.calculators.door_calculator import DoorCalculator
from utils.calculators.hatch_calculator import HatchCalculator
from utils.calculators.gate_calculator import GateCalculator
from utils.calculators.transom_calculator import TransomCalculator
from utils.calculators.glass_calculator import GlassCalculator, GlassCalcParams
from utils.validators import validate_dimensions
from constants import PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM


@pytest.fixture
def base_prices() -> PriceData:
    """Фикстура с эталонными тарифами из базового прайс-листа."""
    p = PriceData()
    p.doors_std_single = 15000.0
    p.doors_wide_markup = 2500.0
    p.doors_per_m2_nonstd = 11000.0
    p.doors_double_std = 28000.0
    p.hatch_std = 4000.0
    p.hatch_wide_markup = 800.0
    p.hatch_per_m2_nonstd = 9000.0
    p.gate_per_m2 = 3500.0
    p.gate_large_per_m2 = 4200.0
    p.transom_per_m2 = 8000.0
    p.transom_min = 4500.0
    p.cutout_price = 800.0
    p.deflector_per_m2 = 3200.0
    p.trim_per_lm = 650.0
    p.closer_price = 2500.0
    p.hinge_price = 300.0
    p.anti_theft_price = 450.0
    p.gkl_price = 1200.0
    p.mount_ear_price = 80.0
    return p


def make_ctx(prod: str, subtype: str, h: float, w: float, is_double: bool, prices: PriceData,
             **kwargs) -> CalculatorContext:
    """Хелпер для быстрого создания контекста."""
    ctx = CalculatorContext(
        product_type=prod, subtype=subtype, height=h, width=w,
        is_double_leaf=is_double, prices=prices, **kwargs
    )
    return ctx


# === ТЕСТЫ ДВЕРЕЙ (п.4.2) ===

class TestDoorCalculator:
    def test_standard_single(self, base_prices: PriceData):
        """Одностворчатая стандартная (1500-2200, 500-1000) -> фиксированная цена."""
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices)
        assert DoorCalculator().calculate(ctx) == 15000.0

    def test_wide_single(self, base_prices: PriceData):
        """Одностворчатая широкая (1500-2200, 1010-1100) -> стандарт + наценка."""
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2100, 1050, False, base_prices)
        expected = base_prices.doors_std_single + base_prices.doors_wide_markup
        assert DoorCalculator().calculate(ctx) == expected

    def test_nonstandard(self, base_prices: PriceData):
        """Одностворчатая нестандартная (>2200 или >1100, <3.6м²) -> м² * площадь, но >= широкой."""
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2400, 1200, False, base_prices)
        # Площадь 2.88. 2.88 * 11000 = 31680. Минимум = 17500.
        expected = base_prices.doors_per_m2_nonstd * 2.88
        assert DoorCalculator().calculate(ctx) == expected

    def test_standard_double(self, base_prices: PriceData):
        """Двухстворчатая стандартная (1500-2200, 800-1300) -> цена из прайса."""
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2100, 1000, True, base_prices)
        assert DoorCalculator().calculate(ctx) == base_prices.doors_double_std

    def test_nonstandard_double(self, base_prices: PriceData):
        """Двухстворчатая нестандартная -> м², но >= стандартной двух."""
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2300, 1400, True, base_prices)
        expected = base_prices.doors_per_m2_nonstd * (2.3 * 1.4)
        assert DoorCalculator().calculate(ctx) == expected

    def test_markup_percent_and_abs(self, base_prices: PriceData):
        """Наценка применяется к итоговой базовой стоимости + опции."""
        ctx = make_ctx(PRODUCT_DOOR, "Техническая", 2000, 900, False, base_prices,
                       markup_percent=10.0, markup_abs=500.0)
        # 15000 * 1.1 + 500 = 17000
        assert DoorCalculator().calculate(ctx) == 17000.0


# === ТЕСТЫ ЛЮКОВ (п.4.3) ===

class TestHatchCalculator:
    def test_standard_single(self, base_prices: PriceData):
        ctx = make_ctx(PRODUCT_HATCH, "Технический", 800, 800, False, base_prices)
        assert HatchCalculator().calculate(ctx) == 4000.0

    def test_double_standard_multiplier(self, base_prices: PriceData):
        """Двустворчатый ≤1000x1000 -> стандарт * 1.2"""
        ctx = make_ctx(PRODUCT_HATCH, "Технический", 900, 900, True, base_prices)
        assert HatchCalculator().calculate(ctx) == 4000.0 * 1.2

    def test_revisional_fixed_vs_m2(self, base_prices: PriceData):
        """Ревизионный: <=0.4м² -> фикс, >0.4м² -> м² * площадь."""
        ctx1 = make_ctx(PRODUCT_HATCH, "Ревизионный", 600, 600, False, base_prices)  # 0.36м²
        assert HatchCalculator().calculate(ctx1) == 4000.0

        ctx2 = make_ctx(PRODUCT_HATCH, "Ревизионный", 800, 800, False, base_prices)  # 0.64м²
        assert round(HatchCalculator().calculate(ctx2), 2) == round(9000.0 * 0.64, 2)


# === ТЕСТЫ ВОРОТ И ФРАМУГ (п.4.4, п.4.5) ===

class TestGateTransomCalculator:
    def test_gate_standard(self, base_prices: PriceData):
        """Стандартные ворота: площадь > 3.6 ИЛИ высота > 2490 (при H<3000, W<3000)."""
        ctx = make_ctx(PRODUCT_GATE, "Технические", 2500, 1500, True, base_prices)
        # Площадь 3.75. Ставка 3500.
        assert GateCalculator().calculate(ctx) == 3500.0 * 3.75

    def test_gate_large(self, base_prices: PriceData):
        """Большие ворота: площадь > 3.6 И (H>=3000 ИЛИ W>=3000)."""
        ctx = make_ctx(PRODUCT_GATE, "Технические", 3000, 2000, True, base_prices)
        # Площадь 6.0. Ставка 4200.
        assert GateCalculator().calculate(ctx) == 4200.0 * 6.0

    def test_transom_min_price_check(self, base_prices: PriceData):
        """Фрамуга: max(м²*площадь, мин_цена)."""
        ctx = make_ctx(PRODUCT_TRANSOM, "Техническая", 200, 500, False, base_prices)
        # Площадь 0.1м². 8000 * 0.1 = 800. Минимум 4500.
        assert TransomCalculator().calculate(ctx) == 4500.0


# === ТЕСТЫ ОПЦИЙ И ВАЛИДАЦИИ (п.5.2, п.5) ===

class TestOptionsAndValidation:
    def test_glass_aspect_ratio_penalty(self, base_prices: PriceData):
        """Стекло с отношением сторон <= 1/5 -> +50%."""
        params = GlassCalcParams(
            height_mm=200, width_mm=1000,  # ratio 0.2
            type_price_m2=2000.0, type_min_price=500.0,
            options_prices=[], double_sided=False
        )
        # 0.2м² * 2000 = 400. >= 500? Нет, берем 500. *1.5 = 750.
        assert GlassCalculator.calculate(params) == 750.0

    def test_glass_double_sided_min_not_doubled(self, base_prices: PriceData):
        """Опция с двух сторон: цена*2, но минимум НЕ удваивается."""
        params = GlassCalcParams(
            height_mm=500, width_mm=500,  # 0.25м²
            type_price_m2=2000.0, type_min_price=1000.0,
            options_prices=[(100.0, 200.0)], double_sided=True
        )
        # База стекла: max(0.25*2000, 1000) = 1000
        # Опция: 0.25 * 100 * 2 = 50. >= 200? Нет, берем 200.
        # Итого: 1000 + 200 = 1200
        assert GlassCalculator.calculate(params) == 1200.0

    @pytest.mark.parametrize("h,w,prod_type,expected_valid", [
        (2000, 900, PRODUCT_DOOR, True),
        (1400, 800, PRODUCT_DOOR, False),  # Высота < 1500
        (800, 800, PRODUCT_HATCH, True),
        (200, 500, PRODUCT_TRANSOM, True),
        (100, 400, PRODUCT_TRANSOM, False)  # Высота < 200
    ])
    def test_dimension_validation(self, h: float, w: float, prod_type: str, expected_valid: bool):
        valid, msg = validate_dimensions(prod_type, h, w)
        assert valid == expected_valid