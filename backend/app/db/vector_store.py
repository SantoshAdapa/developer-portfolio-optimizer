"""Vector store abstraction over ChromaDB operations."""

import logging

from app.db.chroma_client import get_collection

logger = logging.getLogger(__name__)

# Default collection names
RESUME_COLLECTION = "resumes"
SKILLS_COLLECTION = "skills"


def store_embeddings(
    collection_name: str,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict] | None = None,
) -> None:
    """Upsert document embeddings into a ChromaDB collection."""
    collection = get_collection(collection_name)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas or [{} for _ in ids],
    )
    logger.info(
        "Stored %d embeddings in collection '%s'", len(ids), collection_name
    )


def query_similar(
    collection_name: str,
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
) -> dict:
    """Query a collection for the most similar documents.

    Returns ChromaDB result dict with keys:
        ids, documents, metadatas, distances
    """
    collection = get_collection(collection_name)

    kwargs: dict = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)
    return results


def delete_by_analysis_id(
    collection_name: str,
    analysis_id: str,
) -> None:
    """Remove all documents for a given analysis_id from a collection."""
    collection = get_collection(collection_name)
    collection.delete(where={"analysis_id": analysis_id})
    logger.info(
        "Deleted embeddings for analysis '%s' from '%s'",
        analysis_id,
        collection_name,
    )


def collection_count(collection_name: str) -> int:
    """Return the number of documents in a collection."""
    collection = get_collection(collection_name)
    return collection.count()
