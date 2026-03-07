"""PDF text extraction using pdfplumber."""

from pathlib import Path

import pdfplumber


def extract_text(file_path: Path) -> str:
    """Extract all text from a PDF file, page by page.

    Returns concatenated text with double-newline page separators.
    Raises FileNotFoundError if path doesn't exist.
    Raises ValueError if no text could be extracted.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

    if not pages:
        raise ValueError("Could not extract any text from the PDF")

    return "\n\n".join(pages)


def extract_sections(text: str) -> dict[str, str]:
    """Attempt to split resume text into labelled sections.

    Looks for common resume headings and groups the text beneath them.
    Returns a dict like {"experience": "...", "skills": "...", ...}.
    An "other" key collects text before the first heading.
    """
    import re

    heading_pattern = re.compile(
        r"^(summary|objective|experience|work\s*history|education|skills|"
        r"technical\s*skills|projects|certifications|awards|publications|"
        r"interests|languages|references|contact)\b",
        re.IGNORECASE | re.MULTILINE,
    )

    matches = list(heading_pattern.finditer(text))

    if not matches:
        return {"other": text}

    sections: dict[str, str] = {}

    # Text before the first heading
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections["other"] = preamble

    for i, match in enumerate(matches):
        key = match.group(1).lower().strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections[key] = content

    return sections
