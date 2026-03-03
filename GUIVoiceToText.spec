# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — GUI Voice To Text.

Exclude api-ms-win-* dan ucrtbase.dll yang bikin ordinal error di mesin lain.
"""

from pathlib import Path

# Prefix system DLL yang HARUS di-exclude supaya ga ordinal error
_EXCLUDE_PREFIXES = (
    "api-ms-win-",
    "ucrtbase",
)

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy.distutils',
        'test',
        'unittest',
        'xmlrpc',
    ],
    noarchive=False,
    optimize=0,
)

# ── Strip system DLLs dari binaries ─────────────────────────────────
_filtered = []
for dest, src, typecode in a.binaries:
    name_lower = Path(dest).name.lower()
    if any(name_lower.startswith(pfx) for pfx in _EXCLUDE_PREFIXES):
        print(f'  [EXCLUDED] {dest}')
        continue
    _filtered.append((dest, src, typecode))
a.binaries = _filtered

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GUIVoiceToText',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
