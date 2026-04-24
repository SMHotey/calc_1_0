"""Вкладка 'Контрагенты'. Управление списком контрагентов и их документами.

Содержит:
- CounterpartiesTab: вкладка для управления контрагентами
- Показывает список контрагентов и их документы
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QLineEdit, QLabel, QSplitter, QFrame
)
from PyQt6.QtCore import Qt
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from controllers.counterparty_controller import CounterpartyController
    from controllers.document_controller import DocumentController

from views.dialogs.counterparty_dialog import CounterpartyDialog
from views.documents_widget import DocumentsWidget
from constants import CounterpartyType


class CounterpartiesTab(QWidget):
    """Вкладка 'Контрагенты' - управление списком клиентов, поставщиков, партнёров.

    Позволяет добавлять, редактировать, удалять контрагентов.
    Поддерживает поиск по имени, ИНН, телефону.
    Показывает документы выбранного контрагента.
    """

    def __init__(self, cpa_ctrl: "CounterpartyController", doc_ctrl: "DocumentController" = None, contacts_ctrl = None):
        """Инициализация вкладки контрагентов.

        Args:
            cpa_ctrl: контроллер контрагентов
            doc_ctrl: контроллер документов (опционально)
            contacts_ctrl: контроллер контактных лиц (опционально)
        """
        super().__init__()
        self.cpa_ctrl = cpa_ctrl
        self.doc_ctrl = doc_ctrl
        self.contacts_ctrl = contacts_ctrl
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Поиск
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по имени, ИНН, телефону...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()
        main_layout.addLayout(search_layout)

        # Сплиттер: список контрагентов + детали с документами
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая панель - список контрагентов
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("Список контрагентов"))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Тип", "Название", "ИНН", "Телефон", "Прайс-лист"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemClicked.connect(self._on_row_clicked)
        self.table.itemDoubleClicked.connect(self._edit_selected)
        
        # Настраиваем ширину столбцов - Название растягивается
        self.table.setColumnWidth(0, 50)   # Тип
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 0)   # Название (будет растянуто)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 100)  # ИНН
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 110)  # Телефон
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 50)  # Прайс-лист
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        left_layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_new = QPushButton("➕ Добавить")
        btn_new.clicked.connect(self._add_new)
        btn_layout.addWidget(btn_new)

        btn_delete = QPushButton("🗑️ Удалить")
        btn_delete.clicked.connect(self._delete_selected)
        btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_widget)

        # Правая панель - документы контрагента
        self.docs_widget = QWidget()
        docs_layout = QVBoxLayout(self.docs_widget)

        if self.doc_ctrl:
            self.docs_container = DocumentsWidget(self.doc_ctrl, counterparty_id=None)
            docs_layout.addWidget(QLabel("📄 Документы контрагента"))
            docs_layout.addWidget(self.docs_container)
        else:
            docs_layout.addWidget(QLabel("📄 Документы контрагента"))
            docs_layout.addWidget(QLabel("Документы будут доступны после инициализации контроллера."))

        splitter.addWidget(self.docs_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

    def _load_data(self):
        self.table.setRowCount(0)
        try:
            for cp in self.cpa_ctrl.get_all():
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Тип (сокращаем: Юридическое лицо -> ЮЛ, Физическое лицо -> ФЛ)
                type_str = cp.type.value if hasattr(cp.type, 'value') else str(cp.type)
                if type_str == "Юридическое лицо":
                    type_str = "ЮЛ"
                elif type_str == "Физическое лицо":
                    type_str = "ФЛ"
                item_type = QTableWidgetItem(type_str)
                item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
                self.table.setItem(row, 0, item_type)
                
                # Название
                item_name = QTableWidgetItem(cp.name)
                self.table.setItem(row, 1, item_name)
                
                # ИНН
                item_inn = QTableWidgetItem(cp.inn or "-")
                self.table.setItem(row, 2, item_inn)
                
                # Телефон
                item_phone = QTableWidgetItem(cp.phone)
                self.table.setItem(row, 3, item_phone)
                
                # Прайс-лист (уменьшенная ширина)
                price_list_str = "Базовый" if not cp.price_list_id else "Перс."
                item_price = QTableWidgetItem(price_list_str)
                item_price.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
                self.table.setItem(row, 4, item_price)
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
                
                # Тип (сокращаем)
                type_str = cp.type.value if hasattr(cp.type, 'value') else str(cp.type)
                if type_str == "Юридическое лицо":
                    type_str = "ЮЛ"
                elif type_str == "Физическое лицо":
                    type_str = "ФЛ"
                item_type = QTableWidgetItem(type_str)
                item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
                self.table.setItem(row, 0, item_type)
                
                self.table.setItem(row, 1, QTableWidgetItem(cp.name))
                self.table.setItem(row, 2, QTableWidgetItem(cp.inn or "-"))
                self.table.setItem(row, 3, QTableWidgetItem(cp.phone))
                
                price_list_str = "Базовый" if not cp.price_list_id else "Перс."
                item_price = QTableWidgetItem(price_list_str)
                item_price.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
                self.table.setItem(row, 4, item_price)
        except Exception:
            pass

    def _on_row_clicked(self, item: QTableWidgetItem):
        """Обрабатывает клик по строке - показывает документы контрагента."""
        row = item.row()
        # Название контрагента во втором столбце
        cp_name = self.table.item(row, 1).text()
        
        # Находим контрагента по имени
        counterparties = self.cpa_ctrl.search(cp_name)
        if not counterparties:
            return
        cp = counterparties[0]
        cp_id = cp.id

        if self.doc_ctrl and hasattr(self, 'docs_container'):
            self.docs_container.counterparty_id = cp_id
            self.docs_container.deal_id = None
            self.docs_container.refresh()

    def _add_new(self):
        dialog = CounterpartyDialog(self.cpa_ctrl, None, self)
        if self.contacts_ctrl:
            dialog.init_contacts_widget(self.contacts_ctrl)
        if self.doc_ctrl:
            dialog.init_documents_widget(self.doc_ctrl)
        if dialog.exec():
            self._load_data()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите контрагента для редактирования.")
            return
        # Название контрагента
        cp_name = self.table.item(row, 1).text()
        
        # Находим контрагента по имени
        counterparties = self.cpa_ctrl.search(cp_name)
        if not counterparties:
            return
        cp_id = counterparties[0].id
        
        dialog = CounterpartyDialog(self.cpa_ctrl, cp_id, self)
        if self.contacts_ctrl:
            dialog.init_contacts_widget(self.contacts_ctrl)
        if self.doc_ctrl:
            dialog.init_documents_widget(self.doc_ctrl)
        if dialog.exec():
            self._load_data()
            # Обновляем документы
            if self.doc_ctrl and hasattr(self, 'docs_container'):
                self.docs_container.refresh()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите контрагента для удаления.")
            return
        # Название контрагента
        cp_name = self.table.item(row, 1).text()
        
        # Находим контрагента по имени
        counterparties = self.cpa_ctrl.search(cp_name)
        if not counterparties:
            return
        cp_id = counterparties[0].id
        
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить контрагента '{cp_name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            result = self.cpa_ctrl.delete(cp_id)
            if result["success"]:
                self._load_data()
                QMessageBox.information(self, "Успех", "Контрагент удалён.")
            else:
                QMessageBox.warning(self, "Ошибка", result["error"])