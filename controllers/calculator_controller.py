"""Контроллер калькулятора: оркестрация расчётов, валидация, подготовка контекста."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from db.database import SessionLocal
from utils.validators import validate_dimensions
from utils.calculators import (
    DoorCalculator, HatchCalculator, GateCalculator, TransomCalculator,
    CalculatorContext, PriceData
)
from utils.calculators.base_calculator import GlassItemData
from constants import PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM
from controllers.price_list_controller import PriceListController
from controllers.hardware_controller import HardwareController


class CalculatorController:
    """
    Контроллер расчёта стоимости изделия.

    Отвечает за:
    - Валидацию входных параметров
    - Преобразование данных из UI в CalculatorContext
    - Выбор и запуск соответствующего калькулятора
    - Возврат детализированного результата
    """

    CALC_MAP = {
        PRODUCT_DOOR: DoorCalculator,
        PRODUCT_HATCH: HatchCalculator,
        PRODUCT_GATE: GateCalculator,
        PRODUCT_TRANSOM: TransomCalculator
    }

    def __init__(self, session: Optional[Session] = None) -> None:
        self.session = session or SessionLocal()
        self.price_ctrl = PriceListController(self.session)
        self.hw_ctrl = HardwareController(self.session)

    def validate_and_calculate(
            self,
            product_type: str,
            subtype: str,
            height: float,
            width: float,
            price_list_id: Optional[int],
            options: Dict[str, Any],
            markup_percent: float = 0.0,
            markup_abs: float = 0.0,
            quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Полный цикл: валидация -> подготовка контекста -> расчёт -> форматирование результата.

        :return: Dict с ключами: success, error, price_per_unit, total_price, details
        """
        # 1. Валидация размеров
        valid, error_msg = validate_dimensions(product_type, height, width)
        if not valid:
            return {"success": False, "error": error_msg}

        # 2. Получение цен
        try:
            prices_dict = self.price_ctrl.get_price_for_calculation(price_list_id)
        except Exception as e:
            return {"success": False, "error": f"Ошибка загрузки прайс-листа: {e}"}

        prices_dict_clean = {
            k: v if v is not None else 0.0
            for k, v in prices_dict.items()
            if k in ["doors_std_single", "doors_per_m2_nonstd", "doors_wide_markup",
                     "doors_double_std", "hatch_std", "hatch_wide_markup", "hatch_per_m2_nonstd",
                     "gate_per_m2", "gate_large_per_m2", "transom_per_m2", "transom_min",
                     "cutout_price", "deflector_per_m2", "trim_per_lm"]
        }
        
        type_prices = self.price_ctrl.get_type_price(price_list_id, product_type, subtype)
        type_specific = {}
        if type_prices:
            type_specific = {
                "type_std_single": type_prices.get("price_std_single", 0),
                "type_double_std": type_prices.get("price_double_std", 0),
                "type_wide_markup": type_prices.get("price_wide_markup", 0),
                "type_per_m2_nonstd": type_prices.get("price_per_m2_nonstd", 0),
                "has_type_specific_price": True
            }
        
        prices = PriceData(**prices_dict_clean, **type_specific)

        # 3. Подготовка контекста
        ctx = self._build_context(
            product_type, subtype, height, width, prices, options,
            markup_percent, markup_abs
        )

        # 4. Расчёт
        try:
            calc_cls = self.CALC_MAP.get(product_type, DoorCalculator)
            calculator = calc_cls()
            price_per_unit = calculator.calculate(ctx)
            total_price = price_per_unit * quantity

            return {
                "success": True,
                "price_per_unit": round(price_per_unit, 2),
                "total_price": round(total_price, 2),
                "quantity": quantity,
                "details": self._build_details(ctx, price_per_unit)
            }
        except Exception as e:
            return {"success": False, "error": f"Ошибка расчёта: {e}"}

    def _build_context(
            self,
            product_type: str,
            subtype: str,
            height: float,
            width: float,
            prices: PriceData,
            options: Dict[str, Any],
            markup_percent: float,
            markup_abs: float
    ) -> CalculatorContext:
        """Преобразует данные из UI в типизированный CalculatorContext."""
        is_double = options.get("is_double_leaf", False)

        # Обработка остекления
        glass_items = []
        for g in options.get("glass_items", []):
            glass_items.append(GlassItemData(
                type_id=g["type_id"],
                height=g["height"],
                width=g["width"],
                options=g.get("option_ids", []),
                double_sided_options=g.get("double_sided", False),
                options_price_m2=g.get("price_per_m2", 0),
                min_price=g.get("min_price", 0),
                opt_prices_mins=g.get("opt_prices", [])
            ))

        # Обработка фурнитуры
        hw_prices = []
        for hw_id in options.get("hardware_ids", []):
            hw = self.hw_ctrl.get_by_id(hw_id)
            if hw:
                hw_prices.append(hw.price)
                # Если замок требует цилиндр и он не выбран отдельно — можно добавить логику

        return CalculatorContext(
            product_type=product_type,
            subtype=subtype,
            height=height,
            width=width,
            is_double_leaf=is_double,
            prices=prices,
            color_external=options.get("color_external", 7035),
            color_internal=options.get("color_internal", options.get("color_external", 7035)),
            metal_thickness=options.get("metal_thickness", "1.0-1.0"),
            glass_items=glass_items,
            closers_count=options.get("closers_count", 0),
            grilles=options.get("grilles", []),
            threshold_enabled=options.get("threshold", False),
            deflector_height_mm=options.get("deflector_height", 0),
            deflector_double_side=options.get("deflector_double", False),
            trim_depth_mm=options.get("trim_depth", 0),
            extra_options=options.get("extra_options", {}),
            markup_percent=markup_percent,
            markup_abs=markup_abs,
            hardware_items=hw_prices
        )

    def _build_details(self, ctx: CalculatorContext, final_price: float) -> Dict[str, Any]:
        """Формирует детализацию расчёта для отображения в UI."""
        return {
            "base_calculation": f"{ctx.product_type} {ctx.subtype} {int(ctx.width)}x{int(ctx.height)}мм",
            "color": f"Внешний: {ctx.color_external}, Внутренний: {ctx.color_internal}",
            "metal": ctx.metal_thickness,
            "glass_count": len(ctx.glass_items),
            "hardware_count": len(ctx.hardware_items),
            "markup": f"{ctx.markup_percent}% + {ctx.markup_abs}₽",
            "final": final_price
        }

    def get_available_glass_types(self, price_list_id: Optional[int]) -> List[Dict[str, Any]]:
        """Возвращает список типов стёкол для выбора в конфигураторе."""
        from models.glass import GlassType
        from sqlalchemy import select

        stmt = select(GlassType).where(GlassType.price_list_id == (price_list_id or 1))
        result = self.session.execute(stmt).scalars().all()
        return [{"id": g.id, "name": g.name, "price_m2": g.price_per_m2, "min_price": g.min_price} for g in result]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()