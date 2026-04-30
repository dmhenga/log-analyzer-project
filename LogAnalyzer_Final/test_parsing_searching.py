from pathlib import Path

from parsing_searching import LogManager, QuerySpec, SearchEngine, SortSpec


def test_parse_template_line():
    manager = LogManager()
    entry = manager.parse_template_line(
        "2026-04-01 10:01:22 ERROR Failed to connect to database"
    )

    assert entry["timestamp"] == "2026-04-01 10:01:22"
    assert entry["level"] == "ERROR"
    assert entry["message"] == "Failed to connect to database"


def test_parse_generic_line():
    entry = LogManager.parse_generic_line("plain unstructured log message")

    assert entry["timestamp"] is None
    assert entry["level"] is None
    assert entry["message"] == "plain unstructured log message"


def test_parse_file_adds_source_and_line_number(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        "2026-04-01 10:01:22 ERROR Failed to connect\n"
        "2026-04-01 10:02:22 INFO Started service\n",
        encoding="utf-8",
    )

    manager = LogManager()
    entries = manager.parse_files([str(log_file)], mode="template")

    assert len(entries) == 2
    assert entries[0]["source_file"] == "app.log"
    assert entries[0]["line_number"] == 1


def test_search_by_keyword():
    entries = [
        {"timestamp": "2026-04-01 10:01:22", "level": "ERROR", "message": "Failed login"},
        {"timestamp": "2026-04-01 10:02:22", "level": "INFO", "message": "Started service"},
    ]

    engine = SearchEngine()
    results = engine.search_logs(entries, QuerySpec(keyword="failed"))

    assert len(results) == 1
    assert results[0]["level"] == "ERROR"


def test_sort_by_timestamp_descending():
    entries = [
        {"timestamp": "2026-04-01 10:01:22", "level": "INFO", "message": "first"},
        {"timestamp": "2026-04-01 11:01:22", "level": "ERROR", "message": "second"},
    ]

    engine = SearchEngine()
    results = engine.sort_logs(entries, SortSpec(key="timestamp", reverse=True))

    assert results[0]["message"] == "second"