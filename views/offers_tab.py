"""Вкладка 'Коммерческие предложения'. Управление списком, экспорт, просмотр."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
from views.offer_table_widget import OfferTableWidget
from controllers.offer_controller import OfferController
from datetime import datetime
import os


class OffersTab(QWidget):
    def __init__(self, offer_ctrl: OfferController, cpa_ctrl, calculator_ctrl):
        super().__init__()
        self.offer_ctrl = offer_ctrl
        self.cpa_ctrl = cpa_ctrl
        self.calc_ctrl = calculator_ctrl
        self._init_ui()
        self._load_offers()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Список КП слева, детали справа
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Список предложений"))
        self.list_offers = QListWidget()
        self.list_offers.currentRowChanged.connect(self._show_offer)
        left_layout.addWidget(self.list_offers)

        btn_new_offer = QPushButton("📄 Новое предложение")
        btn_new_offer.clicked.connect(self._create_new_offer)
        left_layout.addWidget(btn_new_offer)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("Позиции"))

        self.table = OfferTableWidget()
        self.table.add_position_requested.connect(self._on_add_position)
        right_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_export_pdf = QPushButton("📥 Экспорт PDF")
        self.btn_export_html = QPushButton("🌐 Экспорт HTML")
        self.btn_export_pdf.clicked.connect(self._export_pdf)
        self.btn_export_html.clicked.connect(self._export_html)
        btn_layout.addWidget(self.btn_export_pdf)
        btn_layout.addWidget(self.btn_export_html)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

    def _load_offers(self):
        self.list_offers.clear()
        offers = self.offer_ctrl.get_all_offers()
        for o in offers:
            item = QListWidgetItem(f"№ {o['number']} | {o['counterparty']} | {o['date']} | {o['total']:,.0f} ₽")
            item.setData(Qt.ItemDataRole.UserRole, o["id"])
            self.list_offers.addItem(item)

    def _show_offer(self, row: int):
        if row < 0: return
        offer_id = self.list_offers.item(row).data(Qt.ItemDataRole.UserRole)
        data = self.offer_ctrl.get_offer_with_items(offer_id)
        if not data: return

        self.current_offer_id = offer_id
        self.table.setRowCount(0)
        for item in data["items"]:
            self.table.append_position(item)

    def _create_new_offer(self):
        # Для упрощения берём первого контрагента или показываем выбор
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