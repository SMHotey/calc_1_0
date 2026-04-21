"""Генерация коммерческих предложений в PDF и HTML.

Содержит:
- ReportGenerator: класс для генерации отчётов КП
- Функции для экспорта в PDF (reportlab) и HTML (Jinja2)
- Регистрация шрифтов для кириллицы
"""

import os
from datetime import datetime
from typing import Dict, List, Any
from jinja2 import Template
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# Попытка регистрации шрифта для корректного кириллического вывода
def _register_fonts() -> None:
    """Регистрирует TTF шрифты из resources/fonts для корректного отображения кириллицы в PDF.

    Сканирует директорию resources/fonts и регистрирует все найденные .ttf файлы.
    При ошибке регистрации - молча игнорирует (используется fallback шрифт).
    """
    font_path = os.path.join(os.path.dirname(__file__), "../resources/fonts")
    if os.path.isdir(font_path):
        for fname in os.listdir(font_path):
            if fname.endswith(".ttf"):
                try:
                    pdfmetrics.registerFont(TTFont(fname[:-4], os.path.join(font_path, fname)))
                except Exception:
                    pass


_HTML_TEMPLATE: str = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>КП №{{ number }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
        .header { border-bottom: 2px solid #0056b3; padding-bottom: 10px; margin-bottom: 20px; }
        .meta { color: #666; font-size: 0.9em; margin-bottom: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #0056b3; color: white; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        .total { margin-top: 20px; font-size: 1.2em; font-weight: bold; text-align: right; }
        .footer { margin-top: 40px; font-size: 0.8em; color: #888; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Коммерческое предложение № {{ number }}</h2>
    </div>
    <div class="meta">
        <p><strong>Дата:</strong> {{ date }}</p>
        <p><strong>Контрагент:</strong> {{ cp_name }} | {{ cp_inn }}</p>
        {% if notes %}<p><strong>Примечание:</strong> {{ notes }}</p>{% endif %}
    </div>
    <table>
        <thead>
            <tr>
                <th>№</th><th>Изделие</th><th>Тип</th><th>ШхВ (мм)</th><th>Кол</th><th>Цена за ед.</th><th>Итого</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.position }}</td>
                <td>{{ item.product_type }}</td>
                <td>{{ item.subtype }}</td>
                <td>{{ "%.0f"|format(item.width) }} x {{ "%.0f"|format(item.height) }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ "%.2f"|format(item.base_price) }} ₽</td>
                <td><strong>{{ "%.2f"|format(item.final_price) }} ₽</strong></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <div class="total">
        Общая сумма: {{ "%.2f"|format(total_amount) }} ₽
    </div>
    <div class="footer">
        <p>Документ сформирован автоматически системой «МеталлоКальк PRO»</p>
    </div>
</body>
</html>
"""


class ReportGenerator:
    """Генератор отчётов в форматах PDF и HTML."""

    def __init__(self) -> None:
        _register_fonts()
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle("CustomHeader", fontSize=16, textColor=colors.HexColor("#0056b3"), spaceAfter=5))
        self.styles.add(ParagraphStyle("CustomMeta", fontSize=10, textColor=colors.gray, spaceAfter=2))
        self.styles.add(ParagraphStyle("CustomTotal", fontSize=14, alignment=2, textColor=colors.HexColor("#0056b3"),
                                       spaceBefore=15))

    def generate_html(self, offer_data: Dict[str, Any]) -> str:
        """
        Рендерит HTML-шаблон коммерческого предложения.

        :param offer_data: Словарь с данными КП (number, date, cp_name, items, total_amount, notes)
        :return: Строка с HTML-разметкой
        """
        tmpl = Template(_HTML_TEMPLATE)
        return tmpl.render(
            date=offer_data.get("date", datetime.now().strftime("%d.%m.%Y")),
            cp_inn=offer_data.get("cp_inn", ""),
            **offer_data
        )

    def generate_pdf(self, offer_data: Dict[str, Any], output_path: str) -> str:
        """
        Генерирует PDF-файл коммерческого предложения.

        :param offer_data: Данные КП
        :param output_path: Полный путь для сохранения файла
        :return: Путь к сохранённому файлу
        """
        doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
        elements = []

        elements.append(Paragraph(f"Коммерческое предложение № {offer_data['number']}", self.styles["CustomHeader"]))
        elements.append(Paragraph(f"Дата: {offer_data.get('date', '')} | Контрагент: {offer_data['cp_name']}",
                                  self.styles["CustomMeta"]))
        if offer_data.get("notes"):
            elements.append(Paragraph(f"Примечание: {offer_data['notes']}", self.styles["Normal"]))
        elements.append(Spacer(1, 10))

        table_data = [["№", "Изделие", "Тип", "ШхВ", "Кол", "Цена", "Итого"]]
        for it in offer_data["items"]:
            table_data.append([
                str(it["position"]),
                it["product_type"],
                it["subtype"],
                f"{int(it['width'])}x{int(it['height'])}",
                str(it["quantity"]),
                f"{it['base_price']:.2f}",
                f"{it['final_price']:.2f}"
            ])
        table_data.append(["", "", "", "", "", "ИТОГО:", f"{offer_data['total_amount']:.2f}"])

        t = Table(table_data, colWidths=[20, 60, 50, 50, 20, 50, 60])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0056b3")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -2), colors.HexColor("#f8f9fa")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e9ecef")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cccccc")),
        ]))
        elements.append(t)
        elements.append(Paragraph(f"Общая сумма: {offer_data['total_amount']:.2f} ₽", self.styles["CustomTotal"]))

        doc.build(elements)
        return output_path