from fastapi import APIRouter, Depends, HTTPException

from app.db import store
from app.models.schemas import CompareRequest, CompareResponse
from app.services.comparison_service import compare_profiles
from app.utils.rate_limit import check_rate_limit

router = APIRouter()


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

    result = compare_profiles(
        score_a=data_a["developer_score"],
        skills_a=data_a.get("skills", []),
        score_b=data_b["developer_score"],
        skills_b=data_b.get("skills", []),
    )

    return CompareResponse(
        analysis_id_a=req.analysis_id_a,
        analysis_id_b=req.analysis_id_b,
        **result,
    )
