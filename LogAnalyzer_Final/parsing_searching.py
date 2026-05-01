"""Log Parsing, Searching, and Sorting Module

Requirements Coverage:
- FR-1.1, FR-1.2, FR-1.3: File import functionality
- FR-2.1.1, FR-2.1.2, FR-2.1.3: Template, Generic, and Regex parsing modes
- FR-2.2: Field extraction (timestamp, level, message, source file, line number)
- FR-3.1, FR-3.2, FR-3.3, FR-3.4: Search and filter operations
- FR-4.1, FR-4.2: Sorting functionality
- NFR-3.1, NFR-3.2: Error handling and validation
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class QuerySpec:
    """Query specification for filtering log entries.
    
    Implements: FR-3.1, FR-3.2, FR-3.3, FR-3.4
    """
    keyword: Optional[str] = None
    exclude_keyword: Optional[str] = None
    level: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class SortSpec:
    """Sort specification for ordering log entries.
    
    Implements: FR-4.1, FR-4.2
    """
    key: str = "timestamp"
    reverse: bool = False


class LogManager:
    """Manages log file parsing with multiple modes.
    
    Implements:
    - FR-1.1, FR-1.2, FR-1.3: File import and validation
    - FR-2.1.1: Template mode parsing
    - FR-2.1.2: Generic mode parsing
    - FR-2.1.3: Regex mode parsing
    - FR-2.2: Field extraction
    - NFR-3.1: Graceful error handling for malformed entries
    """
    # Implements FR-2.1.1: Template mode regex pattern
    TEMPLATE_REGEX = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
        r"(?P<level>[A-Za-z]+)\s+"
        r"(?P<message>.+)$"
    )

    TIMESTAMP_FORMATS = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%d/%m/%Y %H:%M:%S",
    ]

    def parse_files(
        self,
        file_paths: list[str],
        mode: str = "template",
        regex_pattern: Optional[str] = None,
    ) -> list[dict]:
        """Parse multiple log files.
        
        Implements:
        - FR-1.1: Support importing one or more log files
        - FR-1.2: Accept .log and .txt file formats
        - FR-1.3: Reject files with unsupported extensions
        - FR-2.1: Support three parsing modes
        """
        all_entries: list[dict] = []

        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            # FR-1.2, FR-1.3: Validate file extension
            if ext not in [".log", ".txt"]:
                continue

            entries = self._parse_single_file(
                file_path=path,
                mode=mode,
                regex_pattern=regex_pattern,
            )
            all_entries.extend(entries)

        return all_entries

    def _parse_single_file(
        self,
        file_path: str,
        mode: str,
        regex_pattern: Optional[str] = None,
    ) -> list[dict]:
        entries: list[dict] = []
        compiled_regex = re.compile(regex_pattern) if regex_pattern else None

        with open(file_path, "r", encoding="utf-8", errors="replace") as handle:
            for idx, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue

                try:
                    if mode == "template":
                        entry = self.parse_template_line(line)
                        if entry is None:
                            entry = self.parse_generic_line(line)
                    elif mode == "regex":
                        entry = self.parse_regex_line(line, compiled_regex)
                        if entry is None:
                            entry = self.parse_generic_line(line)
                    else:
                        entry = self.parse_generic_line(line)

                    entry["source_file"] = os.path.basename(file_path)
                    entry["line_number"] = idx
                    entries.append(entry)

                except Exception:
                    entries.append(
                        {
                            "timestamp": None,
                            "level": "PARSE_ERROR",
                            "message": line,
                            "source_file": os.path.basename(file_path),
                            "line_number": idx,
                        }
                    )

        return entries

    def parse_template_line(self, line: str) -> Optional[dict]:
        """Parse structured log line using template mode.
        
        Implements: FR-2.1.1 - Template Mode parsing
        """
        match = self.TEMPLATE_REGEX.match(line)
        if not match:
            return None

        groups = match.groupdict()
        # FR-2.2: Extract timestamp, level, and message fields
        return {
            "timestamp": groups.get("timestamp"),
            "level": groups.get("level"),
            "message": groups.get("message"),
        }

    def parse_regex_line(
        self,
        line: str,
        compiled_regex: Optional[re.Pattern],
    ) -> Optional[dict]:
        """Parse log line using custom regex pattern.
        
        Implements: FR-2.1.3 - Regex Mode with user-defined patterns
        """
        # NFR-3.2: Validation happens during regex compilation
        if compiled_regex is None:
            return None

        match = compiled_regex.search(line)
        if not match:
            return None

        groups = match.groupdict()
        # FR-2.2: Extract fields from named groups
        return {
            "timestamp": groups.get("timestamp"),
            "level": groups.get("level"),
            "message": groups.get("message") or line,
        }

    @staticmethod
    def parse_generic_line(line: str) -> dict:
        """Parse unstructured log line as plain text.
        
        Implements: FR-2.1.2 - Generic Mode parsing
        """
        return {
            "timestamp": None,
            "level": None,
            "message": line.strip(),
        }

    def parse_timestamp(self, ts: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string into datetime object.
        
        Implements: FR-2.2 - Timestamp field extraction
        Supports: FR-3.4 - Date range filtering
        """
        if not ts:
            return None

        for fmt in self.TIMESTAMP_FORMATS:
            try:
                return datetime.strptime(ts, fmt)
            except (ValueError, TypeError):
                continue

        return None


