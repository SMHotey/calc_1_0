"""Диалог создания/редактирования сделки с workflow."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QPushButton,
    QMessageBox, QLabel, QFrame, QDateEdit, QLineEdit, QComboBox,
    QTextEdit, QGroupBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from typing import Optional
from controllers.deal_controller import DealController
from constants import DealStatus


class DealDialog(QDialog):
    """Модальное окно для создания/редактирования сделки.

    Позволяет:
    - Указать номер и контрагента
    - Просматривать/редактировать workflow (счёт, предоплата, оплата)
    - Завершить или отменить сделку
    """

    def __init__(
            self,
            controller: DealController,
            deal_id: Optional[int] = None,
            counterparty_id: Optional[int] = None,
            commercial_offer_id: Optional[int] = None,
            parent=None
    ):
        super().__init__(parent)
        self.controller = controller
        self.deal_id = deal_id
        self.editing = deal_id is not None
        self.initial_counterparty_id = counterparty_id
        self.initial_offer_id = commercial_offer_id

        self.setWindowTitle("Редактирование сделки" if self.editing else "Новая сделка")
        self.resize(600, 700)
        self._init_ui()

        if self.editing:
            self._load_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # === ОСНОВНЫЕ ДАННЫЕ ===
        basic_group = QGroupBox("Основные данные")
        basic_layout = QFormLayout()

        self.inp_number = QLineEdit()
        self.inp_number.setPlaceholderText("Номер сделки (например, С-2026-0001)")
        basic_layout.addRow("Номер:", self.inp_number)

        self.combo_status = QComboBox()
        for status in DealStatus:
            self.combo_status.addItem(status.value, status)
        basic_layout.addRow("Статус:", self.combo_status)

        # Выбор контрагента
        from controllers.counterparty_controller import CounterpartyController
        self.cpa_ctrl = CounterpartyController()
        self.combo_counterparty = QComboBox()
        self.combo_counterparty.addItem("— Выберите контрагента —", None)
        for cp in self.cpa_ctrl.get_all():
            self.combo_counterparty.addItem(cp.name, cp.id)
        basic_layout.addRow("Контрагент:", self.combo_counterparty)

        self.inp_created = QDateEdit()
        self.inp_created.setCalendarPopup(True)
        self.inp_created.setDisplayFormat("dd.MM.yyyy")
        self.inp_created.setDate(QDate.currentDate())
        self.inp_created.setEnabled(False)
        basic_layout.addRow("Дата создания:", self.inp_created)

        basic_group.setLayout(basic_layout)
        main_layout.addWidget(basic_group)

        # === СЧЁТ ===
        invoice_group = QGroupBox("Выставленный счёт")
        invoice_layout = QFormLayout()

        self.inp_invoice_number = QLineEdit()
        self.inp_invoice_number.setPlaceholderText("Номер счёта")
        invoice_layout.addRow("Номер счёта:", self.inp_invoice_number)

        self.date_invoice = QDateEdit()
        self.date_invoice.setCalendarPopup(True)
        self.date_invoice.setDisplayFormat("dd.MM.yyyy")
        self.date_invoice.setDate(QDate.currentDate())
        invoice_layout.addRow("Дата счёта:", self.date_invoice)

        self.spin_invoice_amount = QDoubleSpinBox()
        self.spin_invoice_amount.setPrefix("")
        self.spin_invoice_amount.setSuffix(" ₽")
        self.spin_invoice_amount.setMaximum(999999999)
        self.spin_invoice_amount.setDecimals(2)
        invoice_layout.addRow("Сумма счёта:", self.spin_invoice_amount)

        invoice_group.setLayout(invoice_layout)
        main_layout.addWidget(invoice_group)

        # === ПРЕДОПЛАТА ===
        prepayment_group = QGroupBox("Предоплата")
        prepayment_layout = QFormLayout()

        self.date_prepayment = QDateEdit()
        self.date_prepayment.setCalendarPopup(True)
        self.date_prepayment.setDisplayFormat("dd.MM.yyyy")
        self.date_prepayment.setDate(QDate.currentDate())
        prepayment_layout.addRow("Дата предоплаты:", self.date_prepayment)

        self.spin_prepayment = QDoubleSpinBox()
        self.spin_prepayment.setPrefix("")
        self.spin_prepayment.setSuffix(" ₽")
        self.spin_prepayment.setMaximum(999999999)
        self.spin_prepayment.setDecimals(2)
        prepayment_layout.addRow("Сумма предоплаты:", self.spin_prepayment)

        prepayment_group.setLayout(prepayment_layout)
        main_layout.addWidget(prepayment_group)

        # === ПОЛНАЯ ОПЛАТА ===
        payment_group = QGroupBox("Полная оплата")
        payment_layout = QFormLayout()

        self.date_full_payment = QDateEdit()
        self.date_full_payment.setCalendarPopup(True)
        self.date_full_payment.setDisplayFormat("dd.MM.yyyy")
        self.date_full_payment.setDate(QDate.currentDate())
        payment_layout.addRow("Дата оплаты:", self.date_full_payment)

        payment_group.setLayout(payment_layout)
        main_layout.addWidget(payment_group)

        # === КОММЕНТАРИЙ ===
        comment_group = QGroupBox("Комментарий")
        comment_layout = QVBoxLayout()
        self.text_comment = QTextEdit()
        self.text_comment.setPlaceholderText("Дополнительная информация...")
        comment_layout.addWidget(self.text_comment)
        comment_group.setLayout(comment_layout)
        main_layout.addWidget(comment_group)

        # === КНОПКИ ===
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)

        btn_complete = QPushButton("✅ Завершить")
        btn_complete.setStyleSheet("background-color: #28a745; color: white;")
        btn_complete.clicked.connect(self._complete_deal)
        btn_layout.addWidget(btn_complete)

        btn_cancel_deal = QPushButton("❌ Отменить")
        btn_cancel_deal.setStyleSheet("background-color: #dc3545; color: white;")
        btn_cancel_deal.clicked.connect(self._cancel_deal)
        btn_layout.addWidget(btn_cancel_deal)

        btn_layout.addStretch()

        btn_save = QPushButton("💾 Сохранить")
        btn_save.setStyleSheet("background-color: #28a745; color: white;")
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_save)

        btn_close = QPushButton("❌ Отмена")
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(btn_close)

        main_layout.addWidget(btn_frame)

    def _load_data(self):
        """Загружает данные сделки."""
        deal = self.controller.get_by_id(self.deal_id)
        if not deal:
            return

        self.inp_number.setText(deal.number or "")

        # Устанавливаем статус
        idx = self.combo_status.findData(deal.status)
        if idx >= 0:
            self.combo_status.setCurrentIndex(idx)

        if deal.created_at:
            self.inp_created.setDate(deal.created_at)

        # Счёт
        if deal.invoice_number:
            self.inp_invoice_number.setText(deal.invoice_number)
        if deal.invoice_date:
            self.date_invoice.setDate(deal.invoice_date)
        if deal.invoice_amount:
            self.spin_invoice_amount.setValue(float(deal.invoice_amount))

        # Предоплата
        if deal.prepayment_date:
            self.date_prepayment.setDate(deal.prepayment_date)
        if deal.prepayment_amount:
            self.spin_prepayment.setValue(float(deal.prepayment_amount))

        # Полная оплата
        if deal.full_payment_date:
            self.date_full_payment.setDate(deal.full_payment_date)

        # Комментарий
        if deal.comment:
            self.text_comment.setPlainText(deal.comment)

    def _complete_deal(self):
        """Завершает сделку."""
        if not self.editing:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните сделку.")
            return

        reply = QMessageBox.question(
            self, "Завершение сделки",
            "Завершить сделку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.controller.complete(self.deal_id)
                self.controller.session.commit()
                QMessageBox.information(self, "Успех", "Сделка завершена.")
                self.accept()
            except Exception as e:
                self.controller.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def _cancel_deal(self):
        """Отменяет сделку."""
        if not self.editing:
            QMessageBox.warning(self, "Внимание", "Сначала сохраните сделку.")
            return

        from PyQt6.QtWidgets import QInputDialog
        reason, ok = QInputDialog.getText(
            self, "Отмена сделки",
            "Укажите причину отмены:",
            QLineEdit.EchoMode.Normal
        )

        if ok and reason.strip():
            try:
                self.controller.cancel(self.deal_id, reason.strip())
                self.controller.session.commit()
                QMessageBox.information(self, "Успех", "Сделка отменена.")
                self.accept()
            except Exception as e:
                self.controller.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def _save(self):
        """Сохраняет сделку."""
        number = self.inp_number.text().strip()
        if not number:
            QMessageBox.warning(self, "Ошибка валидации", "Введите номер сделки.")
            return

        counterparty_id = self.combo_counterparty.currentData()
        if not counterparty_id:
            QMessageBox.warning(self, "Ошибка валидации", "Выберите контрагента.")
            return

        try:
            status = self.combo_status.currentData()
            data = {
                "number": number,
                "status": status,
                "comment": self.text_comment.toPlainText().strip() or None,
                "invoice_number": self.inp_invoice_number.text().strip() or None,
                "invoice_date": self.date_invoice.date().toPyDate(),
                "invoice_amount": self.spin_invoice_amount.value(),
                "prepayment_date": self.date_prepayment.date().toPyDate(),
                "prepayment_amount": self.spin_prepayment.value(),
                "full_payment_date": self.date_full_payment.date().toPyDate(),
            }

            # Обнуляем пустые суммы
            if data["invoice_amount"] == 0:
                data["invoice_amount"] = None
            if data["prepayment_amount"] == 0:
                data["prepayment_amount"] = None

            if self.editing:
                self.controller.update(self.deal_id, data)
            else:
                self.controller.create(
                    number=number,
                    counterparty_id=counterparty_id,
                    commercial_offer_id=self.initial_offer_id,
                    comment=data["comment"]
                )

            self.controller.session.commit()
            self.accept()
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Ошибка сохранения", str(e))