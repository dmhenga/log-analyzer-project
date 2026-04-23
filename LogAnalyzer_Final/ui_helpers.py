import re
import types
from collections import Counter


def _extract_timestamp_from_message(message, current_timestamp):
    if current_timestamp:
        return current_timestamp

    if not message:
        return None

    # app server format: 2026-04-10 08:00:00,001
    app_match = re.match(r'^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2}),\d+', message)
    if app_match:
        year, month, day, hour, minute, second = app_match.groups()
        return f"{year}-{month}-{day} {hour}:{minute}:{second}"

    # Apache/Nginx format: [10/Apr/2026:13:55:36 -0700]
    access_match = re.search(r'\[(\d{2})/([A-Za-z]{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2})\s[+-]\d{4}\]', message)
    if access_match:
        day, month_str, year, hour, minute, second = access_match.groups()
        months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                  'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
        month = months.get(month_str, '01')
        return f"{year}-{month}-{day} {hour}:{minute}:{second}"

    return None


def _extract_level_from_message(message, current_level):
    if current_level and current_level.upper() not in ("UNKNOWN", "PARSE_ERROR"):
        return current_level

    if not message:
        return None

    # try timestamp + LEVEL pattern first
    level_match = re.search(r'\d{2}:\d{2}:\d{2},?\d*\s+([A-Z]+)\s+[\[\s]', message)
    if level_match:
        return level_match.group(1)

    # fall back to keyword scan
    for keyword in ['CRITICAL', 'ERROR', 'WARNING', 'WARN', 'INFO', 'DEBUG']:
        if re.search(r'\b' + keyword + r'\b', message, re.IGNORECASE):
            return keyword

    return None


def _extract_http_status_category(message):
    if not message:
        return None

    status_match = re.search(r'(?:[\"\s>]\s*|->[\s]*)([1-5]\d{2})(?:\s|:|$)', message)
    if status_match:
        return status_match.group(1)[0] + "00"

    return None


def _has_http_status_entries(entries):
    if not entries:
        return False
    for entry in entries[:10]:
        if _extract_http_status_category(entry.get("message", "")):
            return True
    return False


def _enhance_entries_with_extracted_levels(entries):
    enhanced = []
    for entry in entries:
        entry_copy = entry.copy()
        extracted_level = _extract_level_from_message(entry.get("message", ""), entry.get("level"))
        if extracted_level:
            entry_copy["level"] = extracted_level
        extracted_timestamp = _extract_timestamp_from_message(entry.get("message", ""), entry.get("timestamp"))
        if extracted_timestamp:
            entry_copy["timestamp"] = extracted_timestamp
        enhanced.append(entry_copy)
    return enhanced


def _enhance_summary_with_http_status(summary, entries):
    if not _has_http_status_entries(entries):
        return summary

    status_counts = Counter()
    for entry in entries:
        status = _extract_http_status_category(entry.get("message", ""))
        if status:
            status_counts[status] += 1
        else:
            status_counts["UNKNOWN"] += 1

    return types.SimpleNamespace(
        total_entries=summary.total_entries,
        level_counts=dict(status_counts),
        source_counts=summary.source_counts,
        time_bucket_counts=summary.time_bucket_counts,
    )


def _extract_useful_message(entry):
    message = (entry.get("message") or "").strip()
    if not message:
        return "Unknown"

    # HTTP logs
    http_match = re.search(r'"([A-Z]+)\s+([^\s]+)\s+HTTP', message)
    if http_match:
        method, path = http_match.groups()
        path = path if len(path) <= 40 else path[:40] + "..."
        return f"{method} {path}"

    # app server logs
    msg_match = re.search(r'\d{2}:\d{2}:\d{2},?\d*\s+([A-Z]+)\s+(.+?)(?:\s*\[|$)', message)
    if msg_match:
        _, msg_text = msg_match.groups()
        msg_text = msg_text.strip()
        msg_text = msg_text if len(msg_text) <= 50 else msg_text[:50] + "..."
        return msg_text if msg_text else "Log message"

    return message[:50] + "..." if len(message) > 50 else message


def _get_useful_top_messages(entries, top_n=3):
    messages = [_extract_useful_message(e) for e in entries if e.get("message")]
    if not messages:
        return []
    return Counter(messages).most_common(top_n)


def _format_summary_as_html(summary, entries, flagged_entries, file_count):
    top_messages = _get_useful_top_messages(entries)

    parts = ["<div style='font-family: Segoe UI, Arial, sans-serif; color: #cdd6f4;'>"]

    parts.append("<div style='margin-bottom: 14px;'>")
    parts.append(f"<div style='font-size: 14px; color: #a6adc8; margin-bottom: 6px;'><b>Files:</b> {file_count}</div>")
    parts.append(f"<div style='font-size: 14px; color: #a6adc8; margin-bottom: 6px;'><b>Entries:</b> {summary.total_entries}</div>")
    parts.append(f"<div style='font-size: 14px; color: #a6adc8;'><b>Flagged:</b> {len(flagged_entries)}</div>")
    parts.append("</div>")

    parts.append("<hr style='border: none; border-top: 1px solid #313244; margin: 10px 0;'>")
    parts.append("<div style='margin-bottom: 12px;'>")
    parts.append("<div style='font-size: 13px; color: #89b4fa; font-weight: bold; margin-bottom: 6px;'>Distribution</div>")

    level_colors = {
        "200": "#a6e3a1", "300": "#89b4fa", "400": "#fab387", "500": "#f38ba8",
        "INFO": "#89b4fa", "DEBUG": "#a6adc8", "WARNING": "#fab387", "WARN": "#fab387",
        "ERROR": "#f38ba8", "CRITICAL": "#e64553",
    }

    for level, count in sorted(summary.level_counts.items()):
        color = level_colors.get(level, "#a6adc8")
        parts.append(
            f"<div style='font-size: 12px; margin-bottom: 4px;'>"
            f"<span style='color: {color}; font-weight: bold;'>{level}</span>: {count}"
            f"</div>"
        )
    parts.append("</div>")

    if top_messages:
        parts.append("<hr style='border: none; border-top: 1px solid #313244; margin: 10px 0;'>")
        parts.append("<div style='margin-bottom: 10px;'>")
        parts.append("<div style='font-size: 13px; color: #89b4fa; font-weight: bold; margin-bottom: 6px;'>Top Messages</div>")
        for message, count in top_messages:
            safe_msg = message.replace("<", "&lt;").replace(">", "&gt;")
            parts.append(
                f"<div style='font-size: 12px; color: #a6adc8; margin-bottom: 6px; word-wrap: break-word;'>"
                f"<b>({count})</b> {safe_msg}"
                f"</div>"
            )
        parts.append("</div>")

    parts.append("</div>")
    return "".join(parts)
