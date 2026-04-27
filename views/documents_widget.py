"""Вкладка 'Документы' для отображения списка документов.

Используется как в сделке, так и в контрагенте.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from controllers.document_controller import DocumentController


class DocumentsWidget(QWidget):
    """Виджет для отображения и управления документами.

    Может использоваться внутри сделки или контрагента.
    Показывает таблицу документов с кнопками добавления, удаления, экспорта.
    """

    def __init__(
            self,
            doc_controller: "DocumentController",
            counterparty_id: Optional[int] = None,
            deal_id: Optional[int] = None,
            parent=None
    ):
        super().__init__(parent)
        self.doc_ctrl = doc_controller
        self.counterparty_id = counterparty_id
        self.deal_id = deal_id
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок с информацией о владельце
        header_layout = QHBoxLayout()
        self.header_label = QLabel("Документы")
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Таблица документов
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Наименование", "Тип", "Дата", "Путь"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(40)  # Высота строк +40%
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("📂 Добавить")
        btn_add.clicked.connect(self._add_document)
        btn_layout.addWidget(btn_add)

        btn_export = QPushButton("📥 Экспорт")
        btn_export.clicked.connect(self._export_document)
        btn_layout.addWidget(btn_export)

        btn_open = QPushButton("📄 Открыть")
        btn_open.clicked.connect(self._open_document)
        btn_layout.addWidget(btn_open)

        btn_delete = QPushButton("🗑️ Удалить")
        btn_delete.clicked.connect(self._delete_document)
        btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _get_documents(self) -> List:
        """Получает документы в зависимости от контекста."""
        if self.deal_id:
            return self.doc_ctrl.get_by_deal(self.deal_id)
        elif self.counterparty_id:
            return self.doc_ctrl.get_by_counterparty(self.counterparty_id)
        return []

    def _load_data(self):
        """Загружает данные документов."""
        self.table.setRowCount(0)
        try:
            for doc in self._get_documents():
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(str(doc.id)))
                self.table.setItem(row, 1, QTableWidgetItem(doc.name or "-"))
                self.table.setItem(row, 2, QTableWidgetItem(f".{doc.file_type}"))
                date_str = doc.document_date.strftime("%d.%m.%Y") if doc.document_date else "-"
                self.table.setItem(row, 3, QTableWidgetItem(date_str))
                # Показываем только имя файла, не полный путь
                file_name = doc.file_path.split("/")[-1] if doc.file_path else "-"
                self.table.setItem(row, 4, QTableWidgetItem(file_name))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить документы:\n{e}")

    def _add_document(self):
        """Добавляет новый документ."""
        from views.dialogs.document_dialog import DocumentDialog

        dialog = DocumentDialog(
            self.doc_ctrl,
            counterparty_id=self.counterparty_id,
            deal_id=self.deal_id,
            parent=self
        )

        if dialog.exec():
            self._load_data()

    def _export_document(self):
        """Экспортирует выбранный документ."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите документ для экспорта.")
            return

        doc_id = int(self.table.item(row, 0).text())
        doc_name = self.table.item(row, 1).text()
        doc_type = self.table.item(row, 2).text().replace(".", "")

        # Формируем имя файла для сохранения
        default_name = f"{doc_name}.{doc_type}"

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить документ",
            default_name,
            f"{doc_type.upper()} Files (*.{doc_type})"
        )

        if path:
            if self.doc_ctrl.export_to_disk(doc_id, path):
                QMessageBox.information(self, "Успех", f"Файл сохранён:\n{path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось экспортировать файл.")

    def _open_document(self):
        """Открывает выбранный документ."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите документ для открытия.")
            return

        doc_id = int(self.table.item(row, 0).text())
        doc = self.doc_ctrl.get_by_id(doc_id)

        if not doc:
            QMessageBox.critical(self, "Ошибка", "Документ не найден.")
            return

        # Сначала пробуем открыть из БД
        if doc.file_content:
            import tempfile
            import os
            import subprocess

            # Создаём временный файл
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"{doc.name}.{doc.file_type}")

            with open(temp_path, "wb") as f:
                f.write(doc.file_content)

            try:
                subprocess.run([temp_path], shell=True)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        # Пробуем открыть с диска
        if doc.file_path and os.path.exists(doc.file_path):
            try:
                subprocess.run([doc.file_path], shell=True)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")
        else:
            QMessageBox.warning(self, "Внимание", "Файл не найден ни в БД, ни на диске.")

    def _delete_document(self):
        """Удаляет выбранный документ."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите документ для удаления.")
            return

        doc_id = int(self.table.item(row, 0).text())
        doc_name = self.table.item(row, 1).text()

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить документ '{doc_name}'?\nФайлы будут удалены с диска.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.doc_ctrl.delete(doc_id, delete_file=True)
                self.doc_ctrl.session.commit()
                self._load_data()
                QMessageBox.information(self, "Успех", "Документ удалён.")
            except Exception as e:
                self.doc_ctrl.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def refresh(self):
        """Обновляет список документов."""
        self._load_data()


# Need os import for _open_document
import os