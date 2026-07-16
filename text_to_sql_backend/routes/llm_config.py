"""CRUD endpoints for customer LLM model configuration."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from db.postgres import get_db
from models.llm_config_schemas import LLMConfigCreate, LLMConfigResponse, LLMConfigUpdate
from services import llm_config_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/llm-configs", tags=["llm-configs"])


@router.post("", response_model=LLMConfigResponse, status_code=201)
def create_llm_config(
    payload: LLMConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LLMConfigResponse:
    config = llm_config_service.create_llm_config(db, current_user.id, payload)
    return LLMConfigResponse.model_validate(config)


@router.get("", response_model=list[LLMConfigResponse])
def list_llm_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LLMConfigResponse]:
    configs = llm_config_service.list_llm_configs(db, current_user.id)
    return [LLMConfigResponse.model_validate(c) for c in configs]


@router.get("/{config_id}", response_model=LLMConfigResponse)
def get_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LLMConfigResponse:
    config = llm_config_service.get_llm_config(db, current_user.id, config_id)
    return LLMConfigResponse.model_validate(config)


@router.put("/{config_id}", response_model=LLMConfigResponse)
def update_llm_config(
    config_id: int,
    payload: LLMConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LLMConfigResponse:
    config = llm_config_service.update_llm_config(db, current_user.id, config_id, payload)
    return LLMConfigResponse.model_validate(config)


@router.delete("/{config_id}", status_code=204, response_model=None)
def delete_llm_config(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    llm_config_service.delete_llm_config(db, current_user.id, config_id)
