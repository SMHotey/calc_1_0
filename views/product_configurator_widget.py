"""Главный конфигуратор: слева параметры/опции, справа таблица КП."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QLayout,
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
from views.dialogs.save_offer_dialog import SaveOfferDialog


class CollapsibleBlock(QWidget):
    """Сворачиваемый блок с кнопкой Развернуть/Свернуть."""

    toggled = pyqtSignal(bool)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._init_ui(title)

    def _init_ui(self, title: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Заголовок с кнопкой
        header = QHBoxLayout()
        header.setSpacing(0)
        header.addStretch()

        self._btn_toggle = QPushButton("▶ Развернуть")
        self._btn_toggle.setStyleSheet(
            "QPushButton { background-color: #a8b2c1; color: white; "
            "border: none; padding: 2px 8px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #8a95a5; }"
        )
        self._btn_toggle.clicked.connect(self._on_toggle)
        header.addWidget(self._btn_toggle)

        self._header_widget = QWidget()
        self._header_widget.setStyleSheet(
            f"background-color: #e8edf2; border: 1px solid #c0c8d4; "
            f"border-radius: 4px; padding: 4px;"
        )
        inner = QVBoxLayout(self._header_widget)
        inner.setContentsMargins(5, 3, 5, 3)
        inner.addLayout(header)

        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet("color: #2c3e50; font-size: 10pt;")
        header.insertWidget(0, title_label)

        layout.addWidget(self._header_widget)

        # Контент (скрыт по умолчанию)
        self._content_widget = QWidget()
        self._content_widget.setVisible(False)
        self._content_widget.setStyleSheet(
            "background-color: #f5f7fa; border: 1px solid #c0c8d4; "
            "border-top: none; border-radius: 0 0 4px 4px; padding: 8px;"
        )
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self._content_widget)

    def _on_toggle(self):
        self._expanded = not self._expanded
        self._content_widget.setVisible(self._expanded)
        self._btn_toggle.setText("▼ Свернуть" if self._expanded else "▶ Развернуть")
        self.toggled.emit(self._expanded)

    def set_expanded(self, expanded: bool):
        """Установить состояние (вызвать до добавления контента)."""
        self._expanded = expanded
        self._content_widget.setVisible(expanded)
        self._btn_toggle.setText("▼ Свернуть" if expanded else "▶ Развернуть")

    def content_layout(self) -> QVBoxLayout:
        """Вернуть layout для добавления виджетов контента."""
        return self._content_layout


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


class VentGrilleEditDialog(QDialog):
    """Модальное окно добавления/редактирования вентиляционной решётки."""
    
    def __init__(self, vent_data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить решётку" if not vent_data else "Редактировать решётку")
        self.resize(350, 280)
        self._vent_data = vent_data or {}
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Выбор типа решётки
        form = QFormLayout()
        self.combo_vent_type = ProtectedComboBox()
        self.combo_vent_type.setMinimumWidth(200)
        # Два типа: техническая и противопожарная
        self.combo_vent_type.addItem("Техническая", "technical")
        self.combo_vent_type.addItem("Противопожарная", "fireproof")
        form.addRow("Тип решётки:", self.combo_vent_type)
        
        # Размеры решётки
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
        
        # Заполнить данными если редактирование
        if self._vent_data:
            self._load_existing_data()
    
    def _load_existing_data(self):
        """Загрузить существующие данные р��шётки."""
        vent_type = self._vent_data.get("vent_type_name", "")
        if vent_type:
            idx = self.combo_vent_type.findText(vent_type)
            if idx >= 0:
                self.combo_vent_type.setCurrentIndex(idx)
        if "height" in self._vent_data:
            self.spin_height.setValue(self._vent_data.get("height", 500))
        if "width" in self._vent_data:
            self.spin_width.setValue(self._vent_data.get("width", 500))
    
    def get_data(self) -> dict:
        """Получить данные решётки."""
        return {
            "vent_type_id": self.combo_vent_type.currentData(),
            "vent_type_name": self.combo_vent_type.currentText(),
            "height": self.spin_height.value(),
            "width": self.spin_width.value()
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
        save_offer_requested: Запрос на сохранение текущего КП (emit с данными)
    """
    calculate_requested = pyqtSignal(dict)
    add_to_offer_requested = pyqtSignal(dict)
    save_offer_requested = pyqtSignal(dict)

    def __init__(self, controller, cpa_ctrl, price_list_ctrl, offer_ctrl=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.cpa_ctrl = cpa_ctrl
        self.price_list_ctrl = price_list_ctrl
        self.offer_ctrl = offer_ctrl  # For saving positions to DB
        self.current_calc_result = None
        self.current_offer_id = None
        self.current_price_list_id = None
        self.current_row_index = -1  # Текущая выбранная строка для редактирования
        self.current_row_item_id = None  # ID позиции в БД (для сохранения в БД)
        self._is_editing_position = False  # Флаг: идёт редактирование существующей позиции
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
        main_layout.setSpacing(10)  # Spacing between left and right
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Сплиттер: левая часть (конфигуратор) / правая часть (таблица)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === ЛЕВАЯ ЧАСТЬ: Конфигуратор ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)  # Equal margins left/right
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(3)  # Minimal spacing
        scroll_layout.setContentsMargins(0, 0, 10, 0)  # 10px для скроллбара
        left_layout.addWidget(scroll)
        
        # 0. Выбор контрагента и прайса
        grp_context = QGroupBox("Контекст")
        context_layout = QFormLayout()
        
        self.combo_cp = ProtectedComboBox()
        self.combo_cp.setMinimumWidth(150)
        self.combo_price = ProtectedComboBox()
        # Remove price date label - not needed
        # self.lbl_price_date = QLabel("")
        
        context_layout.addRow("Контрагент:", self.combo_cp)
        context_layout.addRow("Прайс:", self.combo_price)
        
        grp_context.setLayout(context_layout)
        scroll_layout.addWidget(grp_context)
        
        # 1. Базовые параметры - Вид и Тип в одной строке
        grp_base = QGroupBox("Параметры изделия")
        base_layout = QVBoxLayout()
        
        self.combo_product = ProtectedComboBox()
        self.combo_product.addItems(PRODUCT_TYPES.keys())
        
        self.combo_type = ProtectedComboBox()
        self.combo_type.addItems(PRODUCT_TYPES[self.combo_product.currentText()])
        
        # Вид + Тип в одной строке
        product_row = QHBoxLayout()
        product_row.addWidget(QLabel("Вид:"))
        product_row.addWidget(self.combo_product)
        product_row.addWidget(QLabel("Тип:"))
        product_row.addWidget(self.combo_type)
        product_row.addStretch()
        base_layout.addLayout(product_row)
        
        # Марка + Количество в одной строке
        self.edit_mark = ProtectedComboBox()
        self.edit_mark.setEditable(True)
        self.edit_mark.setPlaceholderText("Марка")
        
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 1000)
        self.spin_qty.setValue(1)
        
        mark_row = QHBoxLayout()
        mark_row.addWidget(QLabel("Марка:"))
        mark_row.addWidget(self.edit_mark)
        mark_row.addWidget(QLabel("Кол-во:"))
        mark_row.addWidget(self.spin_qty)
        mark_row.addStretch()
        base_layout.addLayout(mark_row)
        
        grp_base.setLayout(base_layout)
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
        
        # RAL row 1 - наружний
        ext_row = QHBoxLayout()
        ext_row.setSpacing(5)
        ext_row.addWidget(QLabel("RAL наружн.:"))
        
        self.combo_ext_color = ProtectedComboBox()
        self.combo_ext_color.setEditable(True)
        self.combo_ext_color.setMinimumWidth(70)
        for r in STANDARD_RAL[:10]:
            self.combo_ext_color.addItem(str(r))
        ext_row.addWidget(self.combo_ext_color)
        
        style_layout.addLayout(ext_row)
        
        # RAL row 2 - внутренний с чекбоксом
        int_row = QHBoxLayout()
        int_row.setSpacing(5)
        self.chk_int_ral = QCheckBox("RAL внутр.:")
        self.chk_int_ral.setChecked(True)  # По умолчанию включено
        int_row.addWidget(self.chk_int_ral)
        
        self.combo_int_color = ProtectedComboBox()
        self.combo_int_color.setEditable(True)
        self.combo_int_color.setMinimumWidth(70)
        self.combo_int_color.addItems([str(r) for r in STANDARD_RAL[:10]])
        self.combo_int_color.setEnabled(True)  # Включено когда чекбокс
        int_row.addWidget(self.combo_int_color)
        
        style_layout.addLayout(int_row)
        
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
        
        # 1) Опции цвета: перенесём в CollapsibleBlock вместо старого toggle
        self.block_color_options = CollapsibleBlock("Опции цвета")
        block_color_layout = self.block_color_options.content_layout()
        color_options_hbox = QHBoxLayout()
        color_options_hbox.setSpacing(20)
        self.chk_moire = QCheckBox("муар")
        self.chk_lac = QCheckBox("лак")
        self.chk_primer = QCheckBox("грунт")
        color_options_hbox.addWidget(self.chk_moire)
        color_options_hbox.addWidget(self.chk_lac)
        color_options_hbox.addWidget(self.chk_primer)
        color_options_hbox.addStretch()
        block_color_layout.addLayout(color_options_hbox)
        style_layout.addWidget(self.block_color_options)
        
        # Старые toggle-кнопки заменены CollapsibleBlock-ми; больше не создаются
        
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
        lock_layout.addWidget(self.combo_lock)
        lock_layout.addWidget(self.btn_add_lock)
        lock_layout.addStretch()
        hw_layout.addLayout(lock_layout)
        
        # Ручка
        handle_layout = QHBoxLayout()
        handle_layout.addWidget(QLabel("Ручка:"))
        self.combo_handle = ProtectedComboBox()
        self.combo_handle.setMinimumWidth(200)
        self.btn_add_handle = QPushButton("+")
        self.btn_add_handle.setFixedWidth(25)
        self.btn_add_handle.setStyleSheet("background-color: #a8b2c1; color: white;")
        handle_layout.addWidget(self.combo_handle)
        handle_layout.addWidget(self.btn_add_handle)
        handle_layout.addStretch()
        hw_layout.addLayout(handle_layout)
        
        # Цилиндр (доступен если выбран цилиндровый замок)
        cyl_layout = QHBoxLayout()
        cyl_layout.addWidget(QLabel("Цилиндр:"))
        self.combo_cylinder = ProtectedComboBox()
        self.combo_cylinder.setMinimumWidth(200)
        self.combo_cylinder.setEnabled(False)  # Сначала недоступен
        self.btn_add_cyl = QPushButton("+")
        self.btn_add_cyl.setFixedWidth(25)
        self.btn_add_cyl.setStyleSheet("background-color: #a8b2c1; color: white;")
        cyl_layout.addWidget(self.combo_cylinder)
        cyl_layout.addWidget(self.btn_add_cyl)
        cyl_layout.addStretch()
        hw_layout.addLayout(cyl_layout)
        
        # Храним текущий выбранный замок для проверки цилиндра
        self._current_lock_requires_cylinder = False
        
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

        # 4.1. Стекло и опции
        self.block_glass = CollapsibleBlock("Стекло и опции")
        glass_block_layout = self.block_glass.content_layout()
        
        # Контент блока стекла
        self.btn_add_glass = QPushButton("Добавить стекло")
        self.btn_add_glass.setStyleSheet("background-color: #28a745; color: white; padding: 5px 15px;")
        glass_block_layout.addWidget(self.btn_add_glass)
        
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
        
        glass_block_layout.addLayout(glass_list_layout)
        
        # Подсказка
        self.lbl_glass_options_hint = QLabel("Двойной щелчок - редактировать")
        self.lbl_glass_options_hint.setStyleSheet("font-size: 9pt; color: #666;")
        glass_block_layout.addWidget(self.lbl_glass_options_hint)
        
        scroll_layout.addWidget(self.block_glass)
        
        # Хранилище данных о выбранных стеклах
        self._glass_items_data = []  # list of dict: {glass_type_id, glass_type_name, height, width, options}
        
        # 4.2. Вентиляционные решётки → заменяем на CollapsibleBlock
        self.block_vent = CollapsibleBlock("Вентиляционные решётки")
        vent_block_layout = self.block_vent.content_layout()
        self.btn_add_vent = QPushButton("Добавить решётку")
        self.btn_add_vent.setStyleSheet("background-color: #28a745; color: white; padding: 5px 15px;")
        self.btn_add_vent.clicked.connect(self._add_vent_grille)
        vent_block_layout.addWidget(self.btn_add_vent)
        
        vent_list_layout = QHBoxLayout()
        self.list_vent = QListWidget()
        self.list_vent.setMaximumHeight(80)
        vent_list_layout.addWidget(self.list_vent)
        
        vent_btn_layout = QVBoxLayout()
        vent_btn_layout.setSpacing(2)
        self.btn_del_vent = QPushButton("✕")
        self.btn_del_vent.setFixedWidth(25)
        self.btn_del_vent.setStyleSheet("background-color: #dc3545; color: white;")
        self.btn_del_vent.clicked.connect(self._remove_selected_vent)
        vent_btn_layout.addWidget(self.btn_del_vent)
        vent_btn_layout.addStretch()
        vent_list_layout.addLayout(vent_btn_layout)
        
        vent_block_layout.addLayout(vent_list_layout)
        scroll_layout.addWidget(self.block_vent)
        
        # Хранилище данных о выбранных решётках
        self._vent_items_data = []  # list of dict: {vent_type_id, vent_type_name, height, width}
        
        # 5. Дополнительные опции
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
        
        # Добор (добавлено по запросу)
        doborr_layout = QHBoxLayout()
        self.chk_doborr = QCheckBox("Добор:")
        self.spin_doborr_depth = QSpinBox()
        self.spin_doborr_depth.setRange(50, 300)
        self.spin_doborr_depth.setValue(100)
        self.spin_doborr_depth.setSuffix(" мм")
        self.spin_doborr_depth.setVisible(False)
        self.spin_doborr_depth.setAlignment(Qt.AlignmentFlag.AlignCenter)
        doborr_layout.addWidget(self.chk_doborr)
        doborr_layout.addWidget(self.spin_doborr_depth)
        doborr_layout.addStretch()

        # Добавляем всё в блок "Дополнительные опции"
        self.block_extra = CollapsibleBlock("Дополнительные опции")
        extra_block_layout = self.block_extra.content_layout()
        for w in [self.chk_threshold, self.chk_hinges, self.hinges_container, self.chk_anti_theft, self.chk_gkl, self.chk_mount_ears, self.mount_ears_input, self.chk_deflector, self.spin_deflector_h, self.deflector_two_sided, self.chk_doborr, self.spin_doborr_depth]:
            if isinstance(w, QLayout):
                extra_block_layout.addLayout(w)
            else:
                extra_block_layout.addWidget(w)
        scroll_layout.addWidget(self.block_extra)

        # 6) Наценка - заменить на CollapsibleBlock
        self.block_markup = CollapsibleBlock("Наценка")
        markup_block_layout = self.block_markup.content_layout()
        # Create spin boxes first (moved from old grp_markup)
        self.spin_markup_pct = QDoubleSpinBox()
        self.spin_markup_pct.setRange(0, 500)
        self.spin_markup_pct.setSuffix(" %")
        self.spin_markup_val = QDoubleSpinBox()
        self.spin_markup_val.setRange(0, 1e6)
        self.spin_markup_val.setPrefix("₽ ")
        form_markup = QFormLayout()
        form_markup.addRow("Процент:", self.spin_markup_pct)
        form_markup.addRow("Фикс.:", self.spin_markup_val)
        markup_block_layout.addLayout(form_markup)
        scroll_layout.addWidget(self.block_markup)
        
        # 7) Прочее (скрыт по умолчанию) -> заменить на CollapsibleBlock
        self.block_other = CollapsibleBlock("Прочее")
        other_block_layout = self.block_other.content_layout()
        # Доставка
        self.spin_delivery = QDoubleSpinBox()
        self.spin_delivery.setRange(0, 1e6)
        self.spin_delivery.setPrefix("₽ ")
        self.spin_delivery.setValue(0)
        delivery_layout = QHBoxLayout()
        delivery_layout.addWidget(QLabel("Доставка:"))
        delivery_layout.addWidget(self.spin_delivery)
        other_block_layout.addLayout(delivery_layout)
        
        # Замер
        self.spin_measurement = QDoubleSpinBox()
        self.spin_measurement.setRange(0, 1e6)
        self.spin_measurement.setPrefix("₽ ")
        self.spin_measurement.setValue(0)
        measure_layout = QHBoxLayout()
        measure_layout.addWidget(QLabel("Замер:"))
        measure_layout.addWidget(self.spin_measurement)
        other_block_layout.addLayout(measure_layout)
        
        # Монтаж
        self.spin_installation = QDoubleSpinBox()
        self.spin_installation.setRange(0, 1e6)
        self.spin_installation.setPrefix("₽ ")
        self.spin_installation.setValue(0)
        install_layout = QHBoxLayout()
        install_layout.addWidget(QLabel("Монтаж:"))
        install_layout.addWidget(self.spin_installation)
        other_block_layout.addLayout(install_layout)
        
        # Бонус клиенту
        self.spin_bonus = QDoubleSpinBox()
        self.spin_bonus.setRange(0, 1e6)
        self.spin_bonus.setPrefix("₽ ")
        self.spin_bonus.setValue(0)
        bonus_layout = QHBoxLayout()
        bonus_layout.addWidget(QLabel("Бонус клиенту:"))
        bonus_layout.addWidget(self.spin_bonus)
        other_block_layout.addLayout(bonus_layout)
        scroll_layout.addWidget(self.block_other)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        left_layout.addWidget(scroll)

        # 5b. Доводчик / Координатор - сворачиваемый блок
        self.block_closer = CollapsibleBlock("Доводчик / Координатор")
        closer_block_layout = self.block_closer.content_layout()
        
        # Доводчик 1 (для одностворчатых или первой створки)
        closer1_layout = QHBoxLayout()
        self.chk_closer1 = QCheckBox("Доводчик 1:")
        self.combo_closer1 = ProtectedComboBox()
        self.combo_closer1.setMinimumWidth(120)
        self.combo_closer1.setEnabled(False)
        self.btn_add_closer1 = QPushButton("+")
        self.btn_add_closer1.setFixedWidth(25)
        self.btn_add_closer1.setStyleSheet("background-color: #a8b2c1; color: white;")
        closer1_layout.addWidget(self.chk_closer1)
        closer1_layout.addWidget(self.combo_closer1)
        closer1_layout.addWidget(self.btn_add_closer1)
        closer1_layout.addStretch()
        closer_block_layout.addLayout(closer1_layout)
        
        # Доводчик 2 (только для 2 створок)
        closer2_layout = QHBoxLayout()
        self.chk_closer2 = QCheckBox("Доводчик 2:")
        self.chk_closer2.setVisible(False)
        self.combo_closer2 = ProtectedComboBox()
        self.combo_closer2.setMinimumWidth(120)
        self.combo_closer2.setVisible(False)
        self.combo_closer2.setEnabled(False)
        self.btn_add_closer2 = QPushButton("+")
        self.btn_add_closer2.setFixedWidth(25)
        self.btn_add_closer2.setStyleSheet("background-color: #a8b2c1; color: white;")
        closer2_layout.addWidget(self.chk_closer2)
        closer2_layout.addWidget(self.combo_closer2)
        closer2_layout.addWidget(self.btn_add_closer2)
        closer2_layout.addStretch()
        closer_block_layout.addLayout(closer2_layout)
        
        # Координатор (показывается при выборе обоих доводчиков)
        coord_layout = QHBoxLayout()
        self.chk_coordinator = QCheckBox("Координатор:")
        self.chk_coordinator.setVisible(False)
        self.chk_coordinator.setEnabled(False)
        self.combo_coordinator_new = ProtectedComboBox()
        self.combo_coordinator_new.setMinimumWidth(120)
        self.combo_coordinator_new.setVisible(False)
        self.combo_coordinator_new.setEnabled(False)
        self.btn_add_coordinator = QPushButton("+")
        self.btn_add_coordinator.setFixedWidth(25)
        self.btn_add_coordinator.setStyleSheet("background-color: #a8b2c1; color: white;")
        coord_layout.addWidget(self.chk_coordinator)
        coord_layout.addWidget(self.combo_coordinator_new)
        coord_layout.addWidget(self.btn_add_coordinator)
        coord_layout.addStretch()
        closer_block_layout.addLayout(coord_layout)
        
        scroll_layout.addWidget(self.block_closer)
        
        # === ПРАВАЯ ЧАСТЬ: Таблица КП (2/3) ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        grp_table = QGroupBox("Позиции КП")
        table_layout = QVBoxLayout()
        
        self.table_offer = QTableWidget()
        self.table_offer.setColumnCount(5)
        self.table_offer.setHorizontalHeaderLabels(["Марка", "Изделие", "Размеры", "Кол-во", "Комплектация"])
        # Растягиваем последний столбец (Комплектация) - он займёт всё доступное пространство
        self.table_offer.horizontalHeader().setStretchLastSection(True)
        self.table_offer.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_offer.setMinimumHeight(300)
        
        # Включаем перенос текста - важно для многострочного отображения
        self.table_offer.setWordWrap(True)
        self.table_offer.setTextElideMode(Qt.TextElideMode.ElideNone)
        
        # Настраиваем столбцы: Комплектация шире (растягивается), остальные минимальные
        # Марка: 50 * 0.6 = 30, Изделие: 140 * 1.35 = 190, Размеры: 70 * 0.8 = 56, Кол-во: 45 * 0.5 = 23
        self.table_offer.setColumnWidth(0, 30)     # Марка
        self.table_offer.setColumnWidth(1, 190)   # Изделие
        self.table_offer.setColumnWidth(2, 55)     # Размеры
        self.table_offer.setColumnWidth(3, 25)    # Кол-во
        
        # Подключаем обработчик выбора строки
        self.table_offer.itemSelectionChanged.connect(self._on_row_selected)
        
        # Контекстное меню
        self.table_offer.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_offer.customContextMenuRequested.connect(self._show_context_menu)
        
        # Двойной щелчок - открыть детализацию
        self.table_offer.cellDoubleClicked.connect(self._show_position_details)
        self.table_offer.verticalHeader().setDefaultSectionSize(40)  # Высота строк +40%
        
        table_layout.addWidget(self.table_offer)
        
        table_btn_layout = QHBoxLayout()
        self.btn_save_offer = QPushButton("Сохранить КП")
        self.btn_save_offer.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        btn_new_offer = QPushButton("Новое КП")
        btn_remove = QPushButton("Удалить поз.")
        self.btn_save_offer.clicked.connect(self._save_offer)
        btn_new_offer.clicked.connect(self._create_new_offer)
        btn_remove.clicked.connect(self._remove_position)
        table_btn_layout.addWidget(self.btn_save_offer)
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
        
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save_position)
        btn_row.addStretch(0)
        actions_layout.addLayout(btn_row)
        grp_actions.setLayout(actions_layout)
        right_layout.addWidget(grp_actions)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Настройка сплиттера - 35% слева, 65% справа
        splitter.setStretchFactor(0, 35)  # Левая часть
        splitter.setStretchFactor(1, 65)  # Правая часть
        splitter.setSizes([350, 900])  # Начальные размеры
        
        main_layout.addWidget(splitter)
        
        # Кнопки должны быть всегда видимы
        self.btn_add.setVisible(True)
        self.lbl_preview.setVisible(True)
        
        self._mark_unsaved_changes()  # Скрываем Save при сбросе формы
        self._update_dimensions_for_product()
        
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
        
        # Skip price date label - removed per UX request
        pass  # self._update_price_date_label()
    
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
                # Format: "Название (вес кг)"
                display_text = f"{c.name} ({c.door_weight:.0f} кг)"
                self.combo_closer1.addItem(display_text, c.id)
                self.combo_closer2.addItem(display_text, c.id)
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

        self.chk_by_opening.toggled.connect(self.check_opening_visibility)
        
        # Сигнал для проверки цилиндра при выборе замка
        self.combo_lock.currentIndexChanged.connect(self._on_lock_changed)
        
        # RAL - автозаполнение внутреннего при изменении
        self.combo_ext_color.currentIndexChanged.connect(self._on_ext_color_changed)
        self.combo_int_color.currentIndexChanged.connect(self._on_int_color_changed)
        
        # Чекбокс RAL внутр - включить/выключить поле
        self.chk_int_ral.toggled.connect(self._toggle_int_ral)
        
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
        
        # Сигнал для стекла
        self.btn_add_glass.clicked.connect(self._add_selected_glass)
        
        # Сигналы для вентиляционных решёток
        self.btn_add_vent.clicked.connect(self._add_vent_grille)
        self.btn_del_vent.clicked.connect(self._remove_selected_vent)
        
        # Новые сигналы для доводчиков
        self.chk_double.toggled.connect(self._on_double_toggled_closer)
        self.chk_closer1.toggled.connect(self._on_closer1_toggled)
        self.chk_closer2.toggled.connect(self._on_closer2_toggled)
        
        # Сигнал для добора
        self.chk_doborr.toggled.connect(self._toggle_doborr_depth)
    
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
    
    def _toggle_by_opening_fields(self, checked: bool):
        """Показать/скрыть поля вычитаемых миллиметров при выборе 'по проёму'."""
        self.spin_by_opening_height.setVisible(checked)
        self.spin_by_opening_width.setVisible(checked)

    def _toggle_deflector_visibility(self, checked: bool):
        """Показывать/скрывать поля отбойной пластины и связанных опций."""
        self.spin_deflector_h.setVisible(checked)
        self.deflector_two_sided.setVisible(checked)

    def _toggle_mount_ears(self, checked: bool):
        """Показывать/скрывать поле ввода количества монтажных ушей."""
        self.mount_ears_input.setVisible(checked)
    
    def _toggle_doborr_depth(self, checked: bool):
        """Показывать/скрывать поле ввода глубины добора."""
        self.spin_doborr_depth.setVisible(checked)
    
    def _add_vent_grille(self):
        """Добавить вентиляционную решётку через модальное окно."""
        dialog = VentGrilleEditDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            vent_name = data.get("vent_type_name", "Техническая")
            self._vent_items_data.append(data)
            self.list_vent.addItem(f"{vent_name} {data.get('height', 0)}x{data.get('width', 0)}")
    
    def _remove_selected_vent(self):
        """Удалить выбранную решётку."""
        current_row = self.list_vent.currentRow()
        if current_row >= 0:
            self.list_vent.takeItem(current_row)
            if current_row < len(self._vent_items_data):
                self._vent_items_data.pop(current_row)
    
    def _on_lock_changed(self, idx: int):
        """Обработка изменения выбора замка - включение/выключение поля цилиндра."""
        lock_id = self.combo_lock.currentData()
        requires_cylinder = False
        
        if lock_id:
            try:
                lock = self.hw_ctrl.get_by_id(lock_id)
                if lock and hasattr(lock, 'has_cylinder'):
                    requires_cylinder = lock.has_cylinder
            except:
                pass
        
        self._current_lock_requires_cylinder = requires_cylinder
        self.combo_cylinder.setEnabled(requires_cylinder)
        
        # Если цилиндр не требуется - сбрасываем выбор
        if not requires_cylinder:
            self.combo_cylinder.setCurrentIndex(0)
    
    def _get_selected_hardware_display(self) -> list:
        """Получить список выбранной фурнитуры для отображения."""
        items = []
        
        # Замок
        lock_name = self.combo_lock.currentText()
        lock_id = self.combo_lock.currentData()
        if lock_id:
            items.append(lock_name)
        
        # Ручка
        handle_name = self.combo_handle.currentText()
        handle_id = self.combo_handle.currentData()
        if handle_id:
            items.append(handle_name)
        
        # Цилиндр (если требуется)
        if self._current_lock_requires_cylinder:
            cyl_name = self.combo_cylinder.currentText()
            cyl_id = self.combo_cylinder.currentData()
            if cyl_id:
                items.append(cyl_name)
        
        return items
    
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
            # Получаем текст из колонки Комплектация (column 4)
            item = self.table_offer.item(row, 4)
            if item:
                text = item.text()
                # Ширина доступной области для текста
                available_width = self.table_offer.columnWidth(4)
                # Если столбец растянут - получаем его реальную ширину
                header = self.table_offer.horizontalHeader()
                if header.sectionResizeMode(4) == QHeaderView.ResizeMode.Stretch:
                    # Приблизительная ширина - вся ширина таблицы минус другие столбцы
                    total_width = self.table_offer.viewport().width()
                    available_width = total_width - 200  # примерно
                
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
                    # Высота строки текста примерно 16px + 15% для запаса
                    new_height = int(lines * 18 * 1.15)
                    # Минимум стандартная высота
                    new_height = max(new_height, 30)
                    self.table_offer.setRowHeight(row, new_height)
                else:
                    # Стандартная высота
                    self.table_offer.setRowHeight(row, 30)
    
    def _update_mark_column_visibility(self):
        """Скрыть столбец Марка, если во всех строках значение пустое."""
        has_mark = False
        for row in range(self.table_offer.rowCount()):
            item = self.table_offer.item(row, 0)
            if item and item.text().strip():
                has_mark = True
                break
        # Скрываем или показываем столбец Марка (column 0)
        self.table_offer.setColumnHidden(0, not has_mark)

    def _mark_unsaved_changes(self):
        """Показать кнопку Сохранить если идёт редактирование позиции."""
        if self._is_editing_position and hasattr(self, 'btn_save_position'):
            self.btn_save_position.setVisible(True)
    
    def _toggle_color_options(self, expanded: bool):
        """Переключение видимости блока Опции цвета."""
        self.btn_color_options_toggle.setText("▼ Опции цвета" if expanded else "▶ Опции цвета")
        self.chk_moire.setVisible(expanded)
        self.chk_lac.setVisible(expanded)
        self.chk_primer.setVisible(expanded)
    
    def _toggle_glass_block(self, expanded: bool):
        """Переключение видимости блока Стекла и опции."""
        self.btn_glass_toggle.setText("▼ Стекло и опции" if expanded else "▶ Стекло и опции")
        self.grp_glass.setVisible(expanded)
    
    def _toggle_vent_block(self, expanded: bool):
        """Переключение видимости блока Вентиляционные решётки."""
        self.btn_vent_toggle.setText("▼ Вентиляционные решётки" if expanded else "▶ Вентиляционные решётки")
        self.grp_vent.setVisible(expanded)
    
    def _toggle_extra_block(self, expanded: bool):
        """Переключение видимости блока Дополнительные опции."""
        self.btn_extra_toggle.setText("▼ Дополнительные опции" if expanded else "▶ Дополнительные опции")
        self.grp_extra.setVisible(expanded)
    
    def _toggle_markup_block(self, expanded: bool):
        """Переключение видимости блока Наценка."""
        self.btn_markup_toggle.setText("▼ Наценка" if expanded else "▶ Наценка")
        self.grp_markup.setVisible(expanded)
    
    def _toggle_other_block(self, expanded: bool):
        """Переключение видимости блока Прочее."""
        self.btn_other_toggle.setText("▼ Прочее" if expanded else "▶ Прочее")
        self.grp_other.setVisible(expanded)
    
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
        self.btn_add_closer1.setEnabled(checked)
        if not checked:
            self.chk_closer2.setChecked(False)
            self.combo_closer2.setEnabled(False)
            self.btn_add_closer2.setEnabled(False)
            self.chk_coordinator.setChecked(False)
            self.chk_coordinator.setEnabled(False)
            self.combo_coordinator_new.setEnabled(False)
            self.btn_add_coordinator.setEnabled(False)
        # Показать координатор если оба доводчика выбраны
        if checked and self.chk_closer2.isChecked():
            self.chk_coordinator.setVisible(True)
            self.chk_coordinator.setEnabled(True)
            self.combo_coordinator_new.setVisible(True)
            self.combo_coordinator_new.setEnabled(True)
            self.btn_add_coordinator.setEnabled(True)
    
    def _on_closer2_toggled(self, checked: bool):
        """Активация доводчика 2."""
        self.combo_closer2.setEnabled(checked)
        self.btn_add_closer2.setEnabled(checked)
        if not checked:
            self.chk_coordinator.setChecked(False)
            self.chk_coordinator.setEnabled(False)
            self.combo_coordinator_new.setEnabled(False)
            self.btn_add_coordinator.setEnabled(False)
        # Показать координатор если оба доводчика выбраны
        if checked and self.chk_closer1.isChecked():
            self.chk_coordinator.setVisible(True)
            self.chk_coordinator.setEnabled(True)
            self.combo_coordinator_new.setVisible(True)
            self.combo_coordinator_new.setEnabled(True)
            self.btn_add_coordinator.setEnabled(True)
    
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
    
    def _toggle_int_ral(self, checked: bool):
        """Включить/выключить поле RAL внутр."""
        self.combo_int_color.setEnabled(checked)
        if not checked:
            # When disabled, sync with outer RAL
            ext_val = self.combo_ext_color.currentText()
            idx = self.combo_int_color.findText(ext_val)
            if idx >= 0:
                self.combo_int_color.setCurrentIndex(idx)
            else:
                self.combo_int_color.setCurrentText(ext_val)
    
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
        # Skip price date label update - removed per UX request
        
        # Сбрасываем флаг ручного ввода внутреннего цвета при смене прайса
        self._ral_internal_manually_set = False
        
        # Перезагружаем выпадающие списки из нового прайса
        self._load_hardware_options()
        
        if self.table_offer.rowCount() > 0:
            self._recalculate_all_items()
    
    def _recalculate_all_items(self):
        """Пересчёт всех позиций КП при смене прайса."""
        if self.table_offer.rowCount() == 0:
            return
        
        # Сохраняем текущие позиции
        items_data = []
        for row in range(self.table_offer.rowCount()):
            item_data = self.table_offer.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if item_data:
                items_data.append(item_data)
        
        if not items_data:
            return
        
        # Очищаем таблицу и пересчитываем каждую позицию
        self.table_offer.setRowCount(0)
        self.last_offer_items = []
        
        price_list_id = self.get_price_list_id()
        
        for item_data in items_data:
            # Пересчитываем с текущим прайс-листом
            result = self.controller.validate_and_calculate(
                item_data.get("product_type", ""),
                item_data.get("subtype", ""),
                item_data.get("height", 0),
                item_data.get("width", 0),
                price_list_id,
                item_data,
                item_data.get("markup_percent", 0),
                item_data.get("markup_abs", 0),
                item_data.get("quantity", 1)
            )
            
            if result.get("success"):
                # Обновляем цену в данных
                item_data["price_per_unit"] = result.get("price_per_unit", 0)
                item_data["total_price"] = result.get("total_price", 0)
                item_data["area"] = result.get("area", 0)
                self.add_position_to_table(item_data)
                self.last_offer_items.append(item_data)
        
        # Обновляем итоговую сумму
        self._update_total()

    
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
            "vent_items": self._vent_items_data,  # Ventilation grilles
            "hardware_items": hw_items,
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
                "deflector_double_side": self.deflector_two_sided.isChecked() if self.chk_deflector.isChecked() else False,
                "doborr": self.chk_doborr.isChecked(),
                "doborr_depth": self.spin_doborr_depth.value() if self.chk_doborr.isChecked() else 0
            },
            "other": {
                "delivery": self.spin_delivery.value() if hasattr(self, 'spin_delivery') else 0,
                "measurement": self.spin_measurement.value() if hasattr(self, 'spin_measurement') else 0,
                "installation": self.spin_installation.value() if hasattr(self, 'spin_installation') else 0,
                "bonus": self.spin_bonus.value() if hasattr(self, 'spin_bonus') else 0
            }
        }
    
    def refresh_price_lists(self):
        """Обновляет выпадающий список прайс-листов извне.
        
        Используется для синхронизации с другими вкладками (например, Прайс),
        когда создаётся новый прайс-лист.
        """
        current_id = self.get_price_list_id()
        self._load_price_lists()
        # Восстанавливаем выбор, если возможно
        if current_id:
            self._select_price_list(current_id)
    
    def _select_price_list(self, price_list_id: int):
        """Выбор прайс-листа в выпадающем списке по ID."""
        for i in range(self.combo_price.count()):
            if self.combo_price.itemData(i) == price_list_id:
                self.combo_price.setCurrentIndex(i)
                return
        # Если не нашли, выбираем базовый (первый)
        if self.combo_price.count() > 0:
            self.combo_price.setCurrentIndex(0)
    
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
    
    def _create_new_offer(self):
        """Создать новое КП. Испускает сигнал с действием."""
        # Сигнал для создания нового КП - передаём текущее количество позиций
        row_count = self.table_offer.rowCount()
        self.add_to_offer_requested.emit({"_action": "create_offer", "current_row_count": row_count})

    def _save_offer(self):
        """Сохранить текущее КП."""
        if not self.current_offer_id:
            QMessageBox.warning(self, "Внимание", "Нет активного КП для сохранения.")
            return
        
        # Сбор данных о КП
        row_count = self.table_offer.rowCount()
        if row_count == 0:
            QMessageBox.warning(self, "Внимание", "Нет позиций для сохранения в КП.")
            return
        
        # Получаем данные о контрагенте
        cp_name = "—"
        cp_id = self.combo_cp.currentData()
        if cp_id:
            try:
                cp = self.cpa_ctrl.get_by_id(cp_id)
                if cp:
                    cp_name = cp.name
            except:
                pass
        
        # Получаем данные о прайсе
        price_list_name = "Базовый прайс"
        price_list_id = self.get_price_list_id()
        
        # Подсчёт сумм
        total_base = 0.0
        total_current = 0.0
        for r in range(row_count):
            item = self.table_offer.item(r, 5)
            if item:
                try:
                    # Цена за единицу
                    price_text = item.text().replace(" ₽", "").replace(",", ".").strip()
                    price = float(price_text)
                    
                    # Кол-во
                    qty_item = self.table_offer.item(r, 4)
                    qty = int(qty_item.text()) if qty_item else 1
                    
                    total_current += price * qty
                    
                    # Для базовой цены используем тот же прайс (упрощённо)
                    total_base += price * qty
                except:
                    pass
        
        markup = total_current - total_base
        
        offer_data = {
            "number": self._get_current_offer_number(),
            "counterparty": cp_name,
            "price_list": price_list_name,
            "items_count": row_count,
            "base_sum": total_base,
            "current_sum": total_current,
            "markup": markup,
            "offer_id": self.current_offer_id
        }
        
        # Показываем диалог
        dialog = SaveOfferDialog(offer_data, self)
        if dialog.exec():
            new_name = dialog.get_name()
            # emit signal for parent to handle actual save
            self.save_offer_requested.emit({
                "offer_id": self.current_offer_id,
                "new_name": new_name
            })

    def _get_current_offer_number(self) -> str:
        """Получить номер текущего КП."""
        # Пытаемся найти номер в таблице или контроллере
        for r in range(self.table_offer.rowCount()):
            item = self.table_offer.item(r, 0)
            if item and item.text():
                # Первый номер в таблице - номер КП
                # Но это позиция, не КП. Нужен отдельный атрибут
                pass
        
        # Попробуем получить из контроллера
        if self.current_offer_id:
            try:
                return self.controller.get_offer_number(self.current_offer_id)
            except:
                pass
        
        # Генерируем авто-номер
        from datetime import datetime
        year_month = datetime.now().strftime("%y%m")
        return f"КО-{year_month}"
    
    def _remove_position(self):
        row = self.table_offer.currentRow()
        if row >= 0:
            self.table_offer.removeRow(row)
            # Номера строк больше не нужны
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
        
        # === Добор ===
        self.chk_doborr.setChecked(extra.get("doborr", False))
        self.spin_doborr_depth.setValue(extra.get("doborr_depth", 100))
        
        # === Прочее ===
        if "other" in config:
            other = config["other"]
            self.spin_delivery.setValue(other.get("delivery", 0))
            self.spin_measurement.setValue(other.get("measurement", 0))
            self.spin_installation.setValue(other.get("installation", 0))
            self.spin_bonus.setValue(other.get("bonus", 0))
        
        # Сохраняем индекс текущей строки и ID позиции в БД
        self.current_row_index = row
        self.current_row_item_id = (config.get("item_id") if config else None)
        self._is_editing_position = (self.current_row_item_id is not None)
        
        # Показываем кнопку Сохранить
        if hasattr(self, 'btn_save_position'):
            self.btn_save_position.setVisible(True)
    
    def _save_position_changes(self):
        """Сохраняет изменения в позиции в БД."""
        if self.current_row_index < 0 or self.current_row_index >= self.table_offer.rowCount():
            QMessageBox.warning(self, "Ошибка", "Выберите позицию для сохранения.")
            return
        
        # Получаем item_id из UserRole
        item = self.table_offer.item(self.current_row_index, 0)
        if not item:
            QMessageBox.warning(self, "Ошибка", "Данные позиции не найдены.")
            return
        
        row_data = item.data(Qt.ItemDataRole.UserRole)
        item_id = row_data.get("item_id") if row_data else None
        
        # Собираем данные из формы
        data = self._collect_config()
        
        if item_id and self.offer_ctrl:
            # Пересчёт цены перед сохранением
            price_list_id = self.get_price_list_id() or 1
            try:
                from controllers.calculator_controller import CalculatorController
                calc_ctrl = CalculatorController()
                result = calc_ctrl.validate_and_calculate(
                    data["product_type"], data["subtype"],
                    data["height"], data["width"],
                    price_list_id, data,
                    data.get("markup_percent", 0),
                    data.get("markup_abs", 0),
                    data.get("quantity", 1)
                )
                if result.get("success"):
                    data["base_price"] = result.get("price_per_unit", 0)
                    data["final_price"] = result.get("total_price", 0) / max(data.get("quantity", 1), 1)
                    data["options"] = result.get("details", {})
                    data["price_per_unit"] = data["base_price"]
                    data["total_price"] = result.get("total_price", 0)
                else:
                    QMessageBox.warning(self, "Ошибка расчёта", result.get("error", "Неизвестная ошибка"))
                    return
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось пересчитать цену: {e}")
                return
            
            # Обновляем в БД
            update_data = {
                "product_type": data["product_type"],
                "subtype": data["subtype"],
                "width": data["width"],
                "height": data["height"],
                "quantity": data.get("quantity", 1),
                "options_": data.get("options", {}),
                "base_price": data["base_price"],
                "markup_percent": data.get("markup_percent", 0),
                "markup_abs": data.get("markup_abs", 0),
                "final_price": data["final_price"],
            }
            
            try:
                self.offer_ctrl.update_item(item_id, update_data)
                self.offer_ctrl.session.commit()
            except Exception as e:
                self.offer_ctrl.session.rollback()
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")
                return
        else:
            # Если нет item_id — только UI update (новые позиции ещё не в БД)
            pass
        
        # Обновляем строку в таблице UI
        self.table_offer.removeRow(self.current_row_index)
        # Добавляем item_id обратно в data
        data["item_id"] = item_id
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
        
        # Марка (column 0) - выравнивание по центру
        mark_item = QTableWidgetItem(item_data.get("mark", ""))
        mark_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_offer.setItem(row, 0, mark_item)
        
        # Изделие: Вид изделия + тип + 2-ств. (если дверь/люк с 2 створками) (column 1)
        product_type = item_data.get("product_type", "")
        subtype = item_data.get("subtype", "")
        is_double = item_data.get("is_double_leaf", False)
        
        # Для дверей и люков добавляем "2-ств." при двух створках
        if is_double and product_type in ("Дверь", "Люк"):
            product_desc = f"{product_type} 2-ств. {subtype}"
        else:
            product_desc = f"{product_type} {subtype}"
        
        product_item = QTableWidgetItem(product_desc)
        product_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_offer.setItem(row, 1, product_item)
        
        # Размеры: формат "ВxШ" (высота x ширина) (column 2)
        w = item_data.get("width", 0)
        h = item_data.get("height", 0)
        size_str = f"{int(h)}x{int(w)}"
        size_item = QTableWidgetItem(size_str)
        size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_offer.setItem(row, 2, size_item)
        
        # Кол-во (column 3) - выравнивание по центру
        qty_item = QTableWidgetItem(str(item_data.get("quantity", 1)))
        qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_offer.setItem(row, 3, qty_item)
        
        # Комплектация: собираем все выбранные опции через запятую (column 4)
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
        # Комплектация (column 4) - создаём ячейку с переносом
        comp_item = QTableWidgetItem(comp_str)
        comp_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.table_offer.setItem(row, 4, comp_item)
        
        # Сохраняем полные данные позиции для загрузки в форму
        # Используем UserRole для хранения всей конфигурации
        price_per_unit = item_data.get("price_per_unit", 0)
        markup_percent = item_data.get("markup_percent", 0)
        markup_abs = item_data.get("markup_abs", 0)
        total_price = item_data.get("total_price", 0)
        quantity = item_data.get("quantity", 1)
        
        # Сохраняем полную конфигурацию в UserRole (column 0 - Марка)
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
        
        # Скрыть столбец Марка, если во всех строках пусто
        self._update_mark_column_visibility()
        
        self.table_offer.repaint()
        
        # Дополнительно обновляем через таймер (для надёжности)
        QTimer.singleShot(10, self.table_offer.viewport().update)
    
    def clear_offer_table(self):
        """Очищает таблицу КП."""
        self.table_offer.setRowCount(0)
        self.last_offer_items.clear()
        self._update_total()
        self.lbl_preview.setText("Добавьте позиции в КП")
        # Показать столбец Марка обратно (он скрыт при пустой таблице)
        self.table_offer.setColumnHidden(0, False)
    
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
    
    def load_item(self, item_id: int):
        """Загружает позицию из БД по ID в форму для редактирования.
        
        Получает данные из OfferController.update_item (через получение item),
        добавляет в таблицу configurator и загружает в форму.
        """
        if not self.offer_ctrl:
            return
        
        # Получаем позицию из БД — ищем в текущем offer если есть
        from sqlalchemy import select
        from models.commercial_offer import OfferItem
        
        # Пытаемся найти позицию в любом КП
        stmt = select(OfferItem).where(OfferItem.id == item_id)
        item = self.offer_ctrl.session.execute(stmt).scalar_one_or_none()
        if not item:
            return
        
        # Запоминаем offer_id если ещё не задан
        if not self.current_offer_id:
            self.current_offer_id = item.offer_id
        
        # Формируем словарь для add_position_to_table
        item_data = {
            "item_id": item.id,
            "mark": getattr(item, 'mark', ''),
            "product_type": item.product_type,
            "subtype": item.subtype,
            "width": item.width,
            "height": item.height,
            "quantity": item.quantity,
            "is_double_leaf": False,  # определяется из options_ если нужно
            "color_external": 7035,
            "color_internal": 7035,
            "metal_thickness": "1.0-1.0",
            "options": item.options_,
            "extra_options": item.options_,
            "hardware_items": [],
            "glass_items": [],
            "glass_items_display": [],
            "base_price": item.base_price,
            "price_per_unit": item.base_price,
            "markup_percent": item.markup_percent,
            "markup_abs": item.markup_abs,
            "final_price": item.final_price,
            "total_price": item.final_price * item.quantity,
        }
        
        # Добавляем в таблицу configurator
        self.add_position_to_table(item_data)
        
        # Загружаем в форму последнюю добавленную строку
        last_row = self.table_offer.rowCount() - 1
        self._load_position_to_form(last_row)
    
    def get_price_list_id(self) -> Optional[int]:
        """Возвращает ID выбранного прайс-листа из выпадающего списка."""
        data = self.combo_price.currentData()
        # Выводим отладку (можно удалить после проверки)
        if data is not None:
            print(f"DEBUG: Selected price_list_id = {data}")
        return data if data is not None else None
    
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
                    if fire_prot:
                        display += " ПП"
                    item = QListWidgetItem(display)
                    item.setData(Qt.ItemDataRole.UserRole, {"type": "Цилиндр", "id": hw_id, "name": name, "code": code, "fire_protected": fire_prot})
                    self.list_hardware.addItem(item)
                    self.list_hardware.setCurrentRow(self.list_hardware.count() - 1)
            elif sender == self.btn_add_closer1:
                closer_id = self.combo_closer1.currentData()
                if closer_id:
                    try:
                        closer = self.closer_ctrl.get_closer_by_id(closer_id)
                        if closer:
                            display = f"Доводчик 1: {closer.name} ({closer.door_weight:.0f} кг)"
                            item = QListWidgetItem(display)
                            item.setData(Qt.ItemDataRole.UserRole, {"type": "Доводчик 1", "id": closer.id, "name": closer.name, "weight": closer.door_weight, "price": closer.price})
                            self.list_hardware.addItem(item)
                            self.list_hardware.setCurrentRow(self.list_hardware.count() - 1)
                    except:
                        pass
            elif sender == self.btn_add_closer2:
                closer_id = self.combo_closer2.currentData()
                if closer_id:
                    try:
                        closer = self.closer_ctrl.get_closer_by_id(closer_id)
                        if closer:
                            display = f"Доводчик 2: {closer.name} ({closer.door_weight:.0f} кг)"
                            item = QListWidgetItem(display)
                            item.setData(Qt.ItemDataRole.UserRole, {"type": "Доводчик 2", "id": closer.id, "name": closer.name, "weight": closer.door_weight, "price": closer.price})
                            self.list_hardware.addItem(item)
                            self.list_hardware.setCurrentRow(self.list_hardware.count() - 1)
                    except:
                        pass
            elif sender == self.btn_add_coordinator:
                coord_id = self.combo_coordinator_new.currentData()
                if coord_id:
                    try:
                        coord = self.closer_ctrl.get_coordinator_by_id(coord_id)
                        if coord:
                            display = f"Координатор: {coord.name}"
                            item = QListWidgetItem(display)
                            item.setData(Qt.ItemDataRole.UserRole, {"type": "Координатор", "id": coord.id, "name": coord.name, "price": coord.price})
                            self.list_hardware.addItem(item)
                            self.list_hardware.setCurrentRow(self.list_hardware.count() - 1)
                    except:
                        pass
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
