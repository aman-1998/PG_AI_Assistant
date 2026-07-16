"""CRUD for customer LLM model configurations (encrypts secrets at rest)."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import LLMConfig
from models.llm_config_schemas import LLMConfigCreate, LLMConfigUpdate
from services.encryption_util import decrypt_text, encrypt_text
from services.llm_factory import validate_llm_credentials


def create_llm_config(db: Session, user_id: int, payload: LLMConfigCreate) -> LLMConfig:
    existing = db.query(LLMConfig).filter(LLMConfig.user_id == user_id, LLMConfig.alias == payload.alias).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already in use")

    try:
        validate_llm_credentials(
            {
                "provider": payload.provider,
                "model_name": payload.model_name,
                "api_key": payload.api_key,
                "secret_key": payload.secret_key,
                "base_url": payload.base_url,
                "region": payload.region,
                "api_version": payload.api_version,
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    config = LLMConfig(
        user_id=user_id,
        alias=payload.alias,
        provider=payload.provider,
        model_name=payload.model_name,
        encrypted_api_key=encrypt_text(payload.api_key, settings.DATA_ENCRYPTION_KEY) if payload.api_key else None,
        encrypted_secret_key=(
            encrypt_text(payload.secret_key, settings.DATA_ENCRYPTION_KEY) if payload.secret_key else None
        ),
        base_url=payload.base_url,
        region=payload.region,
        api_version=payload.api_version,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def list_llm_configs(db: Session, user_id: int) -> list[LLMConfig]:
    return db.query(LLMConfig).filter(LLMConfig.user_id == user_id).order_by(LLMConfig.created_at).all()


def get_llm_config(db: Session, user_id: int, config_id: int) -> LLMConfig:
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id, LLMConfig.user_id == user_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LLM config not found")
    return config


def update_llm_config(db: Session, user_id: int, config_id: int, payload: LLMConfigUpdate) -> LLMConfig:
    config = get_llm_config(db, user_id, config_id)
    data = payload.model_dump(exclude_unset=True)
    api_key = data.pop("api_key", None)
    secret_key = data.pop("secret_key", None)

    # Re-validate against the real provider whenever anything that affects
    # connectivity changes, so bad credentials/model names never get saved.
    connectivity_fields = {"model_name", "base_url", "region", "api_version"}
    if api_key or secret_key or connectivity_fields & data.keys():
        creds = {
            "provider": config.provider,
            "model_name": data.get("model_name", config.model_name),
            "api_key": api_key
            or (decrypt_text(config.encrypted_api_key, settings.DATA_ENCRYPTION_KEY) if config.encrypted_api_key else None),
            "secret_key": secret_key
            or (
                decrypt_text(config.encrypted_secret_key, settings.DATA_ENCRYPTION_KEY)
                if config.encrypted_secret_key
                else None
            ),
            "base_url": data.get("base_url", config.base_url),
            "region": data.get("region", config.region),
            "api_version": data.get("api_version", config.api_version),
        }
        try:
            validate_llm_credentials(creds)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    for field, value in data.items():
        setattr(config, field, value)
    if api_key:
        config.encrypted_api_key = encrypt_text(api_key, settings.DATA_ENCRYPTION_KEY)
    if secret_key:
        config.encrypted_secret_key = encrypt_text(secret_key, settings.DATA_ENCRYPTION_KEY)
    db.commit()
    db.refresh(config)
    return config


def delete_llm_config(db: Session, user_id: int, config_id: int) -> None:
    config = get_llm_config(db, user_id, config_id)
    db.delete(config)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete this LLM model because it has already been used in one or more chats. "
            "Delete those chat sessions first, or keep this model.",
        ) from exc


def get_decrypted_credentials(config: LLMConfig) -> dict:
    return {
        "provider": config.provider,
        "model_name": config.model_name,
        "api_key": decrypt_text(config.encrypted_api_key, settings.DATA_ENCRYPTION_KEY) if config.encrypted_api_key else None,
        "secret_key": (
            decrypt_text(config.encrypted_secret_key, settings.DATA_ENCRYPTION_KEY) if config.encrypted_secret_key else None
        ),
        "base_url": config.base_url,
        "region": config.region,
        "api_version": config.api_version,
    }
