import logging

from fastapi import APIRouter, HTTPException, UploadFile

from app.models.schemas import ResumeUploadResponse
from app.services.recommendation_service import extract_skills_with_ai
from app.services.resume_service import (
    cleanup_file,
    extract_text_from_pdf,
    save_upload,
)
from app.utils.validators import validate_pdf_file

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for analysis data (would be a DB in production)
_resume_store: dict[str, dict] = {}


def get_resume_store() -> dict[str, dict]:
    return _resume_store


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile):
    """Upload a PDF resume, extract text, and identify skills."""
    # Validate file
    error = validate_pdf_file(file.filename or "", file.content_type)
    if error:
        raise HTTPException(status_code=400, detail=error)

    try:
        analysis_id, file_path = await save_upload(file)
    except ValueError as e:
        raise HTTPException(status_code=413, detail=str(e))

    try:
        resume_text = extract_text_from_pdf(file_path)
    except ValueError as e:
        cleanup_file(file_path)
        raise HTTPException(status_code=422, detail=str(e))

    # Extract skills via AI
    try:
        skills = await extract_skills_with_ai(resume_text)
    except Exception:
        logger.exception("Skill extraction failed")
        skills = []

    # Store for later use by analysis/recommendations endpoints
    _resume_store[analysis_id] = {
        "text": resume_text,
        "skills": skills,
        "filename": file.filename,
    }

    # Clean up uploaded file
    cleanup_file(file_path)

    return ResumeUploadResponse(
        analysis_id=analysis_id,
        filename=file.filename or "unknown.pdf",
        extracted_text_preview=resume_text[:500],
        skills=skills,
    )