class SearchEngine:
    """Handles searching, filtering, and sorting of log entries.
    
    Implements:
    - FR-3.1, FR-3.2, FR-3.3, FR-3.4: Search and filter operations
    - FR-4.1, FR-4.2: Sorting functionality
    - NFR-1.2: Fast search/filter performance
    """
    def __init__(self) -> None:
        self.log_manager = LogManager()

    def search_logs(self, log_entries: list[dict], query: QuerySpec) -> list[dict]:
        """Filter log entries based on query specification.
        
        Implements:
        - FR-3.1: Keyword filtering (case-insensitive)
        - FR-3.2: Exclusion keyword filtering
        - FR-3.3: Log level filtering
        - FR-3.4: Date range filtering
        """
        filtered_logs: list[dict] = []

        start_dt = None
        end_dt = None

        if query.start_date:
            start_dt = datetime.strptime(query.start_date, "%Y-%m-%d")
        if query.end_date:
            end_dt = datetime.strptime(query.end_date, "%Y-%m-%d")

        for entry in log_entries:
            timestamp_str = entry.get("timestamp")
            entry_time = self.log_manager.parse_timestamp(timestamp_str)

            # FR-3.4: Date range filtering
            if start_dt or end_dt:
                if entry_time is None:
                    continue
                if start_dt and entry_time < start_dt:
                    continue
                if end_dt and entry_time > end_dt:
                    continue

            # FR-3.3: Log level filtering
            if query.level and (entry.get("level") or "").upper() != query.level.upper():
                continue

            message = (entry.get("message") or "").lower()

            # FR-3.1: Keyword filtering (case-insensitive)
            if query.keyword and query.keyword.lower() not in message:
                continue

            # FR-3.2: Exclude keyword filtering
            if query.exclude_keyword and query.exclude_keyword.lower() in message:
                continue

            filtered_logs.append(entry)

        return filtered_logs

    def sort_logs(self, log_entries: list[dict], sort_spec: SortSpec) -> list[dict]:
        """Sort log entries by specified criteria.
        
        Implements:
        - FR-4.1: Sort by timestamp, level, message, or source_file
        - FR-4.2: Ascending and descending sort orders
        """
        min_datetime = datetime.min

        def safe_sort_key(entry: dict):
            value = entry.get(sort_spec.key)

            # FR-4.1: Sort by timestamp with proper datetime handling
            if sort_spec.key == "timestamp":
                dt = self.log_manager.parse_timestamp(value)
                return dt if dt is not None else min_datetime

            return value if value is not None else ""

        try:
            # FR-4.2: Apply ascending or descending sort order
            return sorted(log_entries, key=safe_sort_key, reverse=sort_spec.reverse)
        except Exception:
            return log_entries

