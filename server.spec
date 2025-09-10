# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hidden_imports = collect_submodules("melo")

import os

import unidic
import unidic_lite
import pykakasi
import g2p_en
import jamo
import gruut

a = Analysis(
    ['server.py'],
    pathex=['.'],
    binaries=[],
    datas=[
            (os.path.join(os.path.dirname(unidic.__file__), "dicdir"), "./unidic/dicdir"),
            (os.path.join(os.path.dirname(unidic_lite.__file__), "dicdir"), "unidic_lite/dicdir"),
            (os.path.join(os.path.dirname(pykakasi.__file__), "data"), "pykakasi/data"),
            (os.path.join(os.path.dirname(jamo.__file__), "data"), "jamo/data"),
            (os.path.join(os.path.dirname(gruut.__file__), "VERSION"), "gruut"),
            # g2p_en 文件
            *[
                (os.path.join(os.path.dirname(g2p_en.__file__), f), "g2p_en")
                for f in ["checkpoint20.npz", "homographs.en"]
            ],
            ('./melo/text/cmudict.rep', './melo/text'),
            ('./melo/text/opencpop-strict.txt', './melo/text')
            # ('./models/', './models')
            ],
    hiddenimports=hidden_imports,
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
    name='server',
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
