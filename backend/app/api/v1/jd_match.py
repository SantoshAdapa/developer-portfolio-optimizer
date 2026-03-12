"""Job-description matching endpoints.

Three matching modes:
- POST /jd-match        → match against pasted JD text (semantic)
- POST /jd-match/role   → match against a predefined role template
- POST /jd-match/level  → match against an experience-level expectation
- GET  /jd-match/roles  → list available role templates
- GET  /jd-match/levels → list available experience levels
"""

import logging

from fastapi import APIRouter, HTTPException

from app.db import store
from app.data.role_templates import EXPERIENCE_LEVELS, ROLE_TEMPLATES
from app.models.schemas import (
    ExperienceLevelInfo,
    JDMatchByLevelRequest,
    JDMatchByRoleRequest,
    JDMatchRequest,
    JDMatchResponse,
    JDMatchSkill,
    RoleTemplateInfo,
    Skill,
)
from app.services.jd_match_service import (
    match_job_description_semantic,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_skills(analysis_id: str) -> list[Skill]:
    stored = store.load("analysis", analysis_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if stored.get("status") == "processing":
        raise HTTPException(status_code=409, detail="Analysis still processing")
    raw = stored.get("skills", [])
    return [Skill(**s) if isinstance(s, dict) else s for s in raw]


def _to_response(analysis_id: str, result: dict) -> JDMatchResponse:
    return JDMatchResponse(
        analysis_id=analysis_id,
        match_percentage=result["match_percentage"],
        matched_skills=[JDMatchSkill(**s) for s in result["matched_skills"]],
        missing_skills=[JDMatchSkill(**s) for s in result["missing_skills"]],
        partial_skills=[JDMatchSkill(**s) for s in result["partial_skills"]],
        preferred_matched=[
            JDMatchSkill(**s) for s in result.get("preferred_matched", [])
        ],
        confidence=result.get("confidence", "medium"),
        label=result.get("label", ""),
        domain_distribution=result.get("domain_distribution", {}),
        summary=result["summary"],
    )


@router.post("", response_model=JDMatchResponse)
async def jd_match(req: JDMatchRequest):
    """Match a developer's skills against a pasted job description (semantic)."""
    skills = _load_skills(req.analysis_id)
    result = await match_job_description_semantic(
        developer_skills=skills,
        jd_text=req.job_description,
    )
    return _to_response(req.analysis_id, result)


@router.post("/role", response_model=JDMatchResponse)
async def jd_match_by_role(req: JDMatchByRoleRequest):
    """Match a developer's skills against a predefined role template."""
    if req.role_key not in ROLE_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown role: {req.role_key}")
    skills = _load_skills(req.analysis_id)
    result = await match_job_description_semantic(
        developer_skills=skills,
        role_key=req.role_key,
    )
    return _to_response(req.analysis_id, result)


@router.post("/level", response_model=JDMatchResponse)
async def jd_match_by_level(req: JDMatchByLevelRequest):
    """Match a developer's profile against an experience-level expectation."""
    if req.experience_level not in EXPERIENCE_LEVELS:
        raise HTTPException(
            status_code=400, detail=f"Unknown level: {req.experience_level}"
        )
    skills = _load_skills(req.analysis_id)
    result = await match_job_description_semantic(
        developer_skills=skills,
        experience_level=req.experience_level,
    )
    return _to_response(req.analysis_id, result)


@router.get("/roles", response_model=list[RoleTemplateInfo])
async def list_roles():
    """List all available role templates."""
    return [
        RoleTemplateInfo(
            key=key,
            label=tmpl["label"],
            required_skills=list(tmpl["required"].keys()),
            preferred_skills=list(tmpl.get("preferred", {}).keys()),
        )
        for key, tmpl in ROLE_TEMPLATES.items()
    ]


@router.get("/levels", response_model=list[ExperienceLevelInfo])
async def list_levels():
    """List all available experience levels."""
    return [
        ExperienceLevelInfo(key=key, label=lvl["label"], description=lvl["description"])
        for key, lvl in EXPERIENCE_LEVELS.items()
    ]
