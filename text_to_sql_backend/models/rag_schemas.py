"""Pydantic schemas for uploaded-file RAG endpoints."""
from __future__ import annotations

import datetime

from pydantic import BaseModel


class UploadedFileResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    size_kb: int
    status: str
    chunk_count: int

    model_config = {"from_attributes": True}


class UploadedFileListResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    size_kb: int
    status: str
    chunk_count: int
    created_at: datetime.datetime
