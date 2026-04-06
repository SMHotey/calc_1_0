"""Вкладка 'Наборы опций'. Управление пресетами конфигураций."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt
from controllers.preset_controller import PresetController
from controllers.price_list_controller import PriceListController


class PresetsTab(QWidget):
    def __init__(self, preset_ctrl: PresetController, price_list_ctrl: PriceListController):
        super().__init__()
        self.preset_ctrl = preset_ctrl
        self.price_list_ctrl = price_list_ctrl
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("Применить выбранный пресет")
        btn_apply.clicked.connect(self._apply_selected)
        btn_delete = QPushButton("Удалить выбранный")
        btn_delete.clicked.connect(self._delete_selected)
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Прайс-лист"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        self.current_price_list_id = None

    def _set_price_list(self, price_list_id: int):
        self.current_price_list_id = price_list_id
        self._load_data()

    def _load_data(self):
        self.table.setRowCount(0)
        if not self.current_price_list_id:
            self.table.setItem(0, 0, QTableWidgetItem("Выберите контрагента с персональным прайс-листом"))
            return
        try:
            for preset in self.preset_ctrl.get_presets_for_price_list(self.current_price_list_id):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(preset["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(preset["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(f"ID: {self.current_price_list_id}"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пресеты:\n{e}")

    def _apply_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите пресет для применения.")
            return
        QMessageBox.information(self, "Информация", 
            "Применение пресета происходит через вкладку 'Калькулятор'.")

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите пресет для удаления.")
            return
        preset_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранный набор опций?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.preset_ctrl.delete_preset(preset_id):
                self._load_data()
                QMessageBox.information(self, "Успех", "Пресет удалён.")
