"""Chunk text for RAG indexing."""

from __future__ import annotations


def chunk_text(text: str, *, chunk_chars: int = 3200, overlap: int = 400) -> list[str]:
    """Rough ~800–1200 token chunks via character windows."""
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_chars:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_chars)
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks
