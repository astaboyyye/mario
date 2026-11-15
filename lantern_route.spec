# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['lantern_route.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/quest_pack', 'resources/quest_pack'), ('resources/fonts', 'resources/fonts'),
           ('resources/lantern_audio', 'resources/lantern_audio'), ('lantern/levels', 'lantern/levels')],
    hiddenimports=[],
    excludes=['panda3d', 'direct', 'tkinter'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='LanternRoute', debug=False, strip=False, upx=True,
          runtime_tmpdir=None, console=False)
