# -*- mode: python ; coding: utf-8 -*-
"""Debug spec — sama kayak GUIVoiceToText.spec tapi console=True."""

from pathlib import Path

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
    name='GUIVoiceToText_debug',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
