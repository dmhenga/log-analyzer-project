from parsing_searching import LogManager, SearchEngine, QuerySpec, SortSpec
from analytics_reporting import AnalyticsEngine

def run_tests():
    manager = LogManager()
    entries = manager.parse_files(["sample_logs/app.log"], mode="template")

    assert len(entries) > 0, "No entries parsed"
    assert any(e.get("level") == "ERROR" for e in entries), "Expected ERROR entries not found"

    search = SearchEngine()
    filtered = search.search_logs(entries, QuerySpec(keyword="database"))
    assert len(filtered) == 1, "Keyword search failed"

    sorted_entries = search.sort_logs(entries, SortSpec(key="timestamp", reverse=False))
    assert sorted_entries[0]["timestamp"] <= sorted_entries[-1]["timestamp"], "Sort failed"

    analytics = AnalyticsEngine()
    summary = analytics.summarize(entries)
    assert summary.total_entries == len(entries), "Summary total mismatch"

    flagged = analytics.flag_entries(entries)
    assert len(flagged) >= 1, "Expected flagged entries"

    print("All basic tests passed.")

if __name__ == "__main__":
    run_tests()
