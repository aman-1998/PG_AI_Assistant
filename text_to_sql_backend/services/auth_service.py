"""Signup / login / JWT issuance and the get_current_user FastAPI dependency."""
from __future__ import annotations

import datetime
import hashlib
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import User
from db.database import get_db

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def signup_user(db: Session, email: str, password: str, full_name: str | None) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return user


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(db: Session, email: str) -> str | None:
    """Generate + store a password-reset token for the user with this email, if
    one exists. Returns the raw token (only ever placed in the emailed link -
    the DB only stores its hash), or None if no such user.

    Callers must respond identically whether or not a token was returned, so
    the API never reveals which emails are registered.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    token = secrets.token_urlsafe(32)
    user.reset_token_hash = _hash_reset_token(token)
    user.reset_token_expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )
    db.add(user)
    db.commit()
    return token


def reset_password_with_token(db: Session, token: str, new_password: str) -> None:
    token_hash = _hash_reset_token(token)
    user = db.query(User).filter(User.reset_token_hash == token_hash).first()
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = user.reset_token_expires_at if user else None
    # SQLite doesn't preserve timezone info, so datetimes come back naive even
    # though they were stored as UTC; normalise before comparing to avoid a
    # "can't compare offset-naive and offset-aware datetimes" TypeError.
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    if not user or not expires_at or expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user.password_hash = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.add(user)
    db.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
