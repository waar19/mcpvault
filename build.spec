# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import copy_metadata

datas = []
datas += copy_metadata('fastmcp')
datas += copy_metadata('mcp')
datas += copy_metadata('typer')

block_cipher = None

a = Analysis(
    ['src/mcpv/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['mcpv.vault', 'mcpv.server', 'mcpv.health', 'mcpv.dashboard', 'mcpv.valve', 'mcpv.cache'],
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
    name='mcpv',
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
