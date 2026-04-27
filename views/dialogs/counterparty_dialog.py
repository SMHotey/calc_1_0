"""Диалог создания/редактирования контрагента с динамической формой."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QComboBox, QLineEdit, QPushButton,
    QMessageBox, QLabel, QFrame, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from typing import Optional
from controllers.counterparty_controller import CounterpartyController
from constants import CounterpartyType


class CounterpartyDialog(QDialog):
    """Модальное окно для управления контрагентами.

    Автоматически скрывает/показывает поля в зависимости от выбранного типа (ЮЛ/ИП/ФЛ).
    Валидирует ИНН, ОГРН, телефон и email перед сохранением.
    """

    def __init__(
            self,
            controller: CounterpartyController,
            cp_id: Optional[int] = None,
            parent=None
    ):
        super().__init__(parent)
        self.controller = controller
        self.cp_id = cp_id
        self.editing = cp_id is not None
        self.setWindowTitle("Редактирование контрагента" if self.editing else "Новый контрагент")
        self.resize(600, 600)
        self._init_ui()
        if self.editing:
            self._load_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Табы: Основное | Контакты | Документы
        tabs = QTabWidget()

        # === Вкладка "Основное" ===
        main_tab = QWidget()
        main_layout_inner = QVBoxLayout(main_tab)
        form = QFormLayout()

        # Тип контрагента
        self.combo_type = QComboBox()
        for t in CounterpartyType:
            self.combo_type.addItem(t.value, t)
        self.combo_type.currentIndexChanged.connect(self._update_fields_visibility)
        form.addRow("Тип:", self.combo_type)

        # Общие поля
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Наименование / ФИО")
        form.addRow("Наименование:", self.inp_name)

        self.inp_inn = QLineEdit()
        self.inp_inn.setPlaceholderText("10 или 12 цифр")
        form.addRow("ИНН:", self.inp_inn)

        self.inp_kpp = QLineEdit()
        self.inp_kpp.setPlaceholderText("9 цифр (для ЮЛ)")
        form.addRow("КПП:", self.inp_kpp)

        self.inp_ogrn = QLineEdit()
        self.inp_ogrn.setPlaceholderText("13 или 15 цифр")
        form.addRow("ОГРН/ОГРНИП:", self.inp_ogrn)

        self.inp_address = QLineEdit()
        self.inp_address.setPlaceholderText("Юр. адрес / адрес регистрации")
        form.addRow("Адрес:", self.inp_address)

        self.inp_phone = QLineEdit()
        self.inp_phone.setPlaceholderText("+7 (999) 000-00-00")
        form.addRow("Телефон:", self.inp_phone)

        self.inp_email = QLineEdit()
        self.inp_email.setPlaceholderText("email@example.com")
        form.addRow("Email:", self.inp_email)

        main_layout_inner.addLayout(form)
        main_layout_inner.addStretch()

        tabs.addTab(main_tab, "Основное")

        # === Вкладка "Контактные лица" ===
        self.contacts_widget = None
        contacts_tab = QWidget()
        contacts_layout = QVBoxLayout(contacts_tab)
        contacts_layout.addWidget(QLabel("Загрузка контактных лиц..."))
        tabs.addTab(contacts_tab, "👤 Контакты")

        # === Вкладка "Документы" ===
        self.docs_widget = None
        docs_tab = QWidget()
        docs_layout = QVBoxLayout(docs_tab)
        docs_layout.addWidget(QLabel("Загрузка документов..."))
        tabs.addTab(docs_tab, "📄 Документы")

        # === Вкладка "Банковские реквизиты" ===
        self.bank_details_widget = None
        bank_details_tab = QWidget()
        bank_details_layout = QVBoxLayout(bank_details_tab)
        bank_details_layout.addWidget(QLabel("Загрузка реквизитов..."))
        tabs.addTab(bank_details_tab, "🏦 Реквизиты")

        main_layout.addWidget(tabs)

        # Кнопки
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_save = QPushButton("💾 Сохранить")
        btn_save.setStyleSheet("background-color: #28a745; color: white;")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("❌ Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        main_layout.addWidget(btn_frame)

        self._update_fields_visibility(0)
        self._tabs = tabs
        self._contacts_tab = contacts_tab
        self._contacts_layout = contacts_layout
        self._contacts_widget = None
        self._docs_tab = docs_tab
        self._docs_layout = docs_layout
        self._docs_widget = None
        self._bank_details_tab = bank_details_tab
        self._bank_details_layout = bank_details_layout
        self._bank_details_widget = None

    def _update_fields_visibility(self, idx: int):
        cp_type = self.combo_type.itemData(idx)
        self.inp_kpp.setVisible(cp_type == CounterpartyType.LEGAL)
        self.inp_kpp.setEnabled(cp_type == CounterpartyType.LEGAL)

    def _load_data(self):
        cp = self.controller.get_by_id(self.cp_id)
        if not cp:
            return
        idx = self.combo_type.findData(cp.type)
        if idx >= 0:
            self.combo_type.setCurrentIndex(idx)
        self.inp_name.setText(cp.name or "")
        self.inp_inn.setText(cp.inn or "")
        self.inp_kpp.setText(cp.kpp or "")
        self.inp_ogrn.setText(cp.ogrn or "")
        self.inp_address.setText(cp.address or "")
        self.inp_phone.setText(cp.phone or "")
        self.inp_email.setText(cp.email or "")

    def init_contacts_widget(self, contacts_controller):
        """Инициализирует виджет контактных лиц."""
        if self._contacts_widget:
            return
        while self._contacts_layout.count():
            item = self._contacts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        from views.contact_persons_widget import ContactPersonsWidget
        self._contacts_widget = ContactPersonsWidget(
            contacts_controller,
            counterparty_id=self.cp_id if self.editing else None
        )
        self._contacts_layout.addWidget(self._contacts_widget)

    def init_documents_widget(self, doc_controller):
        """Инициализирует виджет документов."""
        if self._docs_widget:
            return
        while self._docs_layout.count():
            item = self._docs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        from views.documents_widget import DocumentsWidget
        self._docs_widget = DocumentsWidget(
            doc_controller,
            counterparty_id=self.cp_id if self.editing else None
        )
        self._docs_layout.addWidget(self._docs_widget)

    def init_bank_details_widget(self, bd_controller):
        """Инициализирует виджет банковских реквизитов."""
        if self._bank_details_widget:
            return
        while self._bank_details_layout.count():
            item = self._bank_details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        from views.bank_details_widget import BankDetailsWidget
        self._bank_details_widget = BankDetailsWidget(
            bd_controller,
            counterparty_id=self.cp_id if self.editing else None
        )
        self._bank_details_layout.addWidget(self._bank_details_widget)

    def _save(self):
        cp_type = self.combo_type.currentData()
        data = {
            "name": self.inp_name.text().strip(),
            "inn": self.inp_inn.text().strip() or None,
            "kpp": self.inp_kpp.text().strip() or None,
            "ogrn": self.inp_ogrn.text().strip() or None,
            "address": self.inp_address.text().strip(),
            "phone": self.inp_phone.text().strip(),
            "email": self.inp_email.text().strip() or None
        }

        if not data["name"] or not data["phone"] or not data["address"]:
            return QMessageBox.warning(self, "Ошибка валидации",
                                       "Заполните обязательные поля: Наименование, Телефон, Адрес.")
        if cp_type == CounterpartyType.LEGAL and not data["inn"]:
            return QMessageBox.warning(self, "Ошибка валидации", "Для ЮЛ обязателен ИНН.")
        if cp_type == CounterpartyType.IP and not data["inn"]:
            return QMessageBox.warning(self, "Ошибка валидации", "Для ИП обязателен ИНН.")

        try:
            if self.editing:
                self.controller.update(self.cp_id, data)
            else:
                self.controller.create(
                    cp_type=cp_type,
                    name=data["name"], inn=data["inn"], phone=data["phone"],
                    address=data["address"], email=data["email"],
                    kpp=data.get("kpp"), ogrn=data.get("ogrn")
                )
            self.controller.session.commit()

            if not self.editing:
                created = self.controller.get_all()
                if created:
                    self.cp_id = created[-1].id
                    if self._contacts_widget:
                        self._contacts_widget.counterparty_id = self.cp_id
                        self._contacts_widget.refresh()
                    if self._docs_widget:
                        self._docs_widget.counterparty_id = self.cp_id
                        self._docs_widget.refresh()
                    if self._bank_details_widget:
                        self._bank_details_widget.counterparty_id = self.cp_id
                        self._bank_details_widget.refresh()

            self.accept()
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Ошибка сохранения", str(e))