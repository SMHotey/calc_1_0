"""Валидация габаритов и параметров изделия согласно правилам п.4.

Содержит:
- validate_dimensions: проверка допустимости размеров для каждого типа изделия

Правила валидации:
- Дверь: высота 1500-2490 мм, ширина 500-2390 мм
- Люк: мин. 300×300, макс. 1490×1490 мм
- Ворота: макс. 6000×6000 мм
- Фрамуга: мин. высота 200 мм, мин. ширина 400 мм
"""

from typing import Tuple
from constants import (
    PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM
)


def validate_dimensions(product_type: str, height: float, width: float) -> Tuple[bool, str]:
    """Проверяет допустимость размеров для выбранного вида изделия.

    Args:
        product_type: Вид изделия (Дверь, Люк, Ворота, Фрамуга)
        height: Высота в мм
        width: Ширина в мм

    Returns:
        Кортеж (успех, сообщение об ошибке):
        - (True, "") - размеры корректны
        - (False, "сообщение") - размеры некорректны, возвращается причина

    Ограничения по типам:
        - Дверь: высота 1500-2490 мм, ширина 500-2390 мм
        - Люк: мин. 300×300 мм, макс. 1490×1490 мм
        - Ворота: макс. 6000×6000 мм
        - Фрамуга: мин. высота 200 мм, мин. ширина 400 мм
    """
    if height <= 0 or width <= 0:
        return False, "Размеры должны быть положительными числами."

    h, w = height, width

    if product_type == PRODUCT_DOOR:
        if h < 1500 or h > 2490:
            return False, "Дверь: высота должна быть от 1500 до 2490 мм."
        if w < 500 or w > 2390:
            return False, "Дверь: ширина должна быть от 500 до 2390 мм."

    elif product_type == PRODUCT_HATCH:
        if h < 300 or w < 300:
            return False, "Люк: минимальные размеры 300x300 мм."
        if h >= 1500 or w >= 1500:
            return False, "Люк: максимальные размеры 1490x1490 мм."

    elif product_type == PRODUCT_GATE:
        if h <= 0 or w <= 0:
            return False, "Ворота: недопустимые размеры."
        if h > 6000 or w > 6000:
            return False, "Ворота: максимальные габариты 6000x6000 мм."

    elif product_type == PRODUCT_TRANSOM:
        if h < 200:
            return False, "Фрамуга: минимальная высота 200 мм."
        if w < 400:
            return False, "Фрамуга: минимальная ширина 400 мм."

    return True, ""