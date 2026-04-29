"""Контроллер калькулятора: расчёты, валидация, подготовка контекста.

Содержит:
- CalculatorController: основной контроллер для расчёта стоимости изделий
- Валидация размеров и параметров
- Выбор соответствующего калькулятора (дверь, люк, ворота, фрамуга)
- Формирование результатов расчёта
"""

import logging
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

# Расчёт логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('calculator_controller')


class CalculatorController:
    """Контроллер расчёта стоимости изделий.

    Отвечает за:
    - Валидация входных параметров (размеры, тип изделия)
    - Преобразование данных из UI в CalculatorContext
    - Выбор и запуск соответствующего калькулятора (стратегия)
    - Результат детализированного расчёта с ценой и составом
    
    Использует паттерн "Strategy" для выбора калькулятора в зависимости от типа изделия.
    """

    # Карта соответствия типа продукта и класса-калькулятора
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
            quantity: int = 1,
            is_personalized: bool = False
    ) -> Dict[str, Any]:
        """Полный цикл расчёта: валидация -> подготовка контекста -> расчёт -> формирование результата.

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
            - total_price: общая сумма (price_per_unit * quantity)
            - details: детализация расчёта
        """
        logger.info(f"=== validate_and_calculate START ===")
        logger.info(f"product_type={product_type}, subtype={subtype}, dims={height}x{width}")
        logger.info(f"markup_percent={markup_percent}, markup_abs={markup_abs}, quantity={quantity}")
        logger.info(f"options keys: {list(options.keys()) if options else []}")
        
        # 1. Валидация размеров
        logger.info("Step 1: Validating dimensions...")
        valid, error_msg = validate_dimensions(product_type, height, width)
        if not valid:
            logger.error(f"Validation failed: {error_msg}")
            return {"success": False, "error": error_msg}

        # 2. Получение цен из прайс-листа
        logger.info("Step 2: Loading prices...")
        try:
            # Явно передаём price_list_id (может быть None для базового)
            logger.info(f"  price_list_id={price_list_id}")
            # Use the is_personalized parameter passed to this function
            prices_dict = self.price_ctrl.get_price_for_calculation(price_list_id, is_personalized=is_personalized)
            logger.info(f"  Loaded prices keys: {list(prices_dict.keys())[:5]}...")
        except Exception as e:
            logger.error(f"Price loading error: {e}")
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
            'threshold_price', 'nonstd_color_markup_pct', 'diff_color_markup', 'seal_per_m2',
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
        # Маппинг: EI-60, EIWS-60 → используем цены как для EIS-60
        original_subtype = subtype  # сохраняем для отображения
        price_subtype = subtype
        if subtype in ("EI 60", "EIWS-60"):
            price_subtype = "EIS-60"
        
        # Get ALL type prices for this price list, then filter
        all_type_prices = self.price_ctrl.get_type_prices(price_list_id)
        type_specific = {}
        for tp in all_type_prices:
            if tp.product_type == product_type and tp.subtype == price_subtype:
                type_specific = {
                    "type_std_single": tp.price_std_single or 0,
                    "type_double_std": tp.price_double_std or 0,
                    "type_wide_markup": tp.price_wide_markup or 0,
                    "type_per_m2_nonstd": tp.price_per_m2_nonstd or 0,
                    "has_type_specific_price": True
                }
                break
        
        # Создание объекта PriceData с ценами
        prices = PriceData(**prices_dict_clean, **type_specific)

        # 3. Подготовка контекста калькулятора (передаём original subtype для отображения)
        ctx = self._build_context(
            product_type, original_subtype, height, width, prices, options,
            markup_percent, markup_abs, price_list_id
        )

        # 4. Расчёт стоимости
        try:
            calc_cls = self.CALC_MAP.get(product_type, DoorCalculator) # По умолчанию - дверь
            calculator = calc_cls()
            price_per_unit = calculator.calculate(ctx)
            total_price = price_per_unit * quantity

            logger.info("Step 4: Building result...")
            result = {
                "success": True,
                "price_per_unit": round(price_per_unit, 2),
                "total_price": round(total_price, 2),
                "quantity": quantity,
                "details": self._build_details(ctx, price_per_unit)
            }
            logger.info(f"Result: price_per_unit={result['price_per_unit']}, total_price={result['total_price']}")
            logger.info(f"Details extras_breakdown: {result['details'].get('extras_breakdown', [])}")
            logger.info("=== validate_and_calculate END ===")
            return result
        except Exception as e:
            logger.exception(f"Calculation error: {e}")
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
            markup_abs: float,
            price_list_id: int | None = None
    ) -> CalculatorContext:
        """Подготавливает данные из UI в типизированный CalculatorContext.

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
        # Default price_list_id = 1 (базовый прайс-лист)
        if price_list_id is None:
            price_list_id = 1
        
        is_double = options.get("is_double_leaf", False)
        
        logger.info(f"_build_context: is_double_leaf={is_double}")
        logger.info(f"_build_context: hardware_ids={options.get('hardware_ids', [])}")
        logger.info(f"_build_context: glass_items={len(options.get('glass_items', []))}")
        logger.info(f"_build_context: extra_options={options.get('extra_options', {})}")
        
        # Обработка остекления (стекла и их опции) - с загрузкой цен из БД
        from controllers.options_controller import OptionsController
        opt_ctrl = OptionsController(self.session)
        
        glass_items = []
        for g in options.get("glass_items", []):
            # Пытаемся получить цену из БД если не передана
            price_per_m2 = g.get("price_per_m2", 0)
            min_price = g.get("min_price", 0)
            
            # Если цена не передана - загружаем из БД
            if price_per_m2 == 0 and min_price == 0:
                type_id = g.get("glass_type_id")
                if type_id:
                    glass_types = opt_ctrl.get_glass_types(price_list_id)
                    for gt in glass_types:
                        if gt.get("id") == type_id:
                            price_per_m2 = gt.get("price_per_m2", 0)
                            min_price = gt.get("min_price", 0)
                            break
            
            glass_items.append(GlassItemData(
                type_id=g["type_id"],
                height=g["height"],
                width=g["width"],
                options=g.get("option_ids", []),
                double_sided_options=g.get("double_sided", False),
                options_price_m2=price_per_m2,
                min_price=min_price,
                opt_prices_mins=g.get("opt_prices", [])
            ))

        # Обработка фурнитуры (получение цен из БД)
        hw_prices = []
        for hw_id in options.get("hardware_ids", []):
            hw = self.hw_ctrl.get_by_id(hw_id)
            if hw:
                hw_prices.append(hw.price)
        
        # Обработка вентиляционных решёток
        vent_items = options.get("vent_items", [])
        logger.info(f"_build_context: vent_items count={len(vent_items)}")
        
        # Загружаем цены на вент.решётки из БД если не переданы
        vent_prices = []
        for v in vent_items:
            price_per_m2 = v.get("price_per_m2", 0)
            min_price = v.get("min_price", 0)
            
            # Если цена не передана - загружаем из БД
            if price_per_m2 == 0 and min_price == 0:
                vent_type_id = v.get("vent_type_id")
                if vent_type_id:
                    vent_types = opt_ctrl.get_vent_types(price_list_id)
                    for vt in vent_types:
                        if vt.get("id") == vent_type_id:
                            price_per_m2 = vt.get("price_per_m2", 0)
                            min_price = vt.get("min_price", 0)
                            break
            
            vent_prices.append({
                "h": v.get("height"),
                "w": v.get("width"),
                "type": v.get("vent_type_id"),
                "price_per_m2": price_per_m2,
                "min_price": min_price
            })
            logger.info(f"_build_context: vent[{len(vent_prices)-1}] loaded price_per_m2={price_per_m2}, min_price={min_price}")
        
        for i, v in enumerate(vent_items):
            logger.info(f"_build_context: vent[{i}] from UI: height={v.get('height')}, width={v.get('width')}, type_id={v.get('vent_type_id')}, price_per_m2={v.get('price_per_m2')}, min_price={v.get('min_price')}")

        # Обработка дополнительных опций (отбойник, доборы и т.д.)
        extra_opts = options.get("extra_options", {})
        # Отборная пластина - может быть как в extra_options так и в другом месте
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
            grilles=vent_prices,  # Используем загруженные цены на вент.решётки
            threshold_enabled=options.get("threshold", False),
            deflector_height_mm=deflector_height,
            deflector_double_side=deflector_double_side,
            trim_depth_mm=options.get("trim_depth", 0),
            extra_options=extra_opts,
            markup_percent=markup_percent,
            markup_abs=markup_abs,
            hardware_items=hw_prices,
            seal_enabled=extra_opts.get("seal", False)
        )

    def _build_details(self, ctx: CalculatorContext, final_price: float) -> Dict[str, Any]:
        """Формирует детализацию расчёта для отображения в UI.

        Args:
            ctx: контекст расчёта
            final_price: итоговая цена

        Returns:
            Словарь с деталями для отображения
        """
        logger.info("=== _build_details START ===")
        base_price = ctx.prices.doors_std_single if ctx.product_type == "Дверь" else 0
        if ctx.prices.has_type_specific_price:
            base_price = ctx.prices.type_std_single
        
        logger.info(f"_build_details: base_price={base_price}, product_type={ctx.product_type}")
        
        # Считаем стоимость дополнительных опций
        extras_breakdown = []
        
        # Металл
        if ctx.metal_thickness != "1.0-1.0":
            mult = {"1.2-1.4": 1.05, "1.4-1.4": 1.08, "1.5-1.5": 1.12, "1.4-2.0": 1.15}.get(ctx.metal_thickness, 1.0)
            extras_breakdown.append({"name": f"Металл {ctx.metal_thickness}", "price": base_price * (mult - 1), "base": 0})
            logger.info(f"  Added metal: {ctx.metal_thickness}, price={base_price * (mult - 1)}")
        
        # Цвет
        std_colors = ["7035", "RAL7035"]
        ext_c = str(ctx.color_external)
        int_c = str(ctx.color_internal)
        if ext_c not in std_colors:
            extras_breakdown.append({"name": f"RAL наружный ({ext_c})", "price": base_price * 0.07, "base": 0})
        if int_c not in std_colors and int_c != ext_c:
            extras_breakdown.append({"name": f"RAL внутренний ({int_c})", "price": base_price * 0.07, "base": 0})
        
        # Порог
        if ctx.threshold_enabled:
            count = 2 if ctx.is_double_leaf else 1
            extras_breakdown.append({"name": f"Автопорог ({count} шт.)", "price": ctx.prices.threshold_price * count, "base": ctx.prices.threshold_price * count})
        
        # Антисъём
        if ctx.extra_options.get("anti_theft_pins"):
            count = 2 if ctx.is_double_leaf else 1
            extras_breakdown.append({"name": f"Противосъёмные штыри ({count} шт.)", "price": ctx.prices.anti_theft_price * count, "base": ctx.prices.anti_theft_price * count})
        
        # ГКЛ
        if ctx.extra_options.get("gkl") and not ctx.is_double_leaf:
            extras_breakdown.append({"name": "ГКЛ наполнение", "price": ctx.prices.gkl_price, "base": ctx.prices.gkl_price})
        
        # Монтажные уши
        ears = ctx.extra_options.get("mount_ears_count", 0)
        if ears > 0:
            extras_breakdown.append({"name": f"Монтажные уши ({ears} шт.)", "price": ctx.prices.mount_ear_price * ears, "base": ctx.prices.mount_ear_price * ears})
        
        # Петли
        hinge_active = ctx.extra_options.get("hinge_count_active", 0)
        hinge_passive = ctx.extra_options.get("hinge_count_passive", 0)
        default_active = ctx.extra_options.get("hinge_default_active", 0)
        default_passive = ctx.extra_options.get("hinge_default_passive", 0)
        
        extra_active = max(0, hinge_active - default_active)
        extra_passive = max(0, hinge_passive - default_passive)
        total_hinges = extra_active + (extra_passive if ctx.is_double_leaf else 0)
        
        if total_hinges > 0:
            extras_breakdown.append({"name": f"Доп. петли ({total_hinges} шт.)", "price": ctx.prices.hinge_price * total_hinges, "base": ctx.prices.hinge_price * total_hinges})
        
        # Доводчики
        if ctx.closers_count > 0:
            extras_breakdown.append({"name": f"Доводчик ({ctx.closers_count} шт.)", "price": ctx.prices.closer_price * ctx.closers_count, "base": ctx.prices.closer_price * ctx.closers_count})
        
        # Покрытие
        if ctx.extra_options.get("coating_moire"):
            extras_breakdown.append({"name": "Покрытие Муар", "price": ctx.prices.moire_price, "base": ctx.prices.moire_price})
        if ctx.extra_options.get("coating_lacquer"):
            area = (ctx.height / 1000.0) * (ctx.width / 1000.0)
            extras_breakdown.append({"name": f"Покрытие Лак ({area:.2f} м²)", "price": area * ctx.prices.lacquer_per_m2, "base": area * ctx.prices.lacquer_per_m2})
        if ctx.extra_options.get("coating_primer"):
            price = ctx.prices.primer_double if ctx.is_double_leaf else ctx.prices.primer_single
            name = "Покрытие Грунт (2 створки)" if ctx.is_double_leaf else "Покрытие Грунт (1 створка)"
            extras_breakdown.append({"name": name, "price": price, "base": price})
        
        # Стекла
        for i, glass in enumerate(ctx.glass_items):
            g_area = (glass.height / 1000.0) * (glass.width / 1000.0)
            glass_price = max(g_area * glass.options_price_m2, glass.min_price)
            extras_breakdown.append({"name": f"Стекло {i+1} ({int(glass.height)}x{int(glass.width)})", "price": glass_price, "base": glass_price})
        
        # Вентиляционные решётки
        for i, gr in enumerate(ctx.grilles):
            g_area = (gr.get('h', 0) / 1000.0) * (gr.get('w', 0) / 1000.0)
            gr_price = max(g_area * gr.get('price_per_m2', 0), gr.get('min_price', 0))
            if gr_price > 0:
                # Добавляем стоимость выреза
                gr_price += ctx.prices.cutout_price
            extras_breakdown.append({"name": f"Вент. решётка {i+1} ({int(gr.get('h', 0))}x{int(gr.get('w', 0))})", "price": gr_price, "base": gr_price})
            logger.info(f"  Added grille: {gr}, price={gr_price}")
        
        # Фурнитура
        for hw_price in ctx.hardware_items:
            if hw_price > 0:
                extras_breakdown.append({"name": "Фурнитура", "price": hw_price, "base": hw_price})
                logger.info(f"  Added hardware: price={hw_price}")

        # Уплотнитель
        if ctx.seal_enabled:
            perimeter_m = 2 * (ctx.height + ctx.width) / 1000.0
            if ctx.is_double_leaf:
                perimeter_m *= 2
            seal_price = perimeter_m * ctx.prices.seal_per_m2
            extras_breakdown.append({"name": f"Уплотнитель ({perimeter_m:.2f} м.п.)", "price": seal_price, "base": seal_price})
        
        logger.info(f"_build_details: final extras_breakdown count = {len(extras_breakdown)}")
        logger.info(f"_build_details: extras_breakdown = {extras_breakdown}")
        
        result = {
            "base_calculation": f"{ctx.product_type} {ctx.subtype} {int(ctx.width)}x{int(ctx.height)} мм",
            "base_price": base_price,
            "metal": ctx.metal_thickness,
            "color_ext": ctx.color_external,
            "color_int": ctx.color_internal,
            "glass_count": len(ctx.glass_items),
            "hardware_count": len(ctx.hardware_items),
            "markup": f"{ctx.markup_percent}% + {ctx.markup_abs}",
            "final": final_price,
            "extras_breakdown": extras_breakdown
        }
        
        logger.info("=== _build_details END ===")
        return result

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


