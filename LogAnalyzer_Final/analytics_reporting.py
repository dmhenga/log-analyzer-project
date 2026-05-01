"""Analytics and Reporting Module

Requirements Coverage:
- FR-5.1.1, FR-5.1.2, FR-5.1.3: Count analytics (total, by level, by source)
- FR-5.1.4: Top recurring messages
- FR-5.1.5: Time-based distribution
- FR-5.1.6: Flagged entries (errors, warnings, keywords)
- FR-6.1: HTML export
- FR-6.2: CSV export
- FR-6.3: Report content with summary statistics
"""

from __future__ import annotations

import csv
import html
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SummaryResult:
    """Container for analytics summary data.
    
    Implements: FR-5.1 (all sub-requirements)
    """
    total_entries: int  # FR-5.1.1
    level_counts: dict[str, int]  # FR-5.1.2
    source_counts: dict[str, int]  # FR-5.1.3
    time_bucket_counts: dict[str, int]  # FR-5.1.5


class AnalyticsEngine:
    """Calculates analytics and statistics for log entries.
    
    Implements:
    - FR-5.1.1: Total entry count
    - FR-5.1.2: Log level distribution
    - FR-5.1.3: Source file distribution
    - FR-5.1.4: Top recurring messages
    - FR-5.1.5: Time-based distribution
    - FR-5.1.6: Flagged entries
    """
    def summarize(self, entries: list[dict]) -> SummaryResult:
        """Generate summary statistics for log entries.
        
        Implements: FR-5.1.1, FR-5.1.2, FR-5.1.3, FR-5.1.5
        """
        level_counts = Counter()
        source_counts = Counter()
        time_bucket_counts = defaultdict(int)

        for entry in entries:
            # FR-5.1.2: Count by log level
            level = (entry.get("level") or "UNKNOWN").upper()
            # FR-5.1.3: Count by source file
            source = entry.get("source_file") or "UNKNOWN"
            timestamp = entry.get("timestamp")

            level_counts[level] += 1
            source_counts[source] += 1

            # FR-5.1.5: Time-based distribution (hourly buckets)
            if timestamp:
                bucket = self._time_bucket(timestamp)
                if bucket:
                    time_bucket_counts[bucket] += 1

        return SummaryResult(
            total_entries=len(entries),  # FR-5.1.1
            level_counts=dict(level_counts),
            source_counts=dict(source_counts),
            time_bucket_counts=dict(time_bucket_counts),
        )

    def top_messages(self, entries: list[dict], top_n: int = 10) -> list[tuple[str, int]]:
        """Identify most frequently occurring messages.
        
        Implements: FR-5.1.4 - Top recurring messages
        """
        normalized = [self._normalize_message(e.get("message", "")) for e in entries if e.get("message")]
        counts = Counter(normalized)
        return counts.most_common(top_n)

    def flag_entries(self, entries: list[dict]) -> list[dict]:
        """Identify entries matching flagging criteria.
        
        Implements: FR-5.1.6 - Flagged entries (errors, warnings, keywords)
        """
        flagged = []
        keywords = ["timeout", "failed", "exception", "denied"]

        for entry in entries:
            level = (entry.get("level") or "").upper()
            msg = (entry.get("message") or "").lower()

            # FR-5.1.6: Flag ERROR and CRITICAL level entries
            if level in {"ERROR", "CRITICAL"}:
                flagged.append(entry)
                continue

            # FR-5.1.6: Flag entries containing specific keywords
            if any(k in msg for k in keywords):
                flagged.append(entry)

        return flagged

    @staticmethod
    def _normalize_message(message: str) -> str:
        message = message.strip().lower()
        message = re.sub(r"\d+", "<num>", message)
        return message

    @staticmethod
    def _time_bucket(timestamp_str: str) -> str | None:
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%m/%Y %H:%M:%S",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.strftime("%Y-%m-%d %H:00")
            except ValueError:
                continue
        return None


