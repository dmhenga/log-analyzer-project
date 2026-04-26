# Log Analyzer & Report Generator (LARG)

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

A standalone Python desktop application built with **PyQt6** for analyzing `.log` and `.txt` files.

## Features
- Import one or more `.log` / `.txt` files
- Parse log lines using:
  - **Template mode**: `timestamp level message`
  - **Generic mode**: plain text fallback
  - **Regex mode**: custom named-group parsing
- Search and filter by:
  - keyword
  - exclude keyword
  - log level
  - date range
- Sort by timestamp, level, message, or source file
- Generate analytics:
  - total entries
  - counts by level
  - top recurring messages
  - time buckets
  - flagged entries
- Export results to:
  - **HTML**
  - **CSV**

## Project Files
- `main.py` — app entry point
- `ui_workflow.py` — PyQt frontend and workflow
- `ui_constants.py` — PyQt frontend resource
- `ui_helpers.py` — PyQt frontend resource
- `ui_widgets.py` — PyQt frontend resource
- `parsing_searching.py` — parsing, searching, sorting
- `analytics_reporting.py` — analytics and reporting
- `sample_logs/` — sample files for testing

## Requirements
- Python 3.10+
- PyQt6
- matplotlib

Install dependencies:
```bash
pip install pyinstaller
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Build Executable
Run this command either after you make changes to the code and want to test, or if you're just pulling from the repo for the first time since the app was made into an executable with UI Workflow updates.

```bash
cd path/to/log-analyzer-project/LogAnalyzer_Final
python -m PyInstaller LogAnalyzer.spec --clean
```

let the build run for a bit, then you should see "Building EXE from EXE-00.toc completed successfully." and "Build complete!" meaning the build finished successfully. Then you can open the .exe file again to test your changes. **The LogAnalyzer.exe file will be located in the dist/ folder after this build completes**

## Build Components
- LogAnalyzer.spec controls the build, do not modify this file unless necessary for adding new modules.
- the `build/` directory is intermediate output and can be ignored (this should already be in the .gitignore)
- the `dist/` directory will be the home for the final executable file
   
