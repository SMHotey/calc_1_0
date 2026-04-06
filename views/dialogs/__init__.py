"""Пакет модальных диалогов управления данными."""

from views.dialogs.counterparty_dialog import CounterpartyDialog
from views.dialogs.price_list_dialog import PriceListDialog
from views.dialogs.hardware_dialog import HardwareDialog
from views.dialogs.glass_dialog import GlassManagementDialog
from views.dialogs.preset_dialog import PresetManagerDialog
from views.dialogs.report_preview_dialog import ReportPreviewDialog

__all__ = [
    "CounterpartyDialog",
    "PriceListDialog",
    "HardwareDialog",
    "GlassManagementDialog",
    "PresetManagerDialog",
    "ReportPreviewDialog"
]