"""Embedding service — generates vector embeddings via Gemini text-embedding-004."""

import logging

import google.generativeai as genai

from app.config import settings
from app.db.vector_store import RESUME_COLLECTION, store_embeddings

logger = logging.getLogger(__name__)


def _ensure_configured() -> None:
    genai.configure(api_key=settings.gemini_api_key)


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for a single text string."""
    _ensure_configured()
    result = genai.embed_content(
        model=f"models/{settings.gemini_embedding_model}",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts.

    Gemini embed_content supports batching via a list of strings.
    """
    if not texts:
        return []

    _ensure_configured()
    result = genai.embed_content(
        model=f"models/{settings.gemini_embedding_model}",
        content=texts,
        task_type="retrieval_document",
    )
    embedding = result["embedding"]
    # Gemini returns list[list[float]] for batch, list[float] for single
    if isinstance(embedding[0], float):
        return [embedding]  # type: ignore[list-item]
    return embedding  # type: ignore[return-value]


async def generate_query_embedding(text: str) -> list[float]:
    """Generate an embedding optimized for retrieval queries."""
    _ensure_configured()
    result = genai.embed_content(
        model=f"models/{settings.gemini_embedding_model}",
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


async def embed_and_store_chunks(
    analysis_id: str,
    chunks: list[str],
    collection_name: str = RESUME_COLLECTION,
) -> int:
    """Embed text chunks and store them in ChromaDB.

    Args:
        analysis_id: Unique identifier to group these chunks.
        chunks: List of text chunks to embed.
        collection_name: ChromaDB collection name.

    Returns:
        Number of chunks stored.
    """
    if not chunks:
        return 0

    embeddings = await generate_embeddings_batch(chunks)

    ids = [f"{analysis_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas: list[dict[str, str | int | float | bool]] = [
        {"analysis_id": analysis_id, "chunk_index": i, "source": "resume"}
        for i in range(len(chunks))
    ]

    store_embeddings(
        collection_name=collection_name,
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info(
        "Embedded and stored %d chunks for analysis '%s'",
        len(chunks),
        analysis_id,
    )
    return len(chunks)
