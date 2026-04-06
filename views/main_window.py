"""Главное окно приложения. Инициализация UI, контроллеров и стилей."""

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
from views.hardware_tab import HardwareTab
from views.glasses_tab import GlassesTab
from views.glasses_tab import GlassesTab
from views.hardware_tab import HardwareTab


class PlaceholderTab(QWidget):
    def __init__(self, name: str):
        super().__init__()
        layout = QVBoxLayout(self)
        lbl = QLabel(f"Модуль '{name}' в разработке. Архитектура готова к интеграции.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("МеталлоКальк PRO v2.0")
        self.resize(1400, 900)
        self._init_controllers()
        self._init_ui()
        self._load_stylesheet()
        self._init_status_bar()

    def _init_controllers(self):
        """Инициализация слоя бизнес-логики."""
        self.price_ctrl = PriceListController()
        self.calc_ctrl = CalculatorController()
        self.cpa_ctrl = CounterpartyController()
        self.offer_ctrl = OfferController()
        self.preset_ctrl = PresetController()

    def _init_ui(self):
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.tab_calc = CalculatorTab(self.calc_ctrl, self.cpa_ctrl, self.preset_ctrl, self.offer_ctrl, self.price_ctrl)
        self.tab_offers = OffersTab(self.offer_ctrl, self.cpa_ctrl, self.calc_ctrl)
        self.tab_prices = PriceTab(self.price_ctrl)
        self.tab_counterparties = CounterpartiesTab(self.cpa_ctrl)
        self.tab_presets = PresetsTab(self.preset_ctrl, self.price_ctrl)

        tabs.addTab(self.tab_calc, "Калькулятор")
        tabs.addTab(self.tab_offers, "КП")
        tabs.addTab(self.tab_prices, "Прайс")
        tabs.addTab(self.tab_counterparties, "Контрагенты")
        tabs.addTab(self.tab_presets, "Наборы опций")

        self.setCentralWidget(tabs)

    def _load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resources/styles.qss")
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            status = self.statusBar()
            if status:
                status.showMessage("Файл стилей не найден. Используется тема по умолчанию.", 5000)

    def _init_status_bar(self):
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("Система готова к работе")

    def closeEvent(self, event):
        """Корректное завершение работы и закрытие сессий БД."""
        reply = QMessageBox.question(
            self, "Выход", "Закрыть приложение?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for ctrl in [self.calc_ctrl, self.cpa_ctrl, self.offer_ctrl, self.price_ctrl, self.preset_ctrl]:
                if hasattr(ctrl, "__exit__"):
                    ctrl.__exit__(None, None, None)
            event.accept()
        else:
            event.ignore()
