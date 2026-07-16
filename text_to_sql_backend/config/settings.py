"""Application settings loaded from environment variables / .env file."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

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
MAX_CHAT_SESSIONS_MAX = 20
MAX_CHAT_SESSIONS_DEFAULT = 15


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres control-plane store.
    # NOTE: for real deployments, override this via the .env file instead of
    # editing this hardcoded default — committing real credentials to source
    # control is a security risk (CWE-798). This default is only meant as a
    # fallback for local dev.
    DATABASE_URL: str = "postgresql+psycopg2://postgres:root@localhost:5432/aiassistant?sslmode=disable"

    # Postgres schema the control-plane tables (and, unless overridden, the RAG
    # tables) are created in/looked up from — instead of the default "public" schema.
    DB_SCHEMA: str = "nltosql"

    # Postgres + pgvector store for uploaded-file RAG (separate from customer Postgres
    # connections). Optional: if unset, reuses DATABASE_URL (same Postgres server, its
    # own rag_files/rag_chunks tables). If unreachable/misconfigured (e.g. pgvector
    # extension unavailable), the uploaded-file RAG feature is disabled but the rest of
    # the app works normally.
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


settings = Settings()
