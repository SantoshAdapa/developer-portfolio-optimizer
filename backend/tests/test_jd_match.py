"""Tests for jd_match_service — experience-level matching and domain distribution."""

import pytest

from app.data.role_templates import compute_domain_distribution
from app.data.skill_normalization import normalize_skill, normalize_skills
from app.models.enums import Proficiency, SkillCategory
from app.models.schemas import Skill
from app.services.jd_match_service import match_job_description_semantic


def _skill(
    name: str,
    cat: str = "language",
    prof: str = "intermediate",
) -> Skill:
    return Skill(
        name=name,
        category=SkillCategory(cat),
        proficiency=Proficiency(prof),
        source="resume",
    )


# ── Skill Normalization ─────────────────────────────────────


def test_normalize_ml_synonyms():
    assert normalize_skill("ML") == "Machine Learning"
    assert normalize_skill("DL") == "Deep Learning"
    assert normalize_skill("sklearn") == "Scikit-Learn"
    assert normalize_skill("nlp") == "Natural Language Processing"


def test_normalize_skills_dedup():
    result = normalize_skills(["ML", "Machine Learning", "ml"])
    assert result == ["Machine Learning"]


def test_normalize_preserves_unknown():
    result = normalize_skill("SomeUnknownTool")
    assert result == "Someunknowntool"


# ── Domain Distribution ─────────────────────────────────────


def test_domain_distribution_ml_skills():
    skills = ["Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "NLP"]
    # All these should be classified as ML/AI
    normalized = normalize_skills(skills)
    dist = compute_domain_distribution(normalized)
    assert "ML/AI" in dist
    # NLP was normalized to "Natural Language Processing"
    assert dist["ML/AI"] == 100


def test_domain_distribution_mixed():
    skills = ["Python", "Machine Learning", "React", "Docker", "SQL"]
    normalized = normalize_skills(skills)
    dist = compute_domain_distribution(normalized)
    # Should have entries for multiple domains
    assert len(dist) >= 3


def test_domain_distribution_no_devops_without_devops_skills():
    skills = ["Machine Learning", "Deep Learning", "PyTorch", "TensorFlow"]
    normalized = normalize_skills(skills)
    dist = compute_domain_distribution(normalized)
    # No DevOps skills → no DevOps in distribution
    assert dist.get("DevOps", 0) == 0


# ── Experience Level Matching ────────────────────────────────


@pytest.mark.asyncio
async def test_experience_level_returns_matched_skills():
    """Experience level matching should return actual matched/partial skills."""
    skills = [
        _skill("Python", "language", "advanced"),
        _skill("Machine Learning", "framework", "intermediate"),
        _skill("TensorFlow", "framework", "beginner"),
    ]
    result = await match_job_description_semantic(
        developer_skills=skills,
        experience_level="junior",
    )
    # Junior expects intermediate proficiency; should have some matched
    assert result["match_percentage"] > 0
    assert len(result["matched_skills"]) > 0 or len(result["partial_skills"]) > 0
    assert result["confidence"] in ("high", "medium", "low")
    # Should not always be 100% confidence
    assert "recommended_skills" in result


@pytest.mark.asyncio
async def test_experience_level_student_easy():
    """Student level should be easier to match."""
    skills = [
        _skill("Python", "language", "beginner"),
        _skill("HTML", "language", "beginner"),
        _skill("CSS", "language", "beginner"),
    ]
    result = await match_job_description_semantic(
        developer_skills=skills,
        experience_level="student",
    )
    # Student expects 3 skills with beginner proficiency
    assert result["match_percentage"] >= 50


@pytest.mark.asyncio
async def test_experience_level_senior_hard():
    """Senior level should be harder to match with beginner skills."""
    skills = [
        _skill("Python", "language", "beginner"),
        _skill("HTML", "language", "beginner"),
    ]
    result = await match_job_description_semantic(
        developer_skills=skills,
        experience_level="senior",
    )
    # Senior expects 14 skills with advanced proficiency
    assert result["match_percentage"] < 50


# ── Role Template Matching ───────────────────────────────────


@pytest.mark.asyncio
async def test_role_match_ml_engineer_with_ml_skills():
    """ML engineer role should match well with ML skills."""
    skills = [
        _skill("Python", "language", "advanced"),
        _skill("Machine Learning", "framework", "advanced"),
        _skill("Deep Learning", "framework", "intermediate"),
        _skill("PyTorch", "framework", "intermediate"),
        _skill("TensorFlow", "framework", "intermediate"),
        _skill("Scikit-Learn", "framework", "intermediate"),
        _skill("Statistics", "framework", "intermediate"),
    ]
    result = await match_job_description_semantic(
        developer_skills=skills,
        role_key="machine_learning_engineer",
    )
    # Should match many required skills
    assert len(result["matched_skills"]) >= 5
    assert result["match_percentage"] >= 40
    assert "recommended_skills" in result


@pytest.mark.asyncio
async def test_result_has_recommended_skills():
    """Result should include recommended_skills field."""
    skills = [_skill("Python", "language", "intermediate")]
    result = await match_job_description_semantic(
        developer_skills=skills,
        role_key="backend_developer",
    )
    assert "recommended_skills" in result
    # Should have recommended skills since we only have Python
    assert len(result["recommended_skills"]) > 0
