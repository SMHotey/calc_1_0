"""Виджет управления банковскими реквизитами.

Используется внутри диалога контрагента для отображения и управления банковскими реквизитами.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from controllers.bank_details_controller import BankDetailsController


class BankDetailsWidget(QWidget):
    """Виджет для управления банковскими реквизитами контрагента.

    Показывает таблицу банковских реквизитов с кнопками добавления, редактирования, удаления.
    Используется внутри диалога контрагента для отображения и управления банковскими реквизитами.
    """

    def __init__(
            self,
            bd_controller: "BankDetailsController",
            counterparty_id: Optional[int] = None,
            parent=None
    ):
        super().__init__(parent)
        self.bd_controller = bd_controller
        self.counterparty_id = counterparty_id
        self._init_ui()
        if counterparty_id is not None:
            self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("🏦 Банковские реквизиты"))

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Банк", "БИК", "Корр. счёт", "Расч. счёт", "Осн."])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self._edit_bank_details)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(40)  # Высота строк +40%
        
        # Ширина столбцов
        self.table.setColumnWidth(0, 150)  # Банк
        self.table.setColumnWidth(1, 80)  # БИК
        self.table.setColumnWidth(2, 130) # Корр. счёт
        self.table.setColumnWidth(3, 130) # Расч. счёт
        
        for i in range(5):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Добавить")
        btn_add.clicked.connect(self._add_bank_details)
        btn_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Редакт.")
        btn_edit.clicked.connect(self._edit_bank_details)
        btn_layout.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️ Удалить")
        btn_delete.clicked.connect(self._delete_bank_details)
        btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _load_data(self):
        self.table.setRowCount(0)
        try:
            bank_details = self.bd_controller.get_by_counterparty(self.counterparty_id)
            for bd in bank_details:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Банк
                item_bank = QTableWidgetItem(bd.bank_name or "-")
                item_bank.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item_bank)
                
                # БИК
                item_bik = QTableWidgetItem(bd.bik or "-")
                item_bik.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 1, item_bik)
                
                # Корр. счёт
                item_corr = QTableWidgetItem(bd.correspondent_account or "-")
                item_corr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 2, item_corr)
                
                # Расч. счёт
                item_sett = QTableWidgetItem(bd.settlement_account or "-")
                item_sett.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 3, item_sett)
                
                # Основной
                item_default = QTableWidgetItem("✓" if bd.is_default else "-")
                item_default.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, item_default)
                
                # Сохраняем ID
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, bd.id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить банковские реквизиты:\n{e}")

    def _add_bank_details(self):
        """Добавляет новые банковские реквизиты."""
        from views.dialogs.bank_details_dialog import BankDetailsDialog
        
        dlg = BankDetailsDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            valid, error = dlg.validate()
            if not valid:
                QMessageBox.warning(self, "Ошибка", error)
                return
            
            try:
                self.bd_controller.create(
                    counterparty_id=self.counterparty_id,
                    bank_name=data["bank_name"],
                    bik=data["bik"],
                    correspondent_account=data["correspondent_account"],
                    settlement_account=data["settlement_account"],
                    is_default=data["is_default"],
                    notes=data["notes"]
                )
                self.bd_controller.session.commit()
                self._load_data()
                QMessageBox.information(self, "Успех", "Банковские реквизиты добавлены.")
            except Exception as e:
                self.bd_controller.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def _edit_bank_details(self, item=None):
        """Редактирует выбранные банковские реквизиты."""
        from views.dialogs.bank_details_dialog import BankDetailsDialog
        
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите реквизиты для редактирования.")
            return
        
        bd_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not bd_id:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить ID записи.")
            return
        
        bd = self.bd_controller.get_by_id(bd_id)
        if not bd:
            return
        
        dlg = BankDetailsDialog(
            bank_name=bd.bank_name or "",
            bik=bd.bik or "",
            correspondent_account=bd.correspondent_account or "",
            settlement_account=bd.settlement_account or "",
            is_default=bd.is_default,
            notes=bd.notes or "",
            parent=self
        )
        if dlg.exec():
            data = dlg.get_data()
            valid, error = dlg.validate()
            if not valid:
                QMessageBox.warning(self, "Ошибка", error)
                return
            
            try:
                self.bd_controller.update(bd_id, data)
                self.bd_controller.session.commit()
                self._load_data()
                QMessageBox.information(self, "Успех", "Банковские реквизиты обновлены.")
            except Exception as e:
                self.bd_controller.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def _delete_bank_details(self):
        """Удаляет выбранные банковские реквизиты."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите реквизиты для удаления.")
            return
        
        # Получаем ID
        bd_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not bd_id:
            bank_name = self.table.item(row, 0).text()
            bik = self.table.item(row, 1).text()
            all_details = self.bd_controller.get_by_counterparty(self.counterparty_id)
            bd = next((b for b in all_details if b.bank_name == bank_name and b.bik == bik), None)
            if bd:
                bd_id = bd.id
            else:
                return
        
        if not bd_id:
            return
        
        bank_name = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить банковские реквизиты '{bank_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.bd_controller.delete(bd_id)
                self.bd_controller.session.commit()
                self._load_data()
                QMessageBox.information(self, "Успех", "Банковские реквизиты удалены.")
            except Exception as e:
                self.bd_controller.session.rollback()
                QMessageBox.critical(self, "Ошибка", str(e))

    def refresh(self):
        """Обновляет список."""
        self._load_data()