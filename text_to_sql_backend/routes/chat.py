"""Chat endpoints: SSE streaming + session/message history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.chat import stream_chat_message
from db.models import ChatMessage, ChatSession, User
from db.postgres import get_db
from models.chat_schemas import (
    ChatMessageResponse,
    ChatSessionRenameRequest,
    ChatSessionResponse,
    ChatStreamRequest,
)
from services import db_connection_service, llm_config_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{connection_id}/stream")
async def chat_stream(
    connection_id: int,
    payload: ChatStreamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    connection = db_connection_service.get_connection(db, current_user.id, connection_id)
    llm_config = llm_config_service.get_llm_config(db, current_user.id, payload.llm_config_id)

    generator = stream_chat_message(
        db=db,
        user_id=current_user.id,
        connection=connection,
        llm_config=llm_config,
        message=payload.message,
        session_id=payload.session_id,
        explicit_intent=payload.intent,
        chat_history_retention_days=current_user.chat_history_retention_days,
        max_chat_sessions=current_user.max_chat_sessions,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSessionResponse]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return [ChatSessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessageResponse]:
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    messages = (
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at).all()
    )
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
def rename_session(
    session_id: int,
    payload: ChatSessionRenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title cannot be empty")
    session.title = title
    db.commit()
    db.refresh(session)
    return ChatSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}", status_code=204, response_model=None)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    db.delete(session)
    db.commit()
