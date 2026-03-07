from fastapi import APIRouter, HTTPException

from app.api.v1.analysis import get_analysis_store
from app.models.schemas import (
    CareerRoadmapResponse,
    PortfolioSuggestionsResponse,
    ProjectIdeasResponse,
)

router = APIRouter()


def _get_analysis(analysis_id: str) -> dict:
    store = get_analysis_store()
    data = store.get(analysis_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
    return data


@router.get("/{analysis_id}/portfolio", response_model=PortfolioSuggestionsResponse)
async def get_portfolio_suggestions(analysis_id: str):
    """Retrieve portfolio improvement suggestions for a completed analysis."""
    data = _get_analysis(analysis_id)
    return PortfolioSuggestionsResponse(
        analysis_id=analysis_id,
        suggestions=data.get("portfolio_suggestions", []),
    )


@router.get("/{analysis_id}/projects", response_model=ProjectIdeasResponse)
async def get_project_ideas(analysis_id: str):
    """Retrieve project ideas for a completed analysis."""
    data = _get_analysis(analysis_id)
    return ProjectIdeasResponse(
        analysis_id=analysis_id,
        project_ideas=data.get("project_ideas", []),
    )


@router.get("/{analysis_id}/roadmap", response_model=CareerRoadmapResponse)
async def get_career_roadmap(analysis_id: str):
    """Retrieve the career roadmap for a completed analysis."""
    data = _get_analysis(analysis_id)
    roadmap = data.get("career_roadmap")
    if not roadmap:
        raise HTTPException(status_code=404, detail="No roadmap generated for this analysis")
    return CareerRoadmapResponse(
        analysis_id=analysis_id,
        roadmap=roadmap,
    )
