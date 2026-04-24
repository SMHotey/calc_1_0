"""Контроллер калькулятора: оркестрация расчётов, валидация, подготовка контекста.

Содержит:
- CalculatorController: основной контроллер для расчёта стоимости изделий
- Валидация размеров и параметров
- Выбор соответствующего калькулятора (дверь, люк, ворота, фрамуга)
- Формирование результатов расчёта
"""

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
    """Контроллер расчёта стоимости изделия.

    Отвечает за:
    - Валидацию входных параметров (размеры, тип продукции)
    - Преобразование данных из UI в CalculatorContext
    - Выбор и запуск соответствующего калькулятора (стратегия)
    - Возврат детализированного результата с ценой и составом
    
    Использует паттерн "Strategy" для выбора калькулятора в зависимости от типа изделия.
    
    Attributes:
        session: SQLAlchemy сессия для работы с БД
        price_ctrl: контроллер прайс-листов для получения цен
        hw_ctrl: контроллер фурнитуры для получения цен на комплектующие
        
    Example:
        ctrl = CalculatorController()
        result = ctrl.validate_and_calculate(
            product_type="Дверь",
            subtype="EI 60",
            height=2100,
            width=900,
            price_list_id=1,
            options={"is_double_leaf": False},
            markup_percent=10,
            quantity=2
        )
    """

    # Карта соответствия типа продукции и класса-калькулятора
    CALC_MAP = {
        PRODUCT_DOOR: DoorCalculator,    # Калькулятор для дверей
        PRODUCT_HATCH: HatchCalculator,   # Калькулятор для люков
        PRODUCT_GATE: GateCalculator,      # Калькулятор для ворот
        PRODUCT_TRANSOM: TransomCalculator  # Калькулятор для фрамуг
    }

    def __init__(self, session: Optional[Session] = None) -> None:
        """Инициализация контроллера.
        
        Args:
            session: опциональная сессия БД. Если не передана - создаётся новая.
        """
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
        """Полный цикл расчёта: валидация -> подготовка контекста -> расчёт -> форматирование результата.

        Args:
            product_type: тип изделия (Дверь, Люк, Ворота, Фрамуга)
            subtype: подтип (Техническая, EI 60 и т.д.)
            height: высота в мм
            width: ширина в мм
            price_list_id: ID прайс-листа (None = использовать базовый)
            options: словарь с опциями изделия (остекление, фурнитура, цвет и т.д.)
            markup_percent: наценка в процентах
            markup_abs: абсолютная наценка в рублях
            quantity: количество изделий

        Returns:
            Dict с ключами:
            - success: True/False
            - error: сообщение об ошибке (если success=False)
            - price_per_unit: цена за единицу
            - total_price: общая цена (price_per_unit * quantity)
            - details: детализация расчёта
        """
        # 1. Валидация размеров
        valid, error_msg = validate_dimensions(product_type, height, width)
        if not valid:
            return {"success": False, "error": error_msg}

        # 2. Получение цен из прайс-листа
        try:
            prices_dict = self.price_ctrl.get_price_for_calculation(price_list_id)
        except Exception as e:
            return {"success": False, "error": f"Ошибка загрузки прайс-листа: {e}"}

        # Очистка цен от None значений (замена на 0.0)
        prices_dict_clean = {
            k: v if v is not None else 0.0
            for k, v in prices_dict.items()
        }
        
        # whitelist только нужных полей для PriceData
        ALLOWED_FIELDS = {
            'doors_price_std_single', 'doors_price_per_m2_nonstd', 'doors_wide_markup', 'doors_double_std',
            'hatch_std', 'hatch_wide_markup', 'hatch_per_m2_nonstd',
            'gate_per_m2', 'gate_large_per_m2', 'transom_per_m2', 'transom_min',
            'cutout_price', 'deflector_per_m2', 'trim_per_lm',
            'closer_price', 'hinge_price', 'anti_theft_price', 'gkl_price', 'mount_ear_price',
            'threshold_price', 'nonstd_color_markup_pct', 'diff_color_markup',
        }
        
        FIELD_MAP = {
            'doors_price_std_single': 'doors_std_single',
            'doors_price_per_m2_nonstd': 'doors_per_m2_nonstd',
            'doors_wide_markup': 'doors_wide_markup',
            'doors_double_std': 'doors_double_std',
        }
        
        prices_dict_clean = {
            FIELD_MAP.get(k, k): v 
            for k, v in prices_dict_clean.items() 
            if k in ALLOWED_FIELDS
        }
        
        # Получение type-specific цен (для конкретного подтипа)
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
        
        # Создание объекта PriceData с ценами
        prices = PriceData(**prices_dict_clean, **type_specific)

        # 3. Подготовка контекста калькулятора
        ctx = self._build_context(
            product_type, subtype, height, width, prices, options,
            markup_percent, markup_abs
        )

        # 4. Расчёт стоимости
        try:
            calc_cls = self.CALC_MAP.get(product_type, DoorCalculator)  # По умолчанию - дверь
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
        """Преобразует данные из UI в типизированный CalculatorContext.

        Args:
            product_type: тип изделия
            subtype: подтип
            height: высота в мм
            width: ширина в мм
            prices: объект с ценами
            options: словарь опций из UI
            markup_percent: наценка %
            markup_abs: наценка руб.

        Returns:
            CalculatorContext для передачи в калькулятор
        """
        is_double = options.get("is_double_leaf", False)

        # Обработка остекления (стёкла и их опции)
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

        # Обработка фурнитуры (получение цен из БД)
        hw_prices = []
        for hw_id in options.get("hardware_ids", []):
            hw = self.hw_ctrl.get_by_id(hw_id)
            if hw:
                hw_prices.append(hw.price)

        # Обработка дополнительных опций (отбойник, доборы и т.д.)
        extra_opts = options.get("extra_options", {})
        # Отбойная пластина - может быть на верхнем уровне или в extra_options
        deflector_height = options.get("deflector_height", None)
        deflector_double_side = options.get("deflector_double_side", None)
        if deflector_height is None:
            deflector_height = extra_opts.get("deflector_height", 0)
        if deflector_double_side is None:
            deflector_double_side = extra_opts.get("deflector_double_side", False)
        
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
            deflector_height_mm=deflector_height,
            deflector_double_side=deflector_double_side,
            trim_depth_mm=options.get("trim_depth", 0),
            extra_options=extra_opts,
            markup_percent=markup_percent,
            markup_abs=markup_abs,
            hardware_items=hw_prices
        )

    def _build_details(self, ctx: CalculatorContext, final_price: float) -> Dict[str, Any]:
        """Формирует детализацию расчёта для отображения в UI.

        Args:
            ctx: контекст расчёта
            final_price: итоговая цена

        Returns:
            Словарь с деталями для отображения
        """
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
        """Возвращает список типов стёкол для выбора в конфигураторе.

        Args:
            price_list_id: ID прайс-листа (None = использовать базовый)

        Returns:
            Список словарей с данными стёкол: id, name, price_m2, min_price
        """
        from models.glass import GlassType
        from sqlalchemy import select

        stmt = select(GlassType).where(GlassType.price_list_id == (price_list_id or 1))
        result = self.session.execute(stmt).scalars().all()
        return [{"id": g.id, "name": g.name, "price_m2": g.price_per_m2, "min_price": g.min_price} for g in result]

    def __enter__(self):
        """Контекстный менеджер - вход."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход (закрытие сессии)."""
        if exc_type:
            self.session.rollback()
        self.session.close()
