"""Job-description matching endpoint."""

import logging

from fastapi import APIRouter, HTTPException

from app.db import store
from app.models.schemas import JDMatchRequest, JDMatchResponse, JDMatchSkill, Skill
from app.services.jd_match_service import match_job_description

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=JDMatchResponse)
async def jd_match(req: JDMatchRequest):
    """Match a developer's skills against a job description."""
    stored = store.load("analysis", req.analysis_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if stored.get("status") == "processing":
        raise HTTPException(status_code=409, detail="Analysis still processing")

    raw_skills = stored.get("skills", [])
    skills = [Skill(**s) if isinstance(s, dict) else s for s in raw_skills]

    result = match_job_description(req.job_description, skills)

    return JDMatchResponse(
        analysis_id=req.analysis_id,
        match_percentage=result["match_percentage"],
        matched_skills=[JDMatchSkill(**s) for s in result["matched_skills"]],
        missing_skills=[JDMatchSkill(**s) for s in result["missing_skills"]],
        partial_skills=[JDMatchSkill(**s) for s in result["partial_skills"]],
        summary=result["summary"],
    )
