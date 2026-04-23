from PyQt6.QtGui import QColor

_LEVEL_COLORS: dict[str, QColor] = {
    "CRITICAL": QColor("#4d0000"),
    "ERROR":    QColor("#3d1515"),
    "WARNING":  QColor("#3d3200"),
    "WARN":     QColor("#3d3200"),
    "DEBUG":    QColor("#202035"),
    "200":      QColor("#1a3a1a"),
    "300":      QColor("#1a2a3a"),
    "400":      QColor("#3a2d1a"),
    "500":      QColor("#3d1520"),
}

# table row colors but with some transparency
_LEVEL_TABLE_COLORS: dict[str, QColor] = {
    "INFO":     QColor(137, 180, 250, 80), 
    "ERROR":    QColor(243, 139, 168, 80), 
    "CRITICAL": QColor(230, 69, 83, 100),  
    "WARNING":  QColor(250, 179, 135, 80), 
    "WARN":     QColor(250, 179, 135, 80), 
    "DEBUG":    QColor(166, 173, 200, 70), 
    "UNKNOWN":  QColor(88, 91, 112, 60),   
    "200":      QColor(166, 227, 161, 80), 
    "300":      QColor(137, 180, 250, 80), 
    "400":      QColor(250, 179, 135, 80), 
    "500":      QColor(243, 139, 168, 80), 
}

_ENTRY_COLUMNS = ["Timestamp", "Level", "Message", "Source File", "Line #"]
_ENTRY_KEYS    = ["timestamp", "level", "message", "source_file", "line_number"]

_LEVEL_CHART_COLORS: dict[str, str] = {
    "INFO":     "#89b4fa",
    "ERROR":    "#f38ba8",
    "CRITICAL": "#e64553",
    "WARNING":  "#fab387",
    "WARN":     "#fab387",
    "DEBUG":    "#a6adc8",
    "UNKNOWN":  "#585b70",
    "200":      "#a6e3a1",
    "300":      "#89b4fa",
    "400":      "#fab387",
    "500":      "#f38ba8",
}

# chart theme
_CHART_BG     = "#181825"
_CHART_AX_BG  = "#1e1e2e"
_CHART_TEXT   = "#cdd6f4"
_CHART_MUTED  = "#a6adc8"
_CHART_GRID   = "#313244"
_CHART_GHOST  = "#45475a"

# app styling
_DARK_STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QToolBar {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    spacing: 8px;
    padding: 6px 10px;
}
QToolBar::separator {
    background-color: #45475a;
    width: 1px;
    margin: 4px 6px;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 6px 16px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #89b4fa;
}
QPushButton:pressed  { background-color: #585b70; }
QPushButton:disabled {
    background-color: #1e1e2e;
    color: #45475a;
    border-color: #313244;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 5px 10px;
    min-height: 28px;
}
QComboBox:hover        { border-color: #89b4fa; }
QComboBox::drop-down   { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
    border: 1px solid #45475a;
    outline: none;
}
QLineEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 5px;
    padding: 5px 10px;
    min-height: 28px;
}
QLineEdit:focus    { border-color: #89b4fa; }
QLineEdit:disabled {
    background-color: #1e1e2e;
    color: #45475a;
    border-color: #313244;
}
QTableWidget {
    background-color: #181825;
    color: #cdd6f4;
    gridline-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    selection-background-color: #304060;
    selection-color: #cdd6f4;
    alternate-background-color: #1e1e35;
}
QTableWidget::item         { padding: 5px 8px; }
QTableWidget::item:selected {
    background-color: #304060;
    color: #cdd6f4;
}
QHeaderView::section {
    background-color: #252535;
    color: #89b4fa;
    border: none;
    border-right: 1px solid #45475a;
    border-bottom: 1px solid #45475a;
    padding: 7px 10px;
    font-weight: bold;
}
QTabWidget::pane {
    border: 1px solid #45475a;
    border-top: none;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #181825;
    color: #a6adc8;
    border: 1px solid #45475a;
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border-bottom: 2px solid #89b4fa;
}
QTabBar::tab:hover:!selected {
    background-color: #252535;
    color: #cdd6f4;
}
QListWidget {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px;
}
QListWidget::item {
    padding: 5px 8px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #313244;
    color: #89b4fa;
}
QListWidget::item:hover { background-color: #252535; }
QPlainTextEdit {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px;
}
QStatusBar {
    background-color: #181825;
    color: #89b4fa;
    border-top: 1px solid #313244;
    padding: 2px 8px;
}
QScrollBar:vertical {
    background-color: #1e1e2e;
    width: 10px;
    border: none;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background-color: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background-color: #1e1e2e;
    height: 10px;
    border: none;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover { background-color: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QSplitter::handle           { background-color: #313244; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:hover      { background-color: #89b4fa; }
QLabel {
    color: #cdd6f4;
    background: transparent;
}
QMessageBox             { background-color: #1e1e2e; }
QMessageBox QLabel      { color: #cdd6f4; }
"""

# sample/placeholder data shown before files are loaded
# or if no ERROR/CRITICAL entries are found
_SAMPLE_ENTRIES: list[dict] = [
    {"timestamp": "2026-04-10 08:01:22", "level": "INFO",     "message": "Service initialized successfully",            "source_file": "app.log",    "line_number": 1},
    {"timestamp": "2026-04-10 08:03:45", "level": "INFO",     "message": "User frank logged in from 192.168.1.10",        "source_file": "app.log",    "line_number": 4},
    {"timestamp": "2026-04-10 08:07:11", "level": "WARNING",  "message": "High memory usage detected: 87%",              "source_file": "system.log", "line_number": 9},
    {"timestamp": "2026-04-10 08:12:03", "level": "ERROR",    "message": "Failed to connect to database after 3 retries",  "source_file": "app.log",    "line_number": 17},
    {"timestamp": "2026-04-10 08:14:55", "level": "INFO",     "message": "Background worker thread started",              "source_file": "worker.log", "line_number": 2},
    {"timestamp": "2026-04-10 08:19:30", "level": "DEBUG",    "message": "Cache miss for key user_session_8821",           "source_file": "cache.log",  "line_number": 33},
    {"timestamp": "2026-04-10 08:22:14", "level": "WARNING",  "message": "Slow query detected (1420ms): SELECT * FROM orders", "source_file": "db.log",   "line_number": 88},
    {"timestamp": "2026-04-10 08:25:00", "level": "ERROR",    "message": "Request timeout after 30s on /api/inventory",    "source_file": "app.log",    "line_number": 41},
    {"timestamp": "2026-04-10 08:31:07", "level": "CRITICAL", "message": "Exception in processing pipeline: NullPointerError", "source_file": "app.log", "line_number": 56},
    {"timestamp": "2026-04-10 08:35:42", "level": "INFO",     "message": "Scheduled maintenance job completed",            "source_file": "cron.log",   "line_number": 7},
]

_SAMPLE_FLAGGED: list[dict] = [
    {"timestamp": "2026-04-10 08:12:03", "level": "ERROR",    "message": "Failed to connect to database after 3 retries",     "source_file": "app.log", "line_number": 17},
    {"timestamp": "2026-04-10 08:25:00", "level": "ERROR",    "message": "Request timeout after 30s on /api/inventory",       "source_file": "app.log", "line_number": 41},
    {"timestamp": "2026-04-10 08:31:07", "level": "CRITICAL", "message": "Exception in processing pipeline: NullPointerError", "source_file": "app.log", "line_number": 56},
]
