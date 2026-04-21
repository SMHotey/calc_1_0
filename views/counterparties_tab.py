"""Вкладка 'Контрагенты'. Управление списком контрагентов.

Содержит:
- CounterpartiesTab: вкладка для управления контрагентами
- CounterpartyDialog: диалог создания/редактирования контрагента
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt
from controllers.counterparty_controller import CounterpartyController
from views.dialogs.counterparty_dialog import CounterpartyDialog


class CounterpartiesTab(QWidget):
    """Вкладка 'Контрагенты' - управление списком клиентов, поставщиков, партнёров.

    Позволяет добавлять, редактировать, удалять контрагентов.
    Поддерживает поиск по имени, ИНН, телефону.
    """

    def __init__(self, cpa_ctrl: CounterpartyController):
        """Инициализация вкладки контрагентов.

        Args:
            cpa_ctrl: контроллер контрагентов
        """
        super().__init__()
        self.cpa_ctrl = cpa_ctrl
        self._init_ui()
        self._load_data()
        self.cpa_ctrl = cpa_ctrl
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени, ИНН, телефону...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        btn_layout = QHBoxLayout()
        btn_new = QPushButton("Добавить контрагента")
        btn_new.clicked.connect(self._add_new)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_selected)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete_selected)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Название", "ИНН", "Телефон", "Прайс-лист"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self._edit_selected)
        layout.addWidget(self.table)

        self._refresh_btn_edit = btn_edit
        self._refresh_btn_delete = btn_delete

    def _load_data(self):
        self.table.setRowCount(0)
        try:
            for cp in self.cpa_ctrl.get_all():
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(cp.id)))
                self.table.setItem(row, 1, QTableWidgetItem(cp.type.value if hasattr(cp.type, 'value') else str(cp.type)))
                self.table.setItem(row, 2, QTableWidgetItem(cp.name))
                self.table.setItem(row, 3, QTableWidgetItem(cp.inn or "-"))
                self.table.setItem(row, 4, QTableWidgetItem(cp.phone))
                self.table.setItem(row, 5, QTableWidgetItem(f"ID: {cp.price_list_id}" if cp.price_list_id else "Базовый"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить контрагентов:\n{e}")

    def _on_search(self, text: str):
        if not text:
            self._load_data()
            return
        self.table.setRowCount(0)
        try:
            for cp in self.cpa_ctrl.search(text):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(cp.id)))
                self.table.setItem(row, 1, QTableWidgetItem(cp.type.value if hasattr(cp.type, 'value') else str(cp.type)))
                self.table.setItem(row, 2, QTableWidgetItem(cp.name))
                self.table.setItem(row, 3, QTableWidgetItem(cp.inn or "-"))
                self.table.setItem(row, 4, QTableWidgetItem(cp.phone))
                self.table.setItem(row, 5, QTableWidgetItem(f"ID: {cp.price_list_id}" if cp.price_list_id else "Базовый"))
        except Exception:
            pass

    def _add_new(self):
        dialog = CounterpartyDialog(self.cpa_ctrl, None, self)
        if dialog.exec():
            self._load_data()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите контрагента для редактирования.")
            return
        cp_id = int(self.table.item(row, 0).text())
        dialog = CounterpartyDialog(self.cpa_ctrl, cp_id, self)
        if dialog.exec():
            self._load_data()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите контрагента для удаления.")
            return
        cp_id = int(self.table.item(row, 0).text())
        cp_name = self.table.item(row, 2).text()
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить контрагента '{cp_name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            result = self.cpa_ctrl.delete(cp_id)
            if result["success"]:
                self._load_data()
                QMessageBox.information(self, "Успех", "Контрагент удалён.")
            else:
                QMessageBox.warning(self, "Ошибка", result["error"])
