"""Input validation utilities."""

import re
from urllib.parse import urlparse

# Allowed MIME types for resume upload
ALLOWED_MIME_TYPES = {"application/pdf"}

# Max filename length to prevent path issues
MAX_FILENAME_LENGTH = 255

_GITHUB_HOST_PATTERN = re.compile(r"^(www\.)?github\.com$", re.IGNORECASE)


def validate_pdf_file(filename: str, content_type: str | None) -> str | None:
    """Validate an uploaded file is a PDF.

    Returns an error message string, or None if valid.
    """
    if not filename:
        return "No filename provided"

    if len(filename) > MAX_FILENAME_LENGTH:
        return "Filename is too long"

    if not filename.lower().endswith(".pdf"):
        return "File must be a PDF (.pdf extension required)"

    if content_type and content_type not in ALLOWED_MIME_TYPES:
        return f"Invalid content type: {content_type}. Expected application/pdf"

    return None


def validate_github_url(url: str) -> str | None:
    """Validate a GitHub profile URL.

    Accepts formats:
      - https://github.com/username
      - http://github.com/username
      - https://www.github.com/username
      - github.com/username  (no scheme)

    Returns an error message string, or None if valid.
    """
    raw = str(url).strip()
    if not raw:
        return "GitHub URL is required"

    # Add scheme if missing
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw

    parsed = urlparse(raw)

    if not parsed.hostname or not _GITHUB_HOST_PATTERN.match(parsed.hostname):
        return "URL must be a github.com address"

    path = parsed.path.strip("/")
    if not path:
        return "URL must include a GitHub username (e.g. github.com/username)"

    # Username is the first path segment
    username = path.split("/")[0]

    # GitHub username rules: alphanumeric + hyphens, 1-39 chars, no leading/trailing hyphen
    if not re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$", username):
        return f"Invalid GitHub username format: {username}"

    return None


def sanitize_filename(filename: str) -> str:
    """Strip unsafe characters from a filename, keeping only alphanumeric, dots, hyphens, underscores."""
    name = re.sub(r"[^\w.\-]", "_", filename)
    # Collapse multiple underscores
    name = re.sub(r"_+", "_", name)
    return name[:MAX_FILENAME_LENGTH]
