from fastapi import APIRouter, HTTPException

from app.db import store
from app.models.schemas import BenchmarkResponse
from app.services.benchmark_service import evaluate_against_benchmarks

router = APIRouter()


@router.get("/{analysis_id}", response_model=BenchmarkResponse)
async def get_benchmarks(analysis_id: str):
    """Compare a completed analysis against predefined developer archetypes."""
    data = store.load("analysis", analysis_id)
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {analysis_id} not found",
        )

    result = evaluate_against_benchmarks(data["developer_score"])

    return BenchmarkResponse(analysis_id=analysis_id, **result)
