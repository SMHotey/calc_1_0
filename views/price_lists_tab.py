"""Вкладка 'Прайс-листы'. Управление базовым и персонализированными прайс-листами."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from controllers.price_list_controller import PriceListController
from views.dialogs.price_list_dialog import PriceListDialog
from views.dialogs.glass_dialog import GlassManagementDialog
from views.dialogs.hardware_dialog import HardwareDialog


class PriceListsTab(QWidget):
    def __init__(self, price_list_ctrl: PriceListController):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        btn_new = QPushButton("Создать персонализированный прайс")
        btn_new.clicked.connect(self._create_personalized)
        btn_edit = QPushButton("Редактировать выбранный")
        btn_edit.clicked.connect(self._edit_selected)
        btn_glass = QPushButton("Управление стёклами")
        btn_glass.clicked.connect(self._manage_glass)
        btn_hardware = QPushButton("Управление фурнитурой")
        btn_hardware.clicked.connect(self._manage_hardware)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_edit)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_glass)
        btn_layout.addWidget(btn_hardware)
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Тип", "Цена (дверь)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self._edit_selected)
        layout.addWidget(self.table)

    def _load_data(self):
        self.table.setRowCount(0)
        try:
            base = self.price_list_ctrl.get_base_price_list()
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(base.id)))
            self.table.setItem(row, 1, QTableWidgetItem(base.name))
            self.table.setItem(row, 2, QTableWidgetItem("Базовый"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{base.doors_price_std_single:,.2f} ₽"))

            for pl in self.price_list_ctrl.get_personalized_lists():
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(pl.id)))
                self.table.setItem(row, 1, QTableWidgetItem(pl.name))
                self.table.setItem(row, 2, QTableWidgetItem("Персонализированный"))
                price = pl.custom_doors_price_std_single or base.doors_price_std_single
                self.table.setItem(row, 3, QTableWidgetItem(f"{price:,.2f} ₽"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить прайс-листы:\n{e}")

    def _create_personalized(self):
        dialog = PriceListDialog(self.price_list_ctrl)
        if dialog.exec():
            self._load_data()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите прайс-лист для редактирования.")
            return
        pl_id = int(self.table.item(row, 0).text())
        pl_type = self.table.item(row, 2).text()
        if pl_type == "Базовый":
            QMessageBox.information(self, "Информация", "Базовый прайс-лист доступен только для просмотра.")
            return
        dialog = PriceListDialog(self.price_list_ctrl, pl_id)
        if dialog.exec():
            self._load_data()

    def _manage_glass(self):
        try:
            base = self.price_list_ctrl.get_base_price_list()
            from controllers.options_controller import OptionsController
            ctrl = OptionsController()
            dialog = GlassManagementDialog(ctrl, base.id, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть:\n{e}")

    def _manage_hardware(self):
        try:
            base = self.price_list_ctrl.get_base_price_list()
            from controllers.hardware_controller import HardwareController
            ctrl = HardwareController()
            dialog = HardwareDialog(ctrl, base.id, None, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть:\n{e}")
