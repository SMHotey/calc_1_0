"""Вкладка 'Прайс'. Полное управление прайс-листом с вложенными вкладками.

Содержит:
- PriceTab: вкладка для управления прайс-листами с вложенными вкладками:
  - Цены: базовые цены на изделия и опции
  - Типы изделий: type-specific цены для разных типов
  - Стекла: типы стёкол
  - Опции стёкол: глобальные опции для всех стёкол
  - Фурнитура: замки, ручки, цилиндры, доводчики
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QLineEdit, QDoubleSpinBox,
    QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QTabWidget, QDialog, QHeaderView, QCheckBox
)
from PyQt6.QtCore import Qt
from controllers.price_list_controller import PriceListController
from controllers.hardware_controller import HardwareController
from controllers.options_controller import OptionsController
from constants import HardwareType, PRODUCT_TYPES, PRODUCT_DOOR, PRODUCT_HATCH, PRODUCT_GATE, PRODUCT_TRANSOM


class PriceEditDialog(QDialog):
    """Диалог редактирования цены дополнительной опции."""
    
    def __init__(self, name: str, price: float, unit: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Редактирование: {name}")
        self.resize(300, 150)
        self._init_ui(name, price, unit)
    
    def _init_ui(self, name: str, price: float, unit: str):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.inp_name = QLineEdit(name)
        self.inp_name.setEnabled(False)  # Название нельзя менять
        form.addRow("Параметр:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e9)
        self.spin_price.setDecimals(2)
        self.spin_price.setValue(price)
        form.addRow("Цена:", self.spin_price)
        
        self.inp_unit = QLineEdit(unit)
        form.addRow("Ед.изм.:", self.inp_unit)
        
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
            "price": self.spin_price.value(),
            "unit": self.inp_unit.text()
        }


class PriceEditWidget(QWidget):
    """Виджет редактирования базовых цен прайс-листа.
    
    Позволяет изменять цены на комплектующие. Показывает только компоненты,
    изделия редактируются на вкладке Изделия.
    """
    
    # Словарь: отображаемое имя -> поле в модели BasePriceList
    PRICE_FIELDS = {
        "Вырез (стекло/решётка)": ("cutout_price", "руб"),
        "Отбойная пластина (м²)": ("deflector_per_m2", "руб/м²"),
        "Добор (м.п.)": ("trim_per_lm", "руб/м.п."),
        "Доп. петля": ("hinge_price", "руб"),
        "Противосъёмные штыри": ("anti_theft_price", "руб"),
        "ГКЛ наполнение": ("gkl_price", "руб"),
        "Монтажные уши": ("mount_ear_price", "руб"),
        "Тех. вентрешетка": ("vent_grate_tech", "руб"),
        "П/п вентрешетка": ("vent_grate_pp", "руб"),
    }
    
    def __init__(self, price_list_ctrl: PriceListController, price_list_id: int = None):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self.price_list_id = price_list_id or self._get_base_id()
        self.price_fields = {}  # name -> field_name mapping
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
        # Фиксированные ширины для колонок
        self.table.setColumnWidth(0, 280)  # Параметр - достаточная ширина
        self.table.setColumnWidth(1, 100)  # Цена
        self.table.setColumnWidth(2, 80)   # Ед.изм.
        # Последний столбец НЕ растягивается - колонки фиксированы
        self.table.setMinimumHeight(400)
        
        # Двойной щелчок для редактирования
        self.table.itemDoubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._on_double_click)
        btn_reset = QPushButton("Обновить")
        btn_reset.clicked.connect(self._load_prices)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_reset)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_prices(self):
        if not self.price_list_id:
            return
        
        self.table.setRowCount(0)
        self.price_fields = {}
        
        try:
            base = self.price_list_ctrl.get_base_price_list()
            self.lbl_name.setText(base.name)
            
            # Загружаем цены из словаря
            for name, (field, unit) in self.PRICE_FIELDS.items():
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Сохраняем имя и поле для редактирования
                item_name = QTableWidgetItem(name)
                item_name.setData(Qt.ItemDataRole.UserRole, field)
                self.table.setItem(row, 0, item_name)
                
                value = getattr(base, field, 0) or 0
                self.table.setItem(row, 1, QTableWidgetItem(f"{value:,.2f}"))
                self.table.setItem(row, 2, QTableWidgetItem(unit))
                
                self.price_fields[name] = (field, value, unit)
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить цены:\n{e}")
    
    def _on_double_click(self, item):
        """Обработка двойного щелчка - открытие диалога редактирования."""
        if item.column() != 1:  # Редактируем только цену (колонка 1)
            return
        
        row = item.row()
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        
        name = name_item.text()
        if name not in self.PRICE_FIELDS:
            return
        
        field, price, unit = self.price_fields[name]
        
        # Открываем диалог
        dialog = PriceEditDialog(name, price, unit, self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                # Обновляем цену в базе
                base = self.price_list_ctrl.get_base_price_list()
                setattr(base, field, data["price"])
                self.price_list_ctrl.update_base(base)
                # Перезагружаем данные
                self._load_prices()
                QMessageBox.information(self, "Успех", "Цена обновлена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def _save_prices(self):
        mapping = {
            "Дверь стандартная": "doors_price_std_single",
            "Дверь нестандарт": "doors_price_per_m2_nonstd",
            "Наценка за ширину": "doors_wide_markup",
            "Дверь двустворчатая стандарт": "doors_double_std",
            "Порог": "threshold_price",
            "Люк стандартный": "hatch_std",
            "Люк нестандарт": "hatch_per_m2_nonstd",
            "Наценка за ширину люка": "hatch_wide_markup",
            "Ворота": "gate_per_m2",
            "Ворота большие": "gate_large_per_m2",
            "Фрамуга": "transom_per_m2",
            "Фрамуга минимум": "transom_min",
            "Вырез": "cutout_price",
            "Отбойная пластина": "deflector_per_m2",
            "Добор": "trim_per_lm",
            "Доп. петля": "hinge_price",
            "Противосъёмные штыри": "anti_theft_price",
            "ГКЛ наполнение": "gkl_price",
            "Монтажные уши": "mount_ear_price",
            "Тех. вентрешетка": "vent_grate_tech",
            "П/п вентрешетка": "vent_grate_pp",
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


class ProductTypesWidget(QWidget):
    """Виджет управления type-specific ценами для типов изделий.
    
    Позволяет редактировать цены для каждого типа изделия
    (Дверь EI 60, Люк технический и т.д.).
    """
    
    def __init__(self, price_list_ctrl: PriceListController, price_list_id: int = None):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self.price_list_id = price_list_id or self._get_base_id()
        self._init_ui()
        self._load_data()
    
    def _get_base_id(self):
        try:
            return self.price_list_ctrl.get_base_price_list().id
        except:
            return None
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        info_layout = QHBoxLayout()
        lbl = QLabel("Type-specific цены для разных типов изделий")
        lbl.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(lbl)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Таблица (сейчас без ID)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Вид", "Тип", "Цена ед.", "Цена 2ств.", "Нестандарт/м²", "Наценка за ширину"
        ])
        # Фиксированные ширины для всех колонок
        self.table.setColumnWidth(0, 120)  # Вид
        self.table.setColumnWidth(1, 150)  # Тип
        self.table.setColumnWidth(2, 90)   # Цена ед.
        self.table.setColumnWidth(3, 90)   # Цена 2ств.
        self.table.setColumnWidth(4, 110)  # Нестандарт/м²
        self.table.setColumnWidth(5, 130)  # Наценка за ширину
        self.table.setMinimumHeight(400)
        layout.addWidget(self.table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить тип")
        btn_add.clicked.connect(self._add_type)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_type)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete_type)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        if not self.price_list_id:
            return
        
        self.table.setRowCount(0)
        try:
            type_prices = self.price_list_ctrl.get_type_prices(self.price_list_id)
            for tp in type_prices:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(tp.product_type))
                self.table.setItem(row, 1, QTableWidgetItem(tp.subtype))
                self.table.setItem(row, 2, QTableWidgetItem(f"{tp.price_std_single:,.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{tp.price_double_std:,.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(f"{tp.price_per_m2_nonstd:,.2f}"))
                self.table.setItem(row, 5, QTableWidgetItem(f"{tp.price_wide_markup:,.2f}"))
                # Сохраняем ID в data для редактирования
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, tp.id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _add_type(self):
        dialog = TypePriceDialog(self.price_list_id, None, self.price_list_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _edit_type(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите тип для редактирования")
            return
        # Получаем ID из UserRole данных
        if self.table.item(row, 0) is None:
            QMessageBox.warning(self, "Внимание", "Выберите тип для редактирования")
            return
        tp_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if tp_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите тип для редактирования")
            return
        dialog = TypePriceDialog(self.price_list_id, tp_id, self.price_list_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _delete_type(self):
        row = self.table.currentRow()
        if row < 0:
            return
        tp_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if tp_id is None:
            return
        reply = QMessageBox.question(self, "Подтверждение", "Удалить тип?")
        if reply == QMessageBox.StandardButton.Yes:
            self.price_list_ctrl.delete_type_price(tp_id)
            self._load_data()


class TypePriceDialog(QDialog):
    """Диалог добавления/редактирования type-specific цены."""
    
    def __init__(self, price_list_id: int, tp_id: int | None, ctrl: PriceListController):
        super().__init__()
        self.price_list_id = price_list_id
        self.tp_id = tp_id
        self.ctrl = ctrl
        self.editing = tp_id is not None
        self.setWindowTitle("Редактирование типа" if self.editing else "Новый тип")
        self.resize(400, 300)
        self._init_ui()
        if self.editing:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Вид изделия
        self.combo_product = QComboBox()
        for prod, subtypes in PRODUCT_TYPES.items():
            self.combo_product.addItem(prod, prod)
        self.combo_product.currentIndexChanged.connect(self._on_product_changed)
        form.addRow("Вид изделия:", self.combo_product)
        
        # Тип
        self.combo_subtype = QComboBox()
        form.addRow("Тип:", self.combo_subtype)
        
        # Цены
        self.spin_std = QDoubleSpinBox()
        self.spin_std.setRange(0, 1e9)
        self.spin_std.setPrefix("₽ ")
        self.spin_std.setDecimals(2)
        form.addRow("Цена ед. (руб):", self.spin_std)
        
        self.spin_double = QDoubleSpinBox()
        self.spin_double.setRange(0, 1e9)
        self.spin_double.setPrefix("₽ ")
        self.spin_double.setDecimals(2)
        form.addRow("Цена 2ств. (руб):", self.spin_double)
        
        self.spin_per_m2 = QDoubleSpinBox()
        self.spin_per_m2.setRange(0, 1e9)
        self.spin_per_m2.setPrefix("₽/м² ")
        self.spin_per_m2.setDecimals(2)
        form.addRow("Нестандарт/м²:", self.spin_per_m2)
        
        # Новое поле - Наценка за ширину
        self.spin_wide = QDoubleSpinBox()
        self.spin_wide.setRange(0, 1e9)
        self.spin_wide.setPrefix("₽ ")
        self.spin_wide.setDecimals(2)
        form.addRow("Наценка за ширину:", self.spin_wide)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
        
        self._update_subtypes()
    
    def _on_product_changed(self):
        self._update_subtypes()
    
    def _update_subtypes(self):
        self.combo_subtype.blockSignals(True)
        self.combo_subtype.clear()
        product = self.combo_product.currentData()
        if product and product in PRODUCT_TYPES:
            for subtype in PRODUCT_TYPES[product]:
                self.combo_subtype.addItem(subtype, subtype)
        self.combo_subtype.blockSignals(False)
    
    def _load_data(self):
        type_prices = self.ctrl.get_type_prices(self.price_list_id)
        for tp in type_prices:
            if tp.id == self.tp_id:
                idx = self.combo_product.findData(tp.product_type)
                if idx >= 0:
                    self.combo_product.setCurrentIndex(idx)
                self._update_subtypes()
                idx = self.combo_subtype.findData(tp.subtype)
                if idx >= 0:
                    self.combo_subtype.setCurrentIndex(idx)
                self.spin_std.setValue(tp.price_std_single or 0)
                self.spin_double.setValue(tp.price_double_std or 0)
                self.spin_per_m2.setValue(tp.price_per_m2_nonstd or 0)
                self.spin_wide.setValue(tp.price_wide_markup or 0)
                break
    
    def _save(self):
        try:
            data = {
                "product_type": self.combo_product.currentData(),
                "subtype": self.combo_subtype.currentData(),
                "price_std_single": self.spin_std.value(),
                "price_double_std": self.spin_double.value(),
                "price_per_m2_nonstd": self.spin_per_m2.value(),
                "price_wide_markup": self.spin_wide.value()
            }
            if self.editing:
                self.ctrl.update_type_price(self.tp_id, data)
            else:
                self.ctrl.create_type_price(self.price_list_id, **data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class GlassesEditWidget(QWidget):
    """Виджет управления типами стёкол прайс-листа.
    
    БЕЗ кнопки "Добавить опцию" - опции вынесены в отдельную вкладку.
    """
    
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
        
        # Таблица (сейчас без ID)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Тип стекла", "Цена/м²", "Мин. цена"])
        # Фиксированные ширины - подстраиваем под содержимое
        self.table.setColumnWidth(0, 250)  # Тип стекла - увеличено для названий
        self.table.setColumnWidth(1, 100)  # Цена/м²
        self.table.setColumnWidth(2, 100)  # Мин. цена
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
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
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
                self.table.setItem(row, 0, QTableWidgetItem(g["name"]))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, g["id"])
                self.table.setItem(row, 1, QTableWidgetItem(f"{g['price_per_m2']:,.2f}"))
                self.table.setItem(row, 2, QTableWidgetItem(f"{g['min_price']:,.2f}"))
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
        glass_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = GlassEditDialog(glass_id, self.price_list_id, self.options_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _delete_glass(self):
        row = self.table.currentRow()
        if row < 0:
            return
        glass_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Подтверждение", "Удалить тип стекла?")
        if reply == QMessageBox.StandardButton.Yes:
            self.options_ctrl.delete_glass_type(glass_id)
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


class GlassOptionsWidget(QWidget):
    """Виджет управления глобальными опциями стёкол.
    
    Опции, не привязанные к конкретному типу стекла,
    доступны для всех стёкол.
    """
    
    def __init__(self, options_ctrl: OptionsController):
        super().__init__()
        self.options_ctrl = options_ctrl
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Информация
        lbl = QLabel("Глобальные опции стёкол (доступны для всех типов)")
        lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl)
        
        # Таблица (сейчас без ID)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Название опции", "Цена/м²", "Мин. цена"])
        # Фиксированные ширины - подстраиваем под содержимое
        self.table.setColumnWidth(0, 300)  # Название опции - больше для длинных названий
        self.table.setColumnWidth(1, 100)  # Цена/м²
        self.table.setColumnWidth(2, 100)  # Мин. цена
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(350)
        layout.addWidget(self.table)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить опцию")
        btn_add.clicked.connect(self._add_option)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_option)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete_option)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _load_data(self):
        self.table.setRowCount(0)
        try:
            options = self.options_ctrl.get_global_glass_options()
            for opt in options:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(opt["name"]))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, opt["id"])
                self.table.setItem(row, 1, QTableWidgetItem(f"{opt['price_per_m2']:,.2f}"))
                self.table.setItem(row, 2, QTableWidgetItem(f"{opt['min_price']:,.2f}"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _add_option(self):
        dialog = GlassOptionEditDialog(None, self.options_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _edit_option(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите опцию")
            return
        opt_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = GlassOptionEditDialog(opt_id, self.options_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _delete_option(self):
        row = self.table.currentRow()
        if row < 0:
            return
        opt_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Подтверждение", "Удалить опцию?")
        if reply == QMessageBox.StandardButton.Yes:
            self.options_ctrl.delete_glass_option(opt_id)
            self._load_data()


class GlassOptionEditDialog(QDialog):
    """Диалог добавления/редактирования глобальной опции стекла."""
    
    def __init__(self, option_id: int | None, options_ctrl: OptionsController):
        super().__init__()
        self.option_id = option_id
        self.options_ctrl = options_ctrl
        self.editing = option_id is not None
        self.setWindowTitle("Редактирование опции" if self.editing else "Новая опция")
        self.resize(350, 180)
        self._init_ui()
        if self.editing:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название опции (плёнка А1, матировка и т.д.)")
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
        options = self.options_ctrl.get_global_glass_options()
        for opt in options:
            if opt["id"] == self.option_id:
                self.inp_name.setText(opt["name"])
                self.spin_price.setValue(opt["price_per_m2"])
                self.spin_min.setValue(opt["min_price"])
                break
    
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return
        try:
            if self.editing:
                self.options_ctrl.update_glass_option(self.option_id, {
                    "name": name,
                    "price_per_m2": self.spin_price.value(),
                    "min_price": self.spin_min.value()
                })
            else:
                self.options_ctrl.create_glass_option(
                    name=name,
                    price_per_m2=self.spin_price.value(),
                    min_price=self.spin_min.value(),
                    glass_type_id=None  # Глобальная опция
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class HardwareEditWidget(QWidget):
    """Виджет управления фурнитурой прайс-листа."""
    
    # Соответствие типа к заголовку окна
    DIALOG_TITLES = {
        HardwareType.LOCK.value: "Новый замок",
        HardwareType.HANDLE.value: "Новая ручка",
        HardwareType.CYLINDER.value: "Новый цилиндровый механизм",
    }
    EDIT_TITLES = {
        HardwareType.LOCK.value: "Редактирование замка",
        HardwareType.HANDLE.value: "Редактирование ручки",
        HardwareType.CYLINDER.value: "Редактирование цилиндра",
    }
    
    def __init__(self, hw_ctrl: HardwareController, price_list_id: int = None, hw_type: str = None):
        super().__init__()
        self.hw_ctrl = hw_ctrl
        self.price_list_id = price_list_id or self._get_base_id()
        self.hw_type = hw_type  # Тип фурнитуры (уже в подвкладке)
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
        
        # Тип фурнитуры уже в подвкладке - фильтр НЕ нужен
        
        # Таблица - увеличенная колонка Наименование
        self.table = QTableWidget()
        # Для цилиндров нет колонки ПП
        if self.hw_type == HardwareType.CYLINDER.value:
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["Наименование", "Цена", "Код", "Описание"])
            # Фиксированные ширины
            self.table.setColumnWidth(0, 220)  # Наименование - широкая
            self.table.setColumnWidth(1, 100)  # Цена
            self.table.setColumnWidth(2, 80)   # Код
            # Описание растягивается
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        else:
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Наименование", "Цена", "Код", "ПП", "Описание"])
            # Фиксированные ширины
            self.table.setColumnWidth(0, 220)  # Наименование - широкая
            self.table.setColumnWidth(1, 100)  # Цена
            self.table.setColumnWidth(2, 80)   # Код
            self.table.setColumnWidth(3, 60)   # ПП
            # Описание растягивается
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
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
            # Используем переданный тип или тот, что указан при создании
            filter_type = hw_type or self.hw_type
            if filter_type:
                items = self.hw_ctrl.get_by_type(filter_type, self.price_list_id)
            else:
                all_items = self.hw_ctrl.get_all_for_price_list(self.price_list_id)
                items = []
                for type_list in all_items.values():
                    items.extend(type_list)
            
            for item in items:
                row = self.table.rowCount()
                self.table.insertRow(row)
                # Сохраняем ID в UserRole
                self.table.setItem(row, 0, QTableWidgetItem(item.name))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item.id)
                self.table.setItem(row, 1, QTableWidgetItem(f"{item.price:,.2f}"))
                self.table.setItem(row, 2, QTableWidgetItem(item.description or "—"))
                # ПП только для не-цилиндров
                if filter_type != HardwareType.CYLINDER.value:
                    self.table.setItem(row, 3, QTableWidgetItem("Да" if item.has_cylinder else "Нет"))
                    self.table.setItem(row, 4, QTableWidgetItem(item.description or "—"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _add_hardware(self):
        if not self.price_list_id:
            QMessageBox.warning(self, "Внимание", "Сначала выберите прайс-лист")
            return
        
        # Тип уже определён подвкладкой - передаём его
        dialog = HardwareEditDialog(self.price_list_id, None, self.hw_ctrl, self.hw_type)
        if dialog.exec():
            self._load_data()
    
    def _edit_hardware(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите элемент")
            return
        
        hw_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = HardwareEditDialog(self.price_list_id, hw_id, self.hw_ctrl, self.hw_type)
        if dialog.exec():
            self._load_data()
    
    def _delete_hardware(self):
        row = self.table.currentRow()
        if row < 0:
            return
        
        hw_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        name = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить '{name}'?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.hw_ctrl.delete(hw_id)
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))


class HardwareEditDialog(QDialog):
    """Диалог добавления/редактирования фурнитуры."""
    
    # Соответствие типа к заголовку
    DIALOG_TITLES = {
        HardwareType.LOCK.value: "Новый замок",
        HardwareType.HANDLE.value: "Новая ручка",
        HardwareType.CYLINDER.value: "Новый цилиндровый механизм",
    }
    EDIT_TITLES = {
        HardwareType.LOCK.value: "Редактирование замка",
        HardwareType.HANDLE.value: "Редактирование ручки",
        HardwareType.CYLINDER.value: "Редактирование цилиндра",
    }
    
    def __init__(self, price_list_id: int, hw_id: int = None, hw_ctrl: HardwareController = None, hw_type: str = None):
        super().__init__()
        self.price_list_id = price_list_id
        self.hw_id = hw_id
        self.hw_ctrl = hw_ctrl
        self.hw_type = hw_type  #预设类型
        self.editing = hw_id is not None
        
        # Динамический заголовок окна
        if self.editing:
            title = self.EDIT_TITLES.get(hw_type, "Редактирование фурнитуры")
        else:
            title = self.DIALOG_TITLES.get(hw_type, "Новая фурнитура")
        self.setWindowTitle(title)
        
        self.resize(450, 350)
        self._init_ui()
        if self.editing:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Тип фурнитуры уже выбран в подвкладке - скрываем выбор
        # (оставляем скрытое поле для совместимости)
        self.combo_type = QComboBox()
        if self.hw_type:
            self.combo_type.addItem(self.hw_type, self.hw_type)
        else:
            for t in HardwareType:
                self.combo_type.addItem(t.value, t.value)
        self.combo_type.setVisible(False)  # Скрываем выбор типа
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название (обязательно)")
        form.addRow("Название *:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e7)
        self.spin_price.setPrefix("₽ ")
        self.spin_price.setDecimals(2)
        form.addRow("Цена:", self.spin_price)
        
        self.inp_code = QLineEdit()
        self.inp_code.setPlaceholderText("Код")
        form.addRow("Код:", self.inp_code)
        
        # ПП - только для не-цилиндров
        if self.hw_type != HardwareType.CYLINDER.value:
            self.chk_pp = QCheckBox("Противопожарная")
            form.addRow("ПП:", self.chk_pp)
        else:
            self.chk_pp = None
        
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Описание, характеристики")
        form.addRow("Описание:", self.inp_desc)
        
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
            # 从description中提取 код (如果有)
            desc = hw.description or ""
            if " | " in desc:
                parts = desc.split(" | ")
                self.inp_code.setText(parts[0] if parts[0] else "")
                self.inp_desc.setText(parts[1] if len(parts) > 1 else "")
            else:
                self.inp_desc.setText(desc)
            if self.chk_pp:
                self.chk_pp.setChecked(hw.has_cylinder)
    
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название фурнитуры.")
            return
        
        data = {
            "type": self.combo_type.currentData(),
            "name": name,
            "price": self.spin_price.value(),
            "description": self.inp_desc.text().strip() or None,
            "has_cylinder": self.chk_pp.isChecked() if self.chk_pp else False
        }
        
        # 如果有 код，添加到description中
        code = self.inp_code.text().strip()
        if code:
            data["description"] = f"{code} | {data['description'] or ''}"
        
        try:
            if self.editing:
                self.hw_ctrl.update(self.hw_id, data)
            else:
                data["price_list_id"] = self.price_list_id
                self.hw_ctrl.create(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class CloserWidget(QWidget):
    """Виджет управления доводчиками и координаторами закрывания."""
    
    def __init__(self, closer_ctrl, price_list_ctrl: PriceListController, price_list_id: int = None):
        super().__init__()
        self.closer_ctrl = closer_ctrl
        self.price_list_ctrl = price_list_ctrl
        self.price_list_id = price_list_id or self._get_base_id()
        self._init_ui()
        self._load_data()
    
    def _get_base_id(self):
        try:
            return self.price_list_ctrl.get_base_price_list().id
        except:
            return None
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Вложенные вкладки
        inner_tabs = QTabWidget()
        
        # Доводчики - БЕЗ ID, увеличенная колонка Наименование
        self.closers_inner = QWidget()
        inner_layout = QVBoxLayout(self.closers_inner)
        
        self.table_closers = QTableWidget()
        self.table_closers.setColumnCount(3)
        self.table_closers.setHorizontalHeaderLabels(["Наименование", "Вес двери", "Цена"])
        
        # Фиксированные ширины - увеличенная колонка Наименование
        self.table_closers.setColumnWidth(0, 250)  # Наименование - широкая
        self.table_closers.setColumnWidth(1, 100)  # Вес двери
        self.table_closers.setColumnWidth(2, 100)  # Цена
        
        self.table_closers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        inner_layout.addWidget(self.table_closers)
        
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self._add_closer)
        btn_edit = QPushButton("Редактировать")
        btn_edit.clicked.connect(self._edit_closer)
        btn_delete = QPushButton("Удалить")
        btn_delete.clicked.connect(self._delete_closer)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        inner_layout.addLayout(btn_layout)
        
        inner_tabs.addTab(self.closers_inner, "Доводчики")
        
        # Координаторы закрывания - БЕЗ ID, увеличенная колонка Наименование
        self.coords_inner = QWidget()
        inner_layout2 = QVBoxLayout(self.coords_inner)
        
        self.table_coords = QTableWidget()
        self.table_coords.setColumnCount(2)
        self.table_coords.setHorizontalHeaderLabels(["Наименование", "Цена"])
        
        # Фиксированные ширины - увеличенная колонка Наименование
        self.table_coords.setColumnWidth(0, 250)  # Наименование - широкая
        self.table_coords.setColumnWidth(1, 100)  # Цена
        
        self.table_coords.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        inner_layout2.addWidget(self.table_coords)
        
        btn_layout2 = QHBoxLayout()
        btn_add2 = QPushButton("Добавить")
        btn_add2.clicked.connect(self._add_coord)
        btn_edit2 = QPushButton("Редактировать")
        btn_edit2.clicked.connect(self._edit_coord)
        btn_delete2 = QPushButton("Удалить")
        btn_delete2.clicked.connect(self._delete_coord)
        btn_layout2.addWidget(btn_add2)
        btn_layout2.addWidget(btn_edit2)
        btn_layout2.addWidget(btn_delete2)
        btn_layout2.addStretch()
        inner_layout2.addLayout(btn_layout2)
        
        inner_tabs.addTab(self.coords_inner, "Координаторы закрывания")
        
        layout.addWidget(inner_tabs)
    
    def _load_data(self):
        if not self.price_list_id:
            return
        
        # Загрузка доводчиков (БЕЗ ID)
        self.table_closers.setRowCount(0)
        try:
            closers = self.closer_ctrl.get_closers(self.price_list_id)
            for c in closers:
                row = self.table_closers.rowCount()
                self.table_closers.insertRow(row)
                # Сохраняем ID в UserRole
                item_name = QTableWidgetItem(c.name)
                item_name.setData(Qt.ItemDataRole.UserRole, c.id)
                self.table_closers.setItem(row, 0, item_name)
                self.table_closers.setItem(row, 1, QTableWidgetItem(f"{c.door_weight:,.0f} кг"))
                self.table_closers.setItem(row, 2, QTableWidgetItem(f"{c.price:,.2f}"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        
        # Загрузка координаторов (БЕЗ ID)
        self.table_coords.setRowCount(0)
        try:
            coords = self.closer_ctrl.get_coordinators(self.price_list_id)
            for c in coords:
                row = self.table_coords.rowCount()
                self.table_coords.insertRow(row)
                # Сохраняем ID в UserRole
                item_name = QTableWidgetItem(c.name)
                item_name.setData(Qt.ItemDataRole.UserRole, c.id)
                self.table_coords.setItem(row, 0, item_name)
                self.table_coords.setItem(row, 1, QTableWidgetItem(f"{c.price:,.2f}"))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _add_closer(self):
        if not self.price_list_id:
            return
        dialog = CloserEditDialog(self.price_list_id, None, self.closer_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _edit_closer(self):
        row = self.table_closers.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите доводчик")
            return
        closer_id = self.table_closers.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = CloserEditDialog(self.price_list_id, closer_id, self.closer_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _delete_closer(self):
        row = self.table_closers.currentRow()
        if row < 0:
            return
        closer_id = self.table_closers.item(row, 0).data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Подтверждение", "Удалить доводчик?")
        if reply == QMessageBox.StandardButton.Yes:
            self.closer_ctrl.delete_closer(closer_id)
            self._load_data()
    
    def _add_coord(self):
        if not self.price_list_id:
            return
        dialog = CoordinatorEditDialog(self.price_list_id, None, self.closer_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _edit_coord(self):
        row = self.table_coords.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите координатор")
            return
        coord_id = self.table_coords.item(row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = CoordinatorEditDialog(self.price_list_id, coord_id, self.closer_ctrl)
        if dialog.exec():
            self._load_data()
    
    def _delete_coord(self):
        row = self.table_coords.currentRow()
        if row < 0:
            return
        coord_id = self.table_coords.item(row, 0).data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Подтверждение", "Удалить координатор?")
        if reply == QMessageBox.StandardButton.Yes:
            self.closer_ctrl.delete_coordinator(coord_id)
            self._load_data()


class CloserEditDialog(QDialog):
    """Диалог добавления/редактирования доводчика."""
    
    def __init__(self, price_list_id: int, closer_id: int = None, closer_ctrl = None):
        super().__init__()
        self.price_list_id = price_list_id
        self.closer_id = closer_id
        self.closer_ctrl = closer_ctrl
        self.editing = closer_id is not None
        self.setWindowTitle("Редактирование доводчика" if self.editing else "Новый доводчик")
        self.resize(350, 200)
        self._init_ui()
        if self.editing:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название доводчика")
        form.addRow("Название:", self.inp_name)
        
        self.spin_weight = QDoubleSpinBox()
        self.spin_weight.setRange(0, 500)
        self.spin_weight.setSuffix(" кг")
        self.spin_weight.setDecimals(0)
        form.addRow("Вес двери:", self.spin_weight)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e6)
        self.spin_price.setPrefix("₽ ")
        self.spin_price.setDecimals(2)
        form.addRow("Цена:", self.spin_price)
        
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
        closer = self.closer_ctrl.get_closer_by_id(self.closer_id)
        if closer:
            self.inp_name.setText(closer.name)
            self.spin_weight.setValue(closer.door_weight)
            self.spin_price.setValue(closer.price)
    
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return
        try:
            if self.editing:
                self.closer_ctrl.update_closer(self.closer_id, name, self.spin_weight.value(), self.spin_price.value())
            else:
                self.closer_ctrl.create_closer(self.price_list_id, name, self.spin_weight.value(), self.spin_price.value())
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class CoordinatorEditDialog(QDialog):
    """Диалог добавления/редактирования координатора."""
    
    def __init__(self, price_list_id: int, coord_id: int = None, closer_ctrl = None):
        super().__init__()
        self.price_list_id = price_list_id
        self.coord_id = coord_id
        self.closer_ctrl = closer_ctrl
        self.editing = coord_id is not None
        self.setWindowTitle("Редактирование координатора" if self.editing else "Новый координатор")
        self.resize(350, 150)
        self._init_ui()
        if self.editing:
            self._load_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название координатора")
        form.addRow("Название:", self.inp_name)
        
        self.spin_price = QDoubleSpinBox()
        self.spin_price.setRange(0, 1e6)
        self.spin_price.setPrefix("₽ ")
        self.spin_price.setDecimals(2)
        form.addRow("Цена:", self.spin_price)
        
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
        coord = self.closer_ctrl.get_coordinator_by_id(self.coord_id)
        if coord:
            self.inp_name.setText(coord.name)
            self.spin_price.setValue(coord.price)
    
    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название")
            return
        try:
            if self.editing:
                self.closer_ctrl.update_coordinator(self.coord_id, name, self.spin_price.value())
            else:
                self.closer_ctrl.create_coordinator(self.price_list_id, name, self.spin_price.value())
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


class CreatePriceListDialog(QDialog):
    """Диалог создания нового прайс-листа."""
    
    def __init__(self, counterparty_ctrl=None, parent=None):
        super().__init__(parent)
        self.counterparty_ctrl = counterparty_ctrl
        self.setWindowTitle("Новый прайс-лист")
        self.resize(400, 200)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название прайс-листа")
        form.addRow("Название:", self.inp_name)
        
        # Выбор контрагента (опционально)
        self.combo_counterparty = QComboBox()
        self.combo_counterparty.addItem("— Без привязки —", None)
        if self.counterparty_ctrl:
            try:
                for cp in self.counterparty_ctrl.get_all():
                    self.combo_counterparty.addItem(cp.name, cp.id)
            except Exception:
                pass
        form.addRow("Контрагент:", self.combo_counterparty)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Создать")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def get_data(self) -> dict:
        return {
            "name": self.inp_name.text().strip(),
            "counterparty_id": self.combo_counterparty.currentData()
        }


class PriceTab(QWidget):
    """Вкладка 'Прайс' - управление ценами, типами изделий, стёклами и фурнитурой.
    
    Структура с вложенными вкладками:
    - Дополнительные опции: базовые цены на опции
    - Изделия: type-specific цены
    - Остекление: стёкла и опции для стекла
    - Фурнитура: замки, ручки, цилиндры
    - Самозакрывание: доводчики и координаторы
    """
    
    def __init__(self, price_list_ctrl: PriceListController, counterparty_ctrl=None):
        super().__init__()
        self.price_list_ctrl = price_list_ctrl
        self.counterparty_ctrl = counterparty_ctrl
        self.hw_ctrl = HardwareController()
        self.options_ctrl = OptionsController()
        from controllers.closer_controller import CloserController
        self.closer_ctrl = CloserController()
        self.current_price_list_id = None
        self._init_ui()
        self._load_price_lists()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Выбор прайс-листа + кнопка создать
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Прайс-лист:"))
        self.combo_price_list = QComboBox()
        self.combo_price_list.currentIndexChanged.connect(self._on_price_list_changed)
        selector_layout.addWidget(self.combo_price_list)
        
        btn_new = QPushButton("Создать новый")
        btn_new.clicked.connect(self._create_new_price_list)
        selector_layout.addWidget(btn_new)
        
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        self.tabs = QTabWidget()
        
        # Дополнительные опции (бывшие "Цены")
        self.price_edit_widget = PriceEditWidget(self.price_list_ctrl)
        # Tab order: Изделия -> Остекление -> Фурнитура -> Самозакрывание -> Дополнительные опции
        
        # Изделия
        self.product_types_widget = ProductTypesWidget(self.price_list_ctrl)
        self.tabs.addTab(self.product_types_widget, "Изделия")
        
        # Остекление
        inner_glass = QTabWidget()
        self.glasses_widget = GlassesEditWidget(self.options_ctrl)
        inner_glass.addTab(self.glasses_widget, "Стекло")
        inner_glass.addTab(GlassOptionsWidget(self.options_ctrl), "Опции для стекла")
        self.tabs.addTab(inner_glass, "Остекление")
        
        # Фурнитура
        inner_hw = QTabWidget()
        self.hw_widgets = {}
        for hw_type, label in [(HardwareType.LOCK.value, "Замки"), (HardwareType.HANDLE.value, "Ручки"), (HardwareType.CYLINDER.value, "Цилиндры")]:
            hw_widget = HardwareEditWidget(self.hw_ctrl, hw_type=hw_type)
            self.hw_widgets[hw_type] = hw_widget
            inner_hw.addTab(hw_widget, label)
        self.tabs.addTab(inner_hw, "Фурнитура")
        
        # Самозакрывание
        self.closer_widget = CloserWidget(self.closer_ctrl, self.price_list_ctrl)
        self.tabs.addTab(self.closer_widget, "Самозакрывание")
        
        # Дополнительные опции (последняя вкладка)
        self.tabs.addTab(self.price_edit_widget, "Дополнительные опции")
        
        layout.addWidget(self.tabs)
    
    def _load_price_lists(self):
        self.combo_price_list.blockSignals(True)
        self.combo_price_list.clear()
        
        # Базовый прайс-лист
        try:
            base = self.price_list_ctrl.get_base_price_list()
            self.combo_price_list.addItem(f"[Базовый] {base.name}", base.id)
        except Exception:
            pass
        
        # Персонализированные прайс-листы
        try:
            for pl in self.price_list_ctrl.get_personalized_lists():
                self.combo_price_list.addItem(pl.name, pl.id)
        except Exception:
            pass
        
        self.combo_price_list.blockSignals(False)
        
        # Выбираем первый (базовый)
        if self.combo_price_list.count() > 0:
            self.combo_price_list.setCurrentIndex(0)
            self._on_price_list_changed(0)
    
    def _on_price_list_changed(self, idx):
        pl_id = self.combo_price_list.currentData()
        self.current_price_list_id = pl_id
        
        # Обновляем все виджеты
        self.price_edit_widget.price_list_id = pl_id
        self.price_edit_widget._load_prices()
        
        self.product_types_widget.price_list_id = pl_id
        self.product_types_widget._load_data()
        
        self.glasses_widget.set_price_list_id(pl_id)
        
        for hw_widget in self.hw_widgets.values():
            hw_widget.set_price_list_id(pl_id)
        
        self.closer_widget.price_list_id = pl_id
        self.closer_widget._load_data()
    
    def _create_new_price_list(self):
        dialog = CreatePriceListDialog(self.counterparty_ctrl, self)
        if dialog.exec():
            data = dialog.get_data()
            if data["name"]:
                try:
                    new_pl = self.price_list_ctrl.create_personalized(
                        data["name"],
                        base_id=self.price_list_ctrl.get_base_price_list().id
                    )
                    # Привязка к контрагенту
                    if data["counterparty_id"]:
                        from models.counterparty import Counterparty
                        cp = self.counterparty_ctrl.get_by_id(data["counterparty_id"])
                        if cp:
                            cp.price_list_id = new_pl.id
                            self.counterparty_ctrl.session.flush()
                    
                    self._load_price_lists()
                    
                    # Находим созданный прайс в комбобоксе
                    for i in range(self.combo_price_list.count()):
                        if self.combo_price_list.itemData(i) == new_pl.id:
                            self.combo_price_list.setCurrentIndex(i)
                            break
                    
                    QMessageBox.information(self, "Успех", "Прайс-лист создан")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", str(e))
