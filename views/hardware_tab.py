"""Вкладка 'Фурнитура'. Управление элементами фурнитуры с ценами из прайса."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QLabel, QComboBox, QDialog, QFormLayout, 
    QLineEdit, QDoubleSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt
from controllers.hardware_controller import HardwareController
from controllers.price_list_controller import PriceListController
from constants import HardwareType


class HardwareEditDialog(QDialog):
    """Диалог добавления/редактирования фурнитуры."""
    
    def __init__(self, item: dict = None):
        super().__init__()
        self.item = item
        self.setWindowTitle("Редактирование фурнитуры" if item else "Новая фурнитура")
        self.resize(400, 350)
        self._init_ui()
        if item:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.combo_type = QComboBox()
        for t in HardwareType:
            self.combo_type.addItem(t.value, t.value)
        form.addRow("Тип:", self.combo_type)
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Модель/Название")
        form.addRow("Название:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e7)
        self.spin_price.setPrefix("₽ ")
        form.addRow("Цена:", self.spin_price)
        
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Описание, характеристики")
        form.addRow("Описание:", self.inp_desc)
        
        self.chk_cylinder = QCheckBox("Требует цилиндровый механизм")
        form.addRow("Опции:", self.chk_cylinder)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        if not self.item:
            return
        idx = self.combo_type.findData(self.item.get("type"))
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
        self.inp_name.setText(self.item.get("name", ""))
        self.spin_price.setValue(self.item.get("price", 0))
        self.inp_desc.setText(self.item.get("description", ""))
        self.chk_cylinder.setChecked(self.item.get("has_cylinder", False))
    
    def get_data(self) -> dict:
        return {
            "type": self.combo_type.currentData(),
            "name": self.inp_name.text().strip(),
            "price": self.spin_price.value(),
            "description": self.inp_desc.text().strip() or None,
            "has_cylinder": self.chk_cylinder.isChecked()
        }


class HardwareTab(QWidget):
    def __init__(self, price_list_ctrl: PriceListController):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self.hw_ctrl = HardwareController()
        self.current_price_list_id = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel("Управление фурнитурой (замки, ручки, цилиндры, доводчики)")
        layout.addWidget(info_label)
        
        self.filter_layout = QHBoxLayout()
        self.filter_layout.addWidget(QLabel("Фильтр по типу:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItem("Все", None)
        for t in HardwareType:
            self.combo_filter.addItem(t.value, t.value)
        self.combo_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.filter_layout.addWidget(self.combo_filter)
        self.filter_layout.addStretch()
        layout.addLayout(self.filter_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Название", "Цена", "Цилиндр", "Описание"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add_hardware)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_hardware)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self._delete_hardware)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_data(self, hw_type: str = None):
        if not self.current_price_list_id:
            self.table.setRowCount(0)
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem("Сначала выберите прайс-лист в Калькуляторе"))
            return
        
        self.table.setRowCount(0)
        try:
            if hw_type:
                items = self.hw_ctrl.get_by_type(hw_type, self.current_price_list_id)
            else:
                all_items = self.hw_ctrl.get_all_for_price_list(self.current_price_list_id)
                items = []
                for type_items in all_items.values():
                    items.extend(type_items)
            
            for item in items:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(item.id)))
                self.table.setItem(row, 1, QTableWidgetItem(item.type))
                self.table.setItem(row, 2, QTableWidgetItem(item.name))
                self.table.setItem(row, 3, QTableWidgetItem(f"{item.price:,.2f} ₽"))
                self.table.setItem(row, 4, QTableWidgetItem("Да" if item.has_cylinder else "—"))
                self.table.setItem(row, 5, QTableWidgetItem(item.description or "—"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def set_price_list(self, price_list_id: int):
        self.current_price_list_id = price_list_id
        self._load_data()
    
    def _on_filter_changed(self, idx: int):
        hw_type = self.combo_filter.currentData()
        self._load_data(hw_type if hw_type else None)
    
    def _add_hardware(self):
        if not self.current_price_list_id:
            QMessageBox.warning(self, "Внимание", "Выберите прайс-лист в Калькуляторе")
            return
        
        dialog = HardwareEditDialog()
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                try:
                    self.hw_ctrl.create(
                        hw_type=data["type"],
                        name=data["name"],
                        price=data["price"],
                        description=data["description"],
                        has_cylinder=data["has_cylinder"],
                        price_list_id=self.current_price_list_id
                    )
                    self._load_data()
                    QMessageBox.information(self, "Успех", "Фурнитура добавлена")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))
    
    def _edit_hardware(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите элемент")
            return
        
        item = self.table.item(row, 0)
        if not item or not item.text().isdigit():
            return
        
        hw_id = int(item.text())
        item = self.hw_ctrl.get_by_id(hw_id)
        if not item:
            return
        
        dialog = HardwareEditDialog({
            "type": item.type,
            "name": item.name,
            "price": item.price,
            "description": item.description,
            "has_cylinder": item.has_cylinder
        })
        
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                try:
                    self.hw_ctrl.update(hw_id, data)
                    self._load_data()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))
    
    def _delete_hardware(self):
        row = self.table.currentRow()
        if row < 0:
            return
        
        item = self.table.item(row, 0)
        if not item or not item.text().isdigit():
            return
        hw_id = int(item.text())
        
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранный элемент фурнитуры?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.hw_ctrl.delete(hw_id)
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
