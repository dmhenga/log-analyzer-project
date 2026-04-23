import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analytics_reporting import (
    AnalyticsEngine,
    CsvExporter,
    HtmlExporter,
    ReportBuilder,
)

from parsing_searching import LogManager, QuerySpec, SearchEngine, SortSpec

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ui_constants import (
    _CHART_AX_BG,
    _CHART_BG,
    _CHART_GHOST,
    _CHART_GRID,
    _CHART_MUTED,
    _CHART_TEXT,
    _DARK_STYLESHEET,
    _LEVEL_CHART_COLORS,
    _SAMPLE_ENTRIES,
    _SAMPLE_FLAGGED,
)
from ui_helpers import (
    _enhance_entries_with_extracted_levels,
    _enhance_summary_with_http_status,
    _format_summary_as_html,
)
from ui_widgets import (
    _StatCard,
    _chart_card,
    _make_entries_table,
    _make_sample_table,
    _populate_table,
)


def _watermark(ax):
    ax.text(
        0.5, 0.5, "SAMPLE DATA",
        transform=ax.transAxes, ha="center", va="center",
        fontsize=22, color="#45475a", alpha=0.55,
        fontweight="bold", rotation=25,
    )


# Main window 
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LARG — Log Analyzer & Report Generator")
        self.setMinimumSize(900, 600)

        self._entries: list[dict] = []
        self._loaded_files: list[str] = []
        self._flagged: list[dict] = []

        self._analytics = AnalyticsEngine()
        self._report_builder = ReportBuilder()
        self._html_exporter = HtmlExporter()
        self._csv_exporter = CsvExporter()

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._build_welcome_screen()
        self._build_dashboard()
        self._build_statusbar()

        self._stack.setCurrentIndex(0)

    #  initial screen for loading the first file

    def _build_welcome_screen(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner = QWidget()
        inner.setFixedWidth(460)
        layout = QVBoxLayout(inner)
        layout.setSpacing(24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("LARG")
        title.setStyleSheet("color: #89b4fa; font-size: 48pt; font-weight: bold; letter-spacing: 6px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Log Analyzer & Report Generator")
        subtitle.setStyleSheet("color: #a6adc8; font-size: 13pt;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #313244;")
        layout.addWidget(divider)

        desc = QLabel(
            "Import a <b>.log</b> or <b>.txt</b> file to analyze it,\n"
            "search for patterns, view analytics, and export reports."
        )
        desc.setStyleSheet("color: #a6adc8; font-size: 11pt;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        load_btn = QPushButton("  Choose File  ")
        load_btn.setStyleSheet(
            "QPushButton {"
            "  background-color: #89b4fa;"
            "  color: #1e1e2e;"
            "  font-size: 12pt;"
            "  font-weight: bold;"
            "  border: none;"
            "  border-radius: 8px;"
            "  padding: 14px 32px;"
            "}"
            "QPushButton:hover { background-color: #b4d0ff; }"
            "QPushButton:pressed { background-color: #7098d8; }"
        )
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.clicked.connect(self._on_load_files)
        layout.addWidget(load_btn)

        outer.addWidget(inner)
        self._stack.addWidget(page)  # index 0

    # Dashboard component
    def _build_dashboard(self):
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # top bar
        topbar = QWidget()
        topbar.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        topbar.setFixedHeight(56)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(16, 8, 16, 8)
        tb_layout.setSpacing(10)

        app_title = QLabel("LARG")
        app_title.setStyleSheet("color: #89b4fa; font-size: 15pt; font-weight: bold; letter-spacing: 2px;")
        tb_layout.addWidget(app_title)

        tb_layout.addSpacing(12)

        self._loaded_label = QLabel("No files loaded")
        self._loaded_label.setStyleSheet("color: #6c7086; font-size: 10pt;")
        tb_layout.addWidget(self._loaded_label)

        tb_layout.addStretch()

        tb_layout.addWidget(QLabel("Parse mode:"))
        self._parse_mode_combo = QComboBox()
        self._parse_mode_combo.addItems(["template", "generic", "regex"])
        self._parse_mode_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        tb_layout.addWidget(self._parse_mode_combo)

        tb_layout.addSpacing(8)

        load_btn = QPushButton("Load Files…")
        load_btn.clicked.connect(self._on_load_files)
        tb_layout.addWidget(load_btn)

        export_html_btn = QPushButton("Export HTML")
        export_html_btn.clicked.connect(self._on_export_html)
        tb_layout.addWidget(export_html_btn)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self._on_export_csv)
        tb_layout.addWidget(export_csv_btn)

        root.addWidget(topbar)

        # Body including the sidebar and main area
        body = QSplitter(Qt.Orientation.Horizontal)

        #sidebar
        sidebar = QWidget()
        sidebar.setStyleSheet("background-color: #181825; border-right: 1px solid #313244;")
        sidebar.setMinimumWidth(240)
        sidebar.setMaximumWidth(500) 
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(14, 18, 14, 18)
        sb_layout.setSpacing(12)

        stats_title = QLabel("Overview")
        stats_title.setStyleSheet("color: #89b4fa; font-size: 10pt; font-weight: bold; letter-spacing: 1px;")
        sb_layout.addWidget(stats_title)

        self._card_total   = _StatCard("Total Entries",  "—", "#89b4fa")
        self._card_errors  = _StatCard("Errors",         "—", "#f38ba8")
        self._card_warns   = _StatCard("Warnings",       "—", "#fab387")
        self._card_flagged = _StatCard("Flagged",        "—", "#f9e2af")
        self._card_files   = _StatCard("Files Loaded",   "—", "#a6e3a1")

        for card in (self._card_total, self._card_errors, self._card_warns,
                     self._card_flagged, self._card_files):
            sb_layout.addWidget(card)

        sb_layout.addSpacing(16)
        summary_title = QLabel("Summary")
        summary_title.setStyleSheet("color: #89b4fa; font-size: 10pt; font-weight: bold; letter-spacing: 1px;")
        sb_layout.addWidget(summary_title)

        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setPlaceholderText("Summary will appear here after loading files…")
        self._summary_text.setStyleSheet(
            "QTextEdit { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 4px; padding: 8px; }"
        )
        sb_layout.addWidget(self._summary_text, stretch=1)

        body.addWidget(sidebar)

        # main dashboard content area
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(16, 14, 16, 10)
        main_layout.setSpacing(10)

        # row for charts
        self._build_charts_row(main_layout)

        #section header row
        section_header = QHBoxLayout()
        entries_title = QLabel("Log Entries")
        entries_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #cdd6f4;")
        section_header.addWidget(entries_title)
        section_header.addStretch()

        # controls for seraching and sorting
        section_header.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Keyword…")
        self._search_input.setMinimumWidth(160)
        section_header.addWidget(self._search_input)

        self._search_btn = QPushButton("Search")
        self._search_btn.clicked.connect(self._on_search)
        section_header.addWidget(self._search_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._on_clear_search)
        section_header.addWidget(self._clear_btn)

        section_header.addSpacing(16)
        section_header.addWidget(QLabel("Sort:"))

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["timestamp", "level", "message", "source_file"])
        self._sort_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        section_header.addWidget(self._sort_combo)

        self._sort_order_combo = QComboBox()
        self._sort_order_combo.addItems(["Ascending", "Descending"])
        self._sort_order_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        section_header.addWidget(self._sort_order_combo)

        self._sort_btn = QPushButton("Sort")
        self._sort_btn.clicked.connect(self._on_sort)
        section_header.addWidget(self._sort_btn)

        main_layout.addLayout(section_header)

        # temp, disable until search and sort files added
        self._search_sort_widgets = [
            self._search_input,
            self._search_btn,
            self._clear_btn,
            self._sort_combo,
            self._sort_order_combo,
            self._sort_btn,
        ]
        for w in self._search_sort_widgets:
            w.setEnabled(True)

        # Entries table, also includes placeholder when no data is loaded yet
        table_container = QWidget()
        table_container.setStyleSheet("background: transparent;")
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

        self._entries_table = _make_entries_table()
        self._entries_table.setVisible(False)
        tc_layout.addWidget(self._entries_table)

        self._entries_placeholder = _make_sample_table(_SAMPLE_ENTRIES, "#89b4fa")
        tc_layout.addWidget(self._entries_placeholder)

        main_layout.addWidget(table_container, stretch=3)

        # Flagged table, also has placeholders like Entries
        flagged_header = QHBoxLayout()
        self._flagged_title = QLabel("Flagged Entries  (0)")
        self._flagged_title.setStyleSheet("font-size: 11pt; font-weight: bold; color: #f9e2af;")
        flagged_header.addWidget(self._flagged_title)
        flagged_header.addStretch()
        main_layout.addLayout(flagged_header)

        flagged_container = QWidget()
        flagged_container.setStyleSheet("background: transparent;")
        fc_layout = QVBoxLayout(flagged_container)
        fc_layout.setContentsMargins(0, 0, 0, 0)
        fc_layout.setSpacing(0)

        self._flagged_table = _make_entries_table()
        self._flagged_table.setVisible(False)
        fc_layout.addWidget(self._flagged_table)

        self._flagged_placeholder = _make_sample_table(_SAMPLE_FLAGGED, "#f9e2af")
        fc_layout.addWidget(self._flagged_placeholder)

        main_layout.addWidget(flagged_container, stretch=1)

        body.addWidget(main_area)
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)

        root.addWidget(body, stretch=1)
        self._stack.addWidget(page) 

    # CHARTS
    def _build_charts_row(self, parent_layout: QVBoxLayout):
        charts_row = QWidget()
        charts_row.setFixedHeight(270)
        row_layout = QHBoxLayout(charts_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        self._fig_pie  = Figure(figsize=(4, 3), facecolor=_CHART_BG)
        self._ax_pie   = self._fig_pie.add_subplot(111)
        self._canvas_pie = FigureCanvas(self._fig_pie)
        row_layout.addWidget(_chart_card("Level Distribution", self._canvas_pie))

        self._fig_bar  = Figure(figsize=(4, 3), facecolor=_CHART_BG)
        self._ax_bar   = self._fig_bar.add_subplot(111)
        self._canvas_bar = FigureCanvas(self._fig_bar)
        row_layout.addWidget(_chart_card("Events by Type", self._canvas_bar))

        self._fig_line = Figure(figsize=(4, 3), facecolor=_CHART_BG)
        self._ax_line  = self._fig_line.add_subplot(111)
        self._canvas_line = FigureCanvas(self._fig_line)
        row_layout.addWidget(_chart_card("Activity Timeline", self._canvas_line))

        parent_layout.addWidget(charts_row)
        self._draw_placeholder_charts()

    def _draw_placeholder_charts(self):
        # placeholder pie chart that displays if no data is loaded yet
        ax = self._ax_pie
        fig = self._fig_pie
        canvas = self._canvas_pie
        ax.clear()
        fig.patch.set_facecolor(_CHART_BG)
        ax.set_facecolor(_CHART_AX_BG)
        sample_labels  = ["INFO", "ERROR", "WARNING", "DEBUG", "CRITICAL"]
        sample_sizes   = [52, 18, 16, 10, 4]
        sample_colors  = [_LEVEL_CHART_COLORS[l] for l in sample_labels]
        wedges, texts, autotexts = ax.pie(
            sample_sizes, labels=sample_labels, colors=sample_colors,
            autopct="%1.0f%%", startangle=90, pctdistance=0.78,
            wedgeprops={"linewidth": 1.5, "edgecolor": _CHART_BG, "alpha": 0.45},
        )
        for t in texts:
            t.set_color(_CHART_MUTED)
            t.set_fontsize(8)
        for at in autotexts:
            at.set_color("#1e1e2e")
            at.set_fontsize(7)
            at.set_fontweight("bold")
            at.set_alpha(0.5)
        _watermark(ax)
        fig.tight_layout()
        canvas.draw()

        # placeholder bar chart that displays if no data is loaded yet
        ax = self._ax_bar
        fig = self._fig_bar
        canvas = self._canvas_bar
        ax.clear()
        fig.patch.set_facecolor(_CHART_BG)
        ax.set_facecolor(_CHART_AX_BG)
        s_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        s_counts = [10, 52, 16, 18, 4]
        s_colors = [_LEVEL_CHART_COLORS[l] for l in s_levels]
        bars = ax.barh(s_levels, s_counts, color=s_colors, height=0.55, alpha=0.4)
        ax.tick_params(colors=_CHART_MUTED, labelsize=8)
        ax.set_xlabel("Count", color=_CHART_MUTED, fontsize=8)
        ax.yaxis.set_tick_params(labelcolor=_CHART_MUTED)
        ax.xaxis.set_tick_params(labelcolor=_CHART_GHOST)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ("bottom", "left"):
            ax.spines[spine].set_color(_CHART_GRID)
        ax.grid(axis="x", color=_CHART_GRID, linewidth=0.5, alpha=0.5)
        for bar, count in zip(bars, s_counts):
            ax.text(
                bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", ha="left",
                color=_CHART_GHOST, fontsize=8,
            )
        _watermark(ax)
        fig.tight_layout()
        canvas.draw()

        # placeholder line chart ""
        ax = self._ax_line
        fig = self._fig_line
        canvas = self._canvas_line
        ax.clear()
        fig.patch.set_facecolor(_CHART_BG)
        ax.set_facecolor(_CHART_AX_BG)
        s_x = list(range(12))
        s_y = [3, 7, 5, 12, 8, 15, 10, 18, 9, 14, 6, 11]
        ax.plot(s_x, s_y, color="#89b4fa", linewidth=2,
                marker="o", markersize=4, markerfacecolor=_CHART_TEXT, alpha=0.4)
        ax.fill_between(s_x, s_y, alpha=0.07, color="#89b4fa")
        ax.set_xticks(s_x)
        ax.set_xticklabels(
            [f"H{i:02d}" for i in s_x],
            rotation=30, ha="right", fontsize=7, color=_CHART_GHOST,
        )
        ax.tick_params(axis="y", colors=_CHART_GHOST, labelsize=7)
        ax.set_ylabel("Entries", color=_CHART_MUTED, fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ("bottom", "left"):
            ax.spines[spine].set_color(_CHART_GRID)
        ax.grid(color=_CHART_GRID, linewidth=0.5, alpha=0.5)
        _watermark(ax)
        fig.tight_layout()
        canvas.draw()

    def _refresh_charts(self, summary: object, top_msgs: list):
        level_counts = summary.level_counts
        time_buckets = summary.time_bucket_counts

        # pie chart showing  the distribution of log levels
        ax = self._ax_pie
        fig = self._fig_pie
        ax.clear()
        fig.patch.set_facecolor(_CHART_BG)
        ax.set_facecolor(_CHART_AX_BG)
        if level_counts:
            labels = list(level_counts.keys())
            sizes  = list(level_counts.values())
            colors = [_LEVEL_CHART_COLORS.get(l, _CHART_GHOST) for l in labels]
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors,
                autopct="%1.0f%%", startangle=90, pctdistance=0.78,
                wedgeprops={"linewidth": 1.5, "edgecolor": _CHART_BG},
            )
            for t in texts:
                t.set_color(_CHART_TEXT)
                t.set_fontsize(8)
            for at in autotexts:
                at.set_color("#1e1e2e")
                at.set_fontsize(7)
                at.set_fontweight("bold")
        else:
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                    ha="center", va="center", color=_CHART_GHOST, style="italic")
        fig.tight_layout()
        self._canvas_pie.draw()

        # bar chart showing events by type
        ax = self._ax_bar
        fig = self._fig_bar
        ax.clear()
        fig.patch.set_facecolor(_CHART_BG)
        ax.set_facecolor(_CHART_AX_BG)
        if level_counts:
            sorted_lc = sorted(level_counts.items(), key=lambda x: x[1])
            levels = [s[0] for s in sorted_lc]
            counts = [s[1] for s in sorted_lc]
            bar_colors = [_LEVEL_CHART_COLORS.get(l, _CHART_GHOST) for l in levels]
            bars = ax.barh(levels, counts, color=bar_colors, height=0.55)
            ax.set_facecolor(_CHART_AX_BG)
            ax.tick_params(colors=_CHART_MUTED, labelsize=8)
            ax.set_xlabel("Count", color=_CHART_MUTED, fontsize=8)
            ax.xaxis.label.set_color(_CHART_MUTED)
            ax.yaxis.set_tick_params(labelcolor=_CHART_TEXT)
            ax.xaxis.set_tick_params(labelcolor=_CHART_MUTED)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            for spine in ("bottom", "left"):
                ax.spines[spine].set_color(_CHART_GRID)
            ax.grid(axis="x", color=_CHART_GRID, linewidth=0.5, alpha=0.7)
            max_c = max(counts) if counts else 1
            for bar, count in zip(bars, counts):
                ax.text(
                    bar.get_width() + max_c * 0.02,
                    bar.get_y() + bar.get_height() / 2,
                    str(count), va="center", ha="left",
                    color=_CHART_TEXT, fontsize=8,
                )
        else:
            for spine in ax.spines.values():
                spine.set_color(_CHART_GRID)
            ax.tick_params(colors=_CHART_GHOST)
            ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                    ha="center", va="center", color=_CHART_GHOST, style="italic")
        fig.tight_layout()
        self._canvas_bar.draw()

        # line chart
        ax = self._ax_line
        fig = self._fig_line
        ax.clear()
        fig.patch.set_facecolor(_CHART_BG)
        ax.set_facecolor(_CHART_AX_BG)
        if time_buckets:
            sorted_b = sorted(time_buckets.items())
            x_labels = [b[0] for b in sorted_b]
            y_values = [b[1] for b in sorted_b]
            x_idx    = list(range(len(x_labels)))
            ax.plot(x_idx, y_values, color="#89b4fa", linewidth=2,
                    marker="o", markersize=4, markerfacecolor=_CHART_TEXT)
            ax.fill_between(x_idx, y_values, alpha=0.15, color="#89b4fa")
            short = [lb[-5:] if len(lb) > 8 else lb for lb in x_labels]
            step  = max(1, len(short) // 6)
            ticks = list(range(0, len(short), step))
            ax.set_xticks(ticks)
            ax.set_xticklabels([short[i] for i in ticks], rotation=30, ha="right")
            ax.tick_params(colors=_CHART_MUTED, labelsize=7)
            ax.set_ylabel("Entries", color=_CHART_MUTED, fontsize=8)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            for spine in ("bottom", "left"):
                ax.spines[spine].set_color(_CHART_GRID)
            ax.grid(color=_CHART_GRID, linewidth=0.5, alpha=0.7)
            ax.tick_params(axis="x", colors=_CHART_MUTED)
            ax.tick_params(axis="y", colors=_CHART_MUTED)
        else:
            for spine in ax.spines.values():
                spine.set_color(_CHART_GRID)
            ax.tick_params(colors=_CHART_GHOST)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.text(0.5, 0.5, "No timeline data", transform=ax.transAxes,
                    ha="center", va="center", color=_CHART_GHOST, style="italic")
        fig.tight_layout()
        self._canvas_line.draw()

    def _make_placeholder(self, heading: str, body: str, accent: str = "#89b4fa") -> QWidget:
        widget = QWidget()
        widget.setStyleSheet(
            "background-color: #181825;"
            "border: 1px dashed #45475a;"
            "border-radius: 8px;"
        )
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        h = QLabel(heading)
        h.setStyleSheet(f"color: {accent}; font-size: 13pt; font-weight: bold; background: transparent; border: none;")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(h)

        b = QLabel(body)
        b.setStyleSheet("color: #585b70; font-size: 10pt; background: transparent; border: none;")
        b.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b.setWordWrap(True)
        layout.addWidget(b)

        return widget

    # Status bar 
    def _build_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._set_status("Ready.")

    def _set_status(self, msg: str):
        self._statusbar.showMessage(msg)

    # Slots 
    def _on_load_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Open Log Files",
            "",
            "Log Files (*.log *.txt);;All Files (*)",
        )
        if not paths:
            return

        self._loaded_files = paths

        # switching the view to dashboard after log files are loaded
        self._stack.setCurrentIndex(1)

        names = ", ".join(Path(p).name for p in paths)
        self._loaded_label.setText(f"{len(paths)} file(s): {names}")

        mode = self._parse_mode_combo.currentText()
        try:
            manager = LogManager()
            self._entries = manager.parse_files(paths, mode=mode)
            self._flagged = self._analytics.flag_entries(self._entries)
            self._refresh_ui()
            self._set_status(
                f"Loaded {len(paths)} file(s) — {len(self._entries)} entries, "
                f"{len(self._flagged)} flagged."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Parse Error", str(exc))
            self._set_status("Error during parsing.")

    def _refresh_ui(self):
        has_entries = bool(self._entries)
        has_flagged = bool(self._flagged)

        _populate_table(self._entries_table, self._entries)
        self._entries_table.setVisible(has_entries)
        self._entries_placeholder.setVisible(not has_entries)

        _populate_table(self._flagged_table, self._flagged)
        self._flagged_table.setVisible(has_flagged)
        self._flagged_placeholder.setVisible(not has_flagged)

        self._flagged_title.setText(f"Flagged Entries  ({len(self._flagged)})")
        self._refresh_summary()

    def _refresh_summary(self):
        if not self._entries:
            # update stat cards with zeros, todo: test and double check...
            self._card_total.set_value("0")
            self._card_errors.set_value("0")
            self._card_warns.set_value("0")
            self._card_flagged.set_value("0")
            self._card_files.set_value(str(len(self._loaded_files)))
            self._summary_text.setHtml("<p style='color: #a6adc8; font-size: 12px;'>No entries parsed. Load a file to get started.</p>")
            self._draw_placeholder_charts()
            return

        # enhanced entries with extracted levels from messages
        enhanced_entries = _enhance_entries_with_extracted_levels(self._entries)
        
        summary = self._analytics.summarize(enhanced_entries)
        # enhanced summary with HTTP status codes if present
        summary = _enhance_summary_with_http_status(summary, enhanced_entries)
        
        # format the summary as HTML, test readability and maybe change styling??
        html_summary = _format_summary_as_html(
            summary, enhanced_entries, self._flagged, len(self._loaded_files)
        )
        self._summary_text.setHtml(html_summary)

        level_counts = summary.level_counts
        # for error/warning counts, handle both level and status logs
        errors = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0) + level_counts.get("500", 0)
        warns  = level_counts.get("WARNING", 0) + level_counts.get("WARN", 0) + level_counts.get("400", 0)
        self._card_total.set_value(str(summary.total_entries))
        self._card_errors.set_value(str(errors))
        self._card_warns.set_value(str(warns))
        self._card_flagged.set_value(str(len(self._flagged)))
        self._card_files.set_value(str(len(self._loaded_files)))
        
        # get the top messages for charts fro mAnalyticsEngine
        top_msgs = self._analytics.top_messages(enhanced_entries)
        self._refresh_charts(summary, top_msgs)

    def _on_search(self):
        keyword = self._search_input.text().strip()
        if not keyword:
            _populate_table(self._entries_table, self._entries)
            return
        try:
            engine = SearchEngine()
            results = engine.search_logs(self._entries, QuerySpec(keyword=keyword))
            _populate_table(self._entries_table, results)
            self._set_status(f"Search: {len(results)} result(s) for '{keyword}'.")
        except Exception as exc:
            QMessageBox.warning(self, "Search Error", str(exc))

    def _on_clear_search(self):
        self._search_input.clear()
        _populate_table(self._entries_table, self._entries)
        self._set_status("Search cleared.")

    def _on_sort(self):
        key = self._sort_combo.currentText()
        reverse = self._sort_order_combo.currentIndex() == 1
        try:
            engine = SearchEngine()
            sorted_entries = engine.sort_logs(self._entries, SortSpec(key=key, reverse=reverse))
            _populate_table(self._entries_table, sorted_entries)
            self._set_status(f"Sorted by '{key}' ({'desc' if reverse else 'asc'}).")
        except Exception as exc:
            QMessageBox.warning(self, "Sort Error", str(exc))

    def _on_export_html(self):
        if not self._loaded_files:
            QMessageBox.information(self, "Export", "No files loaded. Load files first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export HTML Report", "report.html", "HTML Files (*.html)"
        )
        if not path:
            return
        try:
            enhanced_entries = _enhance_entries_with_extracted_levels(self._entries)
            summary = self._analytics.summarize(enhanced_entries)
            # enhanced summary with HTTP status codes if theyre  present
            summary = _enhance_summary_with_http_status(summary, enhanced_entries)
            top_msgs = self._analytics.top_messages(enhanced_entries)
            report = self._report_builder.build_report(
                enhanced_entries, summary, top_msgs, self._flagged, self._loaded_files
            )
            self._html_exporter.export(report, path)
            QMessageBox.information(self, "Export", f"HTML report saved to:\n{path}")
            self._set_status(f"HTML exported → {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))

    def _on_export_csv(self):
        if not self._loaded_files:
            QMessageBox.information(self, "Export", "No files loaded. Load files first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "entries.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            self._csv_exporter.export(self._entries, path)
            QMessageBox.information(self, "Export", f"CSV saved to:\n{path}")
            self._set_status(f"CSV exported → {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))


# entry point
def run_app() -> None:
    # needs to be called before QApplication is created for consistent scaling on diff displays
    # try testing on different resolutions
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    base_font = app.font()
    base_font.setFamily("Segoe UI")
    base_font.setPointSize(11)
    app.setFont(base_font)

    app.setStyleSheet(_DARK_STYLESHEET)

    window = MainWindow()

    # first round of testing responsiveness logic... trying tooccupy 85% of the primary screen's available area
    # adjust ratio/margins if needed
    screen = app.primaryScreen()
    if screen:
        geo = screen.availableGeometry()
        w = int(geo.width() * 0.85)
        h = int(geo.height() * 0.85)
        window.resize(w, h)
        window.move(
            geo.x() + (geo.width() - w) // 2,
            geo.y() + (geo.height() - h) // 2,
        )
    else:
        window.resize(1280, 720)

    window.show()
    sys.exit(app.exec())
