"""RAG pipeline — retrieval-augmented generation using ChromaDB + Gemini."""

import json
import logging

from app.ai.embeddings import generate_query_embedding
from app.ai.gemini_client import generate_json
from app.db.vector_store import RESUME_COLLECTION, query_similar
from app.models.schemas import GitHubSummary, Skill

logger = logging.getLogger(__name__)


async def retrieve_relevant_chunks(
    query: str,
    analysis_id: str,
    n_results: int = 5,
    collection_name: str = RESUME_COLLECTION,
) -> list[str]:
    """Retrieve the most relevant resume chunks for a given query.

    Embeds the query, then performs cosine similarity search in ChromaDB
    filtered to the specific analysis_id.
    """
    query_embedding = await generate_query_embedding(query)

    results = query_similar(
        collection_name=collection_name,
        query_embedding=query_embedding,
        n_results=n_results,
        where={"analysis_id": analysis_id},
    )

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    logger.info(
        "Retrieved %d chunks for query (distances: %s)",
        len(documents),
        [round(d, 3) for d in distances[:3]],
    )
    return documents


def build_rag_context(
    retrieved_chunks: list[str],
    skills: list[Skill] | None = None,
    github: GitHubSummary | None = None,
) -> str:
    """Assemble RAG context from retrieved chunks + structured data."""
    parts: list[str] = []

    if retrieved_chunks:
        chunks_text = "\n---\n".join(retrieved_chunks)
        parts.append(f"## Relevant Resume Sections\n{chunks_text}")

    if skills:
        skill_lines = [
            f"- {s.name} ({s.category.value}, {s.proficiency.value})"
            for s in skills
        ]
        parts.append("## Extracted Skills\n" + "\n".join(skill_lines))

    if github:
        gh_lines = [
            f"Username: {github.username}",
            f"Public repos: {github.public_repos}",
            f"Followers: {github.followers}",
            f"Total stars: {github.total_stars}",
            f"Commit frequency: {github.commit_frequency.value}",
            f"Top languages: {json.dumps(github.top_languages)}",
        ]
        if github.notable_repos:
            for r in github.notable_repos[:8]:
                gh_lines.append(
                    f"  Repo: {r.name} | {r.language or 'N/A'} | "
                    f"★{r.stars} | {r.description or ''}"
                )
        parts.append("## GitHub Profile\n" + "\n".join(gh_lines))

    return "\n\n".join(parts)


async def rag_generate(
    task_query: str,
    prompt_template: str,
    analysis_id: str,
    skills: list[Skill] | None = None,
    github: GitHubSummary | None = None,
    n_chunks: int = 5,
) -> dict | list:
    """Full RAG pipeline: retrieve → augment → generate.

    1. Retrieves relevant resume chunks from ChromaDB
    2. Builds context from chunks + skills + GitHub data
    3. Inserts context into prompt template
    4. Sends to Gemini and parses JSON response

    Args:
        task_query: The query used for retrieval (e.g. "career experience and skills").
        prompt_template: A prompt string with a {context} placeholder.
        analysis_id: The analysis to retrieve chunks for.
        skills: Extracted skills (optional).
        github: GitHub summary (optional).
        n_chunks: Number of chunks to retrieve.

    Returns:
        Parsed JSON response from Gemini.
    """
    # Step 1: Retrieve
    chunks = await retrieve_relevant_chunks(
        query=task_query,
        analysis_id=analysis_id,
        n_results=n_chunks,
    )

    # Step 2: Augment
    context = build_rag_context(chunks, skills, github)

    # Step 3: Generate
    full_prompt = prompt_template.replace("{context}", context)
    result = await generate_json(full_prompt)

    logger.info(
        "RAG pipeline completed for analysis '%s' (retrieved %d chunks)",
        analysis_id,
        len(chunks),
    )
    return result
