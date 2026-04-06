"""Инициализация движка БД, сессий, создание схемы и заполнение демо-данными."""

import os
import logging
from typing import Generator

from sqlalchemy import create_engine, inspect, event
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

logger: logging.Logger = logging.getLogger(__name__)

DB_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metalcalc.db")
DATABASE_URL: str = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Генератор сессии БД с автоматическим закрытием."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Создаёт таблицы при первом запуске и заполняет их начальными данными."""
    insp = inspect(engine)
    if not insp.has_table("base_price_list"):
        logger.info("Схема БД не найдена. Создаю таблицы и заполняю демо-данными...")
        # Импорт моделей должен происходить здесь, чтобы Base.metadata был заполнен
        from models.price_list import BasePriceList, PersonalizedPriceList
        from models.counterparty import Counterparty
        from models.glass import GlassType
        from models.hardware import HardwareItem

        Base.metadata.create_all(bind=engine)
        _seed_demo_data(SessionLocal)
        logger.info("База данных успешно инициализирована.")
    else:
        logger.info("Схема БД существует. Проверка актуальности...")
        # В реальном проекте здесь был бы Alembic. Для standalone приложения достаточно create_all.
        from models.price_list import BasePriceList
        from models.glass import GlassType
        Base.metadata.create_all(bind=engine)


