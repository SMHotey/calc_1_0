"""Диалог добавления/редактирования контактного лица."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt


class ContactPersonDialog(QDialog):
    """Модальное окно для добавления/редактирования контактного лица.
    
    Показывает все поля сразу вместо последовательных диалогов.
    """

    def __init__(self, name: str = "", position: str = "", 
                 phone: str = "", email: str = "", parent=None):
        """Инициализация диалога.
        
        Args:
            name: текущее ФИО (для редактирования)
            position: текущая должность
            phone: текущий телефон
            email: текущий email
            parent: родительский виджет
        """
        super().__init__(parent)
        self.setWindowTitle("Контактное лицо" if not name else "Редактирование контакта")
        self.resize(400, 280)
        self._init_ui(name, position, phone, email)

    def _init_ui(self, name: str, position: str, phone: str, email: str):
        layout = QVBoxLayout(self)
        
        # Заголовок
        lbl_title = QLabel("📋 Контактное лицо")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_title)
        
        # Форма с полями
        form = QFormLayout()
        
        # ФИО
        self.inp_name = QLineEdit(name)
        self.inp_name.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО*:", self.inp_name)
        
        # Должность
        self.inp_position = QLineEdit(position)
        self.inp_position.setPlaceholderText("Менеджер")
        form.addRow("Должность:", self.inp_position)
        
        # Телефон
        self.inp_phone = QLineEdit(phone)
        self.inp_phone.setPlaceholderText("+7 (495) 123-45-67")
        form.addRow("Телефон:", self.inp_phone)
        
        # Email
        self.inp_email = QLineEdit(email)
        self.inp_email.setPlaceholderText("email@example.com")
        form.addRow("Email:", self.inp_email)
        
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
            Словарь с полями: name, position, phone, email
        """
        return {
            "name": self.inp_name.text().strip(),
            "position": self.inp_position.text().strip() or None,
            "phone": self.inp_phone.text().strip() or None,
            "email": self.inp_email.text().strip() or None
        }
    
    def validate(self) -> tuple:
        """Валидация данных.
        
        Returns:
            (True, None) если данные корректны
            (False, error_message) если есть ошибки
        """
        name = self.inp_name.text().strip()
        if not name:
            return False, "Введите ФИО контактного лица"
        
        return True, None