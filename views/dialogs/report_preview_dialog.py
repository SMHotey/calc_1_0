"""Диалог предпросмотра коммерческого предложения в HTML."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from typing import Dict, Any
from controllers.offer_controller import OfferController


class ReportPreviewDialog(QDialog):
    """
    Модальное окно для предпросмотра КП в HTML-формате.
    Позволяет экспортировать в файл или напечатать.
    """

    def __init__(self, offer_id: int, offer_controller: OfferController, parent=None):
        super().__init__(parent)
        self.offer_id = offer_id
        self.controller = offer_controller
        self.setWindowTitle(f"Предпросмотр КП #{offer_id}")
        self.resize(900, 700)
        self._init_ui()
        self._render_preview()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        layout.addWidget(self.browser)

        btn_layout = QHBoxLayout()
        self.btn_save_html = QPushButton("🌐 Сохранить HTML")
        self.btn_save_html.clicked.connect(self._save_html)
        self.btn_print = QPushButton("🖨️ Печать / PDF")
        self.btn_print.clicked.connect(self._print_pdf)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_save_html)
        btn_layout.addWidget(self.btn_print)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _render_preview(self):
        try:
            html_content = self.controller.export_to_html(self.offer_id)
            self.browser.setHtml(html_content)
        except Exception as e:
            self.browser.setHtml(f"<h3>Ошибка загрузки данных</h3><p>{e}</p>")

    def _save_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить HTML", "offer.html", "HTML Files (*.html)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.controller.export_to_html(self.offer_id))
                QMessageBox.information(self, "Успех", f"Файл сохранён:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def _print_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт в PDF", "offer.pdf", "PDF Files (*.pdf)")
        if path:
            try:
                self.controller.export_to_pdf(self.offer_id, path)
                QMessageBox.information(self, "Успех", f"PDF-файл успешно создан:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка генерации PDF", str(e))