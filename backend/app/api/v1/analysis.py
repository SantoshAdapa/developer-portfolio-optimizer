import asyncio
import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile

from app.ai.embeddings import embed_and_store_chunks
from app.models.schemas import AnalysisResponse
from app.services.github_service import analyze_github_profile
from app.services.recommendation_service import (
    extract_skills_with_ai,
    generate_career_roadmap,
    generate_portfolio_suggestions,
    generate_project_ideas,
)
from app.services.resume_service import (
    chunk_text,
    cleanup_file,
    extract_text_from_pdf,
    save_upload,
)
from app.services.scoring_service import compute_developer_score
from app.utils.rate_limit import check_rate_limit
from app.utils.validators import validate_github_url, validate_pdf_file

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared store so recommendation endpoints can look up results
_analysis_store: dict[str, dict] = {}


def get_analysis_store() -> dict[str, dict]:
    return _analysis_store


@router.post("", response_model=AnalysisResponse, dependencies=[Depends(check_rate_limit)])
async def run_analysis(
    file: UploadFile,
    github_url: str = Form(""),
):
    """Full analysis pipeline: resume + optional GitHub."""
    # ── Validate inputs ────────────────────────────────
    pdf_error = validate_pdf_file(file.filename or "", file.content_type)
    if pdf_error:
        raise HTTPException(status_code=400, detail=pdf_error)

    github_summary = None
    if github_url:
        gh_error = validate_github_url(github_url)
        if gh_error:
            raise HTTPException(status_code=400, detail=gh_error)

    # ── Save & extract resume ──────────────────────────
    try:
        analysis_id, file_path = await save_upload(file)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    try:
        resume_text = extract_text_from_pdf(file_path)
    except ValueError as e:
        cleanup_file(file_path)
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        cleanup_file(file_path)

    # ── Parallel: skills extraction + GitHub analysis + embed chunks ──
    resume_chunks = chunk_text(resume_text)
    coros = [
        extract_skills_with_ai(resume_text),
        embed_and_store_chunks(analysis_id, resume_chunks),
    ]
    if github_url:
        coros.append(analyze_github_profile(github_url))

    results = await asyncio.gather(*coros, return_exceptions=True)

    # Unpack skills
    skills = results[0] if not isinstance(results[0], Exception) else []
    if isinstance(results[0], Exception):
        logger.exception("Skill extraction failed", exc_info=results[0])

    # Unpack embedding result (index 1) — log but don't block
    if isinstance(results[1], Exception):
        logger.warning("Embedding storage failed: %s", results[1])

    # Unpack GitHub (if requested)
    if github_url and len(results) > 2:
        if isinstance(results[2], Exception):
            logger.exception("GitHub analysis failed", exc_info=results[2])
        else:
            github_summary = results[2]

    # ── Scoring ────────────────────────────────────────
    developer_score = compute_developer_score(resume_text, skills, github_summary)

    # ── AI recommendations (parallel, with RAG) ────────
    suggestion_coro = generate_portfolio_suggestions(resume_text, skills, github_summary, analysis_id)
    project_coro = generate_project_ideas(skills, github_summary, analysis_id)
    roadmap_coro = generate_career_roadmap(resume_text, skills, github_summary, analysis_id)

    rec_results = await asyncio.gather(
        suggestion_coro, project_coro, roadmap_coro, return_exceptions=True
    )

    portfolio_suggestions = rec_results[0] if not isinstance(rec_results[0], Exception) else []
    project_ideas = rec_results[1] if not isinstance(rec_results[1], Exception) else []
    career_roadmap = rec_results[2] if not isinstance(rec_results[2], Exception) else None

    for i, r in enumerate(rec_results):
        if isinstance(r, Exception):
            logger.exception("Recommendation generation %d failed", i, exc_info=r)

    # ── Persist for GET endpoints ──────────────────────
    _analysis_store[analysis_id] = {
        "resume_text": resume_text,
        "skills": skills,
        "github_summary": github_summary,
        "developer_score": developer_score,
        "portfolio_suggestions": portfolio_suggestions,
        "project_ideas": project_ideas,
        "career_roadmap": career_roadmap,
    }

    return AnalysisResponse(
        analysis_id=analysis_id,
        developer_score=developer_score,
        skills=skills,
        github_summary=github_summary,
        portfolio_suggestions=portfolio_suggestions,
        project_ideas=project_ideas,
        career_roadmap=career_roadmap,
    )
