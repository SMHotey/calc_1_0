"""Модели опций позиций КП.

Содержит ORM-модели для хранения опций позиций КП в виде отдельных таблиц:
- OfferItemGlass: стекло с его опциями (inline JSON)
- OfferItemVent: вентиляционная решётка
- OfferItemLock: замок
- OfferItemHandle: ручка
- OfferItemCylinder: цилиндр
- OfferItemCloser: доводчик
- OfferItemCoordinator: координатор

Каждая модель содержит метод get_prices() для dual-price расчёта.
"""

from sqlalchemy import String, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base


class OfferItemGlass(Base):
    """Стекло в позиции КП.
    
    Хранит стекло с его опциями (inline в таблице). Для стёкол с
    множественными опциями (типпрофиля, заполнения, etc) используется
    JSON-поле options_data.
    
    Attributes:
        id: уникальный идентификатор
        offer_item_id: ссылка на позицию КП
        quantity: количество стёкол
        glass_type: тип стекла (из справочника)
        width, height: размеры в мм
        options_data: JSON с опциями стекла
        short_name_kp: сокращённое название для КП
        short_name_prod: сокращённое название для производства
        base_price: базовая цена из прайса
        current_price: текущая цена (с учётом наценок)
        offer_item: родительская позиция
    """
    __tablename__ = "offer_item_glass"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_item_id: Mapped[int] = mapped_column(ForeignKey("offer_item.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    glass_type: Mapped[str] = mapped_column(String(100))
    width: Mapped[float]
    height: Mapped[float]
    options_data: Mapped[dict] = mapped_column(JSON, default=dict)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float]
    current_price: Mapped[float]
    
    offer_item = relationship("OfferItem", back_populates="glasses")
    
    def get_prices(self) -> tuple[float, float]:
        """Возвращает кортеж (базовая цена, текущая цена).
        
        Returns:
            tuple: (base_price, current_price)
        """
        return (self.base_price, self.current_price)


class OfferItemVent(Base):
    """Вентиляционная решётка в позиции КП.
    
    Attributes:
        id: уникальный идентификатор
        offer_item_id: ссылка на позицию КП
        quantity: количество решёток
        vent_type_id: ссылка на тип в прайсе
        short_name_kp: сокращённое название для КП
        short_name_prod: сокращённое название для производства
        base_price: базовая цена из прайса
        current_price: текущая цена (с учётом наценок)
        offer_item: родительская позиция
    """
    __tablename__ = "offer_item_vent"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_item_id: Mapped[int] = mapped_column(ForeignKey("offer_item.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    vent_type_id: Mapped[int | None] = mapped_column(ForeignKey("vent_type.id"), nullable=True)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float]
    current_price: Mapped[float]
    
    offer_item = relationship("OfferItem", back_populates="vents")
    
    def get_prices(self) -> tuple[float, float]:
        """Возвращает кортеж (базовая цена, текущая цена).
        
        Returns:
            tuple: (base_price, current_price)
        """
        return (self.base_price, self.current_price)


class OfferItemLock(Base):
    """Замок в позиции КП.
    
    Attributes:
        id: уникальный идентификатор
        offer_item_id: ссылка на позицию КП
        quantity: количество замков
        lock_id: ссылка на замок в прайсе
        short_name_kp: сокращённое название для КП
        short_name_prod: сокращённое название для производства
        base_price: базовая цена из прайса
        current_price: текущая цена (с учётом наценок)
        offer_item: родительская позиция
    """
    __tablename__ = "offer_item_lock"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_item_id: Mapped[int] = mapped_column(ForeignKey("offer_item.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    lock_id: Mapped[int | None] = mapped_column(ForeignKey("hardware_item.id"), nullable=True)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float]
    current_price: Mapped[float]
    
    offer_item = relationship("OfferItem", back_populates="locks")
    
    def get_prices(self) -> tuple[float, float]:
        """Возвращает кортеж (базовая цена, текущая цена).
        
        Returns:
            tuple: (base_price, current_price)
        """
        return (self.base_price, self.current_price)


class OfferItemHandle(Base):
    """Ручка в позиции КП.
    
    Attributes:
        id: уникальный идентификатор
        offer_item_id: ссылка на позицию КП
        quantity: количество ручек
        handle_id: ссылка на ручку в прайсе
        short_name_kp: сокращённое название для КП
        short_name_prod: сокращённое название для производства
        base_price: базовая цена из прайса
        current_price: текущая цена (с учётом наценок)
        offer_item: родительская позиция
    """
    __tablename__ = "offer_item_handle"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_item_id: Mapped[int] = mapped_column(ForeignKey("offer_item.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    handle_id: Mapped[int | None] = mapped_column(ForeignKey("hardware_item.id"), nullable=True)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float]
    current_price: Mapped[float]
    
    offer_item = relationship("OfferItem", back_populates="handles")
    
    def get_prices(self) -> tuple[float, float]:
        """Возвращает кортеж (базовая цена, текущая цена).
        
        Returns:
            tuple: (base_price, current_price)
        """
        return (self.base_price, self.current_price)


class OfferItemCylinder(Base):
    """Цилиндр в позиции КП.
    
    Attributes:
        id: уникальный идентификатор
        offer_item_id: ссылка на позицию КП
        quantity: количество цилиндров
        cylinder_id: ссылка на цилиндр в прайсе
        short_name_kp: сокращённое название для КП
        short_name_prod: сокращённое название для производства
        base_price: базовая цена из прайса
        current_price: текущая цена (с учётом наценок)
        offer_item: родительская позиция
    """
    __tablename__ = "offer_item_cylinder"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_item_id: Mapped[int] = mapped_column(ForeignKey("offer_item.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    cylinder_id: Mapped[int | None] = mapped_column(ForeignKey("hardware_item.id"), nullable=True)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float]
    current_price: Mapped[float]
    
    offer_item = relationship("OfferItem", back_populates="cylinders")
    
    def get_prices(self) -> tuple[float, float]:
        """Возвращает кортеж (базовая цена, текущая цена).
        
        Returns:
            tuple: (base_price, current_price)
        """
        return (self.base_price, self.current_price)


class OfferItemCloser(Base):
    """Доводчик в позиции КП.
    
    Attributes:
        id: уникальный идентификатор
        offer_item_id: ссылка на позицию КП
        quantity: количество доводчиков
        closer_id: ссылка на доводчик в прайсе
        short_name_kp: сокращённое название для КП
        short_name_prod: сокращённое название для производства
        base_price: базовая цена из прайса
        current_price: текущая цена (с учётом наценок)
        offer_item: родительская позиция
    """
    __tablename__ = "offer_item_closer"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_item_id: Mapped[int] = mapped_column(ForeignKey("offer_item.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    closer_id: Mapped[int | None] = mapped_column(ForeignKey("closer.id"), nullable=True)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float]
    current_price: Mapped[float]
    
    offer_item = relationship("OfferItem", back_populates="closers")
    
    def get_prices(self) -> tuple[float, float]:
        """Возвращает кортеж (базовая цена, текущая цена).
        
        Returns:
            tuple: (base_price, current_price)
        """
        return (self.base_price, self.current_price)


class OfferItemCoordinator(Base):
    """Координатор в позиции КП.
    
    Attributes:
        id: уникальный идентификатор
        offer_item_id: ссылка на позицию КП
        quantity: количество координаторов
        coordinator_id: ссылка на координатор в прайсе
        short_name_kp: сокращённое название для КП
        short_name_prod: сокращённое название для производства
        base_price: базовая цена из прайса
        current_price: текущая цена (с учётом наценок)
        offer_item: родительская позиция
    """
    __tablename__ = "offer_item_coordinator"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_item_id: Mapped[int] = mapped_column(ForeignKey("offer_item.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    coordinator_id: Mapped[int | None] = mapped_column(ForeignKey("coordinator.id"), nullable=True)
    short_name_kp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    short_name_prod: Mapped[str | None] = mapped_column(String(50), nullable=True)
    base_price: Mapped[float]
    current_price: Mapped[float]
    
    offer_item = relationship("OfferItem", back_populates="coordinators")
    
    def get_prices(self) -> tuple[float, float]:
        """Возвращает кортеж (базовая цена, текущая цена).
        
        Returns:
            tuple: (base_price, current_price)
        """
        return (self.base_price, self.current_price)