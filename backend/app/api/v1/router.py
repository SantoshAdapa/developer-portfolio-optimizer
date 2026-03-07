from fastapi import APIRouter

from app.api.v1 import analysis, github, recommendations, resume

v1_router = APIRouter()

v1_router.include_router(resume.router, prefix="/resume", tags=["Resume"])
v1_router.include_router(github.router, prefix="/github", tags=["GitHub"])
v1_router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
v1_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
