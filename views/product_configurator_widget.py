"""Главный конфигуратор: слева параметры/опции, справа таблица КП."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QGroupBox, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QPushButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QScrollArea, QSplitter, QInputDialog, QListWidget, QListWidgetItem,
    QMenu, QDialog, QPlainTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QWheelEvent, QFontMetrics
from typing import Dict, Any, Optional
from constants import PRODUCT_TYPES, STANDARD_RAL, HardwareType
from utils.validators import validate_dimensions
from controllers.hardware_controller import HardwareController
from controllers.options_controller import OptionsController
from controllers.closer_controller import CloserController


class ProtectedComboBox(QComboBox):
    """Защищённый комбобокс - раскрывается только при явном щелчке.
    
    Предотвращает случайное раскрытие при наведении курсора
    и изменение значений колёсиком мыши без явного фокуса.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._require_explicit_click = True
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def wheelEvent(self, event: QWheelEvent):
        """Блокируем изменение значения колёсиком мыши без фокуса."""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()
    
    def mousePressEvent(self, event):
        """Обрабатываем только явный левый щелчок для раскрытия."""
        if self._require_explicit_click and event.button() == Qt.MouseButton.LeftButton:
            # Проверяем, что клик в области раскрытия
            # Если комбобокс уже "горячий" - раскрываем, иначе просто устанавливаем фокус
            if self.isHot():
                super().mousePressEvent(event)
            else:
                # Не раскрываем, только фокус
                self.setFocus()
                event.accept()
        else:
            super().mousePressEvent(event)
    
    def isHot(self) -> bool:
        """Проверяет, находится ли курсор над кнопкой раскрытия."""
        # Получаем геометрию кнопки раскрытия (стрелочка справа)
        # Стандартная ширина ~20px
        width = self.width()
        height = self.height()
        mouse_x = self.mapFromGlobal(self.cursor().pos()).x()
        # Считаем что курсор над стрелочкой если в правой части
        return mouse_x >= width - 25


