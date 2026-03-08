"""ChromaDB connection and collection management."""

import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create a ChromaDB client (singleton)."""
    global _client
    if _client is None:
        try:
            _client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            # Verify connectivity
            _client.heartbeat()
            logger.info(
                "Connected to ChromaDB at %s:%s",
                settings.chroma_host,
                settings.chroma_port,
            )
        except Exception:
            logger.warning(
                "ChromaDB server unavailable at %s:%s — falling back to ephemeral client",
                settings.chroma_host,
                settings.chroma_port,
            )
            _client = chromadb.EphemeralClient(
                settings=ChromaSettings(anonymized_telemetry=False),
            )
    return _client


def get_collection(name: str) -> chromadb.Collection:
    """Get or create a named ChromaDB collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def reset_client() -> None:
    """Reset the singleton client (useful for testing)."""
    global _client
    _client = None
