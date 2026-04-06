"""Диалог управления персонализированными прайс-листами."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox,
    QPushButton, QMessageBox, QLabel, QScrollArea, QGroupBox
)
from PyQt6.QtCore import Qt
from typing import Optional
from controllers.price_list_controller import PriceListController


class PriceListDialog(QDialog):
    """
    Диалог создания/редактирования персонализированного прайс-листа.
    Копирует значения из базового прайса при создании.
    """

    def __init__(self, controller: PriceListController, pl_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.pl_id = pl_id
        self.editing = pl_id is not None
        self.setWindowTitle("Редактирование прайс-листа" if self.editing else "Новый персонализированный прайс")
        self.resize(450, 600)
        self._init_ui()
        if self.editing:
            self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QGroupBox()
        form = QFormLayout(container)

        self.inp_name = QLineEdit()
        form.addRow("Название:", self.inp_name)

        self.spin_doors_std = QDoubleSpinBox();
        self.spin_doors_std.setRange(0, 1e9);
        self.spin_doors_std.setPrefix("₽ ")
        form.addRow("Дверь стандарт. (ед.):", self.spin_doors_std)

        self.spin_doors_nonstd = QDoubleSpinBox();
        self.spin_doors_nonstd.setRange(0, 1e9);
        self.spin_doors_nonstd.setPrefix("₽/м² ")
        form.addRow("Дверь нестандарт. (м²):", self.spin_doors_nonstd)

        self.spin_doors_wide = QDoubleSpinBox();
        self.spin_doors_wide.setRange(0, 1e9);
        self.spin_doors_wide.setPrefix("₽ ")
        form.addRow("Наценка за ширину:", self.spin_doors_wide)

        self.spin_cutout = QDoubleSpinBox();
        self.spin_cutout.setRange(0, 1e9);
        self.spin_cutout.setPrefix("₽ ")
        form.addRow("Вырез под стекло/решётку:", self.spin_cutout)

        self.spin_transom_min = QDoubleSpinBox();
        self.spin_transom_min.setRange(0, 1e9);
        self.spin_transom_min.setPrefix("₽ ")
        form.addRow("Мин. цена фрамуги:", self.spin_transom_min)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_layout = QVBoxLayout()
        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("❌ Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _load_data(self):
        # Загрузка данных упрощена: в проде используется прямой запрос к PersonalizedPriceList
        # Здесь заполняем демо-значениями или из контроллера
        pl = self.controller.personal_repo.get_by_id(self.pl_id)
        if pl:
            self.inp_name.setText(pl.name or "")
            self.spin_doors_std.setValue(pl.custom_doors_price_std_single or 0)
            self.spin_doors_nonstd.setValue(pl.custom_doors_price_per_m2_nonstd or 0)
            self.spin_doors_wide.setValue(pl.custom_doors_wide_markup or 0)
            self.spin_cutout.setValue(pl.custom_cutout_price or 0)
        else:
            # Если новый - берём базу
            base = self.controller.get_base_price_list()
            self.inp_name.setText(f"Копия {base.name}")
            self.spin_doors_std.setValue(base.doors_price_std_single or 0)
            self.spin_doors_nonstd.setValue(base.doors_price_per_m2_nonstd or 0)
            self.spin_doors_wide.setValue(base.doors_wide_markup or 0)
            self.spin_cutout.setValue(base.cutout_price or 0)

    def _save(self):
        if not self.inp_name.text().strip():
            return QMessageBox.warning(self, "Ошибка", "Укажите название прайс-листа.")

        data = {
            "name": self.inp_name.text().strip(),
            "custom_doors_price_std_single": self.spin_doors_std.value(),
            "custom_doors_price_per_m2_nonstd": self.spin_doors_nonstd.value(),
            "custom_doors_wide_markup": self.spin_doors_wide.value(),
            "custom_cutout_price": self.spin_cutout.value()
        }

        try:
            if self.editing:
                self.controller.update_personalized(self.pl_id, data)
            else:
                self.controller.create_personalized(name=data["name"])
            QMessageBox.information(self, "Успех", "Прайс-лист сохранён.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))