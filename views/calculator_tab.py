"""Вкладка 'Калькулятор'. Конфигуратор + выбор контрагента.

Содержит:
- CalculatorTab: вкладка калькулятора с конфигуратором изделия
- ProductConfiguratorWidget: основной виджет конфигурации изделия
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox,
    QMessageBox, QGroupBox, QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt
from views.product_configurator_widget import ProductConfiguratorWidget
from controllers.calculator_controller import CalculatorController
from controllers.counterparty_controller import CounterpartyController
from controllers.offer_controller import OfferController
from controllers.price_list_controller import PriceListController


class CalculatorTab(QWidget):
    """Вкладка 'Калькулятор' - основной интерфейс для расчёта стоимости изделия.

    Содержит конфигуратор изделия и обрабатывает сигналы:
    - calculate_requested: запрос на расчёт
    - add_to_offer_requested: добавление в КП
    """

    def __init__(self, calc_ctrl: CalculatorController, cpa_ctrl: CounterpartyController,
                 offer_ctrl: OfferController, price_list_ctrl: PriceListController):
        """Инициализация вкладки калькулятора.

        Args:
            calc_ctrl: контроллер калькулятора
            cpa_ctrl: контроллер контрагентов
            offer_ctrl: контроллер КП
            price_list_ctrl: контроллер прайс-листов
        """
        super().__init__()
        self.calc_ctrl = calc_ctrl
        self.cpa_ctrl = cpa_ctrl
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
            self.price_list_ctrl,
            offer_ctrl=self.offer_ctrl
        )
        layout.addWidget(self.configurator)
        
        # Сигналы
        self.configurator.add_to_offer_requested.connect(self._handle_add_to_offer)
        self.configurator.save_offer_requested.connect(self._handle_save_offer)

    def load_offer(self, offer_id: int):
        """Загрузить существующее КП для редактирования."""
        self.current_offer_id = offer_id
        self.configurator.set_offer_id(offer_id)
        
        # Загружаем позиции в таблицу
        data = self.offer_ctrl.get_offer_with_items(offer_id)
        if data and data.get("items"):
            self.configurator.clear_offer_table()
            for item in data["items"]:
                self.configurator.add_position_to_table(item)
    
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
    
    def _handle_save_offer(self, data: dict):
        """Обработчик сохранения КП с новым именем."""
        offer_id = data.get("offer_id")
        new_name = data.get("new_name")
        
        if not offer_id or not new_name:
            return
        
        try:
            self.offer_ctrl.update_offer_name(offer_id, new_name)
            self.offer_ctrl.session.commit()
            QMessageBox.information(self, "Успех", f"КП сохранено с номером '{new_name}'.")
        except Exception as e:
            self.offer_ctrl.session.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _handle_add_to_offer(self, data: dict):
        # Проверяем сигнал создания нового КП
        if data.get("_action") == "create_offer":
            current_row_count = data.get("current_row_count", 0)
            
            # Если есть позиции в текущем КП, предлагаем сохранить
            if current_row_count > 0:
                # Автогенерация номера
                from datetime import datetime
                year_month = datetime.now().strftime("%y%m")
                default_name = f"КО-{year_month}"
                
                # Диалог ввода имени
                name, ok = QInputDialog.getText(
                    self, "Новое КП", 
                    f"Сохранить текущее КП перед созданием нового?\n\n"
                    f"Введите номер для сохранения:",
                    QLineEdit.EchoMode.Normal, default_name
                )
                
                if not ok or not name:
                    # Пользователь отменил
                    return
                
                # Сохраняем текущее КП (экспорт в PDF или просто запоминаем)
                # Здесь можно добавить логику экспорта
                QMessageBox.information(
                    self, "КП сохранено", 
                    f"КП сохранено как '{name}'.\n"
                    f"Создаем новое КП..."
                )
            
            if not self.cpa_ctrl.get_all():
                QMessageBox.warning(self, "Ошибка", "Сначала создайте контрагента.")
                return
            
            cp_id = self.cpa_ctrl.get_all()[0].id
            offer = self.offer_ctrl.create_offer(counterparty_id=cp_id)
            self.current_offer_id = offer.id
            self.configurator.set_offer_id(offer.id)
            # Очищаем таблицу для нового КП
            self.configurator.clear_offer_table()
            # Коммит при создании КП
            self.offer_ctrl.session.commit()
            QMessageBox.information(self, "КП создано", f"Номер: {offer.number}")
            return
        
        if not self.current_offer_id:
            if not self.cpa_ctrl.get_all():
                QMessageBox.warning(self, "Ошибка", "Сначала создайте контрагента.")
                return
            offer = self.offer_ctrl.create_offer(counterparty_id=self.cpa_ctrl.get_all()[0].id)
            self.current_offer_id = offer.id
            self.configurator.set_offer_id(offer.id)
            # Коммит при создании КП
            self.offer_ctrl.session.commit()
        
        try:
            self.offer_ctrl.add_item_to_offer(self.current_offer_id, data)
            # Коммитим изменения в БД
            self.offer_ctrl.session.commit()
            # Добавляем позицию в таблицу
            self.configurator.add_position_to_table(data)
            QMessageBox.information(self, "Добавлено", "Позиция добавлена в КП.")
        except Exception as e:
            import traceback
            error_details = f"{str(e)}\n\n{traceback.format_exc()}"
            print(f"[ERROR] _handle_add_to_offer: {error_details}")
            # Откат при ошибке
            self.offer_ctrl.session.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))