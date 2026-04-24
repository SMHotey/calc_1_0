"""Вкладка 'Коммерческие предложения'. Управление списком, экспорт, просмотр.

Содержит:
- OffersTab: вкладка для управления коммерческими предложениями
- OfferTableWidget: таблица позиций в КП
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QLabel, QComboBox, QLineEdit, QMenu, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from views.offer_table_widget import OfferTableWidget
from controllers.offer_controller import OfferController
from datetime import datetime, timedelta


class OffersTab(QWidget):
    """Вкладка 'Коммерческие предложения' - управление списком КП, экспорт, просмотр.

    UI: слева фильтры + список КП, справа - детали выбранного КП с позициями.
    Позволяет создавать новые КП, добавлять позиции, экспортировать в PDF/HTML.
    
    Сигналы:
        edit_offer_requested: Запрос на редактирование КП в калькуляторе (offer_id)
        create_deal_requested: Запрос на создание сделки из КП (offer_id)
    """
    edit_offer_requested = pyqtSignal(int)
    create_deal_requested = pyqtSignal(int)

    def __init__(self, offer_ctrl: OfferController, cpa_ctrl, calculator_ctrl, deal_ctrl=None):
        """Инициализация вкладки КП.

        Args:
            offer_ctrl: контроллер коммерческих предложений
            cpa_ctrl: контроллер контрагентов
            calculator_ctrl: контроллер калькулятора
            deal_ctrl: контроллер сделок (опционально)
        """
        super().__init__()
        self.offer_ctrl = offer_ctrl
        self.cpa_ctrl = cpa_ctrl
        self.calc_ctrl = calculator_ctrl
        self.deal_ctrl = deal_ctrl
        self._init_ui()
        self._load_offers()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # === ФИЛЬТРЫ ===
        filter_layout = QHBoxLayout()
        
        # Фильтр по контрагенту
        filter_layout.addWidget(QLabel("Контрагент:"))
        self.combo_filter_cp = QComboBox()
        self.combo_filter_cp.setMinimumWidth(150)
        self.combo_filter_cp.addItem("Все", None)
        try:
            for cp in self.cpa_ctrl.get_all():
                self.combo_filter_cp.addItem(cp.name, cp.id)
        except:
            pass
        self.combo_filter_cp.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.combo_filter_cp)
        
        # Фильтр по дате
        filter_layout.addWidget(QLabel("Дата:"))
        self.combo_filter_date = QComboBox()
        self.combo_filter_date.setMinimumWidth(120)
        self.combo_filter_date.addItems(["Все", "Сегодня", "Эта неделя", "Этот месяц", "Этот год"])
        self.combo_filter_date.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.combo_filter_date)
        
        # Фильтр по названию
        filter_layout.addWidget(QLabel("Название:"))
        self.edit_filter_name = QLineEdit()
        self.edit_filter_name.setPlaceholderText("Поиск по номеру...")
        self.edit_filter_name.setMinimumWidth(120)
        self.edit_filter_name.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.edit_filter_name)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Сплиттер: слева список КП, справа - детали
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая панель - список КП
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Список предложений"))
        self.list_offers = QListWidget()
        self.list_offers.currentRowChanged.connect(self._show_offer)
        
        # Контекстное меню для списка КП
        self.list_offers.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_offers.customContextMenuRequested.connect(self._show_list_context_menu)
        
        left_layout.addWidget(self.list_offers)

        btn_new_offer = QPushButton("📄 Новое предложение")
        btn_new_offer.clicked.connect(self._create_new_offer)
        left_layout.addWidget(btn_new_offer)

        # Правая панель - позиции
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Позиции"))

        self.table = OfferTableWidget()
        self.table.add_position_requested.connect(self._on_add_position)
        right_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_export_pdf = QPushButton("📥 Экспорт PDF")
        self.btn_export_html = QPushButton("🌐 Экспорт HTML")
        self.btn_details = QPushButton("📋 Подробно")
        self.btn_create_deal = QPushButton("📝 Создать сделку")
        self.btn_create_deal.setEnabled(False)
        self.btn_create_deal.clicked.connect(self._create_deal_from_offer_btn)
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        self.btn_export_html.clicked.connect(self._export_html)
        self.btn_details.clicked.connect(self._show_item_details)
        btn_layout.addWidget(self.btn_export_pdf)
        btn_layout.addWidget(self.btn_export_html)
        btn_layout.addWidget(self.btn_details)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_create_deal)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def _apply_filters(self):
        """Применить фильтры к списку КП."""
        self.list_offers.clear()
        
        # Параметры фильтров
        cp_id = self.combo_filter_cp.currentData()
        date_filter = self.combo_filter_date.currentText()
        name_filter = self.edit_filter_name.text().strip().lower()
        
        # Получаем все КП
        offers = self.offer_ctrl.get_all_offers()
        
        for o in offers:
            # Фильтр по контрагенту - сравниваем по имени контрагента
            if cp_id:
                cp_name_from_filter = self.combo_filter_cp.currentText()
                o_counterparty = o.get("counterparty", "")
                # Пропускаем если имя контрагента не совпадает
                if cp_name_from_filter and cp_name_from_filter != "Все" and o_counterparty != cp_name_from_filter:
                    continue
            
            # Фильтр по дате
            if date_filter != "Все":
                try:
                    offer_date = datetime.strptime(o["date"], "%d.%m.%Y")
                    now = datetime.now()
                    
                    if date_filter == "Сегодня":
                        if offer_date.date() != now.date():
                            continue
                    elif date_filter == "Эта неделя":
                        week_start = now - timedelta(days=now.weekday())
                        if offer_date.date() < week_start.date():
                            continue
                    elif date_filter == "Этот месяц":
                        if offer_date.year != now.year or offer_date.month != now.month:
                            continue
                    elif date_filter == "Этот год":
                        if offer_date.year != now.year:
                            continue
                except:
                    pass
            
            # Фильтр по названию
            if name_filter and name_filter not in o["number"].lower():
                continue
            
            # Добавляем в список
            item = QListWidgetItem(f"№ {o['number']} | {o['counterparty']} | {o['date']} | {o['total']:,.0f} ₽")
            item.setData(Qt.ItemDataRole.UserRole, o["id"])
            self.list_offers.addItem(item)

    def _load_offers(self):
        """Загрузить все КП (без фильтров)."""
        self._apply_filters()

    def _show_offer(self, row: int):
        if row < 0: return
        offer_id = self.list_offers.item(row).data(Qt.ItemDataRole.UserRole)
        data = self.offer_ctrl.get_offer_with_items(offer_id)
        if not data: return

        self.current_offer_id = offer_id
        self.table.setRowCount(0)
        for item in data["items"]:
            self.table.append_position(item)
        
        # Скрыть столбец Марка, если во всех строках пусто
        self.table.update_mark_column_visibility()
        
        # Обновить состояние кнопки "Создать сделку"
        self._update_create_deal_button()

    def _update_create_deal_button(self):
        """Обновляет состояние кнопки создания сделки."""
        if not hasattr(self, "current_offer_id") or not self.deal_ctrl:
            self.btn_create_deal.setEnabled(False)
            self.btn_create_deal.setToolTip("Выберите КП")
            return

        # Проверяем, есть ли уже активная сделка для этого КП
        from sqlalchemy import select
        from models.deal import Deal
        from constants import DealStatus

        stmt = select(Deal).where(
            Deal.commercial_offer_id == self.current_offer_id,
            Deal.status != DealStatus.CANCELLED
        )
        existing_deals = list(self.deal_ctrl.session.execute(stmt).scalars().all())

        if existing_deals:
            self.btn_create_deal.setEnabled(False)
            self.btn_create_deal.setToolTip("Для этого КП уже есть сделка")
        else:
            self.btn_create_deal.setEnabled(True)
            self.btn_create_deal.setToolTip("Создать сделку на основании выбранного КП")

    def _create_deal_from_offer_btn(self):
        """Создать сделку по кнопке."""
        if not hasattr(self, "current_offer_id"):
            return

        if not self.deal_ctrl:
            QMessageBox.warning(self, "Ошибка", "Контроллер сделок не инициализирован.")
            return

        try:
            deal = self.deal_ctrl.create_from_offer(self.current_offer_id)
            self.deal_ctrl.session.commit()
            QMessageBox.information(
                self, "Успех",
                f"Создана сделка '{deal.number}'"
            )
            self._update_create_deal_button()
            self.create_deal_requested.emit(self.current_offer_id)
        except ValueError as e:
            QMessageBox.warning(self, "Внимание", str(e))
        except Exception as e:
            self.deal_ctrl.session.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _create_new_offer(self):
        if not self.cpa_ctrl.get_all():
            QMessageBox.warning(self, "Ошибка", "Сначала создайте контрагента.")
            return
        offer = self.offer_ctrl.create_offer(counterparty_id=self.cpa_ctrl.get_all()[0].id)
        self._load_offers()
        idx = self.list_offers.count() - 1
        self.list_offers.setCurrentRow(idx)

    def _on_add_position(self):
        QMessageBox.information(self, "Информация",
                                "Добавление позиции происходит через вкладку 'Калькулятор'. Для редактирования дважды кликните по строке.")

    def _export_pdf(self):
        if not hasattr(self, "current_offer_id"):
            return QMessageBox.warning(self, "Внимание", "Выберите предложение для экспорта.")
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить PDF",
                                              f"КП_{self.list_offers.currentItem().text()[:10]}.pdf",
                                              "PDF Files (*.pdf)")
        if path:
            self.offer_ctrl.export_to_pdf(self.current_offer_id, path)
            QMessageBox.information(self, "Успех", f"Файл сохранён:\n{path}")

    def _export_html(self):
        if not hasattr(self, "current_offer_id"):
            return QMessageBox.warning(self, "Внимание", "Выберите предложение для экспорта.")
        html_content = self.offer_ctrl.export_to_html(self.current_offer_id)
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить HTML", "offer.html", "HTML Files (*.html)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_content)
            QMessageBox.information(self, "Успех", "HTML-файл успешно сгенерирован.")

    def _show_list_context_menu(self, pos: QPoint):
        """Показать контекстное меню для списка КП."""
        item = self.list_offers.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Действия меню
        action_edit = menu.addAction("✏️ Редактировать")
        action_edit.triggered.connect(lambda: self._edit_offer(item))
        
        action_rename = menu.addAction("📝 Переименовать")
        action_rename.triggered.connect(lambda: self._rename_offer(item))
        
        menu.addSeparator()
        
        action_prod_order = menu.addAction("📋 Заявка на производство")
        action_prod_order.triggered.connect(lambda: self._show_placeholder(item, "Заявка на производство"))
        
        action_invoice = menu.addAction("💳 Формы счета")
        action_invoice.triggered.connect(lambda: self._show_placeholder(item, "Формы счета"))
        
        action_price_agree = menu.addAction("✅ Согласование цены")
        action_price_agree.triggered.connect(lambda: self._show_placeholder(item, "Согласование цены"))
        
        menu.addSeparator()
        
        action_create_deal = menu.addAction("📝 Создать сделку")
        action_create_deal.triggered.connect(lambda: self._create_deal_from_offer(item))
        
        menu.addSeparator()
        
        action_delete = menu.addAction("🗑️ Удалить")
        action_delete.triggered.connect(lambda: self._delete_offer(item))
        
        menu.exec(self.list_offers.viewport().mapToGlobal(pos))

    def _edit_offer(self, item: QListWidgetItem):
        """Редактировать выбранное КП в калькуляторе."""
        offer_id = item.data(Qt.ItemDataRole.UserRole)
        self.edit_offer_requested.emit(offer_id)

    def _rename_offer(self, item: QListWidgetItem):
        """Переименовать выбранное КП."""
        offer_id = item.data(Qt.ItemDataRole.UserRole)
        current_name = item.text().split(" | ")[0].replace("№ ", "")
        
        new_name, ok = QInputDialog.getText(
            self, "Переименовать КП",
            "Введите новый номер КП:",
            QLineEdit.EchoMode.Normal,
            current_name
        )
        
        if ok and new_name.strip():
            try:
                self.offer_ctrl.update_offer_name(offer_id, new_name.strip())
                self.offer_ctrl.session.commit()
                self._load_offers()
                QMessageBox.information(self, "Успех", f"КП переименовано в '{new_name}'.")
            except Exception as e:
                self.offer_ctrl.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def _delete_offer(self, item: QListWidgetItem):
        """Удалить выбранное КП с подтверждением."""
        offer_id = item.data(Qt.ItemDataRole.UserRole)
        offer_name = item.text().split(" | ")[0].replace("№ ", "")
        
        reply = QMessageBox.question(
            self, "Удалить КП",
            f"Удалить КП '{offer_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Удаляем через контроллер
                self.offer_ctrl.offer_repo.delete(offer_id)
                self.offer_ctrl.session.commit()
                self._load_offers()
                QMessageBox.information(self, "Успех", "КП удалено.")
            except Exception as e:
                self.offer_ctrl.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def _show_placeholder(self, item: QListWidgetItem, feature_name: str):
        """Показать заглушку для нереализованной функции."""
        offer_name = item.text().split(" | ")[0].replace("№ ", "")
        QMessageBox.information(
            self, feature_name,
            f"Функция '{feature_name}' для КП '{offer_name}' находится в разработке."
        )

    def _create_deal_from_offer(self, item: QListWidgetItem):
        """Создать сделку на основании выбранного КП."""
        if not self.deal_ctrl:
            QMessageBox.warning(self, "Ошибка", "Контроллер сделок не инициализирован.")
            return

        offer_id = item.data(Qt.ItemDataRole.UserRole)
        offer_name = item.text().split(" | ")[0].replace("№ ", "")

        reply = QMessageBox.question(
            self, "Создание сделки",
            f"Создать сделку на основании КП '{offer_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                deal = self.deal_ctrl.create_from_offer(offer_id)
                self.deal_ctrl.session.commit()
                QMessageBox.information(
                    self, "Успех",
                    f"Создана сделка '{deal.number}'\nПерейти на вкладку 'Сделки'?"
                )
                self.create_deal_requested.emit(offer_id)
            except ValueError as e:
                QMessageBox.warning(self, "Внимание", str(e))
            except Exception as e:
                self.deal_ctrl.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def _show_item_details(self):
        """Показать детальный расчёт выбранной позиции."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите позицию в таблице")
            return
        
        # Получаем данные позиции из строки таблицы
        item_data = {}
        columns = ["Марка", "Изделие", "Размеры", "Кол-во", "Комплектация"]
        for c, col_name in enumerate(columns):
            item = self.table.item(row, c)
            item_data[col_name] = item.text() if item else ""
        
        # Получаем данные для расчёта
        product_text = item_data.get("Изделие", "")
        if not product_text:
            return
        
        # Парсим данные: "Дверь Техническая"
        parts = product_text.split()
        if len(parts) >= 2:
            product_type = parts[0]
            subtype = parts[1]
        else:
            product_type = product_text
            subtype = ""
        
        # Парсим размеры: "2100*1000"
        dims = item_data.get("Размеры", "").split("*")
        if len(dims) == 2:
            try:
                height = int(dims[0])
                width = int(dims[1])
            except:
                height, width = 2100, 1000
        else:
            height, width = 2100, 1000
        
        quantity = int(item_data.get("Кол-во", 1) or 1)
        
        # Выполняем расчёт
        try:
            result = self.calc_ctrl.validate_and_calculate(
                product_type=product_type,
                subtype=subtype,
                height=height,
                width=width,
                price_list_id=1,  # Базовый прайс
                options={},
                markup_percent=0,
                quantity=quantity
            )
            
            if not result.get("success"):
                QMessageBox.warning(self, "Ошибка", result.get("error", "Неизвестная ошибка"))
                return
            
            # Формируем детальный отчёт
            base_price = result.get("price_per_unit", 0)
            
            details_text = f"""Детализация позиции:
━━━━━━━━━━━━━━━━━━━━━━━
Изделие: {product_type} {subtype}
Размеры: {height} x {width} мм
Количество: {quantity}
━━━━━━━━━━━━━━━━━━━━━━━
Базовая стоимость: {base_price:,.2f} руб.
Итого за {quantity} шт.: {base_price * quantity:,.2f} руб."""
            
            # Показываем в диалоге
            from PyQt6.QtWidgets import QDialog, QTextEdit
            dlg = QDialog(self)
            dlg.setWindowTitle("Детализация позиции")
            dlg.resize(500, 400)
            layout = QVBoxLayout(dlg)
            
            text = QTextEdit()
            text.setReadOnly(True)
            text.setText(details_text)
            layout.addWidget(text)
            
            btn = QPushButton("Закр��ть")
            btn.clicked.connect(dlg.accept)
            layout.addWidget(btn)
            
            dlg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось рассчитать: {e}")