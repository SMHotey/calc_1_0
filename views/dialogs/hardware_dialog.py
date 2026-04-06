"""Диалог управления фурнитурой (замки, ручки, цилиндры, доводчики)."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QComboBox, QLineEdit, QDoubleSpinBox,
    QCheckBox, QPushButton, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from typing import Optional
from controllers.hardware_controller import HardwareController
from constants import HardwareType
import os


class HardwareDialog(QDialog):
    """CRUD-диалог для добавления/редактирования элементов фурнитуры."""

    def __init__(self, controller: HardwareController, price_list_id: int, hw_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.price_list_id = price_list_id
        self.hw_id = hw_id
        self.editing = hw_id is not None
        self.setWindowTitle("Фурнитура: редактирование" if self.editing else "Добавить фурнитуру")
        self.resize(450, 400)
        self._init_ui()
        if self.editing:
            self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_type = QComboBox()
        for t in HardwareType:
            self.combo_type.addItem(t.value, t.value)
        form.addRow("Тип:", self.combo_type)

        self.inp_name = QLineEdit();
        self.inp_name.setPlaceholderText("Модель/Название")
        form.addRow("Название:", self.inp_name)

        self.spin_price = QDoubleSpinBox();
        self.spin_price.setRange(0, 1e6);
        self.spin_price.setPrefix("₽ ")
        form.addRow("Цена:", self.spin_price)

        self.inp_desc = QLineEdit();
        self.inp_desc.setPlaceholderText("Описание, характеристики")
        form.addRow("Описание:", self.inp_desc)

        self.inp_img = QLineEdit()
        self.inp_img.setReadOnly(True)
        btn_browse = QPushButton("📁 Выбрать фото")
        btn_browse.clicked.connect(self._browse_image)
        img_layout = QHBoxLayout()
        img_layout.addWidget(self.inp_img)
        img_layout.addWidget(btn_browse)
        form.addRow("Изображение:", img_layout)

        self.chk_cylinder = QCheckBox("Требует цилиндровый механизм")
        form.addRow("Флаг:", self.chk_cylinder)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("❌ Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.inp_img.setText(path)

    def _load_data(self):
        hw = self.controller.get_by_id(self.hw_id)
        if hw:
            idx = self.combo_type.findData(hw.type)
            if idx >= 0: self.combo_type.setCurrentIndex(idx)
            self.inp_name.setText(hw.name)
            self.spin_price.setValue(hw.price)
            self.inp_desc.setText(hw.description or "")
            self.inp_img.setText(hw.image_path or "")
            self.chk_cylinder.setChecked(hw.has_cylinder)

    def _save(self):
        if not self.inp_name.text().strip():
            return QMessageBox.warning(self, "Ошибка", "Укажите название фурнитуры.")

        img_path = self.inp_img.text().strip()
        if img_path and not os.path.isfile(img_path):
            return QMessageBox.warning(self, "Ошибка", "Указанный файл изображения не найден.")

        rel_path = os.path.relpath(img_path, "resources/images") if img_path else None

        try:
            data = {
                "hw_type": self.combo_type.currentData(),
                "name": self.inp_name.text().strip(),
                "price": self.spin_price.value(),
                "description": self.inp_desc.text().strip() or None,
                "image_path": rel_path,
                "has_cylinder": self.chk_cylinder.isChecked(),
                "price_list_id": self.price_list_id
            }
            if self.editing:
                self.controller.update(self.hw_id, {k: v for k, v in data.items() if k != "hw_type"})
            else:
                self.controller.create(**data)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))