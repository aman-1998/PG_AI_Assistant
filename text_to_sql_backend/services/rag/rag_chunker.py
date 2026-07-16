"""RAG Chunker — simple, content-agnostic text chunking.

Splits on paragraph/line boundaries where possible, falling back to a hard
character split, with a small overlap so context isn't lost at chunk
boundaries. Every chunk is prefixed with the source filename so it reads as
a self-contained snippet when retrieved standalone.
"""
from __future__ import annotations

from config.rag_config import rag_config

CHUNK_SIZE = rag_config.CHUNK_SIZE
CHUNK_OVERLAP = rag_config.CHUNK_OVERLAP
MIN_CHUNK_SIZE = rag_config.MIN_CHUNK_SIZE


def _split_text(text: str) -> list[str]:
    """Greedy paragraph-aware split into ~CHUNK_SIZE-char pieces with overlap."""
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= CHUNK_SIZE:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(para) <= CHUNK_SIZE:
            current = para
        else:
            # Hard-split an oversized paragraph
            for i in range(0, len(para), CHUNK_SIZE - CHUNK_OVERLAP):
                piece = para[i : i + CHUNK_SIZE]
                if piece:
                    chunks.append(piece)
            current = ""
    if current:
        chunks.append(current)

    # Apply overlap between consecutive chunks for continuity
    overlapped: list[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0 or CHUNK_OVERLAP <= 0:
            overlapped.append(chunk)
        else:
            prefix = chunks[i - 1][-CHUNK_OVERLAP:]
            overlapped.append(f"{prefix}{chunk}")
    return overlapped


def chunk_text(text: str, source: str) -> list[dict]:
    """Returns list of {text, chunk_index, source}, dropping chunks below
    MIN_CHUNK_SIZE."""
    pieces = _split_text(text)
    chunks = []
    for idx, piece in enumerate(pieces):
        stripped = piece.strip()
        if len(stripped) < MIN_CHUNK_SIZE:
            continue
        chunks.append({"text": f"[{source}]\n{stripped}", "chunk_index": idx, "source": source})
    return chunks
