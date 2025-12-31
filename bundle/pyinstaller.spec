# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all required data files
datas = [
    ('../viu_media/assets', 'viu_media/assets'),
]

# Collect all required hidden imports
# Include viu_media and all its submodules to ensure menu modules are bundled
hiddenimports = [
    'click',
    'rich',
    'requests',
    'yt_dlp',
    'python_mpv',
    'fuzzywuzzy',
    'viu_media',
    'viu_media.cli.interactive.menu',
    'viu_media.cli.interactive.menu.media',
    # Explicit menu modules (PyInstaller doesn't always pick these up)
    'viu_media.cli.interactive.menu.media.downloads',
    'viu_media.cli.interactive.menu.media.download_episodes',
    'viu_media.cli.interactive.menu.media.dynamic_search',
    'viu_media.cli.interactive.menu.media.episodes',
    'viu_media.cli.interactive.menu.media.main',
    'viu_media.cli.interactive.menu.media.media_actions',
    'viu_media.cli.interactive.menu.media.media_airing_schedule',
    'viu_media.cli.interactive.menu.media.media_characters',
    'viu_media.cli.interactive.menu.media.media_review',
    'viu_media.cli.interactive.menu.media.player_controls',
    'viu_media.cli.interactive.menu.media.play_downloads',
    'viu_media.cli.interactive.menu.media.provider_search',
    'viu_media.cli.interactive.menu.media.results',
    'viu_media.cli.interactive.menu.media.servers',
] + collect_submodules('viu_media')

a = Analysis(
    ['../viu_media/viu.py'],  # Changed entry point
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
     strip=True,  # Strip debug information
    optimize=2   # Optimize bytecode   noarchive=False
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
      optimize=2  # Optimize bytecode  cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='viu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../viu_media/assets/icons/logo.ico'
)
