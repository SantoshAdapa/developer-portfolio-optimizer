import logging

from fastapi import APIRouter, Depends, HTTPException

from app.db import store
from app.models.schemas import (
    CompareRequest,
    CompareResponse,
    DeveloperScore,
    GitHubSummary,
    RadarScores,
    Skill,
)
from app.services.comparison_service import compare_profiles
from app.utils.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()


def _reconstruct_score(raw: dict | DeveloperScore) -> DeveloperScore:
    """Rebuild a DeveloperScore from a stored dict (or pass through if already a model)."""
    if isinstance(raw, DeveloperScore):
        return raw
    return DeveloperScore(**raw)


def _reconstruct_skills(raw: list) -> list[Skill]:
    """Rebuild Skill objects from stored dicts."""
    skills: list[Skill] = []
    for item in raw:
        if isinstance(item, Skill):
            skills.append(item)
        elif isinstance(item, dict):
            try:
                skills.append(Skill(**item))
            except Exception:
                continue
    return skills


def _reconstruct_github(raw: dict | GitHubSummary | None) -> GitHubSummary | None:
    """Rebuild GitHubSummary from a stored dict."""
    if raw is None:
        return None
    if isinstance(raw, GitHubSummary):
        return raw
    try:
        return GitHubSummary(**raw)
    except Exception:
        return None


def _reconstruct_radar(raw: dict | RadarScores | None) -> RadarScores | None:
    """Rebuild RadarScores from a stored dict."""
    if raw is None:
        return None
    if isinstance(raw, RadarScores):
        return raw
    try:
        return RadarScores(**raw)
    except Exception:
        return None


@router.post(
    "", response_model=CompareResponse, dependencies=[Depends(check_rate_limit)]
)
async def compare_developers(req: CompareRequest):
    """Compare two completed analyses side-by-side."""
    data_a = store.load("analysis", req.analysis_id_a)
    if not data_a:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {req.analysis_id_a} not found",
        )

    data_b = store.load("analysis", req.analysis_id_b)
    if not data_b:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {req.analysis_id_b} not found",
        )

    try:
        score_a = _reconstruct_score(data_a["developer_score"])
        score_b = _reconstruct_score(data_b["developer_score"])
        skills_a = _reconstruct_skills(data_a.get("skills", []))
        skills_b = _reconstruct_skills(data_b.get("skills", []))
        github_a = _reconstruct_github(data_a.get("github_summary"))
        github_b = _reconstruct_github(data_b.get("github_summary"))
        radar_a = _reconstruct_radar(data_a.get("radar_scores"))
        radar_b = _reconstruct_radar(data_b.get("radar_scores"))
    except Exception:
        logger.exception("Failed to reconstruct analysis data for comparison")
        raise HTTPException(
            status_code=500,
            detail="Failed to load analysis data for comparison. Please re-run analysis.",
        )

    result = compare_profiles(
        score_a=score_a,
        skills_a=skills_a,
        score_b=score_b,
        skills_b=skills_b,
        github_a=github_a,
        github_b=github_b,
        radar_scores_a=radar_a,
        radar_scores_b=radar_b,
    )

    return CompareResponse(
        analysis_id_a=req.analysis_id_a,
        analysis_id_b=req.analysis_id_b,
        **result,
    )
