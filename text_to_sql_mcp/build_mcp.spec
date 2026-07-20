# PyInstaller spec for the text_to_sql_mcp desktop sidecar.
#
# Build (from the text_to_sql_mcp folder, with its venv active):
#   pyinstaller build_mcp.spec --noconfirm
#
# Produces a onedir bundle at dist/pg-ai-mcp/ whose entry binary is
# pg-ai-mcp(.exe). The desktop shell (Tauri) ships this folder and spawns the
# binary as a background process alongside the backend.
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []
hiddenimports = []

_collect_packages = [
    "mcp",
    "matplotlib",
    "PIL",
    "psycopg2",
]
for _pkg in _collect_packages:
    try:
        _d, _b, _h = collect_all(_pkg)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception as _exc:  # noqa: BLE001
        print(f"[build_mcp.spec] skipping {_pkg}: {_exc}")

hiddenimports += collect_submodules("uvicorn")
# Tool modules are imported for their @mcp.tool() registration side-effects; some
# are referenced only via the star-import in server.py, so pin them explicitly.
hiddenimports += collect_submodules("tools")

a = Analysis(
    ["server.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pg-ai-mcp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="pg-ai-mcp",
)
