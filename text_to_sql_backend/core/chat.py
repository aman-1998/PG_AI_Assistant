"""Core chat orchestration: resolve intent -> build agent -> stream tokens/tool
events over SSE -> persist the turn to Postgres. Mirrors ai-service/core/chat.py's
astream_events() loop, with chat_sessions/chat_messages persistence instead of
the reference's in-memory-only session store.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import time
from typing import AsyncGenerator

from sqlalchemy.orm import Session

from core import orchestrator
from db.models import ChatMessage, ChatSession, DatabaseConnection, LLMConfig
from services.llm_config_service import get_decrypted_credentials
from services.llm_factory import extract_provider_error_message

_HISTORY_TURNS = 10


def _sse(event_type: str, **payload) -> str:
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data)}\n\n"


def _extract_text(content) -> str:
    """LangChain message content is usually a plain string, but some providers
    (notably Anthropic) stream it as a list of content blocks, e.g.
    [{"type": "text", "text": "..."}] or [{"type": "thinking", ...}] - pull out
    just the actual text pieces so replies aren't silently dropped."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)
    return ""


def _get_or_create_session(
    db: Session,
    *,
    user_id: int,
    connection: DatabaseConnection,
    llm_config: LLMConfig,
    session_id: int | None,
    first_message: str,
    max_chat_sessions: int,
) -> ChatSession:
    if session_id:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
            .first()
        )
        if session:
            return session
    title = first_message.strip().splitlines()[0][:80] if first_message.strip() else None
    session = ChatSession(
        user_id=user_id,
        database_connection_id=connection.id,
        llm_config_id=llm_config.id,
        title=title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    _prune_excess_sessions(db, user_id=user_id, connection_id=connection.id, max_chat_sessions=max_chat_sessions)
    return session


def _prune_excess_sessions(db: Session, *, user_id: int, connection_id: int, max_chat_sessions: int) -> None:
    """Keep at most `max_chat_sessions` sessions per (user, database connection),
    deleting the oldest ones (by last-updated) beyond that count. Runs whenever
    a new session is created, mirroring ChatGPT's "drop the oldest chat" behavior.
    """
    session_ids = [
        s.id
        for s in db.query(ChatSession.id)
        .filter(ChatSession.user_id == user_id, ChatSession.database_connection_id == connection_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    ]
    stale_ids = session_ids[max_chat_sessions:]
    if not stale_ids:
        return
    db.query(ChatSession).filter(ChatSession.id.in_(stale_ids)).delete(synchronize_session=False)
    db.commit()


def _purge_expired_messages(db: Session, user_id: int, retention_days: int) -> None:
    """Delete this user's chat messages older than their configured retention
    window. Runs on every chat request, scoped to their own sessions only.
    """
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)
    session_ids = [s.id for s in db.query(ChatSession.id).filter(ChatSession.user_id == user_id)]
    if not session_ids:
        return
    db.query(ChatMessage).filter(
        ChatMessage.session_id.in_(session_ids), ChatMessage.created_at < cutoff
    ).delete(synchronize_session=False)
    db.commit()


def _load_history(db: Session, session_id: int, retention_days: int) -> list[dict]:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=retention_days)
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id, ChatMessage.created_at >= cutoff)
        .order_by(ChatMessage.created_at.desc())
        .limit(_HISTORY_TURNS * 2)
        .all()
    )
    messages.reverse()
    # Some older assistant turns were persisted with empty content (e.g. from
    # before the Bedrock non-streaming fallback was added, or a tool-only turn
    # with no text). Replaying an empty-content message back to Bedrock's
    # Converse API is rejected outright ("The content field in the Message
    # object at messages.N is empty"), so drop them - they add no useful
    # context anyway.
    return [{"role": m.role, "content": m.content} for m in messages if m.content]


def _persist_turn(
    db: Session,
    session: ChatSession,
    *,
    user_message: str,
    assistant_reply: str,
    tool_calls: list[dict],
    intent: str,
) -> None:
    # An empty assistant reply (e.g. a tool-only turn where the final leg
    # never produced any text) must never be stored as-is - replaying it as
    # history later gets rejected outright by Bedrock's Converse API. See
    # `_load_history` above for the corresponding read-side guard.
    assistant_reply = assistant_reply or "(no response)"
    db.add(ChatMessage(session_id=session.id, role="user", content=user_message))
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_reply,
            tool_calls_json=json.dumps(tool_calls) if tool_calls else None,
            intent=intent,
        )
    )
    db.commit()


