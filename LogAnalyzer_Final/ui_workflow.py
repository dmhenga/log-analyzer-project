from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

from parsing_searching import LogManager, QuerySpec, SearchEngine, SortSpec
from analytics_reporting import AnalyticsEngine, ReportBuilder, HtmlExporter, CsvExporter


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Log Analyzer & Report Generator (LARG)")
        self.resize(1200, 750)

        self.log_manager = LogManager()
        self.search_engine = SearchEngine()
        self.analytics_engine = AnalyticsEngine()
        self.report_builder = ReportBuilder()

        self.all_entries = []
        self.current_entries = []
        self.loaded_files: List[str] = []

        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        layout.addWidget(self._build_file_controls())
        layout.addWidget(self._build_filter_controls())
        layout.addWidget(self._build_results_table())
        layout.addWidget(self._build_summary_box())

    def _build_file_controls(self) -> QGroupBox:
        box = QGroupBox("File Ingestion / Parsing")
        layout = QGridLayout(box)

        self.btn_select_files = QPushButton("Select Log Files")
        self.btn_select_folder = QPushButton("Select Folder")

        self.parse_mode_combo = QComboBox()
        self.parse_mode_combo.addItems(["template", "generic", "regex"])

        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText(
            r"Optional regex with named groups: (?P<timestamp>...)(?P<level>...)(?P<message>...)"
        )

        layout.addWidget(QLabel("Parse Mode:"), 0, 0)
        layout.addWidget(self.parse_mode_combo, 0, 1)
        layout.addWidget(self.btn_select_files, 0, 2)
        layout.addWidget(self.btn_select_folder, 0, 3)

        layout.addWidget(QLabel("Regex Pattern:"), 1, 0)
        layout.addWidget(self.regex_input, 1, 1, 1, 3)

        self.btn_select_files.clicked.connect(self.select_files)
        self.btn_select_folder.clicked.connect(self.select_folder)

        return box

    def _build_filter_controls(self) -> QGroupBox:
        box = QGroupBox("Search / Filter / Sort")
        layout = QGridLayout(box)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Keyword in message")

        self.exclude_input = QLineEdit()
        self.exclude_input.setPlaceholderText("Exclude keyword")

        self.level_combo = QComboBox()
        self.level_combo.addItems(["", "INFO", "WARN", "WARNING", "ERROR", "DEBUG", "CRITICAL"])

        self.start_date_input = QLineEdit()
        self.start_date_input.setPlaceholderText("Start date YYYY-MM-DD")

        self.end_date_input = QLineEdit()
        self.end_date_input.setPlaceholderText("End date YYYY-MM-DD")

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["timestamp", "level", "message", "source_file"])

        self.desc_checkbox = QCheckBox("Descending")

        self.btn_apply_filters = QPushButton("Apply Filters")
        self.btn_reset_filters = QPushButton("Reset")
        self.btn_export_html = QPushButton("Export HTML")
        self.btn_export_csv = QPushButton("Export CSV")

        layout.addWidget(QLabel("Keyword:"), 0, 0)
        layout.addWidget(self.keyword_input, 0, 1)
        layout.addWidget(QLabel("Exclude:"), 0, 2)
        layout.addWidget(self.exclude_input, 0, 3)

        layout.addWidget(QLabel("Level:"), 1, 0)
        layout.addWidget(self.level_combo, 1, 1)
        layout.addWidget(QLabel("Start Date:"), 1, 2)
        layout.addWidget(self.start_date_input, 1, 3)

        layout.addWidget(QLabel("End Date:"), 2, 0)
        layout.addWidget(self.end_date_input, 2, 1)
        layout.addWidget(QLabel("Sort By:"), 2, 2)
        layout.addWidget(self.sort_combo, 2, 3)

        button_row = QHBoxLayout()
        button_row.addWidget(self.desc_checkbox)
        button_row.addWidget(self.btn_apply_filters)
        button_row.addWidget(self.btn_reset_filters)
        button_row.addStretch()
        button_row.addWidget(self.btn_export_html)
        button_row.addWidget(self.btn_export_csv)

        layout.addLayout(button_row, 3, 0, 1, 4)

        self.btn_apply_filters.clicked.connect(self.apply_filters)
        self.btn_reset_filters.clicked.connect(self.reset_filters)
        self.btn_export_html.clicked.connect(self.export_html)
        self.btn_export_csv.clicked.connect(self.export_csv)

        return box

    def _build_results_table(self) -> QGroupBox:
        box = QGroupBox("Log Entries")
        layout = QVBoxLayout(box)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Timestamp", "Level", "Message", "Source File", "Line #"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)
        return box

    def _build_summary_box(self) -> QGroupBox:
        box = QGroupBox("Summary / Analytics")
        layout = QVBoxLayout(box)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)

        layout.addWidget(self.summary_text)
        return box

    def select_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Log Files",
            "",
            "Log Files (*.log *.txt);;All Files (*.*)",
        )
        if not paths:
            return
        self._load_entries(paths)

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        folder_path = Path(folder)
        paths = [
            str(p) for p in folder_path.iterdir()
            if p.is_file() and p.suffix.lower() in {".log", ".txt"}
        ]
        if not paths:
            QMessageBox.information(self, "No Files", "No .log or .txt files found in selected folder.")
            return

        self._load_entries(paths)

    def _load_entries(self, file_paths: List[str]) -> None:
        mode = self.parse_mode_combo.currentText().strip().lower()
        regex = self.regex_input.text().strip() or None

        try:
            self.loaded_files = file_paths
            self.all_entries = self.log_manager.parse_files(
                file_paths=file_paths,
                mode=mode,
                regex_pattern=regex,
            )
            self.current_entries = list(self.all_entries)
            self._refresh_view()
        except Exception as exc:
            QMessageBox.critical(self, "Load Error", f"Failed to load files:\n{exc}")

    def apply_filters(self) -> None:
        try:
            query = QuerySpec(
                keyword=self.keyword_input.text().strip() or None,
                exclude_keyword=self.exclude_input.text().strip() or None,
                level=self.level_combo.currentText().strip() or None,
                start_date=self.start_date_input.text().strip() or None,
                end_date=self.end_date_input.text().strip() or None,
            )
            sort_spec = SortSpec(
                key=self.sort_combo.currentText().strip(),
                reverse=self.desc_checkbox.isChecked(),
            )

            filtered = self.search_engine.search_logs(self.all_entries, query)
            self.current_entries = self.search_engine.sort_logs(filtered, sort_spec)
            self._refresh_view()
        except ValueError:
            QMessageBox.warning(self, "Invalid Date", "Please use YYYY-MM-DD for date filters.")

    def reset_filters(self) -> None:
        self.keyword_input.clear()
        self.exclude_input.clear()
        self.level_combo.setCurrentIndex(0)
        self.start_date_input.clear()
        self.end_date_input.clear()
        self.sort_combo.setCurrentText("timestamp")
        self.desc_checkbox.setChecked(False)

        self.current_entries = list(self.all_entries)
        self._refresh_view()

    def _refresh_view(self) -> None:
        self._populate_table(self.current_entries)

        summary = self.analytics_engine.summarize(self.current_entries)
        top_lines = self.analytics_engine.top_messages(self.current_entries, top_n=5)
        flagged = self.analytics_engine.flag_entries(self.current_entries)

        report_text = self.report_builder.render_summary_text(
            summary=summary,
            top_messages=top_lines,
            flagged_entries=flagged,
            file_count=len(self.loaded_files),
        )
        self.summary_text.setPlainText(report_text)

    def _populate_table(self, entries: list[dict]) -> None:
        self.table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            values = [
                entry.get("timestamp") or "",
                entry.get("level") or "",
                entry.get("message") or "",
                entry.get("source_file") or "",
                str(entry.get("line_number", "")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col in (0, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, col, item)

    def export_html(self) -> None:
        if not self.current_entries:
            QMessageBox.information(self, "No Data", "There are no entries to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML Report",
            "larg_report.html",
            "HTML Files (*.html)",
        )
        if not path:
            return

        summary = self.analytics_engine.summarize(self.current_entries)
        top_lines = self.analytics_engine.top_messages(self.current_entries, top_n=10)
        flagged = self.analytics_engine.flag_entries(self.current_entries)

        report = self.report_builder.build_report(
            entries=self.current_entries,
            summary=summary,
            top_messages=top_lines,
            flagged_entries=flagged,
            loaded_files=self.loaded_files,
        )
        HtmlExporter().export(report, path)
        QMessageBox.information(self, "Export Complete", "HTML report exported successfully.")

    def export_csv(self) -> None:
        if not self.current_entries:
            QMessageBox.information(self, "No Data", "There are no entries to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            "larg_results.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        CsvExporter().export(self.current_entries, path)
        QMessageBox.information(self, "Export Complete", "CSV export completed successfully.")


def run_app() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
