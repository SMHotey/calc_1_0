"""Диалог детализации позиции в коммерческом предложении."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGroupBox, QPushButton, QTableWidget, 
    QTableWidgetItem, QScrollArea, QWidget, QHeaderView
)
from PyQt6.QtCore import Qt

logger = logging.getLogger('item_details_dialog')


class ItemDetailsDialog(QDialog):
    """Модальное окно для отображения полной детализации позиции КП.
    
    Показывает:
    - Основную информацию (тип, размеры, количество)
    - Таблицу комплектации с ценами
    - Базовая стоимость = стоимость изделия БЕЗ дополнительных опций
    - Все опции расписываются построчно с ценами
    """

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.setWindowTitle("Детализация позиции")
        self.resize(600, 500)
        
        logger.info(f"=== ItemDetailsDialog created ===")
        logger.info(f"item_data keys: {list(item_data.keys())}")
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # === Основная информация ===
        product_type = self.item_data.get('product_type', '-')
        subtype = self.item_data.get('subtype', '')
        width = self.item_data.get('width', 0)
        height = self.item_data.get('height', 0)
        quantity = self.item_data.get('quantity', 1)
        
        product_desc = f"{product_type} {subtype}" if subtype else product_type
        
        self._add_info_section(scroll_layout, "Основное", [
            f"Изделие: {product_desc}",
            f"Размеры: {int(width)} x {int(height)} мм",
            f"Количество: {quantity} шт.",
        ])
        
        # === Базовая стоимость (без опций) ===
        final_price = self.item_data.get('final_price', 0)
        extras = self.item_data.get('extras_breakdown', [])
        
        # Вычисляем базовую стоимость
        options_sum = sum(e.get('price', 0) for e in extras)
        base_price = final_price - options_sum
        if base_price < 0:
            base_price = 0
        
        # === Таблица опций ===
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Опция", "Стоимость, руб."])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.setMinimumHeight(200)
        table.verticalHeader().setDefaultSectionSize(40)  # Высота строк +40%
        
        # Базовая стоимость
        table.insertRow(0)
        table.setItem(0, 0, QTableWidgetItem("Базовая стоимость (изделие без опций)"))
        table.item(0, 0).setTextAlignment(Qt.AlignmentFlag.AlignLeft)
        base_item = QTableWidgetItem(f"{base_price:,.2f}")
        base_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
        table.setItem(0, 1, base_item)
        
        # Опции
        row = 1
        for extra in extras:
            name = str(extra.get('name', ''))
            price = extra.get('price', 0)
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(name))
            table.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            price_item = QTableWidgetItem(f"{price:,.2f}" if price > 0 else "0.00")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            table.setItem(row, 1, price_item)
            row += 1
        
        # Наценка
        markup_pct = self.item_data.get('markup_percent', 0)
        markup_abs = self.item_data.get('markup_abs', 0)
        if markup_pct > 0 or markup_abs > 0:
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(f"Наценка {markup_pct}%"))
            table.item(row, 0).setTextAlignment(Qt.AlignmentFlag.AlignLeft)
            markup_item = QTableWidgetItem(f"{markup_abs:,.2f}")
            markup_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            table.setItem(row, 1, markup_item)
        
        scroll_layout.addWidget(table)
        
        # === Итог ===
        total_label = QLabel(f"Итого: {final_price:,.2f} руб. x {quantity} шт. = {final_price * quantity:,.2f} руб.")
        total_label.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 10px;")
        scroll_layout.addWidget(total_label)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # === Кнопка закрытия ===
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def _add_info_section(self, layout, title: str, lines: list):
        """Добавляет секцию с заголовком и списком строк."""
        group = QGroupBox(title)
        group_layout = QVBoxLayout()
        for line in lines:
            label = QLabel(line)
            label.setWordWrap(True)
            group_layout.addWidget(label)
        group.setLayout(group_layout)
        layout.addWidget(group)