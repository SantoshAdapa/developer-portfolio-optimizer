import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.models.schemas import GitHubAnalysisResponse, GitHubAnalyzeRequest
from app.services.github_service import analyze_github_profile
from app.utils.validators import validate_github_url

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for GitHub analysis results
_github_store: dict[str, dict] = {}


def get_github_store() -> dict[str, dict]:
    return _github_store


@router.post("/analyze", response_model=GitHubAnalysisResponse)
async def analyze_github(body: GitHubAnalyzeRequest):
    """Analyze a GitHub profile and return a summary."""
    url = str(body.github_url)
    error = validate_github_url(url)
    if error:
        raise HTTPException(status_code=400, detail=error)

    try:
        summary = await analyze_github_profile(url)
    except Exception:
        logger.exception("GitHub analysis failed for %s", url)
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub data")

    analysis_id = uuid.uuid4().hex[:12]
    _github_store[analysis_id] = {"summary": summary}

    return GitHubAnalysisResponse(
        analysis_id=analysis_id,
        summary=summary,
    )
