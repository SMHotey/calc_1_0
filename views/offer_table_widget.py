"""Кастомный виджет таблицы коммерческих предложений с Drag & Drop."""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QPoint
import json


class OfferTableWidget(QTableWidget):
    """
    Таблица позиций КП.

    Поддерживает:
    - Внутренний Drag & Drop для смены порядка
    - Сигналы для синхронизации с контроллером
    - Контекстное меню
    """
    items_reordered = pyqtSignal(int, int)
    item_removed = pyqtSignal(int)
    add_position_requested = pyqtSignal()
    item_double_clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._setup_signals()

    def _init_ui(self):
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(
            ["№", "Изделие", "Тип", "Размеры (ШxВ)", "Кол-во", "Цена ед.", "Наценка", "Итого"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Drag & Drop настройки
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.viewport().setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def _setup_signals(self):
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.cellDoubleClicked.connect(self._on_cell_double_click)

    def mimeData(self, indexes):
        mime = QMimeData()
        if not indexes:
            return mime
        row = indexes[0].row()
        # Храним строку и внутренний ID позиции
        payload = json.dumps({"row": row}).encode("utf-8")
        mime.setData("application/x-offer-item", payload)
        return mime

    def dropEvent(self, event):
        if event.source() == self:
            mime_data = event.mimeData()
            if mime_data.hasFormat("application/x-offer-item"):
                try:
                    data = json.loads(mime_data.data("application/x-offer-item").decode("utf-8"))
                    from_row = data["row"]
                    drop_row = self.rowAt(event.position().toPoint().y())

                    if drop_row == -1:
                        drop_row = self.rowCount() - 1
                    if from_row != drop_row:
                        if from_row < drop_row:
                            drop_row -= 1
                        self._move_row(from_row, drop_row)
                        self.items_reordered.emit(from_row, drop_row)
                        event.accept()
                        return
                except Exception:
                    pass
        super().dropEvent(event)

    def _move_row(self, from_row: int, to_row: int):
        count = self.columnCount()
        row_content = []
        for c in range(count):
            item = self.item(from_row, c)
            row_content.append({
                "text": item.text() if item else "",
                "alignment": item.textAlignment() if item else Qt.AlignmentFlag.AlignCenter
            })

        self.removeRow(from_row)
        if to_row > from_row:
            to_row -= 1

        self.insertRow(to_row)
        for c, content in enumerate(row_content):
            new_item = QTableWidgetItem(content["text"])
            new_item.setTextAlignment(content["alignment"])
            self.setItem(to_row, c, new_item)

        self.update_row_numbers()

    def update_row_numbers(self):
        for r in range(self.rowCount()):
            self.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.item(r, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def _show_context_menu(self, pos: QPoint):
        item = self.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction("➕ Добавить позицию").triggered.connect(lambda: self.add_position_requested.emit())
        menu.addAction("🗑️ Удалить позицию").triggered.connect(lambda: self.item_removed.emit(item.row()))
        menu.exec(self.mapToGlobal(pos))

    def _on_cell_double_click(self, row: int, col: int):
        """Эмитирует данные позиции при двойном клике для редактирования."""
        data = {}
        for c in range(1, self.columnCount()):
            it = self.item(row, c)
            if it:
                key = self.horizontalHeaderItem(c).text()
                data[key] = it.text()
        self.item_double_clicked.emit(data)

    def append_position(self, item_data: dict):
        """Добавляет строку позиции из данных контроллера."""
        row = self.rowCount()
        self.insertRow(row)
        mappings = [
            ("product_type", 1), ("subtype", 2),
            ("width", 3, lambda d: f"{int(d['width'])}x{int(d['height'])}"),
            ("quantity", 4), ("base_price", 5, lambda d: f"{d['base_price']:,.2f} ₽"),
            ("markup_pct", 6, lambda d: f"{d['markup_pct']}% + {d['markup_abs']:,.2f} ₽"),
            ("final_price", 7, lambda d: f"{d['final_price']:,.2f} ₽")
        ]
        self.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        for key, col, *fmt in mappings:
            val = item_data.get(key, "")
            txt = fmt[0](item_data) if fmt else str(val)
            self.setItem(row, col, QTableWidgetItem(txt))
            self.item(row, col).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scrollToBottom()