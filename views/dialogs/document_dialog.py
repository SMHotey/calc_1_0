"""Диалог загрузки/редактирования документа."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QPushButton,
    QMessageBox, QLabel, QFrame, QDateEdit, QLineEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from typing import Optional
import os
from controllers.document_controller import DocumentController
from constants import DOCUMENT_FILE_FILTERS


class DocumentDialog(QDialog):
    """Модальное окно для создания/редактирования документа.

    Позволяет:
    - Загрузить файл через диалог
    - Указать наименование и дату документа
    - Сохранить файл в БД и на диск
    """

    def __init__(
            self,
            controller: DocumentController,
            doc_id: Optional[int] = None,
            counterparty_id: Optional[int] = None,
            deal_id: Optional[int] = None,
            parent=None
    ):
        super().__init__(parent)
        self.controller = controller
        self.doc_id = doc_id
        self.counterparty_id = counterparty_id
        self.deal_id = deal_id
        self.editing = doc_id is not None
        self.selected_file_path = ""

        self.setWindowTitle("Редактирование документа" if self.editing else "Новый документ")
        self.resize(500, 300)
        self._init_ui()

        if self.editing:
            self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Наименование
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Наименование документа")
        form.addRow("Наименование:", self.inp_name)

        # Дата документа
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        form.addRow("Дата:", self.date_edit)

        # Путь к файлу
        file_layout = QHBoxLayout()
        self.inp_file_path = QLineEdit()
        self.inp_file_path.setReadOnly(True)
        self.inp_file_path.setPlaceholderText("Выберите файл...")
        file_layout.addWidget(self.inp_file_path)

        btn_browse = QPushButton("📂 Обзор...")
        btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(btn_browse)
        form.addRow("Файл:", file_layout)

        # Тип файла (подсказка)
        self.lbl_file_type = QLabel("")
        self.lbl_file_type.setStyleSheet("color: gray;")
        form.addRow("", self.lbl_file_type)

        layout.addLayout(form)

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
        layout.addWidget(btn_frame)

    def _browse_file(self):
        """Открывает диалог выбора файла."""
        file_filter = ";;".join(DOCUMENT_FILE_FILTERS)
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите документ",
            "",
            file_filter
        )

        if path:
            self.selected_file_path = path
            self.inp_file_path.setText(path)

            # Устанавливаем имя файла как наименование, если оно пустое
            if not self.inp_name.text():
                base_name = os.path.splitext(os.path.basename(path))[0]
                self.inp_name.setText(base_name)

            # Показываем тип файла
            ext = os.path.splitext(path)[1].lower().lstrip(".")
            self.lbl_file_type.setText(f"Тип файла: .{ext}")

    def _load_data(self):
        """Загружает данные документа для редактирования."""
        doc = self.controller.get_by_id(self.doc_id)
        if not doc:
            return

        self.inp_name.setText(doc.name or "")

        if doc.document_date:
            self.date_edit.setDate(doc.document_date)

        if doc.file_path:
            self.inp_file_path.setText(doc.file_path)
            self.selected_file_path = doc.file_path

            ext = doc.file_type or os.path.splitext(doc.file_path)[1].lower().lstrip(".")
            self.lbl_file_type.setText(f"Тип файла: .{ext}")

    def _save(self):
        """Сохраняет документ."""
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка валидации", "Введите наименование документа.")
            return

        if not self.editing and not self.selected_file_path:
            QMessageBox.warning(self, "Ошибка валидации", "Выберите файл.")
            return

        document_date = self.date_edit.date().toPyDate()

        try:
            if self.editing:
                # Редактирование - только метаданные
                self.controller.update(self.doc_id, {
                    "name": name,
                    "document_date": document_date
                })
                self.controller.session.commit()
            else:
                # Создание нового документа
                self.controller.create(
                    name=name,
                    file_path=self.selected_file_path,
                    counterparty_id=self.counterparty_id,
                    deal_id=self.deal_id,
                    document_date=document_date,
                    save_to_disk=True
                )
                self.controller.session.commit()

            self.accept()
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Ошибка сохранения", str(e))