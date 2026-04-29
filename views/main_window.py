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
from controllers.price_list_controller import PriceListController
from controllers.deal_controller import DealController
from controllers.document_controller import DocumentController
from controllers.contact_person_controller import ContactPersonController
from controllers.bank_details_controller import BankDetailsController
from views.calculator_tab import CalculatorTab
from views.offers_tab import OffersTab
from views.price_tab import PriceTab
from views.counterparties_tab import CounterpartiesTab
from views.deals_tab import DealsTab


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
    
    UI Layout:
        ┌─────────────────────────────────────────────┐
        │  [Калькулятор] [КП] [Прайс] [Контрагенты]  │
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
        self.deal_ctrl = DealController()
        self.doc_ctrl = DocumentController()
        self.contacts_ctrl = ContactPersonController()
        self.bank_details_ctrl = BankDetailsController()

    def _init_ui(self):
        """Создание пользовательского интерфейса.

        Создаёт QTabWidget с вкладками и размещает его в центре окна.
        Каждая вкладка инициализируется со своим контроллером.
        """
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Инициализация вкладок с передачей контроллеров
        self.tab_calc = CalculatorTab(self.calc_ctrl, self.cpa_ctrl, self.offer_ctrl, self.price_ctrl)
        self.tab_offers = OffersTab(self.offer_ctrl, self.cpa_ctrl, self.calc_ctrl, self.deal_ctrl)
        
        # Связь сигнала редактирования КП из вкладки КП
        self.tab_offers.edit_offer_requested.connect(self._on_edit_offer_requested)
        
        # Сигнал загрузки позиции из КП в калькулятор
        self.tab_offers.load_position_requested.connect(self._on_load_position_requested)
        
        # Связь сигнала создания сделки из КП
        self.tab_offers.create_deal_requested.connect(self._on_create_deal_requested)
        
        self.tab_prices = PriceTab(self.price_ctrl, self.cpa_ctrl)
        # Связь: обновление списка прайс-листов на вкладке Калькулятор при изменении в Прайсе
        self.tab_prices.price_lists_changed.connect(self.tab_calc.refresh_price_lists)
        self.tab_counterparties = CounterpartiesTab(self.cpa_ctrl, self.doc_ctrl, self.contacts_ctrl, self.bank_details_ctrl)
        self.tab_deals = DealsTab(self.deal_ctrl, self.cpa_ctrl, self.doc_ctrl)

        # Добавление вкладок
        tabs.addTab(self.tab_calc, "Калькулятор")
        tabs.addTab(self.tab_offers, "КП")
        tabs.addTab(self.tab_prices, "Прайс")
        tabs.addTab(self.tab_counterparties, "Контрагенты")
        tabs.addTab(self.tab_deals, "Сделки")

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
            if hasattr(self, 'tab_calc') and hasattr(self.tab_calc, 'configurator'):
                configurator = self.tab_calc.configurator
                if hasattr(configurator, 'table_offer'):
                    unsaved_positions = configurator.table_offer.rowCount()
        except Exception:
            pass  # Если не удалось получить - просто не показываем доп. информацию
        
        # Формируем сообщение
        if unsaved_positions > 0:
            msg = f"В текущем КП есть {unsaved_positions} позиций.\nОни будут потеряны при выходе."
            reply = QMessageBox.question(
                self, "Выход", msg,
                QMessageBox.StandardButton.SaveAll | QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Close
            )
            if reply == QMessageBox.StandardButton.SaveAll:
                # Сохраняем текущее КП перед выходом
                if hasattr(self, 'tab_calc') and hasattr(self.tab_calc, 'configurator'):
                    configurator = self.tab_calc.configurator
                    if configurator.current_offer_id and configurator.table_offer.rowCount() > 0:
                        # Вызываем сохранение
                        configurator._save_offer()
                self._close_controllers()
                event.accept()
            elif reply == QMessageBox.StandardButton.Close:
                # Закрываем без сохранения
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
        for ctrl in [self.calc_ctrl, self.cpa_ctrl, self.offer_ctrl, self.price_ctrl, self.deal_ctrl, self.doc_ctrl]:
            if hasattr(ctrl, "__exit__"):
                ctrl.__exit__(None, None, None)

    def _on_edit_offer_requested(self, offer_id: int):
        """Обработчик редактирования КП - переключает на вкладку калькулятора и загружает КП."""
        # Переключаем на вкладку калькулятора
        tabs = self.centralWidget()
        tabs.setCurrentWidget(self.tab_calc)
        # Загружаем КП в калькулятор
        self.tab_calc.load_offer(offer_id)

    def _on_load_position_requested(self, item_id: int):
        """Загружает одну позицию из вкладки КП в калькулятор для редактирования."""
        # Переключаем на вкладку калькулятора
        tabs = self.centralWidget()
        tabs.setCurrentWidget(self.tab_calc)
        # Загружаем позицию в конфигуратор
        self.tab_calc.configurator.load_item(item_id)

    def _on_create_deal_requested(self, offer_id: int):
        """Обработчик создания сделки из КП - переключает на вкладку сделок."""
        tabs = self.centralWidget()
        tabs.setCurrentWidget(self.tab_deals)
