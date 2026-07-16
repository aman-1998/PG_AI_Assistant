"""Pydantic schemas for chat sessions/messages."""
from __future__ import annotations

import datetime

from pydantic import BaseModel


class ChatStreamRequest(BaseModel):
    message: str
    llm_config_id: int
    session_id: int | None = None
    intent: str | None = None  # optional override: sql_generation|explain_plan|optimization|documentation


class ToolCall(BaseModel):
    tool_name: str
    tool_input: dict
    tool_output: str | None = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    intent: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    id: int
    database_connection_id: int
    llm_config_id: int
    title: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class ChatSessionRenameRequest(BaseModel):
    title: str
