"""Configuration for text_to_sql_mcp, loaded from environment / .env file."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Must match text_to_sql_backend's DB_CONNECTION_TOKEN_SECRET exactly.
    DB_CONNECTION_TOKEN_SECRET: str = "change-this-shared-secret-with-mcp"

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


settings = Settings()
