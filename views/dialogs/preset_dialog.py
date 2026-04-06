"""Диалог управления наборами опций (пресетами)."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional, Dict, Any
from controllers.preset_controller import PresetController


class PresetManagerDialog(QDialog):
    """
    Диалог сохранения, загрузки и управления пресетами.
    """
    preset_applied = pyqtSignal(dict)

    def __init__(self, controller: PresetController, price_list_id: int, current_config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.controller = controller
        self.price_list_id = price_list_id
        self.current_config = current_config
        self.setWindowTitle("Управление наборами опций")
        self.resize(400, 350)
        self._init_ui()
        self._load_presets()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.list_presets = QListWidget()
        layout.addWidget(self.list_presets)

        form_layout = QHBoxLayout()
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Название нового набора")
        self.btn_save = QPushButton("💾 Сохранить текущий")
        self.btn_save.clicked.connect(self._save_preset)
        form_layout.addWidget(self.inp_name)
        form_layout.addWidget(self.btn_save)
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton("✅ Применить выбранный")
        self.btn_apply.clicked.connect(self._apply_preset)
        self.btn_delete = QPushButton("🗑️ Удалить")
        self.btn_delete.clicked.connect(self._delete_preset)
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _load_presets(self):
        self.list_presets.clear()
        presets = self.controller.get_presets_for_price_list(self.price_list_id)
        for p in presets:
            self.list_presets.addItem(
                QListWidgetItem(p["name"]).setData(Qt.ItemDataRole.UserRole, p["id"]) or QListWidgetItem(p["name"]))

    def _get_selected_id(self) -> Optional[int]:
        items = self.list_presets.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def _save_preset(self):
        name = self.inp_name.text().strip()
        if not name:
            return QMessageBox.warning(self, "Ошибка", "Введите название пресета.")
        try:
            self.controller.create_preset(name, self.price_list_id, self.current_config)
            self._load_presets()
            QMessageBox.information(self, "Успех", f"Набор '{name}' сохранён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _apply_preset(self):
        preset_id = self._get_selected_id()
        if preset_id is None:
            return QMessageBox.warning(self, "Ошибка", "Выберите пресет для применения.")
        try:
            new_config = self.controller.apply_preset(preset_id, self.current_config)
            self.preset_applied.emit(new_config)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка применения", str(e))

    def _delete_preset(self):
        preset_id = self._get_selected_id()
        if preset_id is None: return
        if QMessageBox.question(self, "Удаление", "Удалить выбранный набор?") == QMessageBox.StandardButton.Yes:
            self.controller.delete_preset(preset_id)
            self._load_presets()