def _seed_demo_data(session_factory: sessionmaker) -> None:
    """Заполняет БД базовыми данными для немедленного использования."""
    from models.price_list import BasePriceList, TypePrice
    from models.counterparty import Counterparty
    from models.counterparty import CounterpartyType
    from models.glass import GlassType, GlassOption
    from models.hardware import HardwareItem
    from constants import HardwareType, CounterpartyType as CPType, PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM

    with session_factory() as session:
        base_pl = BasePriceList(name="Базовый системный прайс")
        
        base_pl.doors_price_std_single = 15000.0
        base_pl.doors_price_per_m2_nonstd = 12000.0
        base_pl.doors_wide_markup = 2500.0
        base_pl.doors_double_std = 28000.0
        base_pl.hatch_std = 4500.0
        base_pl.hatch_wide_markup = 800.0
        base_pl.hatch_per_m2_nonstd = 9000.0
        base_pl.gate_per_m2 = 3800.0
        base_pl.gate_large_per_m2 = 4500.0
        base_pl.transom_per_m2 = 8500.0
        base_pl.transom_min = 4500.0
        base_pl.cutout_price = 800.0
        base_pl.deflector_per_m2 = 3200.0
        base_pl.trim_per_lm = 650.0
        base_pl.closer_price = 2500.0
        base_pl.hinge_price = 300.0
        base_pl.anti_theft_price = 450.0
        base_pl.gkl_price = 1200.0
        base_pl.mount_ear_price = 80.0
        
        session.add(base_pl)
        session.flush()

        type_prices_data = [
            (PRODUCT_DOOR, "Техническая", 15000, 28000, 2500, 12000),
            (PRODUCT_DOOR, "EI 60", 22000, 38000, 3500, 14500),
            (PRODUCT_DOOR, "EIS 60", 28000, 48000, 4500, 18000),
            (PRODUCT_DOOR, "EIWS 60", 28000, 48000, 4500, 18000),
            (PRODUCT_DOOR, "Квартирная", 18000, 32000, 3000, 13000),
            (PRODUCT_DOOR, "Однолистовая", 12000, 0, 2000, 10000),
            
            (PRODUCT_HATCH, "Технический", 4500, 0, 800, 9000),
            (PRODUCT_HATCH, "EI 60", 6500, 0, 1200, 11000),
            (PRODUCT_HATCH, "Ревизионный", 3500, 0, 600, 7500),
            
            (PRODUCT_GATE, "Технические", 0, 0, 0, 3800),
            (PRODUCT_GATE, "EI 60", 0, 0, 0, 5200),
            (PRODUCT_GATE, "Однолистовые", 0, 0, 0, 4500),
            
            (PRODUCT_TRANSOM, "Техническая", 0, 0, 0, 8500),
            (PRODUCT_TRANSOM, "EI 60", 0, 0, 0, 11500),
        ]
        
        for prod_type, subtype, std_s, double_s, wide_m, per_m2 in type_prices_data:
            tp = TypePrice(
                price_list_id=base_pl.id,
                product_type=prod_type,
                subtype=subtype,
                price_std_single=std_s,
                price_double_std=double_s,
                price_wide_markup=wide_m,
                price_per_m2_nonstd=per_m2
            )
            session.add(tp)

        glass1 = GlassType(name="Армированное 4мм", price_per_m2=1800.0, min_price=600.0, price_list_id=base_pl.id)
        glass2 = GlassType(name="Прозрачное закалённое 6мм", price_per_m2=2400.0, min_price=900.0, price_list_id=base_pl.id)
        glass3 = GlassType(name="Матовое триплекс 8мм", price_per_m2=3500.0, min_price=1200.0, price_list_id=base_pl.id)
        glass4 = GlassType(name="Тонированное 6мм", price_per_m2=2800.0, min_price=1000.0, price_list_id=base_pl.id)
        session.add_all([glass1, glass2, glass3, glass4])
        session.flush()
        
        session.add_all([
            GlassOption(glass_type_id=glass1.id, name="Матировка", price_per_m2=500.0, min_price=200.0),
            GlassOption(glass_type_id=glass1.id, name="Пленка Anti-COVID", price_per_m2=800.0, min_price=300.0),
            GlassOption(glass_type_id=glass2.id, name="Наклейка на стекло", price_per_m2=400.0, min_price=150.0),
            GlassOption(glass_type_id=glass3.id, name="Пескоструй", price_per_m2=600.0, min_price=250.0),
            GlassOption(glass_type_id=glass4.id, name="Зеркальная пленка", price_per_m2=700.0, min_price=280.0),
        ])

        session.add_all([
            HardwareItem(type="Замок", name="Cisa 15011", price=4800.0,
                description="Цилиндровый замок для металлических дверей", has_cylinder=True, price_list_id=base_pl.id),
            HardwareItem(type="Замок", name="Mottura 54.535", price=6200.0,
                description="Сувальдный замок повышенной секретности", has_cylinder=False, price_list_id=base_pl.id),
            HardwareItem(type="Замок", name="Kerberos 211.0", price=3500.0,
                description="Цилиндровый замок эконом-класса", has_cylinder=True, price_list_id=base_pl.id),
            HardwareItem(type="Ручка", name="Hoppe Barcelona F9", price=1800.0,
                description="Нажимная ручка, нерж. сталь", price_list_id=base_pl.id),
            HardwareItem(type="Ручка", name="Armadilloenza", price=2200.0,
                description="Ручка скоба из нержавейки", price_list_id=base_pl.id),
            HardwareItem(type="Цилиндровый механизм", name="EVVA 3KS 30/30", price=4200.0,
                description="Высокосекретный цилиндр 3KS", price_list_id=base_pl.id),
            HardwareItem(type="Цилиндровый механизм", name="Cisa Asix PX", price=3800.0,
                description="Электронный цилиндр с кодом", price_list_id=base_pl.id),
            HardwareItem(type="Доводчик", name="DORMA TS93", price=3200.0,
                description="Доводчик для дверей до 120кг", price_list_id=base_pl.id),
            HardwareItem(type="Доводчик", name="Geze TS500", price=2800.0,
                description="Доводчик для дверей до 100кг", price_list_id=base_pl.id),
        ])

        session.add(Counterparty(
            type=CPType.LEGAL, name='ООО "СтальМонтаж"', inn="7712345678", kpp="771201001",
            ogrn="1127746123456", address="г. Москва, ул. Промышленная, д. 15",
            phone="+7 (495) 123-45-67", email="info@stalmont.ru", price_list_id=base_pl.id
        ))
        session.add(Counterparty(
            type=CPType.LEGAL, name='ИП Сидоров А.С.', inn="772501234567", kpp="",
            ogrn="304770123456789", address="Московская обл., г. Подольск, ул. Советская, д. 10",
            phone="+7 (916) 234-56-78", email="sidorov@pochta.ru", price_list_id=base_pl.id
        ))
        session.add(Counterparty(
            type=CPType.NATURAL, name='Петров Иван Петрович', inn="",
            address="г. Тверь, ул. Ленина, д. 25, кв. 10",
            phone="+7 (903) 111-22-33", email=""
        ))

        session.commit()
        logger.info("Демо-данные успешно загружены.")