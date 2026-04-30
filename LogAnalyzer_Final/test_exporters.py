from analytics_reporting import AnalyticsEngine, CsvExporter, HtmlExporter, ReportBuilder


def test_csv_exporter_writes_file(tmp_path):
    entries = [
        {
            "timestamp": "2026-04-01 10:01:22",
            "level": "ERROR",
            "message": "Failed to connect",
            "source_file": "app.log",
            "line_number": 1,
        }
    ]

    output = tmp_path / "entries.csv"
    CsvExporter().export(entries, str(output))

    text = output.read_text(encoding="utf-8")

    assert "timestamp,level,message,source_file,line_number" in text
    assert "Failed to connect" in text


def test_html_exporter_writes_report(tmp_path):
    entries = [
        {
            "timestamp": "2026-04-01 10:01:22",
            "level": "ERROR",
            "message": "Failed to connect",
            "source_file": "app.log",
            "line_number": 1,
        }
    ]

    engine = AnalyticsEngine()
    summary = engine.summarize(entries)
    flagged = engine.flag_entries(entries)

    report = ReportBuilder().build_report(
        entries=entries,
        summary=summary,
        top_messages=engine.top_messages(entries),
        flagged_entries=flagged,
        loaded_files=["app.log"],
    )

    output = tmp_path / "report.html"
    HtmlExporter().export(report, str(output))

    text = output.read_text(encoding="utf-8")

    assert "Log Analyzer & Report Generator" in text
    assert "Failed to connect" in text
    assert "Total Entries" in text