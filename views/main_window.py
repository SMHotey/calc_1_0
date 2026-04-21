"""Главное окно приложения. Инициализация UI, контроллеров и стилей.

Содержит:
- MainWindow: главное окно приложения с вкладками
- PlaceholderTab: заглушка для ещё нереализованных модулей
- Инициализация всех контроллеров
- Загрузка QSS стилей (если есть)
- Управление жизненным циклом приложения
"""

import os
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QMessageBox, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSettings
from controllers.calculator_controller import CalculatorController
from controllers.counterparty_controller import CounterpartyController
from controllers.offer_controller import OfferController
from controllers.preset_controller import PresetController
from controllers.price_list_controller import PriceListController
from views.calculator_tab import CalculatorTab
from views.offers_tab import OffersTab
from views.price_tab import PriceTab
from views.counterparties_tab import CounterpartiesTab
from views.presets_tab import PresetsTab


class PlaceholderTab(QWidget):
    """Заглушка для модулей, которые ещё не реализованы.
    
    Отображает сообщение о том, что модуль в разработке.
    Используется для модулей GlassesTab и HardwareTab.
    """
    def __init__(self, name: str):
        """Создаёт виджет-заглушку.

        Args:
            name: название модуля для отображения в сообщении
        """
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel(f"Модуль '{name}' в разработке. Архитектура готова к интеграции.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Главное окно приложения МеталлоКальк PRO.

    Содержит:
    - Пять вкладок: Калькулятор, КП, Прайс, Контрагенты, Наборы опций
    - Инициализацию всех контроллеров при запуске
    - Загрузку стилей из resources/styles.qss
    - Статус bar с сообщениями
    - Обработку закрытия приложения с подтверждением

    Attributes:
        price_ctrl: контроллер прайс-листов
        calc_ctrl: контроллер калькулятора
        cpa_ctrl: контроллер контрагентов
        offer_ctrl: контроллер коммерческих предложений
        preset_ctrl: контроллер наборов опций

    UI Layout:
        ┌─────────────────────────────────────────────┐
        │  [Калькулятор] [КП] [Прайс] [Контрагенты] [Наборы опций]  │
        ├─────────────────────────────────────────────┤
        │                                             │
        │            Содержимое вкладки               │
        │                                             │
        ├─────────────────────────────────────────────┤
        │  Статус: Система готова к работе            │
        └─────────────────────────────────────────────┘
    """

    def __init__(self):
        """Инициализация главного окна.

        Создаёт окно, устанавливает заголовок, инициализирует контроллеры,
        создаёт UI с вкладками, загружает стили.
        """
        super().__init__()
        self.setWindowTitle("МеталлоКальк PRO v2.0")
        self.resize(1400, 900)
        self._init_controllers()
        self._init_ui()
        self._load_stylesheet()
        self._init_status_bar()

    def _init_controllers(self):
        """Инициализация слоя бизнес-логики.

        Создаёт экземпляры всех контроллеров для работы с данными.
        """
        self.price_ctrl = PriceListController()
        self.calc_ctrl = CalculatorController()
        self.cpa_ctrl = CounterpartyController()
        self.offer_ctrl = OfferController()
        self.preset_ctrl = PresetController()

    def _init_ui(self):
        """Создание пользовательского интерфейса.

        Создаёт QTabWidget с пятью вкладками и размещает его в центре окна.
        Каждая вкладка инициализируется со своим контроллером.
        """
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Инициализация вкладок с передачей контроллеров
        self.tab_calc = CalculatorTab(self.calc_ctrl, self.cpa_ctrl, self.preset_ctrl, self.offer_ctrl, self.price_ctrl)
        self.tab_offers = OffersTab(self.offer_ctrl, self.cpa_ctrl, self.calc_ctrl)
        self.tab_prices = PriceTab(self.price_ctrl, self.cpa_ctrl)
        self.tab_counterparties = CounterpartiesTab(self.cpa_ctrl)
        self.tab_presets = PresetsTab(self.preset_ctrl, self.price_ctrl)

        # Добавление вкладок
        tabs.addTab(self.tab_calc, "Калькулятор")
        tabs.addTab(self.tab_offers, "КП")
        tabs.addTab(self.tab_prices, "Прайс")
        tabs.addTab(self.tab_counterparties, "Контрагенты")
        tabs.addTab(self.tab_presets, "Наборы опций")

        self.setCentralWidget(tabs)

    def _load_stylesheet(self):
        """Загрузка файла стилей (QSS).

        Пытается загрузить styles.qss из resources/. Если файл не найден,
        используется тема по умолчанию и выводится сообщение в статус bar.
        """
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources/styles.qss")
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            status = self.statusBar()
            if status:
                status.showMessage("Файл стилей не найден. Используется тема по умолчанию.", 5000)

    def _init_status_bar(self):
        """Инициализация статус bar.

        Создаёт статус bar в нижней части окна с приветственным сообщением.
        """
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("Система готова к работе")

    def closeEvent(self, event):
        """Корректное завершение работы приложения.

        Показывает диалог подтверждения выхода. Если пользователь подтверждает -
        закрывает все сессии БД контроллеров.

        Args:
            event: событие закрытия окна
        """
        # Проверяем, есть ли несохранённые позиции в КП
        unsaved_positions = 0
        try:
            # Получаем количество позиций в текущем КП калькулятора
            if hasattr(self, 'tab_calc') and hasattr(self.tab_calc, '_configurator'):
                configurator = self.tab_calc._configurator
                if hasattr(configurator, 'table_offer'):
                    unsaved_positions = configurator.table_offer.rowCount()
        except Exception:
            pass  # Если не удалось получить - просто не показываем доп. информацию
        
        # Формируем сообщение
        if unsaved_positions > 0:
            msg = f"В текущем КП есть {unsaved_positions} позиций.\nОни будут потеряны при выходе.\n\nСохранить КП перед выходом?"
            reply = QMessageBox.question(
                self, "Выход", msg,
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                # Переключаем на вкладку калькулятора, пользователь сохранит вручную
                if hasattr(self, 'tab_calc'):
                    self.centralWidget().setCurrentWidget(self.tab_calc)
                event.ignore()
            elif reply == QMessageBox.StandardButton.Discard:
                # Выходим без сохранения
                self._close_controllers()
                event.accept()
            else:
                # Отмена
                event.ignore()
        else:
            # Нет позиций - просто подтверждаем выход
            reply = QMessageBox.question(
                self, "Выход", "Закрыть приложение?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._close_controllers()
                event.accept()
            else:
                event.ignore()
    
    def _close_controllers(self):
        """Закрывает все контроллеры (освобождение сессий БД)."""
        for ctrl in [self.calc_ctrl, self.cpa_ctrl, self.offer_ctrl, self.price_ctrl, self.preset_ctrl]:
            if hasattr(ctrl, "__exit__"):
                ctrl.__exit__(None, None, None)
