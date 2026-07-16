"""Upload endpoints for the RAG feature: .sql files and images (ER diagrams,
schema screenshots) scoped to one database connection. Content is parsed,
chunked, embedded (local model) and stored in a dedicated pgvector store —
never mixed with the control-plane Postgres store or the customer's own Postgres.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config.rag_config import rag_config
from db.models import User
from db.postgres import get_db
from models.rag_schemas import UploadedFileListResponse, UploadedFileResponse
from services import db_connection_service, llm_config_service
from services.auth_service import get_current_user
from services.rag import rag_service
from services.rag.rag_service import RagDisabledError

router = APIRouter(prefix="/database-connections/{connection_id}/uploads", tags=["rag-uploads"])


@router.post("", response_model=UploadedFileResponse, status_code=201)
async def upload_file(
    connection_id: int,
    llm_config_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadedFileResponse:
    db_connection_service.get_connection(db, current_user.id, connection_id)  # 404s if not owned
    llm_config = llm_config_service.get_llm_config(db, current_user.id, llm_config_id)
    llm_credentials = llm_config_service.get_decrypted_credentials(llm_config)

    content = await file.read()
    max_bytes = rag_config.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"File exceeds {rag_config.MAX_UPLOAD_MB}MB limit"
        )

    try:
        record = rag_service.ingest_file(
            filename=file.filename or "upload",
            content=content,
            connection_id=connection_id,
            user_id=current_user.id,
            llm_credentials=llm_credentials,
        )
    except RagDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return UploadedFileResponse.model_validate(record)


@router.get("", response_model=list[UploadedFileListResponse])
def list_uploads(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UploadedFileListResponse]:
    db_connection_service.get_connection(db, current_user.id, connection_id)
    files = rag_service.list_uploaded_files(connection_id, current_user.id)
    return [UploadedFileListResponse.model_validate(f) for f in files]


@router.delete("/{file_id}", status_code=204, response_model=None)
def delete_upload(
    connection_id: int,
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    db_connection_service.get_connection(db, current_user.id, connection_id)
    deleted = rag_service.delete_uploaded_file(file_id, connection_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
