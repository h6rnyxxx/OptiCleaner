# -*- mode: python ; coding: utf-8 -*-
import os
import PyQt5
from PyInstaller.utils.hooks import collect_data_files

datas = [('images', 'images')]
if os.path.exists('cyber_visuals.html'):
    datas += [('cyber_visuals.html', '.')]
elif os.path.exists('images/cyber_visuals.html'):
    datas += [('images/cyber_visuals.html', '.')]
datas += collect_data_files('qtawesome')

qt5_dir = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5')
res_dir = os.path.join(qt5_dir, 'resources')
if os.path.isdir(res_dir):
    datas += [(res_dir, 'PyQt5/Qt5/resources')]

binaries = []
proc_exe = os.path.join(qt5_dir, 'bin', 'QtWebEngineProcess.exe')
if os.path.isfile(proc_exe):
    binaries += [(proc_exe, 'PyQt5/Qt5/bin')]


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['psutil', 'qtawesome', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebEngineCore', 'requests', 'sqlite3', 'uuid'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OptiCleaner',
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
    icon=['images/icon.ico'],
)
