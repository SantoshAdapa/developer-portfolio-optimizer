import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import GitHubAnalysisResponse, GitHubAnalyzeRequest
from app.services.github_service import analyze_github_profile, extract_username
from app.utils.rate_limit import check_rate_limit

from app.db import store as db_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/analyze",
    response_model=GitHubAnalysisResponse,
    dependencies=[Depends(check_rate_limit)],
)
async def analyze_github(body: GitHubAnalyzeRequest):
    """Analyze a GitHub profile and return a summary."""
    try:
        username = extract_username(body.github_username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        summary = await analyze_github_profile(username)
    except Exception as exc:
        detail = str(exc)
        if "rate limit" in detail.lower():
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please configure a GITHUB_TOKEN or wait a moment.",
            )
        logger.exception("GitHub analysis failed for %s", username)
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub data")

    analysis_id = uuid.uuid4().hex[:12]
    db_store.save("github", analysis_id, {"summary": summary})

    return GitHubAnalysisResponse(
        analysis_id=analysis_id,
        summary=summary,
    )
