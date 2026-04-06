"""Главный конфигуратор: слева параметры/опции, справа таблица КП."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QGroupBox, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QScrollArea, QSplitter, QInputDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any, Optional
from constants import PRODUCT_TYPES, STANDARD_RAL, HardwareType
from utils.validators import validate_dimensions


# Константы для размеров по типам изделий
DIMENSION_RANGES = {
    "Люк": {
        "height_default": 1000,
        "height_values": list(range(300, 1401, 100)),
        "width_default": 1000,
        "width_values": list(range(300, 1401, 100))
    },
    "Дверь": {
        "height_default": 2100,
        "height_values": list(range(1500, 2401, 100)),
        "width_default": 1000,
        "width_values": list(range(500, 1901, 100))
    },
    "Ворота": {
        "height_default": 2500,
        "height_values": list(range(2200, 3501, 100)),
        "width_default": 2000,
        "width_values": list(range(2200, 3501, 100))
    },
    "Фрамуга": {
        "height_default": 200,
        "height_values": list(range(200, 1501, 100)),
        "width_default": 1000,
        "width_values": list(range(500, 2001, 100))
    }
}


class DimensionWidget(QWidget):
    """Виджет для ввода размера: выпадающий список + кнопки +/- внутри."""
    
    def __init__(self, values: list, default_val: int, parent=None):
        super().__init__(parent)
        self._values = values
        self._min = min(values)
        self._max = max(values)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Выпадающий список
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.addItems([str(v) for v in values])
        
        # Найти индекс значения по умолчанию или ближайшего
        default_idx = 0
        for i, v in enumerate(values):
            if v >= default_val:
                default_idx = i
                break
        self.combo.setCurrentIndex(default_idx)
        
        # Кнопки внутри (цвет как у полосы прокрутки)
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(0)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        
        btn_up = QPushButton("▲")
        btn_up.setFixedWidth(18)
        btn_up.setFixedHeight(14)
        btn_up.setStyleSheet("font-size: 7pt; padding: 0; background-color: #a8b2c1; color: white; border: 1px solid #8a95a5;")
        btn_up.clicked.connect(self._on_up)
        
        btn_down = QPushButton("▼")
        btn_down.setFixedWidth(18)
        btn_down.setFixedHeight(14)
        btn_down.setStyleSheet("font-size: 7pt; padding: 0; background-color: #a8b2c1; color: white; border: 1px solid #8a95a5;")
        btn_down.clicked.connect(self._on_down)
        
        btn_layout.addWidget(btn_up)
        btn_layout.addWidget(btn_down)
        
        layout.addWidget(self.combo)
        layout.addLayout(btn_layout)
        
        # Подключение сигнала для ручного ввода
        self.combo.lineEdit().editingFinished.connect(self._on_manual_input)
    
    def _on_up(self):
        idx = self.combo.currentIndex()
        if idx < len(self._values) - 1:
            self.combo.setCurrentIndex(idx + 1)
    
    def _on_down(self):
        idx = self.combo.currentIndex()
        if idx > 0:
            self.combo.setCurrentIndex(idx - 1)
    
    def _on_manual_input(self):
        """Ручной ввод - оставить как есть без автоматических изменений."""
        # Не делаем никаких преобразований - оставляем как пользователь ввёл
        pass
    
    def value(self) -> int:
        try:
            return int(self.combo.currentText())
        except ValueError:
            return self._values[self.combo.currentIndex()] if self.combo.currentIndex() >= 0 else self._values[0]
    
    def setValue(self, val: int):
        # Округление до 10 в меньшую сторону
        rounded = (val // 10) * 10
        if rounded < self._min:
            rounded = self._min
        if rounded > self._max:
            rounded = self._max
        # Найти в списке
        for i, v in enumerate(self._values):
            if v >= rounded:
                self.combo.setCurrentIndex(i)
                return
        self.combo.setCurrentIndex(0)
    
    def setRange(self, values: list):
        """Обновить список значений."""
        self._values = values
        self._min = min(values)
        self._max = max(values)
        current_val = self.value()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems([str(v) for v in values])
        self.combo.blockSignals(False)
        self.setValue(current_val)


class ProductConfiguratorWidget(QWidget):
    """
    Конфигуратор изделия с двумя панелями.
    
    Сигналы:
        calculate_requested: Данные конфигурации для расчёта
        add_to_offer_requested: Готовые данные позиции для добавления в КП
        save_preset_requested: Текущие опции для сохранения в пресет
    """
    calculate_requested = pyqtSignal(dict)
    add_to_offer_requested = pyqtSignal(dict)
    save_preset_requested = pyqtSignal(dict)

    def __init__(self, controller, cpa_ctrl, price_list_ctrl, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cpa_ctrl = cpa_ctrl
        self.price_list_ctrl = price_list_ctrl
        self.current_calc_result = None
        self.current_offer_id = None
        self.current_price_list_id = None
        self.last_offer_items = []  # Для фрамуги - последние изделия в КП
        self._ral_internal_manually_set = False
        self._init_ui()
        self._connect_signals()
        self._load_counterparties()
        self._load_price_lists()
    
    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Сплиттер: левая часть (конфигуратор) / правая часть (таблица)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === ЛЕВАЯ ЧАСТЬ: Конфигуратор (1/3) ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 0. Выбор контрагента и прайса
        grp_context = QGroupBox("Контекст")
        context_layout = QFormLayout()
        
        self.combo_cp = QComboBox()
        self.combo_price = QComboBox()
        self.lbl_price_date = QLabel("")
        self.lbl_price_date.setStyleSheet("font-size: 9pt; color: #666;")
        
        context_layout.addRow("Контрагент:", self.combo_cp)
        
        price_row = QHBoxLayout()
        price_row.addWidget(self.combo_price)
        price_row.addWidget(self.lbl_price_date)
        context_layout.addRow("Прайс:", price_row)
        
        grp_context.setLayout(context_layout)
        scroll_layout.addWidget(grp_context)
        
        # 1. Базовые параметры
        grp_base = QGroupBox("Параметры изделия")
        form_base = QFormLayout()
        
        self.combo_product = QComboBox()
        self.combo_product.addItems(PRODUCT_TYPES.keys())
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(PRODUCT_TYPES[self.combo_product.currentText()])
        
        self.edit_mark = QComboBox()
        self.edit_mark.setEditable(True)
        self.edit_mark.setPlaceholderText("Марка (обозначение в проекте)")
        
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 1000)
        self.spin_qty.setValue(1)
        
        form_base.addRow("Вид:", self.combo_product)
        form_base.addRow("Тип:", self.combo_type)
        form_base.addRow("Марка:", self.edit_mark)
        form_base.addRow("Количество:", self.spin_qty)
        grp_base.setLayout(form_base)
        scroll_layout.addWidget(grp_base)
        
        # 2. Размеры изделия (включая 2 створки)
        grp_size = QGroupBox("Размеры изделия")
        size_form = QFormLayout()
        size_form.setSpacing(10)
        
        self.chk_by_opening = QCheckBox("по проёму")
        
        ranges = DIMENSION_RANGES["Дверь"]
        self.dim_h = DimensionWidget(ranges["height_values"], ranges["height_default"])
        self.dim_w = DimensionWidget(ranges["width_values"], ranges["width_default"])
        
        size_form.addRow("Высота:", self.dim_h)
        size_form.addRow("Ширина:", self.dim_w)
        size_form.addRow("", self.chk_by_opening)
        
        # 2 створки - внутри блока размеров
        double_layout = QHBoxLayout()
        self.chk_double = QCheckBox("2 створки")
        self.lbl_active = QLabel("Активная:")
        self.chk_equal = QCheckBox("равн.")
        self.dim_active = DimensionWidget(list(range(200, 1001, 100)), 900)
        
        # Скрываем всё, кроме чекбокса 2 створки
        self.lbl_active.setVisible(False)
        self.chk_equal.setVisible(False)
        self.dim_active.setVisible(False)
        
        double_layout.addWidget(self.chk_double)
        double_layout.addWidget(self.lbl_active)
        double_layout.addWidget(self.dim_active)
        double_layout.addWidget(self.chk_equal)
        double_layout.addStretch()
        
        size_form.addRow("", double_layout)
        
        grp_size.setLayout(size_form)
        scroll_layout.addWidget(grp_size)
        
        # 3. Цвета и металл
        grp_style = QGroupBox("Оформление")
        style_layout = QVBoxLayout()
        
        # RAL row
        ral_layout = QHBoxLayout()
        ral_layout.setSpacing(10)
        
        ext_label = QLabel("RAL наружн.:")
        ext_label.setFixedWidth(80)
        ral_layout.addWidget(ext_label)
        
        self.combo_ext_color = QComboBox()
        self.combo_ext_color.setEditable(True)
        self.combo_ext_color.setMinimumWidth(80)
        for r in STANDARD_RAL[:10]:
            self.combo_ext_color.addItem(str(r))
        ral_layout.addWidget(self.combo_ext_color)
        
        int_label = QLabel("RAL внутр.:")
        int_label.setFixedWidth(75)
        ral_layout.addWidget(int_label)
        
        self.combo_int_color = QComboBox()
        self.combo_int_color.setEditable(True)
        self.combo_int_color.setMinimumWidth(80)
        self.combo_int_color.addItems([str(r) for r in STANDARD_RAL[:10]])
        ral_layout.addWidget(self.combo_int_color)
        
        style_layout.addLayout(ral_layout)
        
        # Metal row
        metal_layout = QHBoxLayout()
        metal_layout.setSpacing(10)
        
        metal_label = QLabel("Металл:")
        metal_label.setFixedWidth(80)
        metal_layout.addWidget(metal_label)
        
        self.combo_metal = QComboBox()
        self.combo_metal.addItems(["1.0-1.0", "1.2-1.4", "1.4-1.4", "1.5-1.5", "1.4-2.0"])
        self.combo_metal.setMinimumWidth(150)
        metal_layout.addWidget(self.combo_metal)
        metal_layout.addStretch()
        
        style_layout.addLayout(metal_layout)
        
        # Комментарий (кнопка)
        comment_layout = QHBoxLayout()
        comment_layout.setSpacing(2)
        
        self.btn_comment_toggle = QPushButton("Комментарий")
        self.btn_comment_toggle.setStyleSheet("background-color: #a8b2c1; color: white; border: 1px solid #8a95a5; padding: 2px 8px;")
        self.btn_comment_toggle.setCheckable(True)
        
        self.edit_comment = QComboBox()
        self.edit_comment.setEditable(True)
        self.edit_comment.setPlaceholderText("Комментарий к заказу")
        self.edit_comment.setVisible(False)
        
        comment_layout.addWidget(self.btn_comment_toggle)
        comment_layout.addWidget(self.edit_comment)
        comment_layout.addStretch()
        
        style_layout.addLayout(comment_layout)
        
        # Опции цвета
        self.btn_color_options_toggle = QPushButton("▶ Опции цвета")
        self.btn_color_options_toggle.setStyleSheet("background-color: #a8b2c1; color: white; border: 1px solid #8a95a5; text-align: left; padding: 2px 8px; font-size: 10pt;")
        self.btn_color_options_toggle.setCheckable(True)
        style_layout.addWidget(self.btn_color_options_toggle)
        
        # Скрытые опции цвета - чекбоксы на одинаковом расстоянии
        color_options_layout = QHBoxLayout()
        color_options_layout.setSpacing(20)
        
        self.chk_moire = QCheckBox("муар")
        self.chk_lac = QCheckBox("лак")
        self.chk_primer = QCheckBox("грунт")
        
        self.chk_moire.setVisible(False)
        self.chk_lac.setVisible(False)
        self.chk_primer.setVisible(False)
        
        color_options_layout.addWidget(self.chk_moire)
        color_options_layout.addWidget(self.chk_lac)
        color_options_layout.addWidget(self.chk_primer)
        color_options_layout.addStretch()
        
        style_layout.addLayout(color_options_layout)
        
        grp_style.setLayout(style_layout)
        scroll_layout.addWidget(grp_style)
        
        # 4. Фурнитура (без доводчика и цилиндра)
        grp_hardware = QGroupBox("Фурнитура")
        hw_layout = QVBoxLayout()
        
        self.list_hardware = QListWidget()
        self.list_hardware.setMaximumHeight(80)
        hw_layout.addWidget(self.list_hardware)
        
        hw_btn_layout = QHBoxLayout()
        btn_add_hw = QPushButton("+ Замок")
        btn_add_hw.setStyleSheet("background-color: #a8b2c1; color: white; border: 1px solid #8a95a5;")
        btn_add_hw.clicked.connect(lambda: self._add_hardware("Замок"))
        btn_add_handle = QPushButton("+ Ручка")
        btn_add_handle.setStyleSheet("background-color: #a8b2c1; color: white; border: 1px solid #8a95a5;")
        btn_add_handle.clicked.connect(lambda: self._add_hardware("Ручка"))
        hw_btn_layout.addWidget(btn_add_hw)
        hw_btn_layout.addWidget(btn_add_handle)
        hw_btn_layout.addStretch()
        hw_layout.addLayout(hw_btn_layout)
        grp_hardware.setLayout(hw_layout)
        scroll_layout.addWidget(grp_hardware)
        
        # 5. Дополнительные опции
        grp_extra = QGroupBox("Дополнительные опции")
        extra_layout = QGridLayout()
        
        self.chk_threshold = QCheckBox("Автопорог")  # Перенесено из Оформление
        self.chk_closer = QCheckBox("Доводчик")
        self.chk_hinges = QCheckBox("Петли усиленные")
        self.chk_anti_theft = QCheckBox("Антивандальные")
        self.chk_gkl = QCheckBox("ГКЛ наполнение")
        self.chk_mount_ears = QCheckBox("Монтажные уши")
        self.chk_deflector = QCheckBox("Отбойная пластина")
        self.spin_deflector_h = QSpinBox()
        self.spin_deflector_h.setRange(100, 1000)
        self.spin_deflector_h.setSuffix(" мм")
        self.spin_deflector_h.setValue(300)
        
        extra_layout.addWidget(self.chk_threshold, 0, 0)
        extra_layout.addWidget(self.chk_closer, 0, 1)
        extra_layout.addWidget(self.chk_hinges, 1, 0)
        extra_layout.addWidget(self.chk_anti_theft, 1, 1)
        extra_layout.addWidget(self.chk_gkl, 2, 0)
        extra_layout.addWidget(self.chk_mount_ears, 2, 1)
        extra_layout.addWidget(self.chk_deflector, 3, 0)
        extra_layout.addWidget(self.spin_deflector_h, 3, 1)
        grp_extra.setLayout(extra_layout)
        scroll_layout.addWidget(grp_extra)
        
        # 6. Наценки
        grp_markup = QGroupBox("Наценка")
        form_markup = QFormLayout()
        self.spin_markup_pct = QDoubleSpinBox()
        self.spin_markup_pct.setRange(0, 500)
        self.spin_markup_pct.setSuffix(" %")
        self.spin_markup_val = QDoubleSpinBox()
        self.spin_markup_val.setRange(0, 1e6)
        self.spin_markup_val.setPrefix("₽ ")
        form_markup.addRow("Процент:", self.spin_markup_pct)
        form_markup.addRow("Фикс.:", self.spin_markup_val)
        grp_markup.setLayout(form_markup)
        scroll_layout.addWidget(grp_markup)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)
        
        # === ПРАВАЯ ЧАСТЬ: Таблица КП (2/3) ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        grp_table = QGroupBox("Позиции КП")
        table_layout = QVBoxLayout()
        
        self.table_offer = QTableWidget()
        self.table_offer.setColumnCount(8)
        self.table_offer.setHorizontalHeaderLabels(["№", "Марка", "Изделие", "Размеры", "Кол", "Цена", "Наценка", "Итого"])
        self.table_offer.horizontalHeader().setStretchLastSection(True)
        self.table_offer.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_offer.setMinimumHeight(300)
        table_layout.addWidget(self.table_offer)
        
        table_btn_layout = QHBoxLayout()
        btn_new_offer = QPushButton("Новое КП")
        btn_remove = QPushButton("Удалить поз.")
        btn_new_offer.clicked.connect(self._create_new_offer)
        btn_remove.clicked.connect(self._remove_position)
        table_btn_layout.addWidget(btn_new_offer)
        table_btn_layout.addWidget(btn_remove)
        table_btn_layout.addStretch()
        table_layout.addLayout(table_btn_layout)
        grp_table.setLayout(table_layout)
        right_layout.addWidget(grp_table)
        
        # Превью и кнопки
        grp_actions = QGroupBox("Расчёт и действия")
        actions_layout = QVBoxLayout()
        
        self.lbl_preview = QLabel("Нажмите 'Рассчитать'")
        self.lbl_preview.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #0056b3; "
            "padding: 10px; background: #e9ecef; border-radius: 6px;"
        )
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_layout.addWidget(self.lbl_preview)
        
        btn_row = QHBoxLayout()
        self.btn_calc = QPushButton("Рассчитать")
        self.btn_calc.setStyleSheet("background-color: #007bff; color: white; padding: 8px 20px;")
        self.btn_add = QPushButton("Добавить в КП")
        self.btn_add.setStyleSheet("background-color: #28a745; color: white; padding: 8px 20px;")
        self.btn_save_preset = QPushButton("Сохранить пресет")
        btn_row.addWidget(self.btn_calc)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save_preset)
        actions_layout.addLayout(btn_row)
        grp_actions.setLayout(actions_layout)
        right_layout.addWidget(grp_actions)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # 1/3 слева, 2/3 справа
        total_width = 1200
        splitter.setSizes([total_width // 3, total_width * 2 // 3])
        
        main_layout.addWidget(splitter)
        
        self.check_color_visibility()
        self._update_dimensions_for_product()
    
    def _load_counterparties(self):
        self.combo_cp.clear()
        self.combo_cp.addItem("— Выберите —", None)
        try:
            for cp in self.cpa_ctrl.get_all():
                self.combo_cp.addItem(cp.name, cp.id)
        except:
            pass
    
    def _load_price_lists(self):
        """Загрузка прайсов в выпадающий список."""
        self.combo_price.clear()
        
        # Базовый прайс всегда первый
        try:
            base = self.price_list_ctrl.get_base_price_list()
            if base:
                self.combo_price.addItem("Базовый прайс", base.id)
                # Формат даты
                date_str = ""
                if hasattr(base, 'updated_at') and base.updated_at:
                    date_str = base.updated_at.strftime("%d.%m.%Y")
                elif hasattr(base, 'created_at') and base.created_at:
                    date_str = base.created_at.strftime("%d.%m.%Y")
                if date_str:
                    self.combo_price.setItemData(0, date_str, Qt.ItemDataRole.ToolTipRole)
        except:
            pass
        
        # Персональные прайсы - от новых к старым
        try:
            personalized = self.price_list_ctrl.get_personalized_lists()
            # Сортировка по дате (новые первые)
            personalized_sorted = sorted(personalized, key=lambda x: (
                getattr(x, 'created_at', None) or getattr(x, 'updated_at', None) or ""
            ), reverse=True)
            
            for pl in personalized_sorted:
                date_str = ""
                if hasattr(pl, 'updated_at') and pl.updated_at:
                    date_str = pl.updated_at.strftime("%d.%m.%Y")
                elif hasattr(pl, 'created_at') and pl.created_at:
                    date_str = pl.created_at.strftime("%d.%m.%Y")
                
                name = getattr(pl, 'name', f'Прайс #{pl.id}')
                if date_str:
                    name += f" ({date_str})"
                
                self.combo_price.addItem(name, pl.id)
                if date_str:
                    self.combo_price.setItemData(self.combo_price.count() - 1, date_str, Qt.ItemDataRole.ToolTipRole)
        except:
            pass
        
        # Показываем дату текущего выбранного прайса
        self._update_price_date_label()
    
    def _update_price_date_label(self):
        """Обновление отображения даты выбранного прайса."""
        data = self.combo_price.currentData()
        date_text = ""
        
        if data:
            try:
                # Получаем дату из прайса
                pl = self.price_list_ctrl.get_price_list_by_id(data)
                if pl:
                    if hasattr(pl, 'updated_at') and pl.updated_at:
                        date_text = f"изменён: {pl.updated_at.strftime('%d.%m.%Y')}"
                    elif hasattr(pl, 'created_at') and pl.created_at:
                        date_text = f"создан: {pl.created_at.strftime('%d.%m.%Y')}"
            except:
                pass
        
        self.lbl_price_date.setText(date_text)
    
    def check_color_visibility(self):
        is_special = "Квартирная" in self.combo_type.currentText() or "Однолистовая" in self.combo_type.currentText()
        self.combo_int_color.setDisabled(is_special)
    
    def _add_hardware(self, hw_type: str):
        item = QListWidgetItem(f"{hw_type}")
        item.setData(Qt.ItemDataRole.UserRole, hw_type)
        self.list_hardware.addItem(item)
    
    def _connect_signals(self):
        self.combo_product.currentTextChanged.connect(
            lambda t: (self.combo_type.clear(), self.combo_type.addItems(PRODUCT_TYPES[t]))
        )
        self.combo_product.currentTextChanged.connect(self.check_color_visibility)
        self.combo_product.currentTextChanged.connect(self._update_dimensions_for_product)
        self.combo_type.currentTextChanged.connect(self.check_color_visibility)
        
        self.combo_cp.currentIndexChanged.connect(self._on_cp_changed)
        self.combo_price.currentIndexChanged.connect(self._on_price_changed)
        
        # Переключатели скрытых блоков
        self.btn_comment_toggle.toggled.connect(self._toggle_comment)
        self.btn_color_options_toggle.toggled.connect(self._toggle_color_options)
        
        # RAL - автозаполнение внутреннего при изменении
        self.combo_ext_color.currentIndexChanged.connect(self._on_ext_color_changed)
        self.combo_int_color.currentIndexChanged.connect(self._on_int_color_changed)
        
        # 2 створки
        self.chk_double.toggled.connect(self._on_double_toggled)
        self.chk_equal.toggled.connect(self._on_equal_toggled)
        self.dim_w.combo.currentIndexChanged.connect(self._on_width_changed)
        
        self.btn_calc.clicked.connect(self._run_calculation)
        self.btn_add.clicked.connect(self._validate_and_add)
        self.btn_save_preset.clicked.connect(self._emit_preset)
    
    def _update_dimensions_for_product(self):
        """Обновление диапазонов размеров в зависимости от типа изделия."""
        product = self.combo_product.currentText()
        ranges = DIMENSION_RANGES.get(product, DIMENSION_RANGES["Дверь"])
        
        # Обновляем выпадающие списки
        self.dim_h.setRange(ranges["height_values"])
        self.dim_h.setValue(ranges["height_default"])
        
        # Для фрамуги - брать ширину из последнего изделия в КП
        if product == "Фрамуга" and self.last_offer_items:
            last_width = self.last_offer_items[-1].get("width", ranges["width_default"])
            self.dim_w.setRange(ranges["width_values"])
            self.dim_w.setValue(last_width)
        else:
            self.dim_w.setRange(ranges["width_values"])
            self.dim_w.setValue(ranges["width_default"])
        
        # Обновляем диапазон активной створки
        self._update_active_leaf_range()
    
    def _update_active_leaf_range(self):
        """Обновление диапазона активной створки в зависимости от ширины изделия."""
        width = self.dim_w.value()
        max_active = (width // 2) + 100  # Округление до 100 в большую сторону
        if max_active > width:
            max_active = width
        active_values = list(range(200, max_active + 100, 100))
        if not active_values:
            active_values = [200]
        self.dim_active.setRange(active_values)
    
    def _on_width_changed(self, idx: int):
        """При изменении ширины обновить диапазон активной створки."""
        if self.chk_double.isChecked():
            self._update_active_leaf_range()
            if self.chk_equal.isChecked():
                self._calc_equal_active_leaf()
    
    def _on_double_toggled(self, checked: bool):
        """Обработка переключения 2 створок - скрыть/показать все связанные поля."""
        self.lbl_active.setVisible(checked)
        self.chk_equal.setVisible(checked)
        self.dim_active.setVisible(checked)
        
        if not checked:
            self.dim_active.setDisabled(True)
            self.chk_equal.setChecked(False)
        else:
            self._update_active_leaf_range()
            if self.chk_equal.isChecked():
                self._calc_equal_active_leaf()
    
    def _on_equal_toggled(self, checked: bool):
        """Обработка переключения 'равн.'"""
        self.dim_active.setDisabled(checked)
        if checked:
            self._calc_equal_active_leaf()
    
    def _calc_equal_active_leaf(self):
        """Расчёт равной активной створки: ширина/2 округлённая до 100 в большую сторону."""
        width = self.dim_w.value()
        active = ((width // 2) + 99) // 100 * 100
        if active < 200:
            active = 200
        self.dim_active.setValue(active)
    
    def _toggle_comment(self, expanded: bool):
        """Переключение видимости блока Комментарий."""
        self.edit_comment.setVisible(expanded)
        self.btn_comment_toggle.setText("▼" if expanded else "▶")
    
    def _toggle_color_options(self, expanded: bool):
        """Переключение видимости блока Опции цвета."""
        self.btn_color_options_toggle.setText("▼ Опции цвета" if expanded else "▶ Опции цвета")
        
        self.chk_moire.setVisible(expanded)
        self.chk_lac.setVisible(expanded)
        self.chk_primer.setVisible(expanded)
    
    def _on_ext_color_changed(self):
        """Автозаполнение RAL внутреннего из наружного."""
        if not self._ral_internal_manually_set:
            ext_val = self.combo_ext_color.currentText()
            # Найти значение в списке или добавить
            idx = self.combo_int_color.findText(ext_val)
            if idx >= 0:
                self.combo_int_color.setCurrentIndex(idx)
            else:
                self.combo_int_color.setCurrentText(ext_val)
    
    def _on_int_color_changed(self):
        """Пользователь изменил внутренний цвет - запоминаем что это ручной ввод."""
        self._ral_internal_manually_set = True
    
    def _on_cp_changed(self, idx: int):
        """Обработка выбора контрагента - автовыбор прайса."""
        cp_id = self.combo_cp.currentData()
        if cp_id:
            try:
                cp = self.cpa_ctrl.get_by_id(cp_id)
                if cp and cp.price_list_id:
                    # У контрагента есть прайс - выбираем его
                    self._select_counterparty_price(cp.price_list_id)
                else:
                    # Нет прайса - выбираем базовый
                    self.combo_price.setCurrentIndex(0)
            except:
                self.combo_price.setCurrentIndex(0)
        else:
            self.combo_price.setCurrentIndex(0)
    
    def _select_counterparty_price(self, price_list_id: int):
        """Выбор прайса контрагента в выпадающем списке."""
        for i in range(self.combo_price.count()):
            if self.combo_price.itemData(i) == price_list_id:
                self.combo_price.setCurrentIndex(i)
                return
        self._on_price_changed(self.combo_price.currentIndex())
    
    def _on_price_changed(self, idx: int):
        """Обработка изменения прайса - пересчёт КП."""
        self._update_price_date_label()
        
        # Сбрасываем флаг ручного ввода внутреннего цвета при смене прайса
        self._ral_internal_manually_set = False
        
        if self.table_offer.rowCount() > 0:
            self._recalculate_all_items()
    
    def _recalculate_all_items(self):
        """Пересчёт всех позиций КП при смене прайса."""
        # TODO: реализовать пересчёт
        pass
    
    def _run_calculation(self):
        self.check_color_visibility()
        
        # Учитываем "по проёму"
        calc_height = self.dim_h.value()
        calc_width = self.dim_w.value()
        
        if self.chk_by_opening.isChecked():
            calc_height -= 20
            calc_width -= 30
        
        data = self._collect_config()
        data["height"] = calc_height
        data["width"] = calc_width
        
        valid, err = validate_dimensions(data["product_type"], calc_height, calc_width)
        if not valid:
            self.lbl_preview.setText(f"Ошибка: {err}")
            self.lbl_preview.setStyleSheet("color: #dc3545;")
            return
        
        self.calculate_requested.emit(data)
    
    def _collect_config(self) -> Dict[str, Any]:
        hw_items = []
        for i in range(self.list_hardware.count()):
            item = self.list_hardware.item(i)
            hw_items.append(item.text())
        
        # Учитываем "по проёму"
        calc_height = self.dim_h.value()
        calc_width = self.dim_w.value()
        
        if self.chk_by_opening.isChecked():
            calc_height -= 20
            calc_width -= 30
        
        return {
            "product_type": self.combo_product.currentText(),
            "subtype": self.combo_type.currentText(),
            "mark": self.edit_mark.currentText(),
            "height": calc_height,
            "width": calc_width,
            "original_height": self.dim_h.value(),
            "original_width": self.dim_w.value(),
            "by_opening": self.chk_by_opening.isChecked(),
            "quantity": self.spin_qty.value(),
            "is_double_leaf": self.chk_double.isChecked(),
            "active_leaf_width": self.dim_active.value() if self.chk_double.isChecked() else 0,
            "color_external": self.combo_ext_color.currentText(),
            "color_internal": self.combo_int_color.currentText(),
            "metal_thickness": self.combo_metal.currentText(),
            "threshold": self.chk_threshold.isChecked(),
            "markup_percent": self.spin_markup_pct.value(),
            "markup_abs": self.spin_markup_val.value(),
            "glass_items": [],
            "hardware_items": hw_items,
            "grilles": [],
            "comment": self.edit_comment.currentText() if self.edit_comment.isVisible() else "",
            "color_options": {
                "moire": self.chk_moire.isChecked(),
                "lac": self.chk_lac.isChecked(),
                "primer": self.chk_primer.isChecked()
            },
            "extra_options": {
                "closer": self.chk_closer.isChecked(),
                "hinges": self.chk_hinges.isChecked(),
                "anti_theft": self.chk_anti_theft.isChecked(),
                "gkl": self.chk_gkl.isChecked(),
                "mount_ears": self.chk_mount_ears.isChecked(),
                "deflector": self.chk_deflector.isChecked(),
                "deflector_height": self.spin_deflector_h.value() if self.chk_deflector.isChecked() else 0
            }
        }
    
    def on_calculation_result(self, result: Dict[str, Any]):
        if result.get("success"):
            qty = result.get("quantity", 1)
            price = result.get("total_price", 0)
            self.lbl_preview.setText(f"Итого за {qty} шт.: {price:,.2f} ₽")
            self.lbl_preview.setStyleSheet("color: #28a745; font-weight: bold;")
            self.current_calc_result = result
        else:
            self.lbl_preview.setText(f"Ошибка: {result.get('error', 'Неизвестная')}")
            self.lbl_preview.setStyleSheet("color: #dc3545;")
    
    def _validate_and_add(self):
        if not hasattr(self, 'current_calc_result') or not self.current_calc_result:
            QMessageBox.warning(self, "Внимание", "Сначала выполните расчёт.")
            return
        
        config = self._collect_config()
        config.update(self.current_calc_result)
        self.add_to_offer_requested.emit(config)
        
        # Сохраняем для фрамуги
        self.last_offer_items.append({"width": config["width"], "height": config["height"]})
    
    def _emit_preset(self):
        data = self._collect_config()
        if hasattr(self, 'current_calc_result') and self.current_calc_result:
            data.update(self.current_calc_result)
        name, ok = QInputDialog.getText(self, "Пресет", "Название набора:")
        if ok and name:
            self.save_preset_requested.emit({"name": name, "options": data})
    
    def _create_new_offer(self):
        self.add_to_offer_requested.emit({"_action": "create_offer"})
    
    def _remove_position(self):
        row = self.table_offer.currentRow()
        if row >= 0:
            self.table_offer.removeRow(row)
            self._update_row_numbers()
            self._update_total()
            
            # Обновляем последние изделия для фрамуги
            if self.last_offer_items and row < len(self.last_offer_items):
                self.last_offer_items.pop(row)
    
    def add_position_to_table(self, item_data: dict):
        row = self.table_offer.rowCount()
        self.table_offer.insertRow(row)
        
        self.table_offer.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table_offer.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Марка между № и Изделие
        self.table_offer.setItem(row, 1, QTableWidgetItem(item_data.get("mark", "")))
        
        self.table_offer.setItem(row, 2, QTableWidgetItem(item_data.get("product_type", "")))
        
        # Размеры с учётом "по проёму"
        by_opening = item_data.get("by_opening", False)
        w = item_data.get("width", 0)
        h = item_data.get("height", 0)
        if by_opening:
            orig_w = item_data.get("original_width", w)
            orig_h = item_data.get("original_height", h)
            size_str = f"{int(orig_w)}x{int(orig_h)} → {int(w)}x{int(h)}"
        else:
            size_str = f"{int(w)}x{int(h)}"
        self.table_offer.setItem(row, 3, QTableWidgetItem(size_str))
        
        self.table_offer.setItem(row, 4, QTableWidgetItem(str(item_data.get("quantity", 1))))
        self.table_offer.setItem(row, 5, QTableWidgetItem(f"{item_data.get('base_price', 0):,.2f}"))
        
        markup = f"{item_data.get('markup_percent', 0)}%"
        self.table_offer.setItem(row, 6, QTableWidgetItem(markup))
        self.table_offer.setItem(row, 7, QTableWidgetItem(f"{item_data.get('final_price', 0):,.2f} ₽"))
        
        self._update_total()
    
    def _update_row_numbers(self):
        for r in range(self.table_offer.rowCount()):
            self.table_offer.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.table_offer.item(r, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def _update_total(self):
        total = 0.0
        for r in range(self.table_offer.rowCount()):
            item = self.table_offer.item(r, 7)
            if item:
                try:
                    total += float(item.text().replace(" ₽", "").replace(",", ""))
                except:
                    pass
        self.lbl_preview.setText(f"Итого КП: {total:,.2f} ₽")
        self.lbl_preview.setStyleSheet("color: #28a745; font-weight: bold; font-size: 12pt;")
    
    def set_offer_id(self, offer_id: int):
        self.current_offer_id = offer_id
    
    def get_price_list_id(self) -> int:
        return self.combo_price.currentData() or None