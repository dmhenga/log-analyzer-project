# Log Analyzer & Report Generator (LARG)

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
- `parsing_searching.py` — parsing, searching, sorting
- `analytics_reporting.py` — analytics and reporting
- `sample_logs/` — sample files for testing
- `tests/` — basic test scripts

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
   
### Modules and Data bundled in the build
The LogAnalyzer.spec controls the build. All four Python modules are explicitly included:

- `main.py` (entry point)
- `ui_workflow.py`
- `analytics_reporting.py`
- `parsing_searching.py`

And `sample_logs/` is bundled as data so the app can demo without an external log file.


## Executable
Located in dist\ directory as LogAnalyzer.exe

## Supported Default Log Format
Template mode expects:
```text
YYYY-MM-DD HH:MM:SS LEVEL Message text
```

Example:
```text
2026-04-01 10:01:22 ERROR Failed to connect to database
```

## Regex Mode
Regex mode may use named groups:
- `timestamp`
- `level`
- `message`

Example:
```regex
^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(?P<level>\w+)\s+(?P<message>.+)$
```

## Notes
- If a line cannot be parsed in template or regex mode, the app falls back to generic mode.
- Date filters should use `YYYY-MM-DD`.
- Exported HTML and CSV files are saved wherever the user chooses.

## Suggested Team Ownership
- **UI / Workflow**
- **Parsing / Searching**
- **Analytics / Reporting / QA**

## Submission Notes
This package includes:
- runnable source code
- frontend
- sample logs
- basic tests
- dependency file
- README