async def stream_chat_message(
    *,
    db: Session,
    user_id: int,
    connection: DatabaseConnection,
    llm_config: LLMConfig,
    message: str,
    session_id: int | None,
    explicit_intent: str | None,
    chat_history_retention_days: int,
    max_chat_sessions: int,
) -> AsyncGenerator[str, None]:
    start = time.perf_counter()
    _purge_expired_messages(db, user_id, chat_history_retention_days)
    session = _get_or_create_session(
        db,
        user_id=user_id,
        connection=connection,
        llm_config=llm_config,
        session_id=session_id,
        first_message=message,
        max_chat_sessions=max_chat_sessions,
    )
    history = _load_history(db, session.id, chat_history_retention_days)
    llm_credentials = get_decrypted_credentials(llm_config)

    yield _sse("session", session_id=session.id)

    try:
        resolved_intent = await orchestrator.resolve_intent(
            explicit_intent=explicit_intent, message=message, history=history, llm_credentials=llm_credentials
        )
        agent = await orchestrator.get_agent_for_intent(
            intent=resolved_intent,
            user_id=user_id,
            connection=connection,
            llm_config_id=llm_config.id,
            llm_credentials=llm_credentials,
        )
    except Exception as exc:  # noqa: BLE001
        yield _sse("error", message=f"Failed to prepare agent: {extract_provider_error_message(exc)}")
        return

    input_messages = history + [{"role": "user", "content": message}]
    reply_text = ""
    tool_calls: list[dict] = []
    # Tracks whether a tool call just finished, so the next bit of assistant
    # text gets a paragraph break inserted before it (see below).
    pending_separator = False
    # Some providers/models - notably AWS Bedrock's ChatBedrockConverse - never
    # emit any on_chat_model_stream events with text at all (confirmed via a
    # debug run: zero stream chunks across every leg, even though the final
    # message clearly has text in on_chat_model_end). Without this fallback,
    # reply_text stays empty for the whole turn and the user gets no response.
    # Track whether real streaming text ever arrived, and separately stash each
    # leg's final text so it can be used instead if streaming never happened.
    streamed_any_text = False
    fallback_text_pieces: list[str] = []

    try:
        async for event in agent.astream_events(
            {"messages": input_messages}, version="v2", config={"recursion_limit": 50}
        ):
            kind = event.get("event")

            if kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                content = getattr(chunk, "content", None) if chunk else None
                text = _extract_text(content)
                if text:
                    # The agent's reply is often split across multiple separate LLM
                    # "legs" around tool calls (e.g. a CREATE TABLE call followed by
                    # an INSERT call). Those text chunks get concatenated back-to-back
                    # with no separator, which can produce things like
                    # "**Step 1**Table created!" or even "**Step 2****Step 3**" (bold
                    # delimiters directly touching) - markdown can fail to render such
                    # runs as bold at all, showing literal asterisks instead. Insert a
                    # paragraph break before resuming text right after a tool call.
                    if pending_separator and reply_text and not reply_text.endswith("\n"):
                        separator = "\n\n"
                        reply_text += separator
                        yield _sse("reply_chunk", content=separator)
                    pending_separator = False
                    reply_text += text
                    yield _sse("reply_chunk", content=text)
                    streamed_any_text = True

            elif kind == "on_chat_model_end":
                output = event.get("data", {}).get("output")
                leg_text = _extract_text(getattr(output, "content", None))
                if leg_text:
                    fallback_text_pieces.append(leg_text)

            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown_tool")
                yield _sse("status", label=f"Running {tool_name}...", tool=tool_name)

            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown_tool")
                tool_input = event.get("data", {}).get("input", {})
                tool_output = event.get("data", {}).get("output")
                tool_calls.append(
                    {
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "tool_output": str(tool_output)[:4000] if tool_output is not None else None,
                    }
                )
                pending_separator = True
                yield _sse("tool_done", tool=tool_name)

    except Exception as exc:  # noqa: BLE001
        # The frontend's "done" handler unconditionally overwrites the message
        # bubble with `reply`, so if reply_text stayed generic here the
        # specific error sent via the "error" event above would get masked a
        # moment later - fold the real reason into reply_text too so it's
        # still visible even after that overwrite.
        error_detail = extract_provider_error_message(exc)
        yield _sse("error", message=f"Agent execution failed: {error_detail}")
        reply_text = reply_text or f"Sorry, something went wrong while processing your request: {error_detail}"
    except (asyncio.CancelledError, GeneratorExit):
        # The client disconnected - most commonly because the user clicked
        # "Stop" mid-stream. Persist whatever partial reply/tool calls were
        # gathered so far so the turn isn't silently lost from history, then
        # re-raise: swallowing GeneratorExit/CancelledError here without
        # propagating it is invalid and would break the generator's shutdown.
        if not streamed_any_text and fallback_text_pieces:
            reply_text = "\n\n".join(fallback_text_pieces)
        _persist_turn(
            db,
            session,
            user_message=message,
            assistant_reply=reply_text or "(stopped by user)",
            tool_calls=tool_calls,
            intent=resolved_intent,
        )
        raise

    if not streamed_any_text and fallback_text_pieces:
        reply_text = "\n\n".join(fallback_text_pieces)
        yield _sse("reply_chunk", content=reply_text)

    _persist_turn(
        db, session, user_message=message, assistant_reply=reply_text, tool_calls=tool_calls, intent=resolved_intent
    )

    duration_ms = int((time.perf_counter() - start) * 1000)
    yield _sse("done", reply=reply_text, tool_calls=tool_calls, duration_ms=duration_ms, intent=resolved_intent)
