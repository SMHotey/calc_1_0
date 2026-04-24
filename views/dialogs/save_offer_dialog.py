"""Диалог сохранения коммерческого предложения."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QLabel, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt
from typing import Optional


class SaveOfferDialog(QDialog):
    """Модальное окно сохранения КП с информацией и возможностью редактирования имени."""

    def __init__(
            self,
            offer_data: dict,
            parent=None
    ):
        super().__init__(parent)
        self._offer_data = offer_data
        self.setWindowTitle("Сохранить КП")
        self.resize(500, 400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Информация о КП
        info_group = QLabel()
        info_group.setText("<b>Информация о КП</b>")
        layout.addWidget(info_group)

        form = QFormLayout()

        # Контрагент
        cp_label = QLabel(self._offer_data.get("counterparty", "—"))
        form.addRow("Контрагент:", cp_label)

        # Прайс-лист
        price_label = QLabel(self._offer_data.get("price_list", "Базовый прайс"))
        form.addRow("Прайс:", price_label)

        # Количество изделий
        qty_label = QLabel(str(self._offer_data.get("items_count", 0)))
        form.addRow("Кол-во изделий:", qty_label)

        # Сумма по базовому прайсу
        base_sum = QLabel(f"{self._offer_data.get('base_sum', 0):,.2f} ₽")
        form.addRow("Сумма (базовый прайс):", base_sum)

        # Сумма по текущему прайсу
        current_sum = QLabel(f"{self._offer_data.get('current_sum', 0):,.2f} ₽")
        form.addRow("Сумма (текущий прайс):", current_sum)

        # Наценка
        markup = QLabel(f"{self._offer_data.get('markup', 0):,.2f} ₽")
        form.addRow("Наценка:", markup)

        layout.addLayout(form)

        # Разделитель
        layout.addWidget(QLabel(""))

        # Наименование
        name_layout = QFormLayout()
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Введите номер КП")
        # Автогенерация имени по умолчанию
        default_name = self._offer_data.get("number", "")
        if default_name:
            self.inp_name.setText(default_name)
        name_layout.addRow("Номер КП:", self.inp_name)
        layout.addLayout(name_layout)

        # Кнопки
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_save = QPushButton("💾 Сохранить")
        btn_save.setStyleSheet("background-color: #28a745; color: white; padding: 8px 15px;")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("❌ Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addWidget(btn_frame)

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            return QMessageBox.warning(self, "Ошибка", "Введите номер КП.")
        self.accept()

    def get_name(self) -> str:
        return self.inp_name.text().strip()