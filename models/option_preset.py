"""Модели наборов опций (пресетов)."""

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.sqlite import JSON
from db.database import Base


class OptionPreset(Base):
    __tablename__ = "option_preset"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    price_list_id: Mapped[int] = mapped_column(ForeignKey("base_price_list.id"))
    price_list = relationship("BasePriceList", back_populates="presets")