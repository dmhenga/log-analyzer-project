from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class QuerySpec:
    keyword: Optional[str] = None
    exclude_keyword: Optional[str] = None
    level: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class SortSpec:
    key: str = "timestamp"
    reverse: bool = False


class LogManager:
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
        all_entries: list[dict] = []

        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
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
        match = self.TEMPLATE_REGEX.match(line)
        if not match:
            return None

        groups = match.groupdict()
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
        if compiled_regex is None:
            return None

        match = compiled_regex.search(line)
        if not match:
            return None

        groups = match.groupdict()
        return {
            "timestamp": groups.get("timestamp"),
            "level": groups.get("level"),
            "message": groups.get("message") or line,
        }

    @staticmethod
    def parse_generic_line(line: str) -> dict:
        return {
            "timestamp": None,
            "level": None,
            "message": line.strip(),
        }

    def parse_timestamp(self, ts: Optional[str]) -> Optional[datetime]:
        if not ts:
            return None

        for fmt in self.TIMESTAMP_FORMATS:
            try:
                return datetime.strptime(ts, fmt)
            except (ValueError, TypeError):
                continue

        return None


class SearchEngine:
    def __init__(self) -> None:
        self.log_manager = LogManager()

    def search_logs(self, log_entries: list[dict], query: QuerySpec) -> list[dict]:
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

            if start_dt or end_dt:
                if entry_time is None:
                    continue
                if start_dt and entry_time < start_dt:
                    continue
                if end_dt and entry_time > end_dt:
                    continue

            if query.level and (entry.get("level") or "").upper() != query.level.upper():
                continue

            message = (entry.get("message") or "").lower()

            if query.keyword and query.keyword.lower() not in message:
                continue

            if query.exclude_keyword and query.exclude_keyword.lower() in message:
                continue

            filtered_logs.append(entry)

        return filtered_logs

    def sort_logs(self, log_entries: list[dict], sort_spec: SortSpec) -> list[dict]:
        min_datetime = datetime.min

        def safe_sort_key(entry: dict):
            value = entry.get(sort_spec.key)

            if sort_spec.key == "timestamp":
                dt = self.log_manager.parse_timestamp(value)
                return dt if dt is not None else min_datetime

            return value if value is not None else ""

        try:
            return sorted(log_entries, key=safe_sort_key, reverse=sort_spec.reverse)
        except Exception:
            return log_entries

