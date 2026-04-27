"""Кастомный виджет таблицы коммерческих предложений с Drag & Drop."""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMenu
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal, QPoint
import json


class OfferTableWidget(QTableWidget):
    """
    Таблица позиций КП (идентична таблице на вкладке Калькулятор).

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
        # 5 столбцов как в калькуляторе: Марка, Изделие, Размеры, Кол-во, Комплектация
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Марка", "Изделие", "Размеры", "Кол-во", "Комплектация"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        # Настройка ширины столбцов: Марка * 0.6 = 30, Изделие * 1.35 = 189, Размеры * 0.8 = 56, Кол-во * 0.5 = 23
        self.setColumnWidth(0, 30)     # Марка
        self.setColumnWidth(1, 189)   # Изделие
        self.setColumnWidth(2, 56)     # Размеры (ВxШ)
        self.setColumnWidth(3, 23)     # Кол-во

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
        for c in range(self.columnCount()):
            it = self.item(row, c)
            if it:
                key = self.horizontalHeaderItem(c).text()
                data[key] = it.text()
        self.item_double_clicked.emit(data)

    def append_position(self, item_data: dict, item_id: int = None):
        """Добавляет строку позиции из данных контроллера.

        Args:
            item_data: словарь с данными позиции
            item_id: ID позиции в БД (для редактирования) — хранится в UserRole
        """
        row = self.rowCount()
        self.insertRow(row)
        row_data_for_user_role = {"item_id": item_id, **item_data}
        
        # Марка (column 0)
        mark = item_data.get("mark", "-")
        self.setItem(row, 0, QTableWidgetItem(mark))
        self.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Изделие (column 1)
        product_type = item_data.get("product_type", "-")
        subtype = item_data.get("subtype", "-")
        product_text = f"{product_type} {subtype}" if subtype else product_type
        self.setItem(row, 1, QTableWidgetItem(product_text))
        self.item(row, 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Размеры (column 2) - формат "ВxШ" (высота x ширина)
        width = item_data.get("width", 0)
        height = item_data.get("height", 0)
        size_text = f"{int(height)}x{int(width)}"
        self.setItem(row, 2, QTableWidgetItem(size_text))
        self.item(row, 2).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Кол-во (column 3)
        quantity = item_data.get("quantity", 1)
        self.setItem(row, 3, QTableWidgetItem(str(quantity)))
        self.item(row, 3).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Комплектация (column 4) - собираем описание оборудования
        comp_parts = []
        
        # Цвета
        ext_color = item_data.get("color_external", "")
        int_color = item_data.get("color_internal", "")
        if ext_color:
            comp_parts.append(f"RAL нар: {ext_color}")
        if int_color:
            comp_parts.append(f"RAL вн: {int_color}")
        
        # Металл
        metal = item_data.get("metal_thickness", "")
        if metal:
            comp_parts.append(f"Металл: {metal}")
        
        # Дополнительные опции
        extra = item_data.get("extra_options", {})
        if extra.get("threshold"):
            comp_parts.append("Автопорог")
        if extra.get("anti_theft_pins"):
            comp_parts.append("Противосъёмные штыри")
        if extra.get("gkl"):
            comp_parts.append("ГКЛ наполнение")
        if extra.get("mount_ears_count"):
            comp_parts.append(f"Монтажные уши: {extra.get('mount_ears_count')}")
        if extra.get("deflector"):
            deflector_text = "Отбойная пластина"
            if extra.get("deflector_double_side"):
                deflector_text += " (2-х сторон)"
            if extra.get("deflector_height"):
                deflector_text += f" {extra.get('deflector_height')}мм"
            comp_parts.append(deflector_text)
        
        # Петли
        is_double = item_data.get("is_double_leaf", False)
        if is_double:
            hinge_active = extra.get("hinge_count_active", 0)
            hinge_passive = extra.get("hinge_count_passive", 0)
            if hinge_active or hinge_passive:
                comp_parts.append(f"Петли: акт={hinge_active}, пасс={hinge_passive}")
        else:
            hinge_count = extra.get("hinge_count_active", 0)
            if hinge_count:
                comp_parts.append(f"Петли: {hinge_count}")
        
        # Фурнитура
        hw_items = item_data.get("hardware_items", [])
        for hw in hw_items:
            hw_lower = hw.lower() if isinstance(hw, str) else ""
            if "замок" in hw_lower:
                if ":" in hw:
                    comp_parts.append(f"замок: {hw.split(':', 1)[1].strip()}")
                else:
                    comp_parts.append(f"замок: {hw}")
            elif "ручк" in hw_lower:
                if ":" in hw:
                    comp_parts.append(f"ручка: {hw.split(':', 1)[1].strip()}")
                else:
                    comp_parts.append(f"ручка: {hw}")
            else:
                if ":" in hw:
                    comp_parts.append(hw.split(":", 1)[1].strip())
                else:
                    comp_parts.append(hw)
        
        # Доводчики
        if extra.get("closer1"):
            comp_parts.append("Доводчик 1")
        if extra.get("closer2"):
            comp_parts.append("Доводчик 2")
        if extra.get("coordinator"):
            comp_parts.append("Координатор")
        
        # Стекла
        glass_items = item_data.get("glass_items_display", item_data.get("glass_items", []))
        for glass in glass_items:
            glass_name = glass.get("glass_type_name", "")
            if glass_name:
                opts = glass.get("options", [])
                if opts:
                    opt_names = ", ".join([o.get("name", "") for o in opts])
                    comp_parts.append(f"{glass_name} ({opt_names})")
                else:
                    comp_parts.append(glass_name)
        
        # Цветовые опции
        color_opts = item_data.get("color_options", {})
        if color_opts.get("moire"):
            comp_parts.append("Муар")
        if color_opts.get("lac"):
            comp_parts.append("Лак")
        if color_opts.get("primer"):
            comp_parts.append("Грунт")
        
        # Если нет комплектации, ��оказываем прочерк
        comp_str = ", ".join(comp_parts) if comp_parts else "-"
        
        comp_item = QTableWidgetItem(comp_str)
        comp_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setItem(row, 4, comp_item)

        self.scrollToBottom()

    def update_mark_column_visibility(self):
        """Скрыть столбец Марка, если во всех строках значение пустое."""
        has_mark = False
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and item.text().strip():
                has_mark = True
                break
        # Скрываем или показываем столбец Марка (column 0)
        self.setColumnHidden(0, not has_mark)