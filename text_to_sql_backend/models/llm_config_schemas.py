"""Pydantic schemas for customer LLM model configuration."""
from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, Field

Provider = Literal["openai", "anthropic", "gemini", "azure_openai", "bedrock"]


class LLMConfigCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    alias: str = Field(min_length=1, max_length=120)
    provider: Provider
    model_name: str
    api_key: str | None = None
    secret_key: str | None = None  # bedrock secret access key
    base_url: str | None = None  # azure endpoint / custom base url
    region: str | None = None  # bedrock region
    api_version: str | None = None  # azure api version


class LLMConfigUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}

    alias: str | None = None
    model_name: str | None = None
    api_key: str | None = None
    secret_key: str | None = None
    base_url: str | None = None
    region: str | None = None
    api_version: str | None = None
    is_active: bool | None = None


class LLMConfigResponse(BaseModel):
    model_config = {"from_attributes": True, "protected_namespaces": ()}

    id: int
    alias: str
    provider: str
    model_name: str
    base_url: str | None = None
    region: str | None = None
    api_version: str | None = None
    is_active: bool
    created_at: datetime.datetime
