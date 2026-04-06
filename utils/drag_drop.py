"""Утилиты для сериализации/десериализации данных при Drag & Drop."""

import json
import base64
from typing import Any, Dict, List


def serialize_drag_payload(data: Dict[str, Any]) -> str:
    """
    Сериализует словарь данных в строку для передачи через QMimeData.
    Использует JSON + Base64 для безопасной передачи специальных символов.
    """
    json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return base64.b64encode(json_bytes).decode("utf-8")


def deserialize_drag_payload(payload: str) -> Dict[str, Any]:
    """Восстанавливает словарь данных из строки MIME."""
    try:
        json_bytes = base64.b64decode(payload.encode("utf-8"))
        return json.loads(json_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Некорректные данные Drag & Drop: {e}")


def reorder_list(items: List[Dict[str, Any]], from_index: int, to_index: int) -> List[Dict[str, Any]]:
    """
    Безопасное перемещение элемента в списке с обновлением поля 'position'.
    """
    if not items or from_index == to_index:
        return items

    item = items.pop(from_index)
    items.insert(to_index, item)

    for idx, itm in enumerate(items):
        itm["position"] = idx + 1

    return items