class ReportBuilder:
    """Builds structured report data.
    
    Implements: FR-6.3 - Report content with summary statistics
    """
    def build_report(
        self,
        entries: list[dict],
        summary: SummaryResult,
        top_messages: list[tuple[str, int]],
        flagged_entries: list[dict],
        loaded_files: list[str],
    ) -> dict:
        """Build complete report structure.
        
        Implements: FR-6.3 - Include summary statistics and entry details
        """
        return {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "loaded_files": loaded_files,
            "summary": summary,
            "top_messages": top_messages,
            "flagged_entries": flagged_entries,
            "entries": entries,
        }

    def render_summary_text(
        self,
        summary: SummaryResult,
        top_messages: list[tuple[str, int]],
        flagged_entries: list[dict],
        file_count: int,
    ) -> str:
        lines = [
            "LARG Summary",
            "=" * 60,
            f"Files Loaded: {file_count}",
            f"Total Entries: {summary.total_entries}",
            f"Flagged Entries: {len(flagged_entries)}",
            "",
            "Counts by Level:",
        ]

        for level, count in sorted(summary.level_counts.items()):
            lines.append(f"  - {level}: {count}")

        lines.append("")
        lines.append("Top Recurring Messages:")
        for message, count in top_messages:
            lines.append(f"  - ({count}) {message}")

        if summary.time_bucket_counts:
            lines.append("")
            lines.append("Time Buckets:")
            for bucket, count in sorted(summary.time_bucket_counts.items()):
                lines.append(f"  - {bucket}: {count}")

        return "\n".join(lines)


class HtmlExporter:
    """Exports log data and analytics to HTML format.
    
    Implements:
    - FR-6.1: Export filtered results to HTML format
    - FR-6.3: Include summary statistics and entry details
    """
    def export(self, report: dict, output_path: str) -> None:
        """Generate HTML report file.
        
        Implements: FR-6.1, FR-6.3
        """
        summary: SummaryResult = report["summary"]
        top_messages = report["top_messages"]
        flagged_entries = report["flagged_entries"]

        html_parts = [
            "<html><head><meta charset='utf-8'><title>LARG Report</title></head><body>",
            "<h1>Log Analyzer & Report Generator</h1>",
            f"<p><strong>Generated:</strong> {html.escape(report['generated_at'])}</p>",
            f"<p><strong>Files:</strong> {html.escape(', '.join(report['loaded_files']))}</p>",
            f"<p><strong>Total Entries:</strong> {summary.total_entries}</p>",
            f"<p><strong>Flagged Entries:</strong> {len(flagged_entries)}</p>",
            "<h2>Counts by Level</h2><ul>",
        ]

        for level, count in sorted(summary.level_counts.items()):
            html_parts.append(f"<li>{html.escape(level)}: {count}</li>")
        html_parts.append("</ul>")

        html_parts.append("<h2>Top Messages</h2><ol>")
        for message, count in top_messages:
            html_parts.append(f"<li>{html.escape(message)} ({count})</li>")
        html_parts.append("</ol>")

        html_parts.append("<h2>Flagged Entries</h2><table border='1' cellpadding='4' cellspacing='0'>")
        html_parts.append("<tr><th>Timestamp</th><th>Level</th><th>Message</th><th>Source File</th><th>Line #</th></tr>")

        for entry in flagged_entries[:200]:
            html_parts.append(
                "<tr>"
                f"<td>{html.escape(str(entry.get('timestamp') or ''))}</td>"
                f"<td>{html.escape(str(entry.get('level') or ''))}</td>"
                f"<td>{html.escape(str(entry.get('message') or ''))}</td>"
                f"<td>{html.escape(str(entry.get('source_file') or ''))}</td>"
                f"<td>{html.escape(str(entry.get('line_number') or ''))}</td>"
                "</tr>"
            )

        html_parts.append("</table></body></html>")

        Path(output_path).write_text("\n".join(html_parts), encoding="utf-8")


class CsvExporter:
    """Exports log entries to CSV format.
    
    Implements: FR-6.2 - Export filtered results to CSV format
    """
    def export(self, entries: list[dict], output_path: str) -> None:
        """Write log entries to CSV file.
        
        Implements: FR-6.2
        """
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["timestamp", "level", "message", "source_file", "line_number"],
            )
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    "timestamp": entry.get("timestamp"),
                    "level": entry.get("level"),
                    "message": entry.get("message"),
                    "source_file": entry.get("source_file"),
                    "line_number": entry.get("line_number"),
                })
