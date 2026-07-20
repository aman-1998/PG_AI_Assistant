# PyInstaller spec for the text_to_sql_backend desktop sidecar.
#
# Build (from the text_to_sql_backend folder, with its venv active):
#   pyinstaller build_backend.spec --noconfirm
#
# Produces a onedir bundle at dist/pg-ai-backend/ whose entry binary is
# pg-ai-backend(.exe). The desktop shell (Tauri) ships this folder and spawns
# the binary as a background process.
#
# onedir (not onefile) is intentional: this app pulls large native deps
# (onnxruntime via fastembed, sqlite-vec, tokenizers). A onefile build would be
# hundreds of MB and re-extract on every launch; onedir starts fast.
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []
hiddenimports = []

# Packages with data files / native libs / lazily-imported submodules that
# PyInstaller's static analysis misses. Wrapped in try/except so an absent
# optional package does not abort the build.
_collect_packages = [
    "sqlite_vec",
    "fastembed",
    "onnxruntime",
    "tokenizers",
    "huggingface_hub",
    "langgraph",
    "langchain",
    "langchain_core",
    "langchain_openai",
    "langchain_anthropic",
    "langchain_google_genai",
    "langchain_aws",
    "langchain_groq",
    "langchain_mcp_adapters",
    "passlib",
    "jose",
    "psycopg2",
]
for _pkg in _collect_packages:
    try:
        _d, _b, _h = collect_all(_pkg)
        datas += _d
        binaries += _b
        hiddenimports += _h
    except Exception as _exc:  # noqa: BLE001
        print(f"[build_backend.spec] skipping {_pkg}: {_exc}")

# Dynamically-selected server internals and password backends.
hiddenimports += collect_submodules("uvicorn")
hiddenimports += [
    "passlib.handlers.bcrypt",
    "bcrypt",
    "email_validator",
]

a = Analysis(
    ["run.py"],
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
    name="pg-ai-backend",
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
    name="pg-ai-backend",
)
