# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('setup_gui.py', '.'),
        ('notion_api.py', '.'),
    ],
    hiddenimports=[
        'rumps',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._darwin',
        'pyperclip',
        'notion_client',
        'dotenv',
        'tkinter',
        'tkinter.ttk',
        'pkg_resources.py2_warn',
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
    [],
    exclude_binaries=True,
    name='Clip to Notion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # デバッグ用にTrue（リリース時はFalseに変更）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Clip to Notion',
)

app = BUNDLE(
    coll,
    name='Clip to Notion.app',
    icon=None,
    bundle_identifier='com.nishimura.cliptonotion',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSUIElement': '1',  # メニューバーのみ（Dockに表示しない）
        'CFBundleShortVersionString': '3.0.0',
        'CFBundleVersion': '3.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 nishimura-hihi-roaki',
        # アクセシビリティ権限のリクエスト用
        'NSAppleEventsUsageDescription': '選択したテキストを取得するために必要です',
    },
)