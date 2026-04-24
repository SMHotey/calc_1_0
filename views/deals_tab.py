"""Вкладка 'Сделки'. Управление списком сделок с фильтрами.

Содержит:
- DealsTab: вкладка для управления сделками
- Детальный просмотр сделки с документами
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QLabel, QComboBox,
    QDateEdit, QLineEdit, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from controllers.deal_controller import DealController
    from controllers.document_controller import DocumentController
    from controllers.counterparty_controller import CounterpartyController

from constants import DealStatus
from views.dialogs.deal_dialog import DealDialog


class DealDetailWidget(QWidget):
    """Виджет детального просмотра сделки.

    Показывает информацию о сделке и вкладку с документами.
    """

    def __init__(
            self,
            deal_ctrl: "DealController",
            doc_ctrl: "DocumentController",
            deal_id: int,
            parent=None
    ):
        super().__init__(parent)
        self.deal_ctrl = deal_ctrl
        self.doc_ctrl = doc_ctrl
        self.deal_id = deal_id
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Информация о сделке
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.Box)
        info_layout = QVBoxLayout(info_frame)

        self.lbl_number = QLabel()
        self.lbl_number.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self.lbl_number)

        self.lbl_status = QLabel()
        info_layout.addWidget(self.lbl_status)

        self.lbl_info = QLabel()
        info_layout.addWidget(self.lbl_info)

        # Кнопки действий
        btn_layout = QHBoxLayout()
        btn_edit = QPushButton("✏️ Редактировать")
        btn_edit.clicked.connect(self._edit_deal)
        btn_layout.addWidget(btn_edit)
        info_layout.addLayout(btn_layout)

        layout.addWidget(info_frame)

        # Документы сделки
        docs_label = QLabel("📄 Документы сделки")
        docs_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(docs_label)

        from views.documents_widget import DocumentsWidget
        self.docs_widget = DocumentsWidget(
            self.doc_ctrl,
            deal_id=self.deal_id
        )
        layout.addWidget(self.docs_widget)

    def _load_data(self):
        """Загружает данные сделки."""
        deal = self.deal_ctrl.get_by_id(self.deal_id)
        if not deal:
            return

        self.lbl_number.setText(f"Сделка: {deal.number}")

        # Цвет статуса
        status_color = self._get_status_color(deal.status)
        self.lbl_status.setText(f"<span style='color: {status_color}'>Статус: {deal.status.value}</span>")

        # Информация
        info_parts = []
        info_parts.append(f"Контрагент: {deal.counterparty.name if deal.counterparty else 'N/A'}")

        if deal.invoice_number:
            amount = f"{float(deal.invoice_amount):,.2f} ₽" if deal.invoice_amount else "N/A"
            info_parts.append(f"Счёт: {deal.invoice_number} от {deal.invoice_date.strftime('%d.%m.%Y') if deal.invoice_date else ''} - {amount}")

        if deal.prepayment_amount:
            info_parts.append(f"Предоплата: {float(deal.prepayment_amount):,.2f} ₽ ({deal.prepayment_date.strftime('%d.%m.%Y') if deal.prepayment_date else ''})")

        if deal.full_payment_date:
            info_parts.append(f"Полная оплата: {deal.full_payment_date.strftime('%d.%m.%Y')}")

        self.lbl_info.setText("<br>".join(info_parts))

    def _get_status_color(self, status: DealStatus) -> str:
        """Возвращает цвет для статуса."""
        colors = {
            DealStatus.DRAFT: "#808080",
            DealStatus.OFFER_SENT: "#17a2b8",
            DealStatus.INVOICE_ISSUED: "#ffc107",
            DealStatus.PREPAYMENT: "#007bff",
            DealStatus.FULL_PAYMENT: "#28a745",
            DealStatus.COMPLETED: "#28a745",
            DealStatus.CANCELLED: "#dc3545",
        }
        return colors.get(status, "#808080")

    def _edit_deal(self):
        """Редактирует сделку."""
        dialog = DealDialog(self.deal_ctrl, deal_id=self.deal_id, parent=self)
        if dialog.exec():
            self._load_data()
            self.docs_widget.refresh()


class DealsTab(QWidget):
    """Вкладка 'Сделки' - управление списком сделок с фильтрами.

    Позволяет:
    - Просматривать список всех сделок
    - Фильтровать по контрагенту, статусу, датам
    - Создавать новые сделки
    - Открывать детальный просмотр сделки
    """

    def __init__(
            self,
            deal_ctrl: "DealController",
            cpa_ctrl: "CounterpartyController",
            doc_ctrl: "DocumentController"
    ):
        super().__init__()
        self.deal_ctrl = deal_ctrl
        self.cpa_ctrl = cpa_ctrl
        self.doc_ctrl = doc_ctrl
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # === ФИЛЬТРЫ (компактно в одну строку) ===
        filter_row = QHBoxLayout()

        filter_row.addWidget(QLabel("Контрагент:"))
        self.combo_filter_cp = QComboBox()
        self.combo_filter_cp.setMinimumWidth(120)
        self.combo_filter_cp.addItem("Все", None)
        try:
            for cp in self.cpa_ctrl.get_all():
                self.combo_filter_cp.addItem(cp.name, cp.id)
        except:
            pass
        self.combo_filter_cp.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.combo_filter_cp)

        filter_row.addWidget(QLabel("Статус:"))
        self.combo_filter_status = QComboBox()
        self.combo_filter_status.setMinimumWidth(100)
        self.combo_filter_status.addItem("Все", None)
        for status in DealStatus:
            self.combo_filter_status.addItem(status.value, status)
        self.combo_filter_status.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.combo_filter_status)

        filter_row.addWidget(QLabel("От:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd.MM.yyyy")
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.dateChanged.connect(self._apply_filters)
        filter_row.addWidget(self.date_from)

        filter_row.addWidget(QLabel("До:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd.MM.yyyy")
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self._apply_filters)
        filter_row.addWidget(self.date_to)

        filter_row.addWidget(QLabel("Поиск:"))
        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("Номер...")
        self.edit_search.setMaximumWidth(100)
        self.edit_search.textChanged.connect(self._apply_filters)
        filter_row.addWidget(self.edit_search)

        filter_row.addStretch()
        main_layout.addLayout(filter_row)

# === ВЕРТИКАЛЬНЫЙ СПЛИТТЕР ===
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Верхняя половина - список сделок
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Номер", "Контрагент", "Статус", "Дата"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(200)
        self.table.itemClicked.connect(self._on_row_clicked)
        
        #equal column widths - Контрагент шире
        header = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 80)  # Номер
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 250)  # Контрагент (шире)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 80)  # Статус
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 80)  # Дата
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        top_layout.addWidget(self.table)

        # Кнопки (только Новая и Удалить - редактирование в деталях)
        btn_layout = QHBoxLayout()
        btn_new = QPushButton("➕ Новая")
        btn_new.clicked.connect(self._create_new_deal)
        btn_layout.addWidget(btn_new)

        btn_delete = QPushButton("🗑️ Удалить")
        btn_delete.clicked.connect(self._delete_selected_deal)
        btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        top_layout.addLayout(btn_layout)

        splitter.addWidget(top_widget)

        # Нижняя половина - детали (с увеличенным местом для документов)
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        placeholder = QLabel("Выберите сделку для просмотра деталей")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_layout.addWidget(placeholder)

        splitter.addWidget(self.detail_widget)
        splitter.setStretchFactor(0, 4)  # уменьшено
        splitter.setStretchFactor(1, 5)  # увеличено на 20%

        main_layout.addWidget(splitter)

    def _apply_filters(self):
        """Применяет фильтры к списку сделок."""
        counterparty_id = self.combo_filter_cp.currentData()
        status = self.combo_filter_status.currentData()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        search = self.edit_search.text().strip()

        from datetime import datetime
        deals = self.deal_ctrl.search(
            query=search if search else None,
            counterparty_id=counterparty_id,
            status=status,
            date_from=datetime.combine(date_from, datetime.min.time()),
            date_to=datetime.combine(date_to, datetime.max.time())
        )

        self.table.setRowCount(0)
        for deal in deals:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Номер (центр)
            item_number = QTableWidgetItem(deal.number)
            item_number.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
            self.table.setItem(row, 0, item_number)
            
            # Контрагент
            self.table.setItem(row, 1, QTableWidgetItem(
                deal.counterparty.name if deal.counterparty else "N/A"
            ))

            # Статус с цветом (центр)
            status_item = QTableWidgetItem(deal.status.value if deal.status else "-")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
            status_item.setData(Qt.ItemDataRole.UserRole, deal.status)
            self.table.setItem(row, 2, status_item)

            # Дата (центр)
            item_date = QTableWidgetItem(
                deal.created_at.strftime("%d.%m.%Y") if deal.created_at else "-"
            )
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
            self.table.setItem(row, 3, item_date)

            # Подсветка строки по статусу
            self._highlight_row(row, deal.status)

    def _highlight_row(self, row: int, status: DealStatus):
        """Подсвечивает строку в зависимости от статуса."""
        colors = {
            DealStatus.DRAFT: QColor(240, 240, 240),
            DealStatus.OFFER_SENT: QColor(230, 244, 255),
            DealStatus.INVOICE_ISSUED: QColor(255, 243, 205),
            DealStatus.PREPAYMENT: QColor(232, 245, 233),
            DealStatus.FULL_PAYMENT: QColor(200, 230, 201),
            DealStatus.COMPLETED: QColor(200, 230, 201),
            DealStatus.CANCELLED: QColor(255, 235, 238),
        }
        color = colors.get(status, QColor(255, 255, 255))
        for col in range(self.table.columnCount()):
            self.table.item(row, col).setBackground(color)

    def _load_data(self):
        """Загружает все сделки."""
        self._apply_filters()

    def _on_row_clicked(self, item: QTableWidgetItem):
        """Показывает детали выбранной сделки."""
        row = item.row()
        # Номер сделки в первом столбце
        deal_number = self.table.item(row, 0).text()
        
        # Находим сделку по номеру
        deals = self.deal_ctrl.search(query=deal_number)
        if not deals:
            return
        deal_id = deals[0].id
        deal = self.deal_ctrl.get_by_id(deal_id)
        if not deal:
            return
        
        # Удаляем старый виджет деталей
        while self.detail_layout.count() > 0:
            widget = self.detail_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Создаём новый виджет деталей
        self.current_detail = DealDetailWidget(
            self.deal_ctrl,
            self.doc_ctrl,
            deal_id
        )
        self.detail_layout.addWidget(self.current_detail)

    def _create_new_deal(self):
        """Создаёт новую сделку."""
        if not self.cpa_ctrl.get_all():
            QMessageBox.warning(self, "Ошибка", "Сначала создайте контрагента.")
            return

        dialog = DealDialog(
            self.deal_ctrl,
            counterparty_id=self.cpa_ctrl.get_all()[0].id,
            parent=self
        )

        if dialog.exec():
            self._load_data()

    def _edit_selected_deal(self):
        """Редактирует выбранную сделку."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите сделку для редактирования.")
            return

        deal_id = int(self.table.item(row, 0).text())
        dialog = DealDialog(self.deal_ctrl, deal_id=deal_id, parent=self)

        if dialog.exec():
            self._load_data()

    def _delete_selected_deal(self):
        """Удаляет выбранную сделку."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите сделку для удаления.")
            return

        deal_id = int(self.table.item(row, 0).text())
        deal_number = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить сделку '{deal_number}'?\nВсе связанные документы будут удалены.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.deal_ctrl.delete(deal_id)
                self.deal_ctrl.session.commit()
                self._load_data()
                QMessageBox.information(self, "Успех", "Сделка удалена.")
            except Exception as e:
                self.deal_ctrl.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def create_deal_from_offer(self, offer_id: int) -> bool:
        """Создаёт сделку на основании коммерческого предложения.

        Args:
            offer_id: ID коммерческого предложения

        Returns:
            True если успешно
        """
        try:
            deal = self.deal_ctrl.create_from_offer(offer_id)
            self.deal_ctrl.session.commit()
            self._load_data()
            QMessageBox.information(
                self, "Успех",
                f"Создана сделка '{deal.number}'"
            )
            return True
        except ValueError as e:
            QMessageBox.warning(self, "Внимание", str(e))
            return False
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return False