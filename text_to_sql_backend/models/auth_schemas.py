"""Pydantic schemas for authentication."""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from config.settings import (
    CHAT_HISTORY_RETENTION_MAX_DAYS,
    CHAT_HISTORY_RETENTION_MIN_DAYS,
    MAX_CHAT_SESSIONS_MAX,
    MAX_CHAT_SESSIONS_MIN,
)


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    chat_history_retention_days: int
    max_chat_sessions: int

    model_config = {"from_attributes": True}


class UpdateChatRetentionRequest(BaseModel):
    """User-configurable "how many days of chat history to keep/use as context"
    setting, editable from the chat UI. Capped at 60 days.
    """

    chat_history_retention_days: int = Field(
        ge=CHAT_HISTORY_RETENTION_MIN_DAYS, le=CHAT_HISTORY_RETENTION_MAX_DAYS
    )


class UpdateMaxChatSessionsRequest(BaseModel):
    """User-configurable "how many chat sessions to keep per database connection"
    setting, editable from the Settings page. Bounded to 1-20.
    """

    max_chat_sessions: int = Field(ge=MAX_CHAT_SESSIONS_MIN, le=MAX_CHAT_SESSIONS_MAX)
