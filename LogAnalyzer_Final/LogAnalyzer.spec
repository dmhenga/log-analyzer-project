# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Log Analyzer.
Produces a single-file executable: LogAnalyzer.exe (Windows) / LogAnalyzer (macOS/Linux).

Build:
    pyinstaller LogAnalyzer.spec
Output appears in the dist/ folder.
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[str(Path(".").resolve())],
    binaries=[],
    datas=[
        # Bundle the sample logs so the app can demo without a real log file
        ("sample_logs", "sample_logs"),
    ],
    hiddenimports=[
        # PyQt6 platform plugin needed on all platforms
        "PyQt6.sip",
        "PyQt6.QtPrintSupport",
        # matplotlib Qt backend
        "matplotlib.backends.backend_qtagg",
        "matplotlib.backends.backend_qt",
        # Our own modules (PyInstaller sometimes misses same-directory modules)
        "ui_workflow",
        "ui_constants",
        "ui_helpers",
        "ui_widgets",
        "analytics_reporting",
        "parsing_searching",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="LogAnalyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # no console window — GUI only
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
