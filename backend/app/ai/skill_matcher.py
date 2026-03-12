"""Semantic skill matching using embedding similarity.

Uses Gemini text-embedding-004 to compute cosine similarity between
skill names, enabling fuzzy/semantic matches like:
  "Deep Learning" ↔ "Neural Networks"
  "NLP" ↔ "Natural Language Processing"

Falls back to normalisation-based matching when embeddings are unavailable.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import math
from typing import NamedTuple, cast

import google.generativeai as genai

from app.config import settings
from app.data.skill_normalization import normalize_skill

logger = logging.getLogger(__name__)

# Cosine-similarity threshold to consider two skills a semantic match
SIMILARITY_THRESHOLD = 0.82

# Cache: skill_text → embedding vector (populated lazily)
_embedding_cache: dict[str, list[float]] = {}


class SkillMatchResult(NamedTuple):
    """Result of matching a single required skill against a developer's skills."""

    skill: str  # canonical name of the required skill
    matched_to: str | None  # the developer skill it matched, or None
    similarity: float  # 0.0 – 1.0
    match_type: str  # "exact" | "alias" | "semantic" | "none"


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


async def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts, using cache where possible."""
    uncached_texts: list[str] = []
    uncached_indices: list[int] = []

    for i, text in enumerate(texts):
        if text.lower() not in _embedding_cache:
            uncached_texts.append(text)
            uncached_indices.append(i)

    if uncached_texts:
        try:
            genai.configure(api_key=settings.gemini_api_key)
            result = await asyncio.to_thread(
                functools.partial(
                    genai.embed_content,
                    model=f"models/{settings.gemini_embedding_model}",
                    content=uncached_texts,
                    task_type="semantic_similarity",
                )
            )
            raw_embeddings = result["embedding"]
            if not isinstance(raw_embeddings, list) or not raw_embeddings:
                return []

            first_item = raw_embeddings[0]
            embeddings: list[list[float]]
            if isinstance(first_item, float):
                embeddings = [cast(list[float], raw_embeddings)]
            else:
                embeddings = cast(list[list[float]], raw_embeddings)

            for text, emb in zip(uncached_texts, embeddings):
                _embedding_cache[text.lower()] = emb
        except Exception:
            logger.warning(
                "Embedding generation failed, falling back to alias matching"
            )
            return []

    return [_embedding_cache.get(t.lower(), []) for t in texts]


def _exact_or_alias_match(
    required_skill: str,
    dev_skills_normalized: dict[str, str],
) -> str | None:
    """Try exact canonical match (case-insensitive).

    ``dev_skills_normalized`` maps canonical_lower → original_name.
    """
    canon = normalize_skill(required_skill).lower()
    return dev_skills_normalized.get(canon)


async def match_skills_semantic(
    required_skills: list[str],
    developer_skills: list[str],
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[SkillMatchResult]:
    """Match required skills against developer skills using multi-tier matching.

    Tier 1: Exact canonical name match (via normalisation).
    Tier 2: Embedding cosine similarity ≥ threshold.
    Tier 3: No match → gap.
    """
    # Normalize developer skills for O(1) lookups
    dev_normalized: dict[str, str] = {}
    for s in developer_skills:
        canon = normalize_skill(s).lower()
        dev_normalized[canon] = s

    results: list[SkillMatchResult] = []
    needs_semantic: list[int] = []  # indices into required_skills

    # Tier 1: exact / alias matching
    for i, req in enumerate(required_skills):
        match = _exact_or_alias_match(req, dev_normalized)
        if match is not None:
            req_canon = normalize_skill(req)
            match_canon = normalize_skill(match)
            mtype = "exact" if req_canon.lower() == match_canon.lower() else "alias"
            results.append(SkillMatchResult(req, match, 1.0, mtype))
        else:
            results.append(SkillMatchResult(req, None, 0.0, "none"))
            needs_semantic.append(i)

    if not needs_semantic or not developer_skills:
        return results

    # Tier 2: semantic matching via embeddings
    unmatched_req = [required_skills[i] for i in needs_semantic]
    all_texts = unmatched_req + developer_skills
    embeddings = await _get_embeddings(all_texts)

    if not embeddings or len(embeddings) < len(all_texts):
        return results  # fallback – keep tier-1 results only

    req_embeddings = embeddings[: len(unmatched_req)]
    dev_embeddings = embeddings[len(unmatched_req) :]

    for idx, req_idx in enumerate(needs_semantic):
        req_emb = req_embeddings[idx]
        if not req_emb:
            continue

        best_sim = 0.0
        best_dev: str | None = None
        for dev_idx, dev_emb in enumerate(dev_embeddings):
            if not dev_emb:
                continue
            sim = _cosine_similarity(req_emb, dev_emb)
            if sim > best_sim:
                best_sim = sim
                best_dev = developer_skills[dev_idx]

        if best_sim >= threshold and best_dev is not None:
            results[req_idx] = SkillMatchResult(
                required_skills[req_idx], best_dev, best_sim, "semantic"
            )
        else:
            results[req_idx] = SkillMatchResult(
                required_skills[req_idx], None, best_sim, "none"
            )

    return results


def match_skills_sync(
    required_skills: list[str],
    developer_skills: list[str],
) -> list[SkillMatchResult]:
    """Synchronous alias-only matching (no embeddings). Fast fallback."""
    dev_normalized: dict[str, str] = {}
    for s in developer_skills:
        canon = normalize_skill(s).lower()
        dev_normalized[canon] = s

    results: list[SkillMatchResult] = []
    for req in required_skills:
        match = _exact_or_alias_match(req, dev_normalized)
        if match is not None:
            req_canon = normalize_skill(req)
            match_canon = normalize_skill(match)
            mtype = "exact" if req_canon.lower() == match_canon.lower() else "alias"
            results.append(SkillMatchResult(req, match, 1.0, mtype))
        else:
            results.append(SkillMatchResult(req, None, 0.0, "none"))
    return results
