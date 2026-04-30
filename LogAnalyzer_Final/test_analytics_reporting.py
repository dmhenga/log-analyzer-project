from analytics_reporting import AnalyticsEngine, ReportBuilder


def sample_entries():
    return [
        {
            "timestamp": "2026-04-01 10:01:22",
            "level": "ERROR",
            "message": "Failed to connect to database",
            "source_file": "app.log",
            "line_number": 1,
        },
        {
            "timestamp": "2026-04-01 10:02:22",
            "level": "INFO",
            "message": "Service started",
            "source_file": "app.log",
            "line_number": 2,
        },
        {
            "timestamp": "2026-04-01 11:02:22",
            "level": "WARNING",
            "message": "Request timeout after 30s",
            "source_file": "server.log",
            "line_number": 3,
        },
    ]


def test_summarize_counts_entries_levels_sources_and_time_buckets():
    engine = AnalyticsEngine()
    summary = engine.summarize(sample_entries())

    assert summary.total_entries == 3
    assert summary.level_counts["ERROR"] == 1
    assert summary.level_counts["INFO"] == 1
    assert summary.source_counts["app.log"] == 2
    assert summary.time_bucket_counts["2026-04-01 10:00"] == 2


def test_flag_entries_finds_errors_and_keywords():
    engine = AnalyticsEngine()
    flagged = engine.flag_entries(sample_entries())

    assert len(flagged) == 2
    assert flagged[0]["level"] == "ERROR"
    assert "timeout" in flagged[1]["message"].lower()


def test_top_messages_normalizes_numbers():
    engine = AnalyticsEngine()
    entries = [
        {"message": "User 123 failed login"},
        {"message": "User 456 failed login"},
    ]

    top = engine.top_messages(entries)

    assert top[0][0] == "user <num> failed login"
    assert top[0][1] == 2


def test_report_builder_creates_report_dict():
    engine = AnalyticsEngine()
    entries = sample_entries()
    summary = engine.summarize(entries)
    flagged = engine.flag_entries(entries)

    report = ReportBuilder().build_report(
        entries=entries,
        summary=summary,
        top_messages=engine.top_messages(entries),
        flagged_entries=flagged,
        loaded_files=["app.log", "server.log"],
    )

    assert report["summary"].total_entries == 3
    assert report["loaded_files"] == ["app.log", "server.log"]
    assert len(report["flagged_entries"]) == 2