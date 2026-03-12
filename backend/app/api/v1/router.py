from fastapi import APIRouter, Depends

from app.api.v1 import (
    analysis,
    benchmarks,
    compare,
    github,
    jd_match,
    recommendations,
    resume,
)
from app.utils.auth import require_api_key

v1_router = APIRouter(dependencies=[Depends(require_api_key)])

v1_router.include_router(resume.router, prefix="/resume", tags=["Resume"])
v1_router.include_router(github.router, prefix="/github", tags=["GitHub"])
v1_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
v1_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
v1_router.include_router(compare.router, prefix="/compare", tags=["Comparison"])
v1_router.include_router(benchmarks.router, prefix="/benchmarks", tags=["Benchmarks"])
v1_router.include_router(jd_match.router, prefix="/jd-match", tags=["JD Match"])
