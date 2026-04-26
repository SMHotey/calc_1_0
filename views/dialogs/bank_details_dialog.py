"""Диалог добавления/редактирования банковских реквизитов."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt


class BankDetailsDialog(QDialog):
    """Модальное окно для добавления/редактирования банковских реквизитов."""

    def __init__(self, bank_name: str = "", bik: str = "", 
                 correspondent_account: str = "", settlement_account: str = "",
                 is_default: bool = False, notes: str = "", parent=None):
        """Инициализация диалога.
        
        Args:
            bank_name: название банка
            bik: БИК
            correspondent_account: корр. счёт
            settlement_account: расчётный счёт
            is_default: основной счёт
            notes: примечание
            parent: родительский виджет
        """
        super().__init__(parent)
        self.setWindowTitle("Банковские реквизиты" if not bank_name else "Редактирование реквизитов")
        self.resize(420, 320)
        self._init_ui(bank_name, bik, correspondent_account, 
                     settlement_account, is_default, notes)

    def _init_ui(self, bank_name: str, bik: str, correspondent_account: str, 
                settlement_account: str, is_default: bool, notes: str):
        layout = QVBoxLayout(self)
        
        # Заголовок
        lbl_title = QLabel("🏦 Банковские реквизиты")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_title)
        
        # Форма с полями
        form = QFormLayout()
        
        # Название банка
        self.inp_bank_name = QLineEdit(bank_name)
        self.inp_bank_name.setPlaceholderText("ПАО Сбербанк")
        form.addRow("Банк*:", self.inp_bank_name)
        
        # БИК
        self.inp_bik = QLineEdit(bik)
        self.inp_bik.setPlaceholderText("044525225")
        self.inp_bik.setMaxLength(9)
        form.addRow("БИК*:", self.inp_bik)
        
        # Корреспондентский счёт
        self.inp_corr = QLineEdit(correspondent_account)
        self.inp_corr.setPlaceholderText("30101810400000000225")
        self.inp_corr.setMaxLength(20)
        form.addRow("Корр. счёт*:", self.inp_corr)
        
        # Расчётный счёт
        self.inp_settlement = QLineEdit(settlement_account)
        self.inp_settlement.setPlaceholderText("40702810938000001234")
        self.inp_settlement.setMaxLength(20)
        form.addRow("Расч. счёт*:", self.inp_settlement)
        
        # Основной
        self.chk_default = QCheckBox("Основной счёт")
        self.chk_default.setChecked(is_default)
        form.addRow("", self.chk_default)
        
        # Примечание
        self.inp_notes = QLineEdit(notes)
        self.inp_notes.setPlaceholderText("Дополнительная информация")
        form.addRow("Примечание:", self.inp_notes)
        
        layout.addLayout(form)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        
        btn_ok = QPushButton("Сохранить")
        btn_ok.clicked.connect(self.accept)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        """Возвращает введённые данные.
        
        Returns:
            Словарь с полями
        """
        return {
            "bank_name": self.inp_bank_name.text().strip(),
            "bik": self.inp_bik.text().strip(),
            "correspondent_account": self.inp_corr.text().strip(),
            "settlement_account": self.inp_settlement.text().strip(),
            "is_default": self.chk_default.isChecked(),
            "notes": self.inp_notes.text().strip() or None
        }
    
    def validate(self) -> tuple:
        """Валидация данных.
        
        Returns:
            (True, None) если данные корректны
            (False, error_message) если есть ошибки
        """
        bank_name = self.inp_bank_name.text().strip()
        if not bank_name:
            return False, "Введите название банка"
        
        bik = self.inp_bik.text().strip()
        if not bik or len(bik) != 9:
            return False, "БИК должен содержать 9 цифр"
        
        corr = self.inp_corr.text().strip()
        if not corr:
            return False, "Введите корреспондентский счёт"
        
        settlement = self.inp_settlement.text().strip()
        if not settlement:
            return False, "Введите расчётный счёт"
        
        return True, None