class GlassEditDialog(QDialog):
    """Модальное окно добавления/редактирования стекла с размерами и опциями."""
    
    def __init__(self, glass_data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить стекло" if not glass_data else "Редактировать стекло")
        self.resize(450, 500)
        self._glass_data = glass_data or {}
        self._selected_options = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Выбор стекла
        form = QFormLayout()
        self.combo_glass_type = ProtectedComboBox()
        self.combo_glass_type.setMinimumWidth(200)
        form.addRow("Стекло:", self.combo_glass_type)
        
        # Размеры стекла
        self.spin_height = QSpinBox()
        self.spin_height.setRange(100, 2000)
        self.spin_height.setSingleStep(10)
        self.spin_height.setSuffix(" мм")
        self.spin_height.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addRow("Высота:", self.spin_height)
        
        self.spin_width = QSpinBox()
        self.spin_width.setRange(100, 2000)
        self.spin_width.setSingleStep(10)
        self.spin_width.setSuffix(" мм")
        self.spin_width.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addRow("Ширина:", self.spin_width)
        
        layout.addLayout(form)
        
        # Секция опций
        options_group = QGroupBox("Опции стекла (до 3)")
        opts_layout = QVBoxLayout()
        
        # Доступные опции
        self.combo_option = ProtectedComboBox()
        self.combo_option.setMinimumWidth(200)
        opts_layout.addWidget(QLabel("Добавить опцию:"))
        
        opt_row = QHBoxLayout()
        opt_row.addWidget(self.combo_option)
        
        self.btn_add_option = QPushButton("+")
        self.btn_add_option.setFixedWidth(30)
        self.btn_add_option.setStyleSheet("background-color: #28a745; color: white;")
        opt_row.addWidget(self.btn_add_option)
        opts_layout.addLayout(opt_row)
        
        # Список выбранных опций
        self.list_options = QListWidget()
        self.list_options.setMaximumHeight(80)
        opts_layout.addWidget(self.list_options)
        
        options_group.setLayout(opts_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Сохранить")
        btn_ok.setStyleSheet("background-color: #007bff; color: white; padding: 5px 15px;")
        btn_cancel = QPushButton("Отмена")
        btn_cancel.setStyleSheet("padding: 5px 15px;")
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        layout.addLayout(btn_layout)
        
        # Сигнал для добавления опции
        self.btn_add_option.clicked.connect(self._on_add_option)
        
        # Заполнить данными если редактирование
        if self._glass_data:
            self._load_existing_data()
    
    def _on_add_option(self):
        """Добавить выбранную опцию в список."""
        # Проверяем лимит 3 опций
        if len(self._selected_options) >= 3:
            QMessageBox.warning(self, "Внимание", "Максимум 3 опции на стекло.")
            return
        
        opt_id = self.combo_option.currentData()
        if opt_id:
            opt_name = self.combo_option.currentText().split(" (")[0]
            opt_price = 0
            # Получаем цену из списка
            opt_data = self.combo_option.currentData()
            if isinstance(opt_data, dict):
                opt_price = opt_data.get("price_per_m2", 0)
            
            # Проверяем, не добавлена ли уже эта опция
            for opt in self._selected_options:
                if opt.get("id") == opt_id:
                    QMessageBox.warning(self, "Внимание", "Эта опция уже добавлена.")
                    return
            
            # Добавляем в список
            self.list_options.addItem(self.combo_option.currentText())
            self._selected_options.append({
                "id": opt_id,
                "name": opt_name,
                "price_per_m2": opt_price
            })
    
    def _load_existing_data(self):
        """Загрузить существующие данные стекла."""
        # Установить значение высоты
        if "height" in self._glass_data:
            self.spin_height.setValue(self._glass_data.get("height", 500))
        if "width" in self._glass_data:
            self.spin_width.setValue(self._glass_data.get("width", 500))
        
        # Загрузить опции
        options = self._glass_data.get("options", [])
        for opt in options:
            self.list_options.addItem(opt["name"])
            self._selected_options.append(opt)
    
    def set_glass_types(self, glass_types: list):
        """Установить доступные типы стёкол."""
        self.combo_glass_type.clear()
        for g in glass_types:
            self.combo_glass_type.addItem(g["name"], g["id"])
    
    def set_glass_options(self, options: list):
        """Установить доступные опции (глобальные)."""
        self.combo_option.clear()
        for o in options:
            self.combo_option.addItem(f"{o['name']} ({o['price_per_m2']:.0f} руб/м²)", o["id"])
    
    def set_all_options(self, options: list):
        """Установить все доступные опции."""
        self.combo_option.clear()
        for o in options:
            self.combo_option.addItem(f"{o['name']} ({o['price_per_m2']:.0f} руб/м²)", o["id"])
    
    def get_data(self) -> dict:
        """Получить данные стекла."""
        return {
            "glass_type_id": self.combo_glass_type.currentData(),
            "glass_type_name": self.combo_glass_type.currentText(),
            "height": self.spin_height.value(),
            "width": self.spin_width.value(),
            "options": self._selected_options.copy()
        }


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
        
        # Выпадающий список - увеличенная ширина на 50%
        self.combo = QComboBox()
        self.combo.setMinimumWidth(120)  # было ~80, теперь 120 (+50%)
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
        # Шаг 10 вместо 100
        new_idx = min(idx + 1, len(self._values) - 1)
        self.combo.setCurrentIndex(new_idx)
    
    def _on_down(self):
        idx = self.combo.currentIndex()
        # Шаг 10 вместо 100
        new_idx = max(idx - 1, 0)
        self.combo.setCurrentIndex(new_idx)
    
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
        self.current_row_index = -1  # Текущая выбранная строка для редактирования
        self.last_offer_items = []  # Для фрамуги - последние изделия в КП
        self._ral_internal_manually_set = False
        
        # Controllers for dropdowns
        self.hw_ctrl = HardwareController()
        self.opt_ctrl = OptionsController()
        self.closer_ctrl = CloserController()
        
        self._init_ui()
        self._connect_signals()
        self._load_counterparties()
        self._load_price_lists()
        self._load_hardware_options()
    
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
        
        self.combo_cp = ProtectedComboBox()
        self.combo_price = ProtectedComboBox()
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
        
        self.combo_product = ProtectedComboBox()
        self.combo_product.addItems(PRODUCT_TYPES.keys())
        
        self.combo_type = ProtectedComboBox()
        self.combo_type.addItems(PRODUCT_TYPES[self.combo_product.currentText()])
        
        self.edit_mark = ProtectedComboBox()
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
        size_layout = QVBoxLayout()
        size_layout.setSpacing(8)
        
        # Подблок "Размер по коробке" / "Размер по проему"
        self.box_by_frame = QGroupBox("Размер по коробке")
        self.box_by_frame.setCheckable(False)
        frame_layout = QHBoxLayout()
        frame_layout.setSpacing(10)
        
        h_frame_label = QLabel("Высота:")
        self.dim_h = DimensionWidget(DIMENSION_RANGES["Дверь"]["height_values"], DIMENSION_RANGES["Дверь"]["height_default"])
        # Центрирование
        self.dim_h.combo.setEditable(True)
        self.dim_h.combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(h_frame_label)
        frame_layout.addWidget(self.dim_h)
        
        w_frame_label = QLabel("Ширина:")
        self.dim_w = DimensionWidget(DIMENSION_RANGES["Дверь"]["width_values"], DIMENSION_RANGES["Дверь"]["width_default"])
        # Центрирование
        self.dim_w.combo.setEditable(True)
        self.dim_w.combo.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(w_frame_label)
        frame_layout.addWidget(self.dim_w)
        frame_layout.addStretch()
        
        self.box_by_frame.setLayout(frame_layout)
        size_layout.addWidget(self.box_by_frame)
        
        # Подблок "Размер по проёму"
        self.chk_by_opening = QCheckBox("Размер по проёму")
        size_layout.addWidget(self.chk_by_opening)
        
        # Поля минус - показываются только при "2 створки"
        minus_layout = QHBoxLayout()
        minus_layout.setSpacing(10)
        self.lbl_height_minus = QLabel("Высота минус:")
        self.lbl_height_minus.setVisible(False)
        minus_layout.addWidget(self.lbl_height_minus)
        
        self.spin_by_opening_height = QSpinBox()
        self.spin_by_opening_height.setRange(0, 500)
        self.spin_by_opening_height.setSingleStep(10)
        self.spin_by_opening_height.setSuffix(" мм")
        self.spin_by_opening_height.setValue(20)
        self.spin_by_opening_height.setVisible(False)
        self.spin_by_opening_height.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minus_layout.addWidget(self.spin_by_opening_height)
        
        self.lbl_width_minus = QLabel("Ширина минус:")
        self.lbl_width_minus.setVisible(False)
        minus_layout.addWidget(self.lbl_width_minus)
        
        self.spin_by_opening_width = QSpinBox()
        self.spin_by_opening_width.setRange(0, 500)
        self.spin_by_opening_width.setSingleStep(10)
        self.spin_by_opening_width.setSuffix(" мм")
        self.spin_by_opening_width.setValue(30)
        self.spin_by_opening_width.setVisible(False)
        self.spin_by_opening_width.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minus_layout.addWidget(self.spin_by_opening_width)
        
        minus_layout.addStretch()
        size_layout.addLayout(minus_layout)
        
        # 2 створки
        double_layout = QHBoxLayout()
        double_layout.setSpacing(10)
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
        
        size_layout.addLayout(double_layout)
        
        grp_size.setLayout(size_layout)
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
        
        self.combo_ext_color = ProtectedComboBox()
        self.combo_ext_color.setEditable(True)
        self.combo_ext_color.setMinimumWidth(80)
        for r in STANDARD_RAL[:10]:
            self.combo_ext_color.addItem(str(r))
        ral_layout.addWidget(self.combo_ext_color)
        
        int_label = QLabel("RAL внутр.:")
        int_label.setFixedWidth(75)
        ral_layout.addWidget(int_label)
        
        self.combo_int_color = ProtectedComboBox()
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
        
        self.combo_metal = ProtectedComboBox()
        self.combo_metal.addItems(["1.0-1.0", "1.2-1.4", "1.4-1.4", "1.5-1.5", "1.4-2.0"])
        self.combo_metal.setMinimumWidth(150)
        metal_layout.addWidget(self.combo_metal)
        metal_layout.addStretch()
        
        style_layout.addLayout(metal_layout)
        
        # Комментарий (переработано) - добавлена кнопка и текстовый комментарий
        comment_layout = QHBoxLayout()
        comment_layout.setSpacing(2)

        self.btn_add_comment = QPushButton("Добавить комментарий")
        self.btn_add_comment.setStyleSheet("background-color: #a8b2c1; color: white; border: 1px solid #8a95a5; padding: 2px 8px;")
        self.btn_add_comment.setCheckable(True)

        self.comment_text_edit = QPlainTextEdit()
        self.comment_text_edit.setPlaceholderText("Введите комментарий к заказу")
        self.comment_text_edit.setVisible(False)
        self.comment_text_edit.setFixedHeight(60)  # около 2 строк

        comment_layout.addWidget(self.btn_add_comment)
        comment_layout.addWidget(self.comment_text_edit)
        comment_layout.addStretch()

        style_layout.addLayout(comment_layout)
        
        # Опции цвета
        self.btn_color_options_toggle = QPushButton("Опции цвета")
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
        
        # 4. Фурнитура - с выпадающими списками из прайса
        grp_hardware = QGroupBox("Фурнитура")
        hw_layout = QVBoxLayout()
        
        # Списки оборудования из прайса
        # Замок
        lock_layout = QHBoxLayout()
        lock_layout.addWidget(QLabel("Замок:"))
        self.combo_lock = ProtectedComboBox()
        self.combo_lock.setMinimumWidth(200)
        self.btn_add_lock = QPushButton("+")
        self.btn_add_lock.setFixedWidth(25)
        self.btn_add_lock.setStyleSheet("background-color: #a8b2c1; color: white;")
        self.btn_add_lock.clicked.connect(self._add_selected_hardware)
        lock_layout.addWidget(self.combo_lock)
        lock_layout.addWidget(self.btn_add_lock)
        hw_layout.addLayout(lock_layout)
        
        # Ручка
        handle_layout = QHBoxLayout()
        handle_layout.addWidget(QLabel("Ручка:"))
        self.combo_handle = ProtectedComboBox()
        self.combo_handle.setMinimumWidth(200)
        self.btn_add_handle = QPushButton("+")
        self.btn_add_handle.setFixedWidth(25)
        self.btn_add_handle.setStyleSheet("background-color: #a8b2c1; color: white;")
        self.btn_add_handle.clicked.connect(self._add_selected_hardware)
        handle_layout.addWidget(self.combo_handle)
        handle_layout.addWidget(self.btn_add_handle)
        hw_layout.addLayout(handle_layout)
        
        # Цилиндр (появляется если выбран цилиндровый замок)
        cyl_layout = QHBoxLayout()
        cyl_layout.addWidget(QLabel("Цилиндр:"))
        self.combo_cylinder = ProtectedComboBox()
        self.combo_cylinder.setMinimumWidth(200)
        self.btn_add_cyl = QPushButton("+")
        self.btn_add_cyl.setFixedWidth(25)
        self.btn_add_cyl.setStyleSheet("background-color: #a8b2c1; color: white;")
        self.btn_add_cyl.clicked.connect(self._add_selected_hardware)
        cyl_layout.addWidget(self.combo_cylinder)
        cyl_layout.addWidget(self.btn_add_cyl)
        hw_layout.addLayout(cyl_layout)
        
        # Список выбранной фурнитуры с кнопкой удаления
        hw_list_layout = QHBoxLayout()
        self.list_hardware = QListWidget()
        self.list_hardware.setMaximumHeight(80)
        hw_list_layout.addWidget(self.list_hardware)
        
        hw_btn_layout = QVBoxLayout()
        hw_btn_layout.setSpacing(2)
        self.btn_del_hardware = QPushButton("✕")
        self.btn_del_hardware.setFixedWidth(25)
        self.btn_del_hardware.setStyleSheet("background-color: #dc3545; color: white;")
        self.btn_del_hardware.clicked.connect(self._remove_selected_hardware)
        hw_btn_layout.addWidget(self.btn_del_hardware)
        hw_btn_layout.addStretch()
        hw_list_layout.addLayout(hw_btn_layout)
        
        hw_layout.addLayout(hw_list_layout)
        
        grp_hardware.setLayout(hw_layout)
        scroll_layout.addWidget(grp_hardware)
        
        # 4.1. Стекла и опции
        grp_glass = QGroupBox("Стекло и опции")
        glass_layout = QVBoxLayout()
        
        # Кнопка добавления стекла через модальное окно
        self.btn_add_glass = QPushButton("Добавить стекло")
        self.btn_add_glass.setStyleSheet("background-color: #28a745; color: white; padding: 5px 15px;")
        glass_layout.addWidget(self.btn_add_glass)
        
        # Список выбранных стекол с кнопкой удаления
        glass_list_layout = QHBoxLayout()
        self.list_glass = QListWidget()
        self.list_glass.setMaximumHeight(120)
        # Включаем двойной щелчок для редактирования
        self.list_glass.itemDoubleClicked.connect(self._edit_glass_item)
        glass_list_layout.addWidget(self.list_glass)
        
        glass_btn_layout = QVBoxLayout()
        glass_btn_layout.setSpacing(2)
        self.btn_del_glass = QPushButton("✕")
        self.btn_del_glass.setFixedWidth(25)
        self.btn_del_glass.setStyleSheet("background-color: #dc3545; color: white;")
        self.btn_del_glass.clicked.connect(self._remove_selected_glass)
        glass_btn_layout.addWidget(self.btn_del_glass)
        glass_btn_layout.addStretch()
        glass_list_layout.addLayout(glass_btn_layout)
        
        glass_layout.addLayout(glass_list_layout)
        
        # Подсказка
        self.lbl_glass_options_hint = QLabel("Двойной щелчок - редактировать")
        self.lbl_glass_options_hint.setStyleSheet("font-size: 9pt; color: #666;")
        glass_layout.addWidget(self.lbl_glass_options_hint)
        
        grp_glass.setLayout(glass_layout)
        scroll_layout.addWidget(grp_glass)
        
        # Хранилище данных о выбранных стёклах
        self._glass_items_data = []  # list of dict: {glass_type_id, glass_type_name, height, width, options}
        
        # 5. Дополнительные опции
        grp_extra = QGroupBox("Дополнительные опции")
        extra_layout = QGridLayout()
        
        self.chk_threshold = QCheckBox("Автопорог")  # Перенесено из Оформление
        self.chk_hinges = QCheckBox("Кол-во петель")
        self.chk_anti_theft = QCheckBox("Противосъёмные штыри")
        self.chk_gkl = QCheckBox("ГКЛ наполнение")
        self.chk_mount_ears = QCheckBox("Монтажные уши")
        self.mount_ears_input = ProtectedComboBox()
        self.mount_ears_input.setEditable(True)
        self.mount_ears_input.addItems(["4", "6", "8", "10"])
        self.mount_ears_input.setVisible(False)
        self.chk_deflector = QCheckBox("Отбойная пластина")
        # Дефлектор: новый input
        self.deflector_height_input = None  # будет создан ниже
        self.spin_deflector_h = QSpinBox()
        self.spin_deflector_h.setRange(100, 1000)
        self.spin_deflector_h.setSuffix(" мм")
        self.spin_deflector_h.setValue(300)
        self.spin_deflector_h.setVisible(False)
        self.deflector_two_sided = QCheckBox("с 2-х сторон")
        self.deflector_two_sided.setVisible(False)

        # Подменяем разметку: создаём контейнер для петель
        self.hinges_single_widget = QWidget()
        hs_layout = QHBoxLayout(self.hinges_single_widget)
        hs_layout.setContentsMargins(0, 0, 0, 0)
        hs_layout.addWidget(QLabel("Кол-во петель (одна створка):"))
        self.spin_hinges_single = QSpinBox()
        self.spin_hinges_single.setRange(1, 8)
        self.spin_hinges_single.setValue(2)
        hs_layout.addWidget(self.spin_hinges_single)

        self.hinges_double_widget = QWidget()
        hd_layout = QHBoxLayout(self.hinges_double_widget)
        hd_layout.setContentsMargins(0, 0, 0, 0)
        hd_layout.addWidget(QLabel("Активная створка:"))
        self.spin_hinges_active = QSpinBox()
        self.spin_hinges_active.setRange(1, 8)
        self.spin_hinges_active.setValue(2)
        hd_layout.addWidget(self.spin_hinges_active)
        hd_layout.addWidget(QLabel("Пассивная створка:"))
        self.spin_hinges_passive = QSpinBox()
        self.spin_hinges_passive.setRange(1, 8)
        self.spin_hinges_passive.setValue(2)
        hd_layout.addWidget(self.spin_hinges_passive)

        self.hinges_container = QWidget()
        hinges_box = QVBoxLayout(self.hinges_container)
        hinges_box.setContentsMargins(0, 0, 0, 0)
        hinges_box.addWidget(self.hinges_single_widget)
        hinges_box.addWidget(self.hinges_double_widget)
        self.hinges_single_widget.setVisible(False)
        self.hinges_double_widget.setVisible(False)

        # Объединяем отбойную пластину и её настройки в одну строку
        deflector_layout = QHBoxLayout()
        deflector_layout.addWidget(self.chk_deflector)
        deflector_layout.addWidget(self.spin_deflector_h)
        deflector_layout.addWidget(self.deflector_two_sided)
        deflector_layout.addStretch()
        
        # Объединяем монтажные уши и кол-во в одну строку
        mount_ears_layout = QHBoxLayout()
        mount_ears_layout.addWidget(self.chk_mount_ears)
        mount_ears_layout.addWidget(self.mount_ears_input)
        mount_ears_layout.addStretch()
        
        # Создаём новую компоновку на основе QVBoxLayout
        extra_vbox = QVBoxLayout()
        extra_vbox.addWidget(self.chk_threshold)
        
        hinges_row = QHBoxLayout()
        hinges_row.addWidget(self.chk_hinges)
        hinges_row.addWidget(self.hinges_container)
        hinges_row.addStretch()
        extra_vbox.addLayout(hinges_row)
        
        extra_vbox.addWidget(self.chk_anti_theft)
        extra_vbox.addWidget(self.chk_gkl)
        extra_vbox.addLayout(mount_ears_layout)
        extra_vbox.addLayout(deflector_layout)
        
        grp_extra.setLayout(extra_vbox)
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

        # 5b. Доводчик / Координатор - новая логика с учётом створок
        grp_closer_new = QGroupBox("Доводчик / Координатор")
        closer_new_layout = QVBoxLayout()
        
        # Доводчик 1 (для одностворчатых или первой створки)
        closer1_layout = QHBoxLayout()
        self.chk_closer1 = QCheckBox("Доводчик 1:")
        self.combo_closer1 = ProtectedComboBox()
        self.combo_closer1.setMinimumWidth(150)
        self.combo_closer1.setEnabled(False)
        closer1_layout.addWidget(self.chk_closer1)
        closer1_layout.addWidget(self.combo_closer1)
        closer1_layout.addStretch()
        closer_new_layout.addLayout(closer1_layout)
        
        # Доводчик 2 (только для 2 створок)
        closer2_layout = QHBoxLayout()
        self.chk_closer2 = QCheckBox("Доводчик 2:")
        self.chk_closer2.setVisible(False)
        self.combo_closer2 = ProtectedComboBox()
        self.combo_closer2.setMinimumWidth(150)
        self.combo_closer2.setVisible(False)
        self.combo_closer2.setEnabled(False)
        closer2_layout.addWidget(self.chk_closer2)
        closer2_layout.addWidget(self.combo_closer2)
        closer2_layout.addStretch()
        closer_new_layout.addLayout(closer2_layout)
        
        # Координатор (показывается при выборе обоих доводчиков)
        coord_layout = QHBoxLayout()
        self.chk_coordinator = QCheckBox("Координатор:")
        self.chk_coordinator.setVisible(False)
        self.chk_coordinator.setEnabled(False)
        self.combo_coordinator_new = ProtectedComboBox()
        self.combo_coordinator_new.setMinimumWidth(150)
        self.combo_coordinator_new.setVisible(False)
        self.combo_coordinator_new.setEnabled(False)
        coord_layout.addWidget(self.chk_coordinator)
        coord_layout.addWidget(self.combo_coordinator_new)
        coord_layout.addStretch()
        closer_new_layout.addLayout(coord_layout)
        
        grp_closer_new.setLayout(closer_new_layout)
        scroll_layout.addWidget(grp_closer_new)
        
        # === ПРАВАЯ ЧАСТЬ: Таблица КП (2/3) ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        grp_table = QGroupBox("Позиции КП")
        table_layout = QVBoxLayout()
        
        self.table_offer = QTableWidget()
        self.table_offer.setColumnCount(6)
        self.table_offer.setHorizontalHeaderLabels(["№", "Марка", "Изделие", "Размеры", "Кол-во", "Комплектация"])
        # Растягиваем последний столбец (Комплектация) - он займёт всё доступное пространство
        self.table_offer.horizontalHeader().setStretchLastSection(True)
        self.table_offer.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_offer.setMinimumHeight(300)
        
        # Включаем перенос текста - важно для многострочного отображения
        self.table_offer.setWordWrap(True)
        self.table_offer.setTextElideMode(Qt.TextElideMode.ElideNone)
        
        # Настраиваем столбцы: Комплектация шире (растягивается), Кол-во уже
        self.table_offer.setColumnWidth(0, 35)    # №
        self.table_offer.setColumnWidth(1, 60)    # Марка
        self.table_offer.setColumnWidth(2, 140)   # Изделие
        self.table_offer.setColumnWidth(3, 70)    # Размеры
        self.table_offer.setColumnWidth(4, 50)    # Кол-во
        
        # Подключаем обработчик выбора строки
        self.table_offer.itemSelectionChanged.connect(self._on_row_selected)
        
        # Контекстное меню
        self.table_offer.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_offer.customContextMenuRequested.connect(self._show_context_menu)
        
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
        actions_layout.setStretch(0, 0)  # Don't stretch
        actions_layout.setStretch(1, 0)
        
        self.lbl_preview = QLabel("Нажмите 'Добавить в КП'")
        self.lbl_preview.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #0056b3; "
            "padding: 10px; background: #e9ecef; border-radius: 6px;"
        )
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_layout.addWidget(self.lbl_preview)
        
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Добавить в КП")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        self.btn_add.setMinimumSize(120, 45)
        
        self.btn_save_position = QPushButton("Сохранить")
        self.btn_save_position.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.btn_save_position.setMinimumSize(120, 45)
        self.btn_save_position.setVisible(False)  # Скрыта по умолчанию
        self.btn_save_position.clicked.connect(self._save_position_changes)
        
        self.btn_save_preset = QPushButton("Сохранить пресет")
        self.btn_save_preset.setMinimumSize(120, 45)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save_position)
        btn_row.addWidget(self.btn_save_preset)
        btn_row.addStretch(0)
        actions_layout.addLayout(btn_row)
        grp_actions.setLayout(actions_layout)
        right_layout.addWidget(grp_actions)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Кнопки должны быть всегда видимы
        self.btn_add.setVisible(True)
        self.btn_save_preset.setVisible(True)
        
        # 45% слева (было ~33%), 55% справа для помещения без скролла
        total_width = 1400
        splitter.setSizes([int(total_width * 0.45), int(total_width * 0.55)])
        
        main_layout.addWidget(splitter)
        
        self.check_color_visibility()
        self.check_opening_visibility()
        self._update_dimensions_for_product()
        
        # Принудительно показываем кнопки
        self.btn_add.setVisible(True)
        self.btn_save_preset.setVisible(True)
        self.lbl_preview.setVisible(True)
        
        # Инициализация состояния доводчиков
        self.combo_closer1.setEnabled(self.chk_closer1.isChecked())
        self.chk_closer2.setVisible(False)
        self.combo_closer2.setVisible(False)
        self.chk_coordinator.setVisible(False)
        self.combo_coordinator_new.setVisible(False)
    
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
    
    def _load_hardware_options(self):
        """Загрузка данных из прайса для выпадающих списков."""
        price_list_id = self.get_price_list_id() or 1
        
        # Замки
        self.combo_lock.clear()
        self.combo_lock.addItem("— Не выбрано —", None)
        try:
            for lock in self.hw_ctrl.get_by_type("Замок", price_list_id):
                self.combo_lock.addItem(f"{lock.name} ({lock.price:,.0f} руб.)", lock.id)
        except:
            pass
        
        # Ручки
        self.combo_handle.clear()
        self.combo_handle.addItem("— Не выбрано —", None)
        try:
            for handle in self.hw_ctrl.get_by_type("Ручка", price_list_id):
                self.combo_handle.addItem(f"{handle.name} ({handle.price:,.0f} руб.)", handle.id)
        except:
            pass
        
        # Цилиндры
        self.combo_cylinder.clear()
        self.combo_cylinder.addItem("— Не выбрано —", None)
        try:
            for cyl in self.hw_ctrl.get_by_type("Цилиндровый механизм", price_list_id):
                self.combo_cylinder.addItem(f"{cyl.name} ({cyl.price:,.0f} руб.)", cyl.id)
        except:
            pass
        
        # Стекла загружаются в модальном диалоге, а не в комбобоксе
        
        # Доводчики (для нового блока)
        self.combo_closer1.clear()
        self.combo_closer1.addItem("— Не выбрано —", None)
        self.combo_closer2.clear()
        self.combo_closer2.addItem("— Не выбрано —", None)
        try:
            for c in self.closer_ctrl.get_closers(price_list_id):
                self.combo_closer1.addItem(f"{c.name} ({c.price:,.0f} руб.)", c.id)
                self.combo_closer2.addItem(f"{c.name} ({c.price:,.0f} руб.)", c.id)
        except:
            pass
        
        # Координаторы
        self.combo_coordinator_new.clear()
        self.combo_coordinator_new.addItem("— Не выбрано —", None)
        try:
            for c in self.closer_ctrl.get_coordinators(price_list_id):
                self.combo_coordinator_new.addItem(f"{c.name} ({c.price:,.0f} руб.)", c.id)
        except:
            pass
    
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
        self.btn_add_comment.toggled.connect(self._toggle_comment)
        self.btn_color_options_toggle.toggled.connect(self._toggle_color_options)
        self.chk_by_opening.toggled.connect(self.check_opening_visibility)
        
        # RAL - автозаполнение внутреннего при изменении
        self.combo_ext_color.currentIndexChanged.connect(self._on_ext_color_changed)
        self.combo_int_color.currentIndexChanged.connect(self._on_int_color_changed)
        
        # 2 створки
        self.chk_double.toggled.connect(self._on_double_toggled)
        self.chk_mount_ears.toggled.connect(self._toggle_mount_ears)
        self.chk_deflector.toggled.connect(self._toggle_deflector_visibility)
        self.chk_hinges.toggled.connect(self._toggle_hinges)
        self.chk_equal.toggled.connect(self._on_equal_toggled)
        self.dim_w.combo.currentIndexChanged.connect(self._on_width_changed)
        # Recalculate hinge defaults on dimension changes
        self.dim_h.combo.currentTextChanged.connect(lambda: self._update_hinge_defaults())
        self.dim_w.combo.currentTextChanged.connect(lambda: self._update_hinge_defaults())
        self.spin_hinges_single.valueChanged.connect(lambda: self._update_hinge_defaults())
        self.spin_hinges_active.valueChanged.connect(lambda: self._update_hinge_defaults())
        self.spin_hinges_passive.valueChanged.connect(lambda: self._update_hinge_defaults())
        
        self.btn_add.clicked.connect(self._validate_and_add)
        self.btn_save_preset.clicked.connect(self._emit_preset)
        
        # Сигнал для стекла
        self.btn_add_glass.clicked.connect(self._add_selected_glass)
        
        # Новые сигналы для доводчиков
        self.chk_double.toggled.connect(self._on_double_toggled_closer)
        self.chk_closer1.toggled.connect(self._on_closer1_toggled)
        self.chk_closer2.toggled.connect(self._on_closer2_toggled)
    
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
        # Обновляем значения по умолчанию для петель
        self._update_hinge_defaults()
    
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
        # Управление видимостью петель
        self.hinges_single_widget.setVisible(not checked and self.chk_hinges.isChecked())
        self.hinges_double_widget.setVisible(checked and self.chk_hinges.isChecked())
        if checked:
            self._update_hinge_defaults()
        else:
            self.spin_hinges_single.setValue(2)
        
        if not checked:
            self.dim_active.setDisabled(True)
            self.chk_equal.setChecked(False)
        else:
            self._update_active_leaf_range()
            if self.chk_equal.isChecked():
                self._calc_equal_active_leaf()

    def _toggle_hinges(self, checked: bool):
        """Показать/скрыть конфигурацию петель в зависимости от режима (одна/две створки)."""
        if self.chk_double.isChecked():
            self.hinges_single_widget.setVisible(False)
            self.hinges_double_widget.setVisible(checked)
        else:
            self.hinges_single_widget.setVisible(checked)
            self.hinges_double_widget.setVisible(False)
        if checked:
            self._update_hinge_defaults()
    
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

    def _update_hinge_defaults(self):
        """Рассчитывает и применяет значения по умолчанию для количества петель."""
        product = self.combo_product.currentText()
        height = self.dim_h.value()
        width = self.dim_w.value()
        per_leaf = 2
        if product == "Ворота":
            per_leaf = 3
        elif product == "Люк":
            per_leaf = 2
        else:
            # Для дверей/прочих - простая логика
            if height < 2300 and width <= 1000:
                per_leaf = 2
            elif height >= 2300 or width > 1000:
                per_leaf = 3

        if self.chk_double.isChecked():
            self.spin_hinges_active.setValue(per_leaf)
            self.spin_hinges_passive.setValue(per_leaf)
            self.hinges_single_widget.setVisible(False)
            self.hinges_double_widget.setVisible(True)
        else:
            self.spin_hinges_single.setValue(per_leaf)
            self.hinges_single_widget.setVisible(True)
            self.hinges_double_widget.setVisible(False)
    
    def _toggle_comment(self, expanded: bool):
        """Переключение видимости блока Комментарий."""
        self.comment_text_edit.setVisible(expanded)
        self.btn_add_comment.setText("▼ Скрыть комментарий" if expanded else "Добавить комментарий")
    
    def _toggle_by_opening_fields(self, checked: bool):
        """Показать/скрыть поля вычитаемых миллиметров при выборе 'по проёму'."""
        self.spin_by_opening_height.setVisible(checked)
        self.spin_by_opening_width.setVisible(checked)
    
    def _toggle_color_options(self, expanded: bool):
        """Переключение видимости блока Опции цвета."""
        self.btn_color_options_toggle.setText("▼ Опции цвета" if expanded else "▶ Опции цвета")
        
        self.chk_moire.setVisible(expanded)
        self.chk_lac.setVisible(expanded)
        self.chk_primer.setVisible(expanded)

    def _toggle_deflector_visibility(self, checked: bool):
        """Показывать/скрывать поля отбойной пластины и связанных опций."""
        self.spin_deflector_h.setVisible(checked)
        self.deflector_two_sided.setVisible(checked)

    def _toggle_mount_ears(self, checked: bool):
        """Показывать/скрывать поле ввода количества монтажных ушей."""
        self.mount_ears_input.setVisible(checked)
    
    def check_opening_visibility(self):
        """Показывать/скрывать поля высота минус и ширина минус при изменении чекбокса."""
        checked = self.chk_by_opening.isChecked()
        # Показываем поля минус и их заголовки
        self.lbl_height_minus.setVisible(checked)
        self.spin_by_opening_height.setVisible(checked)
        self.lbl_width_minus.setVisible(checked)
        self.spin_by_opening_width.setVisible(checked)
        
        # Переименовать подблок
        if checked:
            self.box_by_frame.setTitle("Размер по проёму")
        else:
            self.box_by_frame.setTitle("Размер по коробке")
        
        # При "по проёму" - делаем размеры недоступными для ввода (расчёт значения по коробке происходит при расчёте)
        if checked:
            self.dim_h.setDisabled(True)
            self.dim_w.setDisabled(True)
        else:
            self.dim_h.setDisabled(False)
            self.dim_w.setDisabled(False)
    
    def _resize_table_rows(self):
        """Обновляет высоту строк таблицы для корректного переноса текста."""
        # Обновляем представление чтобы получить правильные размеры
        self.table_offer.viewport().update()
        
        # Для каждой строки вычисляем требуемую высоту
        for row in range(self.table_offer.rowCount()):
            height = self.table_offer.verticalHeader().sectionSize(row)
            # Получаем текст из колонки Комплектация (column 5)
            item = self.table_offer.item(row, 5)
            if item:
                text = item.text()
                # Ширина доступной области для текста
                available_width = self.table_offer.columnWidth(5)
                # Если столбец растянут - получаем его реальную ширину
                header = self.table_offer.horizontalHeader()
                if header.sectionResizeMode(5) == QHeaderView.ResizeMode.Stretch:
                    # Прибли��ительная ширина - вся ширина таблицы минус другие столбцы
                    total_width = self.table_offer.viewport().width()
                    available_width = total_width - 300  # примерно
                
                # Вычисляем требуемую высоту
                font = item.font() or self.table_offer.font()
                from PyQt6.QtGui import QFontMetrics
                fm = QFontMetrics(font)
                text_width = fm.horizontalAdvance(text)
                
                # Если текст шире чем колонка - нужен перенос
                if text_width > available_width and available_width > 0:
                    # Вычисляем количество строк
                    lines = (text_width // available_width) + 1
                    # Минимум 2 строки, максимум разумное количество
                    lines = max(lines, 2)
                    # Высота строки текста примерно 16px
                    new_height = lines * 18
                    # Минимум стандартная высота
                    new_height = max(new_height, 30)
                    self.table_offer.setRowHeight(row, new_height)
                else:
                    # Стандартная высота
                    self.table_offer.setRowHeight(row, 30)
    
    def _on_double_toggled_closer(self, checked: bool):
        """Управление видимостью доводчика 2 при 2 створках."""
        self.chk_closer2.setVisible(checked)
        self.combo_closer2.setVisible(checked)
        if not checked:
            self.chk_closer2.setChecked(False)
            self.combo_closer2.setEnabled(False)
        else:
            self.combo_closer2.setEnabled(self.chk_closer2.isChecked())
    
    def _on_closer1_toggled(self, checked: bool):
        """Активация доводчика 1."""
        self.combo_closer1.setEnabled(checked)
        # Показать координатор если оба доводчика выбраны
        if checked and self.chk_closer2.isChecked():
            self.chk_coordinator.setVisible(True)
            self.chk_coordinator.setEnabled(True)
            self.combo_coordinator_new.setVisible(True)
            self.combo_coordinator_new.setEnabled(True)
    
    def _on_closer2_toggled(self, checked: bool):
        """Активация доводчика 2."""
        self.combo_closer2.setEnabled(checked)
        # Показать координатор если оба доводчика выбраны
        if checked and self.chk_closer1.isChecked():
            self.chk_coordinator.setVisible(True)
            self.chk_coordinator.setEnabled(True)
            self.combo_coordinator_new.setVisible(True)
            self.combo_coordinator_new.setEnabled(True)
    
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
        
        # Перезагружаем выпадающие списки из нового прайса
        self._load_hardware_options()
        
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
            calc_height -= self.spin_by_opening_height.value()
            calc_width -= self.spin_by_opening_width.value()
        
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
            calc_height -= self.spin_by_opening_height.value()
            calc_width -= self.spin_by_opening_width.value()
        
        # Рассчитываем значения по умолчанию для петель
        product = self.combo_product.currentText()
        height = self.dim_h.value()
        width = self.dim_w.value()
        per_leaf = 2
        if product == "Ворота":
            per_leaf = 3
        elif product == "Люк":
            per_leaf = 2
        else:
            if height < 2300 and width <= 1000:
                per_leaf = 2
            elif height >= 2300 or width > 1000:
                per_leaf = 3
        
        # Для двустворчатых - учитываем ширину активной створки
        active_width = self.dim_active.value() if self.chk_double.isChecked() else 0
        if self.chk_double.isChecked():
            if height >= 2300:
                per_leaf = 3
            elif width > 1300 and active_width >= 1000:
                per_leaf = 3
        
        # Количество петель
        hinge_count_active = self.spin_hinges_single.value()
        hinge_count_passive = self.spin_hinges_passive.value() if self.chk_double.isChecked() else 0
        hinge_default = per_leaf
        
        # Количество монтажных ушей
        mount_ears_count = 0
        if self.chk_mount_ears.isChecked():
            try:
                mount_ears_count = int(self.mount_ears_input.currentText())
            except:
                mount_ears_count = 4
        
        # Значения по умолчанию для ушей
        mount_ears_default = 6 if product == "Ворота" else 4
        
        # Преобразование данных о стёклах для калькулятора
        glass_items_calc = []
        for g in self._glass_items_data:
            # Извлекаем ID опций из списка словарей
            option_ids = []
            if g.get("options"):
                for opt in g["options"]:
                    if isinstance(opt, dict):
                        opt_id = opt.get("id")
                        if opt_id:
                            option_ids.append(opt_id)
                    elif isinstance(opt, int):
                        option_ids.append(opt)
            
            glass_items_calc.append({
                "type_id": g.get("glass_type_id"),
                "height": g.get("height", 0),
                "width": g.get("width", 0),
                "option_ids": option_ids
            })
        
        return {
            "product_type": self.combo_product.currentText(),
            "subtype": self.combo_type.currentText(),
            "mark": self.edit_mark.currentText(),
            "height": calc_height,
            "width": calc_width,
            "original_height": self.dim_h.value(),
            "original_width": self.dim_w.value(),
            "by_opening": self.chk_by_opening.isChecked(),
            "by_opening_height_deduction": self.spin_by_opening_height.value(),
            "by_opening_width_deduction": self.spin_by_opening_width.value(),
            "quantity": self.spin_qty.value(),
            "is_double_leaf": self.chk_double.isChecked(),
            "active_leaf_width": self.dim_active.value() if self.chk_double.isChecked() else 0,
            "color_external": self.combo_ext_color.currentText(),
            "color_internal": self.combo_int_color.currentText(),
            "metal_thickness": self.combo_metal.currentText(),
            "threshold": self.chk_threshold.isChecked(),
            "markup_percent": self.spin_markup_pct.value(),
            "markup_abs": self.spin_markup_val.value(),
            "glass_items": glass_items_calc,  # For calculator
            "glass_items_display": self._glass_items_data,  # For display in table
            "hardware_items": hw_items,
            "grilles": [],
            "comment": self.comment_text_edit.toPlainText() if self.comment_text_edit.isVisible() else "",
            "color_options": {
                "moire": self.chk_moire.isChecked(),
                "lac": self.chk_lac.isChecked(),
                "primer": self.chk_primer.isChecked()
            },
            "extra_options": {
                "closer1": self.chk_closer1.isChecked(),
                "closer2": self.chk_closer2.isChecked() if hasattr(self, 'chk_closer2') else False,
                "coordinator": self.chk_coordinator.isChecked() if hasattr(self, 'chk_coordinator') else False,
                "hinge_count_active": hinge_count_active if not self.chk_double.isChecked() else self.spin_hinges_active.value(),
                "hinge_count_passive": 0 if not self.chk_double.isChecked() else self.spin_hinges_passive.value(),
                "hinge_default_active": hinge_default,
                "hinge_default_passive": hinge_default if self.chk_double.isChecked() else 0,
                "anti_theft_pins": self.chk_anti_theft.isChecked(),
                "gkl": self.chk_gkl.isChecked(),
                "mount_ears_count": mount_ears_count,
                "mount_ears_default": mount_ears_default,
                "deflector": self.chk_deflector.isChecked(),
                "deflector_height": self.spin_deflector_h.value() if self.chk_deflector.isChecked() else 0,
                "deflector_double_side": self.deflector_two_sided.isChecked() if self.chk_deflector.isChecked() else False
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
        # Динамический расчёт при добавлении в КП
        config = self._collect_config()
        
        # Выполняем расчёт
        price_list_id = self.get_price_list_id()
        if price_list_id is None:
            price_list_id = 1
        
        try:
            from controllers.calculator_controller import CalculatorController
            calc_ctrl = CalculatorController()
            result = calc_ctrl.validate_and_calculate(
                config["product_type"],
                config["subtype"],
                config["height"],
                config["width"],
                price_list_id,
                config,
                config.get("markup_percent", 0),
                config.get("markup_abs", 0),
                config.get("quantity", 1)
            )
            if result.get("success"):
                config.update(result)
                # Добавляем ключи, ожидаемые offer_controller
                config["base_price"] = result.get("price_per_unit", 0)
                config["final_price"] = result.get("total_price", 0)
                config["options"] = result.get("details", {})
                
                # Обновляем preview с результатом
                qty = result.get("quantity", 1)
                price = result.get("total_price", 0)
                self.lbl_preview.setText(f"Итого за {qty} шт.: {price:,.2f} ₽")
                self.lbl_preview.setStyleSheet("color: #28a745; font-weight: bold;")
                self.current_calc_result = result
            else:
                QMessageBox.warning(self, "Ошибка расчёта", result.get("error", "Неизвестная ошибка"))
                return
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить расчёт: {e}")
            return
        
        # Обновляем preview для случая, если расчёт не выполнялся
        if not self.current_calc_result:
            self.current_calc_result = config
        
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
        """Создать новое КП. Испускает сигнал с действием."""
        # Сигнал для создания нового КП - передаём текущее количество позиций
        row_count = self.table_offer.rowCount()
        self.add_to_offer_requested.emit({"_action": "create_offer", "current_row_count": row_count})
    
    def _remove_position(self):
        row = self.table_offer.currentRow()
        if row >= 0:
            self.table_offer.removeRow(row)
            self._update_row_numbers()
            self._update_total()
            
            # Обновляем последние изделия для фрамуги
            if self.last_offer_items and row < len(self.last_offer_items):
                self.last_offer_items.pop(row)
    
    def _show_context_menu(self, pos):
        """Показать контекстное меню при правом клике на позицию."""
        row = self.table_offer.rowAt(pos.y())
        if row < 0:
            return
        
        # Выделяем строку под курсором
        self.table_offer.selectRow(row)
        
        menu = QMenu(self)
        
        # Действия
        action_delete = menu.addAction("Удалить")
        action_delete.triggered.connect(self._remove_position)
        
        action_duplicate = menu.addAction("Дублировать")
        action_duplicate.triggered.connect(lambda: self._duplicate_position(row))
        
        action_details = menu.addAction("Подробно")
        action_details.triggered.connect(lambda: self._show_position_details(row))
        
        menu.exec(self.table_offer.viewport().mapToGlobal(pos))
    
    def _duplicate_position(self, row: int):
        """Дублирует позицию в таблице."""
        if row < 0 or row >= self.table_offer.rowCount():
            return
        
        # Получаем данные из текущей позиции
        item = self.table_offer.item(row, 0)
        if not item:
            return
        
        # Получаем все сохраненные данные
        row_data = item.data(Qt.ItemDataRole.UserRole)
        
        # Создаем копию данных
        data = {}
        if row_data:
            data = row_data.copy()
        
        # Копируем данные из всех колонок
        data["mark"] = self.table_offer.item(row, 1).text() if self.table_offer.item(row, 1) else ""
        
        # Изделие - берем полный текст
        product_text = self.table_offer.item(row, 2).text() if self.table_offer.item(row, 2) else ""
        
        # Определяем тип изделия
        product_type = ""
        subtype = ""
        is_double = False
        
        if "2-ств." in product_text:
            is_double = True
            # Парсим "Дверь 2-ств. Техническая"
            parts = product_text.replace("2-ств.", "").strip().split(None, 1)
            if len(parts) >= 1:
                product_type = parts[0]
            if len(parts) >= 2:
                subtype = parts[1]
        else:
            # Парсим "Дверь Техническая"
            parts = product_text.strip().split(None, 1)
            if len(parts) >= 1:
                product_type = parts[0]
            if len(parts) >= 2:
                subtype = parts[1]
        
        data["product_type"] = product_type
        data["subtype"] = subtype
        data["is_double_leaf"] = is_double
        
        # Размеры - формат "ВxШ" (высота x ширина)
        size_text = self.table_offer.item(row, 3).text() if self.table_offer.item(row, 3) else ""
        if "x" in size_text:
            parts = size_text.split("x")
            if len(parts) == 2:
                # Первое - высота, второе - ширина
                data["height"] = int(parts[0])
                data["width"] = int(parts[1])
        
        # Количество
        qty_text = self.table_offer.item(row, 5).text() if self.table_offer.item(row, 5) else "1"
        data["quantity"] = int(qty_text) if qty_text.isdigit() else 1
        
        # Добавляем в таблицу
        self.add_position_to_table(data)
    
    def _show_position_details(self, row: int):
        """Показывает подробную информацию о позиции."""
        if row < 0 or row >= self.table_offer.rowCount():
            return
        
        item = self.table_offer.item(row, 0)
        if not item:
            return
        
        row_data = item.data(Qt.ItemDataRole.UserRole)
        
        # Получаем данные для формирования цены с опциями
        base_price = 0
        if row_data:
            base_price = row_data.get('price_per_unit', 0)
        
        # Формируем текст информации
        details_text = "Детализация позиции:\n"
        details_text += "=" * 50 + "\n\n"
        
        # Основные данные
        product_text = self.table_offer.item(row, 2).text() if self.table_offer.item(row, 2) else '-'
        size_text = self.table_offer.item(row, 3).text() if self.table_offer.item(row, 3) else '-'
        mark = self.table_offer.item(row, 1).text() if self.table_offer.item(row, 1) else '-'
        qty_text = self.table_offer.item(row, 5).text() if self.table_offer.item(row, 5) else '1'
        
        details_text += f"Изделие: {product_text}\n"
        details_text += f"Размеры: {size_text}\n"
        details_text += f"Марка: {mark}\n"
        details_text += f"Количество: {qty_text}\n\n"
        
        details_text += "-" * 50 + "\n"
        
        # Базовая стоимость
        details_text += f"Базовая стоимость изделия: {base_price:,.2f} руб.\n\n"
        
        # Комплектация с ценами
        comp_text = self.table_offer.item(row, 4).text() if self.table_offer.item(row, 4) else ""
        
        # Парсим комплектацию для отображения построчно
        if comp_text:
            opts = comp_text.split(", ")
            for opt in opts:
                details_text += f"  • {opt}\n"
        
        details_text += "\n" + "-" * 50 + "\n"
        
        # Ценообразование
        if row_data:
            price_per_unit = row_data.get('price_per_unit', 0)
            markup_pct = row_data.get('markup_percent', 0)
            markup_abs = row_data.get('markup_abs', 0)
            total = row_data.get('total_price', 0)
            
            details_text += f"Цена за 1 шт: {price_per_unit:,.2f} руб.\n"
            details_text += f"Наценка: {markup_pct}%"
            if markup_abs > 0:
                details_text += f" + {markup_abs:,.0f} руб."
            details_text += "\n"
            details_text += f"Итого за 1 шт: {price_per_unit + markup_abs * (1 + markup_pct/100):,.2f} руб.\n"
            details_text += f"Итого за {qty_text} шт: {total:,.2f} руб.\n"
        
        # Показываем в диалоге
        from PyQt6.QtWidgets import QTextEdit, QVBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("Подробно о позиции")
        dialog.setMinimumSize(550, 450)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(details_text)
        layout.addWidget(text_edit)
        
        # Кнопка закрытия
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec()
        text_edit.setReadOnly(True)
        text_edit.setText(details_text)
        layout.addWidget(text_edit)
        
        # Кнопка закрытия
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _load_position_to_form(self, row: int):
        """Загружает данные позиции в форму (левая панель)."""
        if row < 0 or row >= self.table_offer.rowCount():
            return
        
        # Получаем полную конфигурацию из UserRole
        item = self.table_offer.item(row, 0)
        if not item:
            return
        
        config = item.data(Qt.ItemDataRole.UserRole)
        if not config:
            return
        
        # === Параметры изделия ===
        product_type = config.get("product_type", "")
        subtype = config.get("subtype", "")
        is_double = config.get("is_double_leaf", False)
        
        if product_type:
            self.combo_product.setCurrentText(product_type)
            # Обновляем subtypes
            self.combo_type.clear()
            self.combo_type.addItems(PRODUCT_TYPES.get(product_type, []))
            if subtype:
                self.combo_type.setCurrentText(subtype)
        
        # 2 створки
        self.chk_double.setChecked(is_double)
        
        # === Размеры изделия ===
        width = config.get("width", 0)
        height = config.get("height", 0)
        by_opening = config.get("by_opening", False)
        
        self.dim_h.setValue(height)
        self.dim_w.setValue(width)
        self.chk_by_opening.setChecked(by_opening)
        
        if by_opening:
            # Загружаем размеры проёма если есть
            extra = config.get("extra_options", {})
            by_h = extra.get("by_opening_height", height)
            by_w = extra.get("by_opening_width", width)
            self.spin_by_opening_height.setValue(by_h)
            self.spin_by_opening_width.setValue(by_w)
        
        # === Марка ===
        mark = config.get("mark", "")
        self.edit_mark.setCurrentText(mark)
        
        # === Количество ===
        quantity = config.get("quantity", 1)
        self.spin_qty.setValue(quantity)
        
        # === Оформление (цвета) ===
        ext_color = config.get("color_external", "")
        int_color = config.get("color_internal", "")
        
        # Ищем цвета в комбобоксах
        ext_color_found = False
        for i in range(self.combo_ext_color.count()):
            if self.combo_ext_color.itemText(i).startswith(ext_color):
                self.combo_ext_color.setCurrentIndex(i)
                ext_color_found = True
                break
        if not ext_color_found and ext_color:
            self.combo_ext_color.setCurrentText(ext_color)
        
        int_color_found = False
        for i in range(self.combo_int_color.count()):
            if self.combo_int_color.itemText(i).startswith(int_color):
                self.combo_int_color.setCurrentIndex(i)
                int_color_found = True
                break
        if not int_color_found and int_color:
            self.combo_int_color.setCurrentText(int_color)
        
        # === Металл ===
        metal = config.get("metal_thickness", "")
        if metal:
            self.combo_metal.setCurrentText(metal)
        
        # === Дополнительные опции ===
        extra = config.get("extra_options", {})
        
        # Порог
        self.chk_threshold.setChecked(extra.get("threshold", False))
        # Противосъёмные штыри
        self.chk_anti_theft.setChecked(extra.get("anti_theft_pins", False))
        # ГКЛ наполнение
        self.chk_gkl.setChecked(extra.get("gkl", False))
        # Монтажные уши
        mount_ears = extra.get("mount_ears_count", 0)
        if mount_ears > 0:
            self.spin_mount_ears.setValue(mount_ears)
        # Отбойная пластина
        self.chk_deflector.setChecked(extra.get("deflector", False))
        if extra.get("deflector"):
            self.chk_deflector_double.setChecked(extra.get("deflector_double_side", False))
        
        # === Фурнитура (замки, ручки, цилиндры) ===
        hw_items = config.get("hardware_items", [])
        
        # Очищаем текущий список фурнитуры
        self.list_hardware.clear()
        
        for hw in hw_items:
            hw_text = hw
            if ":" in hw:
                # Формат "Замок: Название" или "Ручка: Название"
                hw_text = hw.split(":", 1)[1].strip()
            # Добавляем в список
            self.list_hardware.addItem(hw_text)
        
        # === Стекла ===
        glass_items = config.get("glass_items", [])
        glass_display = config.get("glass_items_display", glass_items)
        
        self.list_glass.clear()
        for glass in glass_display:
            glass_name = glass.get("glass_type_name", "")
            if glass_name:
                opts = glass.get("options", [])
                if opts:
                    opt_names = ", ".join([o.get("name", "") for o in opts])
                    self.list_glass.addItem(f"{glass_name} ({opt_names})")
                else:
                    self.list_glass.addItem(glass_name)
        
        # === Доводчики и координатор ===
        self.chk_closer1.setChecked(extra.get("closer1", False))
        self.chk_closer2.setChecked(extra.get("closer2", False))
        self.chk_coordinator.setChecked(extra.get("coordinator", False))
        
        # === Комментарий ===
        comment = config.get("comment", "")
        if comment:
            self.comment_text_edit.setPlainText(comment)
        else:
            self.comment_text_edit.clear()
        
        # Сохраняем индекс текущей строки
        self.current_row_index = row
        
        # Показываем кнопку Сохранить
        if hasattr(self, 'btn_save_position'):
            self.btn_save_position.setVisible(True)
    
    def _save_position_changes(self):
        """Сохраняет изменения в выбранной позиции."""
        if self.current_row_index < 0 or self.current_row_index >= self.table_offer.rowCount():
            QMessageBox.warning(self, "Ошибка", "Выберите позицию для сохранения.")
            return
        
        # Собираем данные из формы
        data = self._collect_config()
        
        # Обновляем строку в таблице (удаляем старую, добавляем новую)
        self.table_offer.removeRow(self.current_row_index)
        self.add_position_to_table(data)
        
        # Возвращаем выбор на ту же строку
        self.table_offer.selectRow(self.current_row_index)
        self.current_row_index = -1
        
        # Скрываем кнопку Сохранить
        if hasattr(self, 'btn_save_position'):
            self.btn_save_position.setVisible(False)
        
        QMessageBox.information(self, "Сохранено", "Изменения сохранены.")
    
    def add_position_to_table(self, item_data: dict):
        row = self.table_offer.rowCount()
        self.table_offer.insertRow(row)
        
        self.table_offer.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.table_offer.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Марка
        self.table_offer.setItem(row, 1, QTableWidgetItem(item_data.get("mark", "")))
        
        # Изделие: Вид изделия + тип + 2-ств. (если дверь/люк с 2 створками)
        product_type = item_data.get("product_type", "")
        subtype = item_data.get("subtype", "")
        is_double = item_data.get("is_double_leaf", False)
        
        # Для дверей и люков добавляем "2-ств." при двух створках
        if is_double and product_type in ("Дверь", "Люк"):
            product_desc = f"{product_type} 2-ств. {subtype}"
        else:
            product_desc = f"{product_type} {subtype}"
        
        self.table_offer.setItem(row, 2, QTableWidgetItem(product_desc))
        
        # Размеры: формат "ВxШ" (высота x ширина)
        by_opening = item_data.get("by_opening", False)
        w = item_data.get("width", 0)
        h = item_data.get("height", 0)
        # Меняем местами: было ШxВ, стало ВxШ
        size_str = f"{int(h)}x{int(w)}"
        self.table_offer.setItem(row, 3, QTableWidgetItem(size_str))
        
        # Комплектация: собираем все выбранные опции через запятую
        comp_parts = []
        
        # Цвета
        ext_color = item_data.get("color_external", "")
        int_color = item_data.get("color_internal", "")
        if ext_color:
            comp_parts.append(f"RAL нар: {ext_color}")
        if int_color:
            comp_parts.append(f"RAL вн: {int_color}")
        
        # Металл
        metal = item_data.get("metal_thickness", "")
        if metal:
            comp_parts.append(f"Металл: {metal}")
        
        # Дополнительные опции
        extra = item_data.get("extra_options", {})
        if extra.get("threshold"):
            comp_parts.append("Автопорог")
        if extra.get("anti_theft_pins"):
            comp_parts.append("Противосъёмные штыри")
        if extra.get("gkl"):
            comp_parts.append("ГКЛ наполнение")
        if extra.get("mount_ears_count"):
            comp_parts.append(f"Монтажные уши: {extra.get('mount_ears_count')}")
        if extra.get("deflector"):
            deflector_text = "Отбойная пластина"
            if extra.get("deflector_double_side"):
                deflector_text += " (2-х сторон)"
            if extra.get("deflector_height"):
                deflector_text += f" {extra.get('deflector_height')}мм"
            comp_parts.append(deflector_text)
        
        # Петли
        if item_data.get("is_double_leaf"):
            hinge_active = extra.get("hinge_count_active", 0)
            hinge_passive = extra.get("hinge_count_passive", 0)
            if hinge_active or hinge_passive:
                comp_parts.append(f"Петли: акт={ hinge_active}, пасс={ hinge_passive}")
        else:
            hinge_count = extra.get("hinge_count_active", 0)
            if hinge_count:
                comp_parts.append(f"Петли: {hinge_count}")
        
        # Фурнитура - отображаем с префиксами "замок: ", "ручка: "
        hw_items = item_data.get("hardware_items", [])
        for hw in hw_items:
            hw_lower = hw.lower()
            if "замок" in hw_lower:
                # Формат "замок: Название"
                if ":" in hw:
                    comp_parts.append(f"замок: {hw.split(':', 1)[1].strip()}")
                else:
                    comp_parts.append(f"замок: {hw}")
            elif "ручк" in hw_lower:
                # Формат "ручка: Название"
                if ":" in hw:
                    comp_parts.append(f"ручка: {hw.split(':', 1)[1].strip()}")
                else:
                    comp_parts.append(f"ручка: {hw}")
            else:
                # Другая фурнитура
                if ":" in hw:
                    comp_parts.append(hw.split(":", 1)[1].strip())
                else:
                    comp_parts.append(hw)
        
        # Доводчики
        if extra.get("closer1"):
            comp_parts.append("Доводчик 1")
        if extra.get("closer2"):
            comp_parts.append("Доводчик 2")
        if extra.get("coordinator"):
            comp_parts.append("Координатор")
        
        # Стекла (используем данные для отображения)
        glass_items = item_data.get("glass_items_display", item_data.get("glass_items", []))
        for glass in glass_items:
            glass_name = glass.get("glass_type_name", "")
            if glass_name:
                opts = glass.get("options", [])
                if opts:
                    opt_names = ", ".join([o.get("name", "") for o in opts])
                    comp_parts.append(f"{glass_name} ({opt_names})")
                else:
                    comp_parts.append(glass_name)
        
        # Цветовые опции
        color_opts = item_data.get("color_options", {})
        if color_opts.get("moire"):
            comp_parts.append("Муар")
        if color_opts.get("lac"):
            comp_parts.append("Лак")
        if color_opts.get("primer"):
            comp_parts.append("Грунт")
        
        comp_str = ", ".join(comp_parts)
        # Кол-во (column 4)
        self.table_offer.setItem(row, 4, QTableWidgetItem(str(item_data.get("quantity", 1))))
        
        # Комплектация (column 5) - создаём ячейку с переносом
        comp_item = QTableWidgetItem(comp_str)
        comp_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.table_offer.setItem(row, 5, comp_item)
        
        # Сохраняем полные данные позиции для загрузки в форму
        # Используем UserRole для хранения всей конфигурации
        price_per_unit = item_data.get("price_per_unit", 0)
        markup_percent = item_data.get("markup_percent", 0)
        markup_abs = item_data.get("markup_abs", 0)
        total_price = item_data.get("total_price", 0)
        quantity = item_data.get("quantity", 1)
        
        # Сохраняем полную конфигурацию в UserRole
        row_data = {
            "price_per_unit": price_per_unit,
            "markup_percent": markup_percent,
            "markup_abs": markup_abs,
            "total_price": total_price,
            "quantity": quantity,
            # Полная конфигурация для загрузки в форму
            "mark": item_data.get("mark", ""),
            "product_type": item_data.get("product_type", ""),
            "subtype": item_data.get("subtype", ""),
            "is_double_leaf": item_data.get("is_double_leaf", False),
            "by_opening": item_data.get("by_opening", False),
            "width": item_data.get("width", 0),
            "height": item_data.get("height", 0),
            "color_external": item_data.get("color_external", ""),
            "color_internal": item_data.get("color_internal", ""),
            "metal_thickness": item_data.get("metal_thickness", ""),
            "extra_options": item_data.get("extra_options", {}),
            "hardware_items": item_data.get("hardware_items", []),
            "glass_items": item_data.get("glass_items", []),
            "glass_items_display": item_data.get("glass_items_display", []),
            "comment": item_data.get("comment", ""),
        }
        self.table_offer.item(row, 0).setData(Qt.ItemDataRole.UserRole, row_data)
        
        self._update_total()
        
        # Обновляем высоту строк таблицы для корректного переноса текста
        self._resize_table_rows()
        self.table_offer.repaint()
        
        # Дополнительно обновляем через таймер (для надёжности)
        QTimer.singleShot(10, self.table_offer.viewport().update)
    
    def clear_offer_table(self):
        """Очищает таблицу КП."""
        self.table_offer.setRowCount(0)
        self.last_offer_items.clear()
        self._update_total()
        self.lbl_preview.setText("Добавьте позиции в КП")
    
    def _update_row_numbers(self):
        for r in range(self.table_offer.rowCount()):
            self.table_offer.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.table_offer.item(r, 0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def _update_total(self):
        # Считаем общую сумму из сохранённых данных
        total = 0.0
        for r in range(self.table_offer.rowCount()):
            item = self.table_offer.item(r, 0)
            if item:
                row_data = item.data(Qt.ItemDataRole.UserRole)
                if row_data:
                    total += row_data.get("total_price", 0)
        
        if self.table_offer.rowCount() > 0:
            self.lbl_preview.setText(f"Итого КП: {total:,.2f} ₽ ({self.table_offer.rowCount()} поз.)")
        else:
            self.lbl_preview.setText("Добавьте позиции в КП")
        self.lbl_preview.setStyleSheet("color: #28a745; font-weight: bold; font-size: 12pt;")
    
    def _on_row_selected(self):
        """Обработка выбора строки в таблице - показываем детали в preview и загружаем в форму."""
        selected = self.table_offer.selectedItems()
        if not selected:
            self._update_total()
            return
        
        row = selected[0].row()
        
        # Загружаем позицию в форму (левая панель)
        self._load_position_to_form(row)
        
        # Показываем детали в preview
        item = self.table_offer.item(row, 0)
        if item:
            row_data = item.data(Qt.ItemDataRole.UserRole)
            if row_data:
                price_per_unit = row_data.get("price_per_unit", 0)
                markup_pct = row_data.get("markup_percent", 0)
                markup_abs = row_data.get("markup_abs", 0)
                total = row_data.get("total_price", 0)
                qty = row_data.get("quantity", 1)
                
                # Формируем текст
                details = f"Цена за 1 шт: {price_per_unit:,.2f} ₽"
                if markup_pct > 0:
                    details += f" | Наценка: {markup_pct}%"
                if markup_abs > 0:
                    details += f" + {markup_abs:,.0f} ₽"
                details += f" | Итого: {total:,.2f} ₽"
                
                self.lbl_preview.setText(details)
                self.lbl_preview.setStyleSheet("color: #0056b3; font-weight: bold;")
                return
        
        self._update_total()
    
    def set_offer_id(self, offer_id: int):
        self.current_offer_id = offer_id
    
    def get_price_list_id(self) -> int:
        return self.combo_price.currentData() or None
    
    def _add_selected_hardware(self):
        """Добавить выбранную фурнитуру из выпадающих списков."""
        sender = self.sender()
        price_list_id = self.get_price_list_id() or 1
        
        # Получить данные о выбранном элементе из прайса
        def get_hw_info(hw_id):
            if not hw_id:
                return None, None, False
            try:
                hw = self.hw_ctrl.get_by_id(hw_id)
                if hw:
                    # code и fire_protected могут отсутствовать в модели
                    code = getattr(hw, 'code', None) or ""
                    fire_protected = getattr(hw, 'fire_protected', False)
                    return hw.name, code, fire_protected
            except:
                pass
            return None, None, False
        
        # Проверяем какой комбобокс используется
        if sender == self.btn_add_lock:
            hw_id = self.combo_lock.currentData()
            name, code, fire_prot = get_hw_info(hw_id)
            if hw_id and name:
                display = f"Замок: {name}"
                if code:
                    display += f" ({code})"
                if fire_prot:
                    display += " ПП"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, {"type": "Замок", "id": hw_id, "name": name, "code": code, "fire_protected": fire_prot})
                self.list_hardware.addItem(item)
                self.list_hardware.setCurrentRow(self.list_hardware.count() - 1)
        elif sender == self.btn_add_handle:
            hw_id = self.combo_handle.currentData()
            name, code, fire_prot = get_hw_info(hw_id)
            if hw_id and name:
                display = f"Ручка: {name}"
                if code:
                    display += f" ({code})"
                if fire_prot:
                    display += " ПП"
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, {"type": "Ручка", "id": hw_id, "name": name, "code": code, "fire_protected": fire_prot})
                self.list_hardware.addItem(item)
                self.list_hardware.setCurrentRow(self.list_hardware.count() - 1)
        elif sender == self.btn_add_cyl:
            hw_id = self.combo_cylinder.currentData()
            name, code, fire_prot = get_hw_info(hw_id)
            if hw_id and name:
                display = f"Цилиндр: {name}"
                if code:
                    display += f" ({code})"
                # Цилиндры не имеют ПП
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, {"type": "Цилиндр", "id": hw_id, "name": name, "code": code, "fire_protected": False})
                self.list_hardware.addItem(item)
                self.list_hardware.setCurrentRow(self.list_hardware.count() - 1)
    
    def _remove_selected_hardware(self):
        """Удалить выбранную фурнитуру из списка."""
        current_row = self.list_hardware.currentRow()
        if current_row >= 0:
            self.list_hardware.takeItem(current_row)
    
    def _add_selected_glass(self):
        """Открыть модальное окно для добавления стекла."""
        # Загружаем доступные типы стёкол
        glass_types = []
        price_list_id = self.get_price_list_id() or 1
        try:
            glass_types = self.opt_ctrl.get_glass_types(price_list_id)
        except:
            pass
        
        if not glass_types:
            QMessageBox.warning(self, "Внимание", "Нет доступных типов стёкол в прайсе.")
            return
        
        # Создаём диалог
        dialog = GlassEditDialog(parent=self)
        dialog.set_glass_types(glass_types)
        
        # Загружаем глобальные опции из прайса
        try:
            global_options = self.opt_ctrl.get_all_glass_options(price_list_id)
            dialog.set_all_options(global_options)
        except:
            pass
        
        # При выборе стекла загружаем его опции (также глобальные)
        def load_options(idx):
            opts = []
            if idx < len(glass_types):
                opts = glass_types[idx].get("options", [])
            # Добавляем глобальные опции
            try:
                global_opts = self.opt_ctrl.get_all_glass_options(price_list_id)
                # Объединяем, исключая дубликаты по id
                existing_ids = {o["id"] for o in opts}
                for go in global_opts:
                    if go["id"] not in existing_ids:
                        opts.append(go)
            except:
                pass
            dialog.set_glass_options(opts)
        
        dialog.combo_glass_type.currentIndexChanged.connect(load_options)
        # Загружаем опции для первого выбранного стекла
        load_options(0)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            
            # Формируем текст для отображения
            options_text = ""
            if data.get("options"):
                opt_names = [o["name"] for o in data["options"]]
                if len(opt_names) > 0:
                    options_text = " (" + ", ".join(opt_names) + ")"
            
            display = f"{data['glass_type_name']} ({data['height']}x{data['width']}){options_text}"
            
            # Сохраняем в список
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self.list_glass.addItem(item)
            self.list_glass.setCurrentRow(self.list_glass.count() - 1)
            
            # Сохраняем данные
            self._glass_items_data.append(data)
    
    def _edit_glass_item(self, item):
        """Редактировать выбранное стекло (двойной щелчок)."""
        row = self.list_glass.row(item)
        if row >= 0 and row < len(self._glass_items_data):
            glass_data = self._glass_items_data[row]
            
            # Загружаем доступные типы стёкол
            glass_types = []
            price_list_id = self.get_price_list_id() or 1
            try:
                glass_types = self.opt_ctrl.get_glass_types(price_list_id)
            except:
                pass
            
            # Создаём диалог для редактирования
            dialog = GlassEditDialog(glass_data=glass_data, parent=self)
            dialog.set_glass_types(glass_types)
            
            # Загружаем глобальные опции из прайса
            try:
                global_options = self.opt_ctrl.get_all_glass_options(price_list_id)
                dialog.set_all_options(global_options)
            except:
                pass
            
            # При выборе стекла загружаем его опции (также глобальные)
            def load_options(idx):
                opts = []
                if idx < len(glass_types):
                    opts = glass_types[idx].get("options", [])
                # Добавляем глобальные опции
                try:
                    global_opts = self.opt_ctrl.get_all_glass_options(price_list_id)
                    # Объединяем, исключая дубликаты по id
                    existing_ids = {o["id"] for o in opts}
                    for go in global_opts:
                        if go["id"] not in existing_ids:
                            opts.append(go)
                except:
                    pass
                dialog.set_glass_options(opts)
            
            dialog.combo_glass_type.currentIndexChanged.connect(load_options)
            # Загружаем опции для текущего стекла
            current_idx = dialog.combo_glass_type.currentIndex()
            load_options(current_idx)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()
                
                # Формируем текст для отображения
                options_text = ""
                if data.get("options"):
                    opt_names = [o["name"] for o in data["options"]]
                    if len(opt_names) > 0:
                        options_text = " (" + ", ".join(opt_names) + ")"
                
                display = f"{data['glass_type_name']} ({data['height']}x{data['width']}){options_text}"
                
                # Обновляем в списке
                item.setText(display)
                item.setData(Qt.ItemDataRole.UserRole, data)
                
                # Обновляем данные
                self._glass_items_data[row] = data
    
    def _remove_selected_glass(self):
        """Удалить выбранное стекло из списка."""
        current_row = self.list_glass.currentRow()
        if current_row >= 0:
            self.list_glass.takeItem(current_row)
            if current_row < len(self._glass_items_data):
                self._glass_items_data.pop(current_row)
    
    def _add_hardware(self, hw_type: str):
        """Legacy method - now uses dropdowns."""
        # This method is kept for compatibility but uses dropdowns now
        if hw_type == "Замок":
            self._add_selected_hardware()
        elif hw_type == "Ручка":
            self._add_selected_hardware()
