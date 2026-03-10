"""Tests for input validation utilities."""

from app.utils.validators import sanitize_filename, validate_github_url, validate_pdf_file


# ── PDF validation ───────────────────────────────────────


def test_pdf_valid():
    assert validate_pdf_file("resume.pdf", "application/pdf") is None


def test_pdf_no_filename():
    assert validate_pdf_file("", "application/pdf") is not None


def test_pdf_wrong_extension():
    err = validate_pdf_file("resume.docx", "application/pdf")
    assert err is not None
    assert "PDF" in err


def test_pdf_wrong_mime():
    err = validate_pdf_file("resume.pdf", "text/plain")
    assert err is not None
    assert "content type" in err.lower() or "Invalid" in err


def test_pdf_long_filename():
    err = validate_pdf_file("a" * 300 + ".pdf", "application/pdf")
    assert err is not None


def test_pdf_none_content_type():
    assert validate_pdf_file("resume.pdf", None) is None


# ── GitHub URL validation ────────────────────────────────


def test_github_valid_https():
    assert validate_github_url("https://github.com/octocat") is None


def test_github_valid_no_scheme():
    assert validate_github_url("github.com/octocat") is None


def test_github_valid_www():
    assert validate_github_url("https://www.github.com/octocat") is None


def test_github_empty():
    assert validate_github_url("") is not None


def test_github_no_username():
    err = validate_github_url("https://github.com/")
    assert err is not None


def test_github_wrong_host():
    err = validate_github_url("https://gitlab.com/user")
    assert err is not None


def test_github_invalid_username():
    err = validate_github_url("https://github.com/-invalid-")
    assert err is not None


# ── Filename sanitization ────────────────────────────────


def test_sanitize_basic():
    assert sanitize_filename("my file (1).pdf") == "my_file_1_.pdf"


def test_sanitize_truncates():
    result = sanitize_filename("a" * 500)
    assert len(result) <= 255
