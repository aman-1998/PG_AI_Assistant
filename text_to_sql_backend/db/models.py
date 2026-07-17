"""ORM models for the Postgres control-plane store."""
from __future__ import annotations

import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.settings import CHAT_HISTORY_RETENTION_DEFAULT_DAYS, MAX_CHAT_SESSIONS_DEFAULT
from db.postgres import Base


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # How many days of chat history to load as context / retain before it's purged.
    # User-configurable from the UI, capped at 60 days (see CHAT_HISTORY_RETENTION_MAX_DAYS).
    chat_history_retention_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=CHAT_HISTORY_RETENTION_DEFAULT_DAYS
    )
    # Max number of chat sessions to keep per database connection. User-configurable
    # from the UI (1-20, see MAX_CHAT_SESSIONS_MIN/MAX). Oldest sessions beyond this
    # count are deleted whenever a new chat session is started.
    max_chat_sessions: Mapped[int] = mapped_column(Integer, nullable=False, default=MAX_CHAT_SESSIONS_DEFAULT)
    # SHA-256 hash of the current password-reset token (never store the raw
    # token), and when it expires. Both null when no reset is pending.
    reset_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    database_connections: Mapped[list["DatabaseConnection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    llm_configs: Mapped[list["LLMConfig"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class DatabaseConnection(Base):
    __tablename__ = "database_connections"
    __table_args__ = (UniqueConstraint("user_id", "alias", name="uq_user_alias"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(120), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=5432)
    db_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    sslmode: Mapped[str] = mapped_column(String(32), default="prefer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_check_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="database_connections")


class LLMConfig(Base):
    __tablename__ = "llm_configs"
    __table_args__ = (UniqueConstraint("user_id", "alias", name="uq_user_llm_alias"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(120), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # openai|anthropic|gemini|azure_openai|bedrock
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_secret_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # bedrock secret access key
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # azure endpoint / custom base url
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)  # bedrock region
    api_version: Mapped[str | None] = mapped_column(String(64), nullable=True)  # azure api version
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="llm_configs")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="llm_config", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    database_connection_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("database_connections.id"), nullable=False, index=True
    )
    llm_config_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("llm_configs.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    llm_config: Mapped["LLMConfig"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user|assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class Feedback(Base):
    """User-submitted product feedback from the "Contact & Feedback" page.
    `rating` is optional (1-5 stars) since a user may just want to leave a
    comment without rating the product.
    """

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship()
