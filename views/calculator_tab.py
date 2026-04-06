"""Вкладка 'Калькулятор'. Конфигуратор + выбор контрагента."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox,
    QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from views.product_configurator_widget import ProductConfiguratorWidget
from controllers.calculator_controller import CalculatorController
from controllers.counterparty_controller import CounterpartyController
from controllers.preset_controller import PresetController
from controllers.offer_controller import OfferController
from controllers.price_list_controller import PriceListController


class CalculatorTab(QWidget):
    def __init__(self, calc_ctrl: CalculatorController, cpa_ctrl: CounterpartyController,
                 preset_ctrl: PresetController, offer_ctrl: OfferController,
                 price_list_ctrl: PriceListController):
        super().__init__()
        self.calc_ctrl = calc_ctrl
        self.cpa_ctrl = cpa_ctrl
        self.preset_ctrl = preset_ctrl
        self.offer_ctrl = offer_ctrl
        self.price_list_ctrl = price_list_ctrl
        self.current_offer_id = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Конфигуратор с таблицей КП
        self.configurator = ProductConfiguratorWidget(
            self.calc_ctrl, 
            self.cpa_ctrl,
            self.price_list_ctrl
        )
        layout.addWidget(self.configurator)
        
        # Сигналы
        self.configurator.calculate_requested.connect(self._handle_calculate)
        self.configurator.save_preset_requested.connect(self._handle_save_preset)
        self.configurator.add_to_offer_requested.connect(self._handle_add_to_offer)
    
    def _handle_calculate(self, config: dict):
        price_list_id = self.configurator.get_price_list_id()
        
        result = self.calc_ctrl.validate_and_calculate(
            config["product_type"], config["subtype"],
            config["height"], config["width"],
            price_list_id, config,
            config["markup_percent"], config["markup_abs"],
            config["quantity"]
        )
        self.configurator.on_calculation_result(result)
    
    def _handle_save_preset(self, payload: dict):
        pl_id = self.configurator.get_price_list_id()
        if pl_id is None:
            QMessageBox.warning(self, "Ошибка", "Нельзя сохранить пресет без персонального прайс-листа.")
            return
        try:
            self.preset_ctrl.create_preset(
                name=payload["name"],
                price_list_id=pl_id,
                options_data=payload.get("options", {})
            )
            QMessageBox.information(self, "Успех", f"Пресет '{payload['name']}' сохранён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
    
    def _handle_add_to_offer(self, data: dict):
        if "_action" in data and data["action"] == "create_offer":
            if not self.cpa_ctrl.get_all():
                QMessageBox.warning(self, "Ошибка", "Сначала создайте контрагента.")
                return
            cp_id = self.cpa_ctrl.get_all()[0].id
            offer = self.offer_ctrl.create_offer(counterparty_id=cp_id)
            self.current_offer_id = offer.id
            self.configurator.set_offer_id(offer.id)
            QMessageBox.information(self, "КП создано", f"Номер: {offer.number}")
            return
        
        if not self.current_offer_id:
            if not self.cpa_ctrl.get_all():
                QMessageBox.warning(self, "Ошибка", "Сначала создайте контрагента.")
                return
            offer = self.offer_ctrl.create_offer(counterparty_id=self.cpa_ctrl.get_all()[0].id)
            self.current_offer_id = offer.id
            self.configurator.set_offer_id(offer.id)
        
        try:
            self.offer_ctrl.add_item_to_offer(self.current_offer_id, data)
            self.configurator.add_position_to_table(data)
            QMessageBox.information(self, "Добавлено", "Позиция добавлена в КП.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
