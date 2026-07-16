"""Signup / login / current-user endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.postgres import get_db
from models.auth_schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    TokenResponse,
    UpdateChatRetentionRequest,
    UpdateMaxChatSessionsRequest,
    UserResponse,
)
from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_password_reset_token,
    get_current_user,
    reset_password_with_token,
    signup_user,
)
from services.email_service import send_password_reset_email
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = signup_user(db, payload.email, payload.password, payload.full_name)
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, expires_in_minutes=settings.JWT_EXPIRE_MINUTES)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, expires_in_minutes=settings.JWT_EXPIRE_MINUTES)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    """Always responds with the same generic message regardless of whether the
    email is registered, to avoid leaking which emails have accounts."""
    token = create_password_reset_token(db, payload.email)
    if token:
        reset_link = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/reset-password?token={token}"
        try:
            send_password_reset_email(payload.email, reset_link)
        except Exception:  # noqa: BLE001 - don't let SMTP errors leak to the client or block the response
            logger.warning("Failed to send password reset email to %s", payload.email, exc_info=True)
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    reset_password_with_token(db, payload.token, payload.new_password)
    return {"message": "Password has been reset successfully. You can now log in."}


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me/chat-retention", response_model=UserResponse)
def update_chat_retention(
    payload: UpdateChatRetentionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserResponse:
    """Update how many days of chat history to keep/use as context (1-60, user-configurable from the UI)."""
    current_user.chat_history_retention_days = payload.chat_history_retention_days
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.patch("/me/max-chat-sessions", response_model=UserResponse)
def update_max_chat_sessions(
    payload: UpdateMaxChatSessionsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserResponse:
    """Update how many chat sessions to keep per database connection (1-20, user-configurable from the UI)."""
    current_user.max_chat_sessions = payload.max_chat_sessions
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
