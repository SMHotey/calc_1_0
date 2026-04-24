"""Виджет управления контактными лицами.

Используется внутри диалога контрагента.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from controllers.contact_person_controller import ContactPersonController


class ContactPersonsWidget(QWidget):
    """Виджет для управления контактными лицами.

    Показывает таблицу контактных лиц с кнопками добавления, редактирования, удаления.
    """

    def __init__(
            self,
            cp_controller: "ContactPersonController",
            counterparty_id: int,
            parent=None
    ):
        super().__init__(parent)
        self.cp_controller = cp_controller
        self.counterparty_id = counterparty_id
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("📋 Контактные лица"))

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ФИО", "Должность", "Телефон", "Email"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Ширина столбцов
        self.table.setColumnWidth(0, 150)  # ФИО
        self.table.setColumnWidth(1, 120) # Должность
        self.table.setColumnWidth(2, 100) # Телефон
        self.table.setColumnWidth(3, 130) # Email
        
        for i in range(4):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Добавить")
        btn_add.clicked.connect(self._add_person)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Редакт.")
        btn_edit.clicked.connect(self._edit_person)
        btn_layout.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️ Удалить")
        btn_delete.clicked.connect(self._delete_person)
        btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_data(self):
        self.table.setRowCount(0)
        try:
            persons = self.cp_controller.get_by_counterparty(self.counterparty_id)
            for person in persons:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # ФИО (центр)
                item_name = QTableWidgetItem(person.name or "-")
                item_name.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
                self.table.setItem(row, 0, item_name)
                
                # Должность
                item_pos = QTableWidgetItem(person.position or "-")
                self.table.setItem(row, 1, item_pos)
                
                # Телефон
                item_phone = QTableWidgetItem(person.phone or "-")
                self.table.setItem(row, 2, item_phone)
                
                # Email
                item_email = QTableWidgetItem(person.email or "-")
                self.table.setItem(row, 3, item_email)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить контактных лиц:\n{e}")

    def _add_person(self):
        """Добавляет новое контактное лицо."""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Новое контактное лицо", "ФИО:")
        if not ok or not name.strip():
            return
        
        position, _ = QInputDialog.getText(self, "Новое контактное лицо", "Должность:", QLineEdit.EchoMode.Normal)
        phone, _ = QInputDialog.getText(self, "Новое контактное лицо", "Телефон:", QLineEdit.EchoMode.Normal)
        email, _ = QInputDialog.getText(self, "Новое контактное лицо", "Email:", QLineEdit.EchoMode.Normal)
        
        try:
            self.cp_controller.create(
                name=name.strip(),
                counterparty_id=self.counterparty_id,
                position=position.strip() or None,
                phone=phone.strip() or None,
                email=email.strip() or None
            )
            self.cp_controller.session.commit()
            self._load_data()
            QMessageBox.information(self, "Успех", "Контактное лицо добавлено.")
        except Exception as e:
            self.cp_controller.session.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _edit_person(self):
        """Редактирует выбранное контактное лицо."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите контактное лицо для редактирования.")
            return
        
        name = self.table.item(row, 0).text()
        position = self.table.item(row, 1).text()
        phone = self.table.item(row, 2).text()
        email = self.table.item(row, 3).text()
        
        # Находим по имени
        persons = self.cp_controller.get_by_counterparty(self.counterparty_id)
        person = next((p for p in persons if p.name == name), None)
        
        if not person:
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(self, "Редактирование", "ФИО:", QLineEdit.EchoMode.Normal, name)
        if not ok:
            return
        
        new_position, _ = QInputDialog.getText(self, "Редактирование", "Должность:", QLineEdit.EchoMode.Normal, position)
        new_phone, _ = QInputDialog.getText(self, "Редактирование", "Телефон:", QLineEdit.EchoMode.Normal, phone)
        new_email, _ = QInputDialog.getText(self, "Редактирование", "Email:", QLineEdit.EchoMode.Normal, email)
        
        try:
            self.cp_controller.update(person.id, {
                "name": new_name.strip(),
                "position": new_position.strip() or None,
                "phone": new_phone.strip() or None,
                "email": new_email.strip() or None
            })
            self.cp_controller.session.commit()
            self._load_data()
            QMessageBox.information(self, "Успех", "Контактное лицо обновлено.")
        except Exception as e:
            self.cp_controller.session.rollback()
            QMessageBox.critical(self, "Ошибка", str(e))

    def _delete_person(self):
        """Удаляет выбранно�� контактное лицо."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите контактное лицо для удаления.")
            return
        
        name = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить контактное лицо '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Находим по имени
            persons = self.cp_controller.get_by_counterparty(self.counterparty_id)
            person = next((p for p in persons if p.name == name), None)
            
            if person:
                try:
                    self.cp_controller.delete(person.id)
                    self.cp_controller.session.commit()
                    self._load_data()
                    QMessageBox.information(self, "Успех", "Контактное лицо удалено.")
                except Exception as e:
                    self.cp_controller.session.rollback()
                    QMessageBox.critical(self, "Ошибка", str(e))

    def refresh(self):
        """Обновляет список."""
        self._load_data()