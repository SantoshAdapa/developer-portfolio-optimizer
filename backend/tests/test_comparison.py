"""Tests for comparison service."""

from app.models.enums import Proficiency, SkillCategory
from app.models.schemas import DeveloperScore, Skill
from app.services.comparison_service import compare_profiles


def _score(overall: int, **cats) -> DeveloperScore:
    defaults = {
        "skill_diversity": 50,
        "github_activity": 50,
        "repo_quality": 50,
        "documentation": 50,
        "community": 50,
    }
    defaults.update(cats)
    return DeveloperScore(overall=overall, categories=defaults, justification="test")


def _skill(name: str) -> Skill:
    return Skill(name=name, category=SkillCategory.LANGUAGE, proficiency=Proficiency.INTERMEDIATE, source="resume")


def test_compare_tie():
    result = compare_profiles(_score(75), [_skill("Python")], _score(75), [_skill("Python")])
    assert result["winner"] == "tie"
    assert result["score_difference"] == 0


def test_compare_a_wins():
    result = compare_profiles(_score(80), [], _score(60), [])
    assert result["winner"] == "developer_a"
    assert result["score_difference"] == 20


def test_compare_b_wins():
    result = compare_profiles(_score(50), [], _score(90), [])
    assert result["winner"] == "developer_b"


def test_skill_gap():
    result = compare_profiles(
        _score(70), [_skill("Python"), _skill("Java")],
        _score(70), [_skill("Python"), _skill("Go")],
    )
    gap_skills = {e["skill"] for e in result["skill_gap"]}
    assert "java" in gap_skills
    assert "go" in gap_skills
    assert "python" not in gap_skills


def test_dimension_comparison_count():
    result = compare_profiles(_score(70), [], _score(70), [])
    assert len(result["dimension_comparison"]) == 5
