"""Утилиты для сериализации/десериализации данных при Drag & Drop.

Содержит:
- serialize_drag_payload: преобразование данных в строку для MIME
- deserialize_drag_payload: восстановление данных из строки
- reorder_list: переупорядочивание списка с обновлением позиций

Используется для перетаскивания позиций в коммерческих предложениях.
"""

import json
import base64
from typing import Any, Dict, List


def serialize_drag_payload(data: Dict[str, Any]) -> str:
    """Сериализует словарь данных в строку для передачи через QMimeData.

    Использует JSON + Base64 для безопасной передачи специальных символов
    через буфер обмена Qt.

    Args:
        data: словарь с данными для передачи

    Returns:
        Строка, закодированная в Base64
    """
    json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return base64.b64encode(json_bytes).decode("utf-8")


def deserialize_drag_payload(payload: str) -> Dict[str, Any]:
    """Восстанавливает словарь данных из строки MIME.

    Args:
        payload: строка, закодированная в Base64

    Returns:
        Восстановленный словарь

    Raises:
        ValueError: при некорректных данных
    """
    try:
        json_bytes = base64.b64decode(payload.encode("utf-8"))
        return json.loads(json_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Некорректные данные Drag & Drop: {e}")


def reorder_list(items: List[Dict[str, Any]], from_index: int, to_index: int) -> List[Dict[str, Any]]:
    """Безопасное перемещение элемента в списке с обновлением поля 'position'.

    Перемещает элемент с одной позиции на другую и пересчитывает
    порядковые номера (position) для всех элементов.

    Args:
        items: список элементов с полем 'position'
        from_index: исходный индекс элемента
        to_index: целевой индекс элемента

    Returns:
        Новый список с обновлёнными позициями

    Example:
        items = [{"id": 1, "position": 1}, {"id": 2, "position": 2}, {"id": 3, "position": 3}]
        reorder_list(items, 0, 2) -> [{"id": 2, "position": 1}, {"id": 3, "position": 2}, {"id": 1, "position": 3}]
    """
    if not items or from_index == to_index:
        return items

    item = items.pop(from_index)
    items.insert(to_index, item)

    for idx, itm in enumerate(items):
        itm["position"] = idx + 1

    return items