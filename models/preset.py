"""РњРѕРґРµР»СЊ РїСЂРµСЃРµС‚Р°: РЅР°Р±РѕСЂ РѕРїС†РёР№ РґР»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РїСЂРёРјРµРЅРµРЅРёСЏ Рє РёР·РґРµР»РёСЏРј.

РЎРѕРґРµСЂР¶РёС‚:
- Preset: РјРѕРґРµР»СЊ РґР»СЏ С…СЂР°РЅРµРЅРёСЏ РЅР°Р±РѕСЂРѕРІ РѕРїС†РёР№ (С†РІРµС‚, РјРµС‚Р°Р»Р» Рё С‚.Рґ.)
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
import json


class Preset(Base):
    """РџСЂРµСЃРµС‚ - РЅР°Р±РѕСЂ РѕРїС†РёР№ РґР»СЏ Р±С‹СЃС‚СЂРѕРіРѕ РїСЂРёРјРµРЅРµРЅРёСЏ."""

    __tablename__ = 'presets'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price_list_id = Column(Integer, ForeignKey('price_lists.id'))
    options_data = Column(Text)  # JSON-СЃС‚СЂРѕРєР° СЃ РѕРїС†РёСЏРјРё

    # РЎРІСЏР·СЊ СЃ РїСЂР°Р№СЃ-Р»РёСЃС‚РѕРј (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ, РґР»СЏ СѓРґРѕР±СЃС‚РІР°)
    price_list = relationship("PriceList", back_populates="presets")

    def __repr__(self):
        return f"<Preset(id={self.id}, name='{self.name}', price_list_id={self.price_list_id})>"

    def get_options_dict(self):
        """Р’РѕР·РІСЂР°С‰Р°РµС‚ РѕРїС†РёРё РєР°Рє СЃР»РѕРІР°СЂСЊ.
        
        Returns:
            dict: СЃР»РѕРІР°СЂСЊ РѕРїС†РёР№, РЅР°РїСЂРёРјРµСЂ {"color": "RAL 7035", "metal": "1.5-1.5"}
        """
        if self.options_data:
            try:
                return json.loads(self.options_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
