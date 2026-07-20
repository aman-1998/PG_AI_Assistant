"""Application settings loaded from environment variables / .env file."""
from __future__ import annotations

import json
import secrets as _secrets
import sys
from pathlib import Path

from platformdirs import user_data_dir
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# When packaged as a desktop app (PyInstaller / frozen), __file__ points inside
# the bundle's temp extraction dir, so anchor to the executable's folder instead;
# in normal (source) runs, anchor to the backend package root (config/ -> root).
_IS_FROZEN = bool(getattr(sys, "frozen", False))
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_APP_ROOT = Path(sys.executable).resolve().parent if _IS_FROZEN else _BACKEND_ROOT

# Anchor the .env file so it's found no matter which working directory the app
# is launched from. In a frozen desktop build a .env is optional (secrets are
# auto-generated below), but power users can still drop one next to the binary.
_ENV_FILE = _APP_ROOT / ".env"

# Application identity used to derive the per-user data directory.
_APP_NAME = "PGAIAssistant"

# Auto-generated secrets are persisted here (outside DATA_DIR, at a fixed
# per-user location both this backend and the MCP server can compute) so they
# stay stable across restarts and are shared between the two processes.
_SECRETS_FILE = Path(user_data_dir(_APP_NAME, appauthor=False)) / "secrets.json"

# Insecure placeholder values shipped as field defaults. When a secret still
# holds its placeholder (i.e. the operator did not set a real one via env/.env),
# it is replaced at startup with a strong, persisted, auto-generated value.
_SECRET_PLACEHOLDERS = {
    "JWT_SECRET": "change-this-jwt-secret",
    "DATA_ENCRYPTION_KEY": "change-this-data-encryption-key",
    "DB_CONNECTION_TOKEN_SECRET": "change-this-shared-secret-with-mcp",
}


def _get_or_create_secret(name: str) -> str:
    """Return a persisted random secret for ``name``, creating the store on first
    use. Shared with text_to_sql_mcp via the same ``secrets.json`` path so the
    DB-connection token secret matches across processes."""
    data: dict[str, str] = {}
    try:
        data = json.loads(_SECRETS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        data = {}
    if not data.get(name):
        data[name] = _secrets.token_urlsafe(48)
        _SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:  # best-effort: restrict to owner on POSIX
            _SECRETS_FILE.chmod(0o600)
        except OSError:
            pass
    return data[name]

# Default location for all runtime data (the SQLite database, etc.). We store
# data OUTSIDE the code/install tree so app updates, re-clones, pip upgrades, and
# read-only installs never overwrite or lose the user's database. On a fresh
# install this resolves to a "data" subfolder of the OS per-user data directory,
# e.g.
#   Windows: %LOCALAPPDATA%\PGAIAssistant\data
#   Linux:   ~/.local/share/PGAIAssistant/data
#   macOS:   ~/Library/Application Support/PGAIAssistant/data
# giving a final DB path of <app-data-dir>/PGAIAssistant/data/app.db. Override
# with the DATA_DIR env var (e.g. a mounted Docker volume, or "./data" for a
# repo-local development database).
_DEFAULT_DATA_DIR = str(Path(user_data_dir(_APP_NAME, appauthor=False)) / "data")

# Bounds for the user-configurable "how many days of chat history to keep/use as
# context" setting (routes/auth.py's PATCH /auth/me/chat-retention, db.models.User).
CHAT_HISTORY_RETENTION_MIN_DAYS = 1
CHAT_HISTORY_RETENTION_MAX_DAYS = 60
CHAT_HISTORY_RETENTION_DEFAULT_DAYS = 30

# Bounds for the user-configurable "how many chat sessions to keep per database
# connection" setting (routes/auth.py's PATCH /auth/me/max-chat-sessions,
# db.models.User). Oldest sessions beyond this count are automatically deleted
# whenever a new chat session is started.
MAX_CHAT_SESSIONS_MIN = 1
MAX_CHAT_SESSIONS_MAX = 25
MAX_CHAT_SESSIONS_DEFAULT = 15


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # Directory where all runtime data is stored (the SQLite database file, plus
    # any future on-disk artifacts). Kept out of the code/install tree so it
    # survives updates and re-installs. Defaults to the OS per-user data dir; set
    # DATA_DIR in the environment/.env to relocate it. A relative value (e.g.
    # "./data") is resolved against the backend package root, never the CWD.
    DATA_DIR: str = _DEFAULT_DATA_DIR

    # Store for uploaded-file RAG (separate from customer database connections).
    # Optional: if unset, reuses the main SQLite database (its own
    # rag_files/rag_chunks tables) via the sqlite-vec extension. If the vector
    # store is unreachable/misconfigured, the uploaded-file RAG feature is
    # disabled but the rest of the app works normally.
    RAG_DATABASE_URL: str | None = None

    # Auth
    JWT_SECRET: str = "change-this-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Encryption
    DATA_ENCRYPTION_KEY: str = "change-this-data-encryption-key"
    DB_CONNECTION_TOKEN_SECRET: str = "change-this-shared-secret-with-mcp"
    DB_CONNECTION_TOKEN_TTL_SECONDS: int = 3600

    # MCP server
    MCP_SERVER_URL: str = "http://localhost:8020/mcp"

    # Email (password-reset link delivery). Defaults to Gmail SMTP - requires a
    # Gmail "App Password" (not the regular account password; Google disabled
    # plain-password SMTP auth) generated at
    # https://myaccount.google.com/apppasswords (requires 2-Step Verification
    # enabled on the account) and set as SMTP_PASSWORD in .env.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "mishraamankpa@gmail.com"
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "mishraamankpa@gmail.com"
    SMTP_FROM_NAME: str = "PG AI Assistant"

    # Base URL of the frontend, used to build the link embedded in
    # password-reset emails (e.g. "{FRONTEND_BASE_URL}/reset-password?token=...").
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    # How long a password-reset token stays valid before it must be re-requested.
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8010
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def DATABASE_URL(self) -> str:
        """SQLite connection URL for the control-plane store, always derived from
        DATA_DIR. The app is SQLite-only (no Postgres), so this is computed
        rather than configured."""
        return f"sqlite:///{(Path(self.DATA_DIR) / 'app.db').as_posix()}"

    @model_validator(mode="after")
    def _resolve_data_dir(self) -> "Settings":
        # Resolve DATA_DIR: expand "~" and resolve a relative value against the
        # backend root (NOT the fragile process CWD) so the same directory is
        # used regardless of where the server is launched. Create it if missing.
        data_dir = Path(self.DATA_DIR).expanduser()
        if not data_dir.is_absolute():
            data_dir = _APP_ROOT / data_dir
        data_dir = data_dir.resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        self.DATA_DIR = str(data_dir)

        # Replace any secret still holding its insecure placeholder default with
        # a strong, persisted, auto-generated value. No-op when the operator has
        # provided real secrets via env/.env (e.g. Docker deployments).
        for _name, _placeholder in _SECRET_PLACEHOLDERS.items():
            if getattr(self, _name) == _placeholder:
                setattr(self, _name, _get_or_create_secret(_name))
        return self


settings = Settings()
