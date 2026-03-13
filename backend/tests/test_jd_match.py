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


def test_normalize_pytorch_aliases():
    assert normalize_skill("torch") == "PyTorch"
    assert normalize_skill("pytorch") == "PyTorch"
    assert normalize_skill("PyTorch") == "PyTorch"


def test_normalize_scikit_learn_aliases():
    assert normalize_skill("scikit-learn") == "Scikit-Learn"
    assert normalize_skill("scikit learn") == "Scikit-Learn"
    assert normalize_skill("sklearn") == "Scikit-Learn"
    assert normalize_skill("sk-learn") == "Scikit-Learn"


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


@pytest.mark.asyncio
async def test_experience_level_not_always_100():
    """Experience level should NOT return 100% for all levels."""
    skills = [
        _skill("Python", "language", "beginner"),
        _skill("HTML", "language", "beginner"),
    ]
    results = {}
    for level in ["student", "fresher", "junior", "mid", "senior"]:
        result = await match_job_description_semantic(
            developer_skills=skills,
            experience_level=level,
        )
        results[level] = result["match_percentage"]

    # Senior should score lower than student with beginner skills
    assert results["senior"] < results["student"]
    # Not all should be 100%
    assert not all(v == 100 for v in results.values())


@pytest.mark.asyncio
async def test_experience_level_distinguishes_proficiency():
    """Advanced skills should score higher on senior than beginner skills."""
    beginner_skills = [
        _skill("Python", "language", "beginner"),
        _skill("Java", "language", "beginner"),
        _skill("SQL", "language", "beginner"),
    ]
    advanced_skills = [
        _skill("Python", "language", "advanced"),
        _skill("Java", "language", "advanced"),
        _skill("SQL", "language", "advanced"),
    ]
    beginner_result = await match_job_description_semantic(
        developer_skills=beginner_skills,
        experience_level="senior",
    )
    advanced_result = await match_job_description_semantic(
        developer_skills=advanced_skills,
        experience_level="senior",
    )
    # Advanced skills should score higher for senior level
    assert advanced_result["match_percentage"] > beginner_result["match_percentage"]


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
async def test_ml_resume_matches_ml_role_higher_than_devops():
    """An ML-heavy resume should score higher on ML role than on DevOps role."""
    ml_skills = [
        _skill("Python", "language", "advanced"),
        _skill("Machine Learning", "framework", "advanced"),
        _skill("Deep Learning", "framework", "advanced"),
        _skill("PyTorch", "framework", "advanced"),
        _skill("TensorFlow", "framework", "intermediate"),
        _skill("Scikit-Learn", "framework", "intermediate"),
        _skill("Statistics", "framework", "intermediate"),
        _skill("Feature Engineering", "framework", "intermediate"),
        _skill("Data Processing", "framework", "intermediate"),
        _skill("Pandas", "framework", "intermediate"),
        _skill("NumPy", "framework", "intermediate"),
    ]

    ml_result = await match_job_description_semantic(
        developer_skills=ml_skills,
        role_key="machine_learning_engineer",
    )
    devops_result = await match_job_description_semantic(
        developer_skills=ml_skills,
        role_key="devops_engineer",
    )

    # ML role should score significantly higher than DevOps for ML skills
    assert ml_result["match_percentage"] > devops_result["match_percentage"]
    # ML should match well
    assert ml_result["match_percentage"] >= 50
    # DevOps should match poorly with ML skills
    assert devops_result["match_percentage"] < ml_result["match_percentage"]


@pytest.mark.asyncio
async def test_devops_resume_matches_devops_higher_than_ml():
    """A DevOps-heavy resume should score higher on DevOps role than ML role."""
    devops_skills = [
        _skill("Docker", "tool", "advanced"),
        _skill("Kubernetes", "tool", "advanced"),
        _skill("Linux", "tool", "advanced"),
        _skill("CI/CD", "tool", "advanced"),
        _skill("Terraform", "tool", "intermediate"),
        _skill("AWS", "cloud", "intermediate"),
        _skill("Git", "tool", "intermediate"),
        _skill("Bash", "language", "intermediate"),
        _skill("Monitoring", "tool", "intermediate"),
        _skill("Python", "language", "intermediate"),
    ]

    ml_result = await match_job_description_semantic(
        developer_skills=devops_skills,
        role_key="machine_learning_engineer",
    )
    devops_result = await match_job_description_semantic(
        developer_skills=devops_skills,
        role_key="devops_engineer",
    )

    # DevOps role should score much higher than ML for DevOps skills
    assert devops_result["match_percentage"] > ml_result["match_percentage"]


@pytest.mark.asyncio
async def test_ml_skills_not_marked_missing_when_present():
    """ML skills that are present in the resume should NOT appear in missing_skills."""
    skills = [
        _skill("Python", "language", "advanced"),
        _skill("Machine Learning", "framework", "advanced"),
        _skill("Deep Learning", "framework", "intermediate"),
        _skill("PyTorch", "framework", "intermediate"),
        _skill("TensorFlow", "framework", "intermediate"),
        _skill("Scikit-Learn", "framework", "intermediate"),
        _skill("Statistics", "framework", "intermediate"),
        _skill("Feature Engineering", "framework", "intermediate"),
        _skill("Data Processing", "framework", "intermediate"),
    ]
    result = await match_job_description_semantic(
        developer_skills=skills,
        role_key="machine_learning_engineer",
    )

    # Skills the developer has should be in matched, not missing
    missing_names = {s["skill"].lower() for s in result["missing_skills"]}
    assert "python" not in missing_names
    assert "machine learning" not in missing_names
    assert "deep learning" not in missing_names
    assert "pytorch" not in missing_names


@pytest.mark.asyncio
async def test_weighted_scoring_prioritizes_required_skills():
    """Required skills should contribute more to the score than preferred skills."""
    # Developer has only preferred skills, not required
    skills = [
        _skill("MLOps", "framework", "intermediate"),
        _skill("Docker", "tool", "intermediate"),
        _skill("AWS", "cloud", "intermediate"),
        _skill("Natural Language Processing", "framework", "intermediate"),
        _skill("Computer Vision", "framework", "intermediate"),
    ]
    result = await match_job_description_semantic(
        developer_skills=skills,
        role_key="machine_learning_engineer",
    )
    # Score should be moderate since only preferred skills are matched
    # Required skills have 3x weight, these are just preferred (2x weight)
    assert result["match_percentage"] < 50


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
