"""Recommendation service — orchestrates AI calls for portfolio, project, and career advice.

Uses the RAG pipeline when embeddings are available, falls back to direct
context injection when ChromaDB is empty for the given analysis.
"""

import json
import logging

import google.generativeai as genai

from app.ai.gemini_client import generate_json
from app.ai.prompts.career_roadmap import CAREER_ROADMAP_PROMPT
from app.ai.prompts.portfolio_suggestions import PORTFOLIO_SUGGESTIONS_PROMPT
from app.ai.prompts.project_ideas import PROJECT_IDEAS_PROMPT
from app.ai.prompts.skill_extraction import SKILL_EXTRACTION_PROMPT
from app.ai.rag_pipeline import build_rag_context, rag_generate
from app.config import settings
from app.models.schemas import (
    CareerRoadmap,
    GitHubSummary,
    Milestone,
    ProjectIdea,
    Skill,
    Suggestion,
)
from app.models.enums import Priority

logger = logging.getLogger(__name__)


def _configure_genai() -> None:
    genai.configure(api_key=settings.gemini_api_key)


# ── Portfolio Suggestions ────────────────────────────────

async def generate_portfolio_suggestions(
    resume_text: str,
    skills: list[Skill],
    github: GitHubSummary | None,
    analysis_id: str | None = None,
) -> list[Suggestion]:
    """Generate portfolio improvement suggestions via RAG or direct context."""
    _configure_genai()

    if analysis_id:
        try:
            raw = await rag_generate(
                task_query="portfolio projects experience skills online presence",
                prompt_template=PORTFOLIO_SUGGESTIONS_PROMPT,
                analysis_id=analysis_id,
                skills=skills,
                github=github,
            )
            return _parse_suggestions(raw)
        except Exception:
            logger.warning("RAG failed for portfolio suggestions, falling back to direct")

    # Fallback: direct context
    context = build_rag_context(
        retrieved_chunks=[resume_text[:3000]],
        skills=skills,
        github=github,
    )
    prompt = PORTFOLIO_SUGGESTIONS_PROMPT.replace("{context}", context)
    raw = await generate_json(prompt)
    return _parse_suggestions(raw)


def _parse_suggestions(raw: list | dict) -> list[Suggestion]:
    items = raw if isinstance(raw, list) else []
    suggestions: list[Suggestion] = []
    for item in items:
        try:
            suggestions.append(Suggestion(
                area=item["area"],
                current_state=item["current_state"],
                recommendation=item["recommendation"],
                priority=Priority(item["priority"]),
                impact=item["impact"],
            ))
        except (KeyError, ValueError) as e:
            logger.warning("Skipping malformed suggestion: %s", e)
    return suggestions


# ── Project Ideas ────────────────────────────────────────

async def generate_project_ideas(
    skills: list[Skill],
    github: GitHubSummary | None,
    analysis_id: str | None = None,
) -> list[ProjectIdea]:
    """Generate project ideas via RAG or direct context."""
    _configure_genai()

    if analysis_id:
        try:
            raw = await rag_generate(
                task_query="technical skills programming languages projects experience",
                prompt_template=PROJECT_IDEAS_PROMPT,
                analysis_id=analysis_id,
                skills=skills,
                github=github,
            )
            return _parse_project_ideas(raw)
        except Exception:
            logger.warning("RAG failed for project ideas, falling back to direct")

    # Fallback: direct context
    context = build_rag_context(
        retrieved_chunks=[],
        skills=skills,
        github=github,
    )
    prompt = PROJECT_IDEAS_PROMPT.replace("{context}", context)
    raw = await generate_json(prompt)
    return _parse_project_ideas(raw)


def _parse_project_ideas(raw: list | dict) -> list[ProjectIdea]:
    items = raw if isinstance(raw, list) else []
    ideas: list[ProjectIdea] = []
    for item in items:
        try:
            ideas.append(ProjectIdea(**item))
        except (TypeError, ValueError) as e:
            logger.warning("Skipping malformed project idea: %s", e)
    return ideas


# ── Career Roadmap ───────────────────────────────────────

async def generate_career_roadmap(
    resume_text: str,
    skills: list[Skill],
    github: GitHubSummary | None,
    analysis_id: str | None = None,
) -> CareerRoadmap:
    """Generate a career roadmap via RAG or direct context."""
    _configure_genai()

    if analysis_id:
        try:
            raw = await rag_generate(
                task_query="career experience education skills goals seniority",
                prompt_template=CAREER_ROADMAP_PROMPT,
                analysis_id=analysis_id,
                skills=skills,
                github=github,
            )
            if isinstance(raw, dict):
                return _parse_roadmap(raw)
        except Exception:
            logger.warning("RAG failed for career roadmap, falling back to direct")

    # Fallback: direct context
    context = build_rag_context(
        retrieved_chunks=[resume_text[:3000]],
        skills=skills,
        github=github,
    )
    prompt = CAREER_ROADMAP_PROMPT.replace("{context}", context)
    raw = await generate_json(prompt)
    return _parse_roadmap(raw)


def _parse_roadmap(raw: dict | list) -> CareerRoadmap:
    if not isinstance(raw, dict):
        return CareerRoadmap()
    milestones = [Milestone(**m) for m in raw.get("milestones", [])]
    return CareerRoadmap(
        current_level=raw.get("current_level", "Unknown"),
        target_role=raw.get("target_role", ""),
        milestones=milestones,
    )


# ── Skill Extraction via AI ──────────────────────────────

async def extract_skills_with_ai(resume_text: str) -> list[Skill]:
    """Use Gemini to extract structured skills from resume text."""
    _configure_genai()

    context = f"## Resume Content\n{resume_text[:4000]}"
    prompt = SKILL_EXTRACTION_PROMPT.replace("{context}", context)
    raw = await generate_json(prompt)

    skills: list[Skill] = []
    items = raw if isinstance(raw, list) else []
    for item in items:
        try:
            skills.append(Skill(**item))
        except (TypeError, ValueError) as e:
            logger.warning("Skipping malformed skill: %s", e)
            continue

    return skills
