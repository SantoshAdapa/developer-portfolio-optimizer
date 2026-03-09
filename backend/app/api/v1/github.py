import logging
import re
import uuid

from fastapi import APIRouter, HTTPException

from app.models.schemas import GitHubAnalysisResponse, GitHubAnalyzeRequest
from app.services.github_service import analyze_github_profile

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for GitHub analysis results
_github_store: dict[str, dict] = {}

_GITHUB_USERNAME_RE = re.compile(
    r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$"
)


def extract_github_username(value: str) -> str:
    """Normalise a GitHub username or profile URL into a plain username."""
    value = value.strip().rstrip("/")
    if "github.com" in value:
        # e.g. https://github.com/SantoshAdapa
        return value.split("/")[-1]
    # Strip leading @ if present
    return value.lstrip("@")


def get_github_store() -> dict[str, dict]:
    return _github_store


@router.post("/analyze", response_model=GitHubAnalysisResponse)
async def analyze_github(body: GitHubAnalyzeRequest):
    """Analyze a GitHub profile and return a summary."""
    username = extract_github_username(body.github_username)

    if not username or not _GITHUB_USERNAME_RE.match(username):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GitHub username: {username}",
        )

    try:
        summary = await analyze_github_profile(username)
    except Exception:
        logger.exception("GitHub analysis failed for %s", username)
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub data")

    analysis_id = uuid.uuid4().hex[:12]
    _github_store[analysis_id] = {"summary": summary}

    return GitHubAnalysisResponse(
        analysis_id=analysis_id,
        summary=summary,
    )
