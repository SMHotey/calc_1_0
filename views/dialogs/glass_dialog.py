"""Диалог управления типами стёкол и их опциями."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFormLayout, QLineEdit, QDoubleSpinBox, QPushButton, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from typing import Optional
from controllers.options_controller import OptionsController


class GlassManagementDialog(QDialog):
    """Управление типами стёкол и доп. опциями (пленки, матировка) в рамках прайс-листа."""

    def __init__(self, controller: OptionsController, price_list_id: int, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.price_list_id = price_list_id
        self.setWindowTitle("Управление стёклами")
        self.resize(700, 500)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая часть: Таблица стёкол
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Цена/м²", "Мин. цена"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        left_layout.addWidget(self.table)
        splitter.addWidget(left_widget)

        # Правая часть: Форма редактирования
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        form = QFormLayout()
        self.inp_name = QLineEdit()
        self.spin_price = QDoubleSpinBox();
        self.spin_price.setRange(0, 1e6);
        self.spin_price.setPrefix("₽ ")
        self.spin_min = QDoubleSpinBox();
        self.spin_min.setRange(0, 1e6);
        self.spin_min.setPrefix("₽ ")
        form.addRow("Название:", self.inp_name)
        form.addRow("Цена за м²:", self.spin_price)
        form.addRow("Минимальная цена:", self.spin_min)
        right_layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Добавить/Обновить")
        self.btn_add.clicked.connect(self._save_glass)
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_delete.clicked.connect(self._delete_glass)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_delete)
        right_layout.addLayout(btn_layout)
        splitter.addWidget(right_widget)

        main_layout.addWidget(splitter)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        main_layout.addWidget(btn_close)

        self.table.itemSelectionChanged.connect(self._fill_form_from_selection)

    def _load_data(self):
        self.table.setRowCount(0)
        glasses = self.controller.get_glass_types(self.price_list_id)
        for g in glasses:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(g["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(g["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(f"{g['price_per_m2']:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{g['min_price']:.2f}"))

    def _fill_form_from_selection(self):
        items = self.table.selectedItems()
        if not items: return
        r = items[0].row()
        self.inp_name.setText(self.table.item(r, 1).text())
        self.spin_price.setValue(float(self.table.item(r, 2).text()))
        self.spin_min.setValue(float(self.table.item(r, 3).text()))
        self.table.setCurrentCell(r, 0)

    def _save_glass(self):
        if not self.inp_name.text().strip():
            return QMessageBox.warning(self, "Ошибка", "Укажите название стекла.")
        selected = self.table.selectedItems()
        if selected:
            glass_id = int(self.table.item(selected[0].row(), 0).text())
            self.controller.update_glass_type(glass_id, {
                "name": self.inp_name.text(),
                "price_per_m2": self.spin_price.value(),
                "min_price": self.spin_min.value()
            })
        else:
            self.controller.create_glass_type(
                self.inp_name.text(), self.spin_price.value(),
                self.spin_min.value(), self.price_list_id
            )
        self._load_data()
        QMessageBox.information(self, "Успех", "Стекло сохранено.")

    def _delete_glass(self):
        selected = self.table.selectedItems()
        if not selected: return
        glass_id = int(self.table.item(selected[0].row(), 0).text())
        if QMessageBox.question(self, "Подтверждение",
                                "Удалить тип стекла? Связанные опции будут удалены.") == QMessageBox.StandardButton.Yes:
            self.controller.delete_glass_type(glass_id)
            self._load_data()