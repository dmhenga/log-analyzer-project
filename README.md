# Log Analyzer & Report Generator (LARG)

A standalone Python desktop application built with **PyQt6** to analyze `.log` and `.txt` files.  
This project is designed as a collaborative Software Engineering group project.

---

## 🚀 Features

- Import one or more log files (`.log`, `.txt`)
- Parsing modes:
  - **Template Mode** → `timestamp level message`
  - **Generic Mode** → fallback for unstructured logs
  - **Regex Mode** → custom parsing using named groups
- Search and filter:
  - Keyword / Exclude keyword
  - Log level
  - Date range
- Sorting:
  - Timestamp
  - Level
  - Message
  - Source file
- Analytics:
  - Total entries
  - Counts by log level
  - Top recurring messages
  - Time buckets
  - Flagged entries (errors, warnings, keywords)
- Export:
  - HTML report
  - CSV file

---

## 🧱 Project Structure
