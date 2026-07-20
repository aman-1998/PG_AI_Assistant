"""Configuration for text_to_sql_mcp, loaded from environment / .env file."""
from __future__ import annotations

import json
import secrets as _secrets
import sys
from pathlib import Path

from platformdirs import user_data_dir
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the optional .env next to the executable when frozen (desktop build),
# otherwise next to this module.
_IS_FROZEN = bool(getattr(sys, "frozen", False))
_APP_ROOT = Path(sys.executable).resolve().parent if _IS_FROZEN else Path(__file__).resolve().parent
_ENV_FILE = _APP_ROOT / ".env"

# Must match text_to_sql_backend: same app name -> same secrets.json path, so the
# auto-generated DB-connection token secret is shared between the two processes.
_APP_NAME = "PGAIAssistant"
_SECRETS_FILE = Path(user_data_dir(_APP_NAME, appauthor=False)) / "secrets.json"
_TOKEN_SECRET_PLACEHOLDER = "change-this-shared-secret-with-mcp"


def _get_or_create_secret(name: str) -> str:
    """Return a persisted random secret for ``name`` from the shared secrets.json,
    creating it if neither process has yet. Kept byte-for-byte compatible with
    text_to_sql_backend's implementation so both read the same value."""
    data: dict[str, str] = {}
    try:
        data = json.loads(_SECRETS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        data = {}
    if not data.get(name):
        data[name] = _secrets.token_urlsafe(48)
        _SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        try:
            _SECRETS_FILE.chmod(0o600)
        except OSError:
            pass
    return data[name]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # Must match text_to_sql_backend's DB_CONNECTION_TOKEN_SECRET exactly.
    DB_CONNECTION_TOKEN_SECRET: str = _TOKEN_SECRET_PLACEHOLDER

    HOST: str = "0.0.0.0"
    PORT: int = 8020

    QUERY_TIMEOUT_SECONDS: int = 30
    MAX_ROWS_RETURNED: int = 500
    MAX_CELL_CHARS: int = 2000
    CONNECTION_POOL_TTL_SECONDS: int = 3600

    DB_CONN_TOKEN_HEADER: str = "X-DB-Conn-Token"

    # CSV/JSON query-result export settings.
    EXPORT_DIR: str = "./exports"
    MAX_EXPORT_ROWS: int = 50_000
    EXPORT_TTL_SECONDS: int = 3600
    # Base URL used to build the download_url returned by export tools. Override
    # in .env if the server is reachable at a different host/port (e.g. behind a
    # reverse proxy) than HOST/PORT above.
    EXPORT_PUBLIC_BASE_URL: str = "http://localhost:8020"

    # ER diagram (PNG) generation settings.
    DIAGRAM_DIR: str = "./diagrams"
    DIAGRAM_TTL_SECONDS: int = 3600

    # Multi-statement .sql script generation settings.
    SQL_SCRIPT_DIR: str = "./sql_scripts"
    SQL_SCRIPT_TTL_SECONDS: int = 3600
    SQL_SCRIPT_MAX_STATEMENTS: int = 500

    # Chart (bar/line/pie PNG) generation settings.
    CHART_DIR: str = "./charts"
    CHART_TTL_SECONDS: int = 3600

    @model_validator(mode="after")
    def _resolve_shared_secret(self) -> "Settings":
        # If the token secret was left as the placeholder (i.e. not supplied via
        # env/.env), pull the shared, persisted, auto-generated value so it
        # matches the backend. No-op when a real secret is configured.
        if self.DB_CONNECTION_TOKEN_SECRET == _TOKEN_SECRET_PLACEHOLDER:
            self.DB_CONNECTION_TOKEN_SECRET = _get_or_create_secret("DB_CONNECTION_TOKEN_SECRET")
        return self


settings = Settings()
