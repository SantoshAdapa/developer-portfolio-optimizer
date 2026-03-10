import uuid
from pathlib import Path

import pdfplumber
from fastapi import UploadFile

from app.config import settings


async def save_upload(file: UploadFile) -> tuple[str, Path]:
    """Save uploaded PDF to disk. Returns (analysis_id, file_path)."""
    analysis_id = uuid.uuid4().hex[:12]
    safe_name = f"{analysis_id}.pdf"
    dest = Path(settings.upload_dir) / safe_name
    limit = settings.max_file_size_bytes

    # Stream in chunks to avoid reading a huge file into memory at once
    size = 0
    with dest.open("wb") as f:
        while chunk := await file.read(64 * 1024):  # 64 KB chunks
            size += len(chunk)
            if size > limit:
                dest.unlink(missing_ok=True)
                raise ValueError(f"File exceeds {settings.max_file_size_mb} MB limit")
            f.write(chunk)

    return analysis_id, dest


_PDF_MAGIC = b"%PDF-"


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    with open(file_path, "rb") as f:
        header = f.read(5)
    if header != _PDF_MAGIC:
        raise ValueError("File is not a valid PDF (bad magic bytes)")

    pages: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def cleanup_file(file_path: Path) -> None:
    """Remove a temporary file if it exists."""
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass
