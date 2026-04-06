"""Вкладка 'Прайс'. Полное управление прайс-листом с ценами на все позиции."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QGroupBox, QLabel, QComboBox, QLineEdit, QDoubleSpinBox,
    QPushButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QTabWidget, QSpinBox, QDialog
)
from PyQt6.QtCore import Qt
from controllers.price_list_controller import PriceListController
from controllers.hardware_controller import HardwareController
from controllers.options_controller import OptionsController
from constants import HardwareType


class PriceEditWidget(QWidget):
    """Виджет редактирования цен прайс-листа."""
    
    def __init__(self, price_list_ctrl: PriceListController, price_list_id: int = None):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self.price_list_id = price_list_id or self._get_base_id()
        self._init_ui()
        self._load_prices()
    
    def _get_base_id(self):
        try:
            return self.price_list_ctrl.get_base_price_list().id
        except:
            return None
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_layout = QHBoxLayout()
        self.lbl_name = QLabel("Базовый системный прайс")
        self.lbl_name.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.lbl_name)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Таблица цен
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Параметр", "Цена", "Ед.изм."])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(400)
        layout.addWidget(self.table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Сохранить изменения")
        btn_save.clicked.connect(self._save_prices)
        btn_reset = QPushButton("Сбросить")
        btn_reset.clicked.connect(self._load_prices)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_prices(self):
        if not self.price_list_id:
            return
        
        self.table.setRowCount(0)
        try:
            base = self.price_list_ctrl.get_base_price_list()
            self.lbl_name.setText(base.name)
            
            prices = [
                ("Дверь стандартная (1500-2200, 500-1000)", base.doors_price_std_single, "руб"),
                ("Дверь нестандарт (м²)", base.doors_price_per_m2_nonstd, "руб/м²"),
                ("Наценка за ширину", base.doors_wide_markup, "руб"),
                ("Дверь двустворчатая стандарт", base.doors_double_std, "руб"),
                ("", 0, ""),
                ("Люк стандартный (до 0.4м²)", base.hatch_std, "руб"),
                ("Люк нестандарт (м²)", base.hatch_per_m2_nonstd, "руб/м²"),
                ("Наценка за ширину люка", base.hatch_wide_markup, "руб"),
                ("", 0, ""),
                ("Ворота (м²)", base.gate_per_m2, "руб/м²"),
                ("Ворота большие (м²)", base.gate_large_per_m2, "руб/м²"),
                ("", 0, ""),
                ("Фрамуга (м²)", base.transom_per_m2, "руб/м²"),
                ("Фрамуга минимум", base.transom_min, "руб"),
                ("", 0, ""),
                ("Вырез", base.cutout_price, "руб"),
                ("Отбойная пластина (м²)", base.deflector_per_m2, "руб/м²"),
                ("Накладка на коробку (м.п.)", base.trim_per_lm, "руб/м.п."),
                ("", 0, ""),
                ("Доводчик", base.closer_price, "руб"),
                ("Петля усиленная", base.hinge_price, "руб"),
                ("Антивандальная защита", base.anti_theft_price, "руб"),
                ("ГКЛ наполнение", base.gkl_price, "руб"),
                ("Монтажные уши", base.mount_ear_price, "руб"),
            ]
            
            self.price_fields = {}
            for name, value, unit in prices:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                if not name:
                    self.table.setItem(row, 0, QTableWidgetItem(""))
                    self.table.setItem(row, 1, QTableWidgetItem(""))
                    self.table.setItem(row, 2, QTableWidgetItem(""))
                    continue
                
                self.table.setItem(row, 0, QTableWidgetItem(name))
                spin = QDoubleSpinBox()
                spin.setRange(0, 1e9)
                spin.setDecimals(2)
                spin.setValue(value)
                self.table.setCellWidget(row, 1, spin)
                self.table.setItem(row, 2, QTableWidgetItem(unit))
                
                key = name.split("(")[0].strip()
                self.price_fields[key] = spin
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить цены:\n{e}")
    
    def _save_prices(self):
        mapping = {
            "Дверь стандартная": "doors_price_std_single",
            "Дверь нестандарт": "doors_price_per_m2_nonstd",
            "Наценка за ширину": "doors_wide_markup",
            "Дверь двустворчатая стандарт": "doors_double_std",
            "Люк стандартный": "hatch_std",
            "Люк нестандарт": "hatch_per_m2_nonstd",
            "Наценка за ширину люка": "hatch_wide_markup",
            "Ворота": "gate_per_m2",
            "Ворота большие": "gate_large_per_m2",
            "Фрамуга": "transom_per_m2",
            "Фрамуга минимум": "transom_min",
            "Вырез": "cutout_price",
            "Отбойная пластина": "deflector_per_m2",
            "Накладка на коробку": "trim_per_lm",
            "Доводчик": "closer_price",
            "Петля усиленная": "hinge_price",
            "Антивандальная защита": "anti_theft_price",
            "ГКЛ наполнение": "gkl_price",
            "Монтажные уши": "mount_ear_price",
        }
        
        try:
            base = self.price_list_ctrl.get_base_price_list()
            for name, field in mapping.items():
                if name in self.price_fields:
                    setattr(base, field, self.price_fields[name].value())
            
            self.price_list_ctrl.update_base(base)
            QMessageBox.information(self, "Сохранено", "Цены обновлены.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class HardwareEditWidget(QWidget):
    """Виджет управления фурнитурой прайс-листа."""
    
    def __init__(self, hw_ctrl: HardwareController, price_list_id: int = None):
        super().__init__()
        self.hw_ctrl = hw_ctrl
        self.price_list_id = price_list_id or self._get_base_id()
        self._init_ui()
        self._load_data()
    
    def _get_base_id(self):
        try:
            base = self.price_list_ctrl.get_base_price_list()
            return base.id if base else None
        except:
            return None
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Фильтр по типу
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Тип:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItem("Все", None)
        for t in HardwareType:
            self.combo_filter.addItem(t.value, t.value)
        self.combo_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.combo_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Тип", "Название", "Цена", "Цилиндр", "Описание"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add_hardware)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_hardware)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete_hardware)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def set_price_list_id(self, pl_id: int):
        self.price_list_id = pl_id
        self._load_data()
    
    def _load_data(self, hw_type: str = None):
        if not self.price_list_id:
            return
        
        self.table.setRowCount(0)
        try:
            if hw_type:
                items = self.hw_ctrl.get_by_type(hw_type, self.price_list_id)
            else:
                all_items = self.hw_ctrl.get_all_for_price_list(self.price_list_id)
                items = []
                for type_list in all_items.values():
                    items.extend(type_list)
            
            for item in items:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(item.id)))
                self.table.setItem(row, 1, QTableWidgetItem(item.type))
                self.table.setItem(row, 2, QTableWidgetItem(item.name))
                self.table.setItem(row, 3, QTableWidgetItem(f"{item.price:,.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem("Да" if item.has_cylinder else "—"))
                self.table.setItem(row, 5, QTableWidgetItem(item.description or "—"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _on_filter_changed(self, idx: int):
        hw_type = self.combo_filter.currentData()
        self._load_data(hw_type if hw_type else None)
    
    def _add_hardware(self):
        if not self.price_list_id:
            QMessageBox.warning(self, "Внимание", "Сначала выберите прайс-лист")
            return
        
        dialog = HardwareEditDialog(self.price_list_id, None, self.hw_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _edit_hardware(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите элемент")
            return
        
        hw_id = int(self.table.item(row, 0).text())
        dialog = HardwareEditDialog(self.price_list_id, hw_id, self.hw_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _delete_hardware(self):
        row = self.table.currentRow()
        if row < 0:
            return
        
        hw_id = int(self.table.item(row, 0).text())
        name = self.table.item(row, 2).text()
        
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить '{name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.hw_ctrl.delete(hw_id)
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))


class HardwareEditDialog(QDialog):
    """Диалог добавления/редактирования фурнитуры."""
    
    def __init__(self, price_list_id: int, hw_id: int = None, hw_ctrl: HardwareController = None):
        super().__init__()
        self.price_list_id = price_list_id
        self.hw_id = hw_id
        self.hw_ctrl = hw_ctrl
        self.editing = hw_id is not None
        self.setWindowTitle("Редактирование фурнитуры" if self.editing else "Новая фурнитура")
        self.resize(450, 350)
        self._init_ui()
        if self.editing:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.combo_type = QComboBox()
        for t in HardwareType:
            self.combo_type.addItem(t.value, t.value)
        form.addRow("Тип:", self.combo_type)
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название (обязательно)")
        form.addRow("Название *:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e7)
        self.spin_price.setPrefix("₽ ")
        self.spin_price.setDecimals(2)
        form.addRow("Цена:", self.spin_price)
        
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Описание, характеристики")
        form.addRow("Описание:", self.inp_desc)
        
        self.chk_cylinder = QCheckBox("Требует цилиндровый механизм")
        form.addRow("Опции:", self.chk_cylinder)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        if not self.hw_ctrl:
            return
        hw = self.hw_ctrl.get_by_id(self.hw_id)
        if hw:
            idx = self.combo_type.findData(hw.type)
            if idx >= 0:
                self.combo_type.setCurrentIndex(idx)
            self.inp_name.setText(hw.name)
            self.spin_price.setValue(hw.price)
            self.inp_desc.setText(hw.description or "")
            self.chk_cylinder.setChecked(hw.has_cylinder)
    
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название фурнитуры.")
            return
        
        if name.lower() in ["замок", "ручка", "цилиндр", "доводчик"]:
            QMessageBox.warning(self, "Ошибка", "Название слишком общее. Укажите конкретную модель.")
            return
        
        data = {
            "type": self.combo_type.currentData(),
            "name": name,
            "price": self.spin_price.value(),
            "description": self.inp_desc.text().strip() or None,
            "has_cylinder": self.chk_cylinder.isChecked()
        }
        
        try:
            if self.editing:
                self.hw_ctrl.update(self.hw_id, data)
            else:
                data["price_list_id"] = self.price_list_id
                self.hw_ctrl.create(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class GlassesEditWidget(QWidget):
    """Виджет управления стёклами прайс-листа."""
    
    def __init__(self, options_ctrl: OptionsController, price_list_id: int = None):
        super().__init__()
        self.options_ctrl = options_ctrl
        self.price_list_id = price_list_id or self._get_base_id()
        self._init_ui()
        self._load_data()
    
    def _get_base_id(self):
        try:
            from controllers.price_list_controller import PriceListController
            ctrl = PriceListController()
            return ctrl.get_base_price_list().id
        except:
            return None
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Тип стекла", "Цена/м²", "Мин. цена", "Опции"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить тип стекла")
        btn_add.clicked.connect(self._add_glass)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_glass)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete_glass)
        btn_add_opt = QPushButton("Добавить опцию")
        btn_add_opt.clicked.connect(self._add_option)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_add_opt)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def set_price_list_id(self, pl_id: int):
        self.price_list_id = pl_id
        self._load_data()
    
    def _load_data(self):
        if not self.price_list_id:
            return
        
        self.table.setRowCount(0)
        try:
            glasses = self.options_ctrl.get_glass_types(self.price_list_id)
            for g in glasses:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(g["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(g["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(f"{g['price_per_m2']:,.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{g['min_price']:,.2f}"))
                opts = ", ".join([o["name"] for o in g.get("options", [])]) or "—"
                self.table.setItem(row, 4, QTableWidgetItem(opts))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _add_glass(self):
        if not self.price_list_id:
            return
        dialog = GlassEditDialog(None, self.price_list_id, self.options_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _edit_glass(self):
        row = self.table.currentRow()
        if row < 0:
            return
        glass_id = int(self.table.item(row, 0).text())
        dialog = GlassEditDialog(glass_id, self.price_list_id, self.options_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _delete_glass(self):
        row = self.table.currentRow()
        if row < 0:
            return
        glass_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "Подтверждение", "Удалить тип стекла?")
        if reply == QMessageBox.StandardButton.Yes:
            self.options_ctrl.delete_glass_type(glass_id)
            self._load_data()
    
    def _add_option(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите тип стекла")
            return
        glass_id = int(self.table.item(row, 0).text())
        dialog = GlassOptionEditDialog(glass_id, self.options_ctrl)
        if dialog.exec():
            self._load_data()


class GlassEditDialog(QDialog):
    """Диалог редактирования типа стекла."""
    
    def __init__(self, glass_id: int, price_list_id: int, options_ctrl: OptionsController):
        super().__init__()
        self.glass_id = glass_id
        self.price_list_id = price_list_id
        self.options_ctrl = options_ctrl
        self.editing = glass_id is not None
        self.setWindowTitle("Редактирование стекла" if self.editing else "Новое стекло")
        self.resize(350, 200)
        self._init_ui()
        if self.editing:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название стекла")
        form.addRow("Название:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e6)
        self.spin_price.setPrefix("₽ ")
        self.spin_price.setDecimals(2)
        form.addRow("Цена/м²:", self.spin_price)
        
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 1e6)
        self.spin_min.setPrefix("₽ ")
        self.spin_min.setDecimals(2)
        form.addRow("Мин. цена:", self.spin_min)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        glasses = self.options_ctrl.get_glass_types(self.price_list_id)
        for g in glasses:
            if g["id"] == self.glass_id:
                self.inp_name.setText(g["name"])
                self.spin_price.setValue(g["price_per_m2"])
                self.spin_min.setValue(g["min_price"])
                break
    
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return
        
        try:
            if self.editing:
                self.options_ctrl.update_glass_type(self.glass_id, {
                    "name": name,
                    "price_per_m2": self.spin_price.value(),
                    "min_price": self.spin_min.value()
                })
            else:
                self.options_ctrl.create_glass_type(
                    name, self.spin_price.value(), self.spin_min.value(), self.price_list_id
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class GlassOptionEditDialog(QDialog):
    """Диалог добавления опции стекла."""
    
    def __init__(self, glass_id: int, options_ctrl: OptionsController):
        super().__init__()
        self.glass_id = glass_id
        self.options_ctrl = options_ctrl
        self.setWindowTitle("Опция стекла")
        self.resize(350, 180)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название опции")
        form.addRow("Название:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e6)
        self.spin_price.setPrefix("₽ ")
        form.addRow("Цена/м²:", self.spin_price)
        
        self.spin_min = QDoubleSpinBox()
        self.spin_min.setRange(0, 1e6)
        self.spin_min.setPrefix("₽ ")
        form.addRow("Мин. цена:", self.spin_min)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            return
        try:
            self.options_ctrl.create_glass_option(
                self.glass_id, name,
                self.spin_price.value(),
                self.spin_min.value()
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class PriceTab(QWidget):
    """Вкладка 'Прайс' - управление ценами, фурнитурой и стёклами."""
    
    def __init__(self, price_list_ctrl: PriceListController):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self.hw_ctrl = HardwareController()
        self.options_ctrl = OptionsController()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # Вкладка цен
        self.price_widget = PriceEditWidget(self.price_list_ctrl)
        tabs.addTab(self.price_widget, "Цены")
        
        # Вкладка фурнитуры
        self.hw_widget = HardwareEditWidget(self.hw_ctrl)
        tabs.addTab(self.hw_widget, "Фурнитура")
        
        # Вкладка стёкол
        self.glass_widget = GlassesEditWidget(self.options_ctrl)
        tabs.addTab(self.glass_widget, "Стекла")
        
        layout.addWidget(tabs)
