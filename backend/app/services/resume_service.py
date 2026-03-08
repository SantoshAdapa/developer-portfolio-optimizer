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
    content = await file.read()

    if len(content) > settings.max_file_size_bytes:
        raise ValueError(f"File exceeds {settings.max_file_size_mb} MB limit")

    dest.write_bytes(content)
    return analysis_id, dest


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    pages: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping word-based chunks for embedding."""
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def cleanup_file(file_path: Path) -> None:
    """Remove a temporary file if it exists."""
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        pass
