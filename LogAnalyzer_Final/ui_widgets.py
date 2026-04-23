from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui_constants import (
    _ENTRY_COLUMNS,
    _LEVEL_COLORS,
    _SAMPLE_ENTRIES,
    _SAMPLE_FLAGGED,
)
from ui_helpers import (
    _extract_http_status_category,
    _extract_level_from_message,
    _extract_timestamp_from_message,
)


def _make_entries_table() -> QTableWidget:
    table = QTableWidget(0, len(_ENTRY_COLUMNS))
    table.setHorizontalHeaderLabels(_ENTRY_COLUMNS)

    header_font = table.horizontalHeader().font()
    header_font.setPointSize(11)
    table.horizontalHeader().setFont(header_font)

    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
    table.verticalHeader().setVisible(False)

    table.verticalHeader().setDefaultSectionSize(28)

    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    return table


def _make_sample_table(entries: list[dict], banner_color: str = "#89b4fa") -> QWidget:
    wrapper = QWidget()
    layout = QVBoxLayout(wrapper)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    banner = QLabel("SAMPLE DATA : load a file with ERROR/CRITICAL entries to see real entries")
    banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
    banner.setStyleSheet(
        f"background-color: #252535;"
        f"color: {banner_color};"
        f"border: 1px dashed {banner_color};"
        f"border-radius: 4px;"
        f"padding: 4px 10px;"
        f"font-size: 9pt;"
        f"font-style: italic;"
    )
    layout.addWidget(banner)

    table = _make_entries_table()
    table.setRowCount(0)
    for row_idx, entry in enumerate(entries):
        table.insertRow(row_idx)
        level = (entry.get("level") or "").upper()
        base_color = _LEVEL_COLORS.get(level)
        cols = [
            str(entry.get("timestamp") or ""),
            str(entry.get("level") or ""),
            entry.get("message", "") or "",
            entry.get("source_file", "") or "",
            str(entry.get("line_number", "") or ""),
        ]
        for col_idx, text in enumerate(cols):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setForeground(QColor("#6c7086"))
            if base_color:
                dim = QColor(base_color)
                dim.setAlpha(80)
                item.setBackground(dim)
            table.setItem(row_idx, col_idx, item)
    layout.addWidget(table)
    return wrapper


def _populate_table(table: QTableWidget, entries: list[dict]) -> None:
    table.setRowCount(0)
    for row_idx, entry in enumerate(entries):
        table.insertRow(row_idx)

        timestamp = entry.get("timestamp")
        if not timestamp:
            timestamp = _extract_timestamp_from_message(entry.get("message", ""), None)

        level = (entry.get("level") or "").upper()
        if not level or level in ("UNKNOWN", "PARSE_ERROR"):
            extracted = _extract_level_from_message(entry.get("message", ""), level)
            if extracted:
                level = extracted.upper()

        color = _LEVEL_COLORS.get(level)

        # if no level found, try to detect HTTP status category and use that as level for coloring
        if not level or level in ("UNKNOWN", "PARSE_ERROR", ""):
            status = _extract_http_status_category(entry.get("message", ""))
            if status:
                level = status  # use status code category (200, 300, 400, 500) as level
                color = _LEVEL_COLORS.get(status)

        cols = [
            str(timestamp or ""),
            str(level or ""),
            entry.get("message", "") or "",
            entry.get("source_file", "") or "",
            str(entry.get("line_number", "") or ""),
        ]
        for col_idx, text in enumerate(cols):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if color:
                item.setBackground(color)
            font = item.font()
            font.setPointSize(11)
            item.setFont(font)
            table.setItem(row_idx, col_idx, item)


def _chart_card(title: str, canvas: object) -> QFrame:
    card = QFrame()
    card.setObjectName("ChartCard")
    card.setStyleSheet(
        "QFrame#ChartCard {"
        "  background-color: #252535;"
        "  border: 1px solid #313244;"
        "  border-radius: 6px;"
        "}"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(10, 8, 10, 6)
    layout.setSpacing(4)
    lbl = QLabel(title)
    lbl.setStyleSheet(
        "color: #89b4fa; font-size: 10pt; font-weight: bold;"
        "background: transparent; border: none;"
    )
    layout.addWidget(lbl)
    layout.addWidget(canvas)
    return card


class _StatCard(QFrame):

    def __init__(self, title: str, value: str = "—", accent: str = "#89b4fa") -> None:
        super().__init__()
        self._accent = accent
        self.setObjectName("StatCard")
        self.setStyleSheet(
            f"QFrame#StatCard {{"
            f"  background-color: #252535;"
            f"  border: 1px solid #313244;"
            f"  border-left: 4px solid {accent};"
            f"  border-radius: 6px;"
            f"  padding: 4px;"
            f"}}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet("color: #a6adc8; font-size: 10pt;")
        layout.addWidget(self._title_lbl)

        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(f"color: {accent}; font-size: 18pt; font-weight: bold;")
        layout.addWidget(self._value_lbl)

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(value)
