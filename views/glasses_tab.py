"""Вкладка 'Стёкла'. Управление типами стёкол и их опциями."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QDialog, QFormLayout, QLineEdit, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from controllers.options_controller import OptionsController
from controllers.price_list_controller import PriceListController


class GlassOptionDialog(QDialog):
    """Диалог добавления/редактирования опции стекла."""
    
    def __init__(self, name: str = "", price: float = 0, min_price: float = 0):
        super().__init__()
        self.setWindowTitle("Опция стекла")
        self.resize(350, 200)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit(name)
        self.inp_name.setPlaceholderText("Название (матировка, пленка...)")
        form.addRow("Название:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e6)
        self.spin_price.setPrefix("₽ ")
        self.spin_price.setValue(price)
        form.addRow("Цена/м²:", self.spin_price)
        
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 1e6)
        self.spin_min.setPrefix("₽ ")
        self.spin_min.setValue(min_price)
        form.addRow("Мин. цена:", self.spin_min)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def get_data(self):
        return {
            "name": self.inp_name.text().strip(),
            "price_per_m2": self.spin_price.value(),
            "min_price": self.spin_min.value()
        }


class GlassesTab(QWidget):
    def __init__(self, price_list_ctrl: PriceListController):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self.options_ctrl = OptionsController()
        self.current_price_list_id = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel("Управление типами стёкол и их опциями")
        layout.addWidget(info_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Тип стекла", "Цена/м²", "Мин. цена", "Опции"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить тип стекла")
        btn_add.clicked.connect(self._add_glass_type)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_glass_type)
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self._delete_glass_type)
        btn_add_opt = QPushButton("Добавить опцию")
        btn_add_opt.clicked.connect(self._add_option)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_add_opt)
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        if not self.current_price_list_id:
            self.table.setRowCount(0)
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem("Сначала выберите прайс-лист в Калькуляторе"))
            return
        
        self.table.setRowCount(0)
        try:
            glasses = self.options_ctrl.get_glass_types(self.current_price_list_id)
            for g in glasses:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(g["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(g["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(f"{g['price_per_m2']:.2f} ₽"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{g['min_price']:.2f} ₽"))
                opts = ", ".join([o["name"] for o in g.get("options", [])]) or "—"
                self.table.setItem(row, 4, QTableWidgetItem(opts))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def set_price_list(self, price_list_id: int):
        self.current_price_list_id = price_list_id
        self._load_data()
    
    def _add_glass_type(self):
        if not self.current_price_list_id:
            QMessageBox.warning(self, "Внимание", "Выберите прайс-лист в Калькуляторе")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Новый тип стекла")
        dialog.resize(350, 200)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        inp_name = QLineEdit()
        inp_name.setPlaceholderText("Название (Армированное, Закалённое...)")
        spin_price = QDoubleSpinBox()
        spin_price.setRange(0, 1e6)
        spin_price.setPrefix("₽ ")
        spin_min = QDoubleSpinBox()
        spin_min.setRange(0, 1e6)
        spin_min.setPrefix("₽ ")
        
        form.addRow("Название:", inp_name)
        form.addRow("Цена/м²:", spin_price)
        form.addRow("Мин. цена:", spin_min)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        
        if dialog.exec():
            if inp_name.text().strip():
                try:
                    self.options_ctrl.create_glass_type(
                        inp_name.text().strip(),
                        spin_price.value(),
                        spin_min.value(),
                        self.current_price_list_id
                    )
                    self._load_data()
                    QMessageBox.information(self, "Успех", "Тип стекла добавлен")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))
    
    def _edit_glass_type(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите тип стекла")
            return
        
        glass_id = int(self.table.item(row, 0).text())
        glass_name = self.table.item(row, 1).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование типа стекла")
        dialog.resize(350, 200)
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        inp_name = QLineEdit(glass_name)
        spin_price = QDoubleSpinBox()
        spin_price.setRange(0, 1e6)
        spin_price.setPrefix("₽ ")
        spin_min = QDoubleSpinBox()
        spin_min.setRange(0, 1e6)
        spin_min.setPrefix("₽ ")
        
        form.addRow("Название:", inp_name)
        form.addRow("Цена/м²:", spin_price)
        form.addRow("Мин. цена:", spin_min)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_cancel = QPushButton("Отмена")
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        
        if dialog.exec():
            if inp_name.text().strip():
                try:
                    self.options_ctrl.update_glass_type(glass_id, {
                        "name": inp_name.text().strip(),
                        "price_per_m2": spin_price.value(),
                        "min_price": spin_min.value()
                    })
                    self._load_data()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))
    
    def _delete_glass_type(self):
        row = self.table.currentRow()
        if row < 0:
            return
        glass_id = int(self.table.item(row, 0).text())
        
        reply = QMessageBox.question(self, "Подтверждение", "Удалить тип стекла и все его опции?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.options_ctrl.delete_glass_type(glass_id)
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def _add_option(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Сначала выберите тип стекла")
            return
        
        glass_id = int(self.table.item(row, 0).text())
        dialog = GlassOptionDialog()
        
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                try:
                    self.options_ctrl.create_glass_option(
                        glass_id,
                        data["name"],
                        data["price_per_m2"],
                        data["min_price"]
                    )
                    self._load_data()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))


from PyQt6.QtWidgets import QLabel
