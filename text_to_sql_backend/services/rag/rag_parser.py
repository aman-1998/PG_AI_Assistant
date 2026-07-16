"""RAG Parser — turns an uploaded file into plain text ready for chunking.

.sql files are already text — decoded as-is (their CREATE TABLE/COMMENT/DDL
statements and inline comments read fine without special parsing).

Images have no text to embed until one is derived: a single vision-capable
LLM call (using the connection's own configured llm_credentials) produces a
description of the image (e.g. an ER diagram or schema screenshot) at
upload time. This is the expensive step that makes persisting the result
worthwhile — chat questions later reuse the stored description instead of
re-running vision inference.
"""
from __future__ import annotations

import base64
import logging

log = logging.getLogger(__name__)

_TEXT_EXTENSIONS = {"sql", "txt"}
_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

_IMAGE_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}

_VISION_PROMPT = (
    "Describe this image in detail for someone building documentation about a SQL database. "
    "If it is an ER diagram, schema diagram, or table structure screenshot, list every table name, "
    "column name, data type, and relationship you can identify. If it is not database-related, "
    "describe what it shows plainly."
)


def supported_extension(filename: str) -> str | None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in _TEXT_EXTENSIONS or ext in _IMAGE_EXTENSIONS:
        return ext
    return None


def _parse_text(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def _parse_image(content: bytes, ext: str, llm_credentials: dict) -> str:
    from langchain_core.messages import HumanMessage

    from services.llm_factory import get_llm_from_credentials

    mime = _IMAGE_MIME.get(ext, "image/png")
    b64 = base64.b64encode(content).decode("ascii")
    llm = get_llm_from_credentials(llm_credentials)
    message = HumanMessage(
        content=[
            {"type": "text", "text": _VISION_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
    )
    try:
        response = llm.invoke([message])
        return response.content if isinstance(response.content, str) else str(response.content)
    except Exception:  # noqa: BLE001
        log.warning("Vision description failed for uploaded image", exc_info=True)
        return "(Image uploaded, but its visual content could not be analyzed by the configured LLM.)"


def parse_upload(filename: str, content: bytes, llm_credentials: dict) -> str:
    """Returns plain text extracted/derived from the upload. Raises ValueError
    for unsupported file types."""
    ext = supported_extension(filename)
    if ext is None:
        raise ValueError(f"Unsupported file type for '{filename}'. Allowed: .sql, .txt, .png, .jpg, .jpeg, .gif, .webp")
    if ext in _TEXT_EXTENSIONS:
        return _parse_text(content)
    return _parse_image(content, ext, llm_credentials)
