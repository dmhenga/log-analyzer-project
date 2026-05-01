"""Log Analyzer & Report Generator (LARG) Application Entry Point

This is the main entry point for the LARG application.

Requirements Coverage:
- NFR-4.1: Cross-platform desktop application (Windows, macOS, Linux)
- NFR-4.2: Requires Python 3.10+

For detailed requirements see Requirements Documentation PDF.
"""

from ui_workflow import run_app

if __name__ == "__main__":
    run_app()
