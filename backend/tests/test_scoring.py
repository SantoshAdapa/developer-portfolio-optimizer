"""Tests for scoring_service — verifies sub-scores and composite score logic."""

from app.models.enums import CommitFrequency, Proficiency, SkillCategory
from app.models.schemas import DeveloperScore, GitHubSummary, RepoSummary, Skill
from app.services.scoring_service import (
    _score_community,
    _score_documentation,
    _score_github_activity,
    _score_repo_quality,
    _score_resume_completeness,
    _score_skill_diversity,
    compute_developer_score,
)


def _skill(name: str, cat: str = "language") -> Skill:
    return Skill(
        name=name,
        category=SkillCategory(cat),
        proficiency=Proficiency.INTERMEDIATE,
        source="resume",
    )


def _github(**overrides) -> GitHubSummary:
    defaults = dict(
        username="test",
        public_repos=5,
        followers=10,
        top_languages={"Python": 60.0},
        total_stars=20,
        commit_frequency=CommitFrequency.WEEKLY,
        notable_repos=[
            RepoSummary(
                name="repo1",
                description="desc",
                stars=10,
                has_readme=True,
                topics=["ml"],
            ),
        ],
    )
    defaults.update(overrides)
    return GitHubSummary(**defaults)


# ── Resume completeness ─────────────────────────────────


def test_resume_completeness_empty():
    assert _score_resume_completeness("") == 0


def test_resume_completeness_all_sections():
    text = "Summary\nExperience\nWork\nEducation\nSkills\nTechnologies\nProjects\nCertifications\nObjective"
    score = _score_resume_completeness(text)
    assert score == 100


def test_resume_completeness_partial():
    text = "Experience section here. Education details."
    score = _score_resume_completeness(text)
    assert 0 < score < 100


# ── Skill diversity ──────────────────────────────────────


def test_skill_diversity_empty():
    assert _score_skill_diversity([]) == 0


def test_skill_diversity_single_category():
    skills = [_skill("Python"), _skill("Java")]
    score = _score_skill_diversity(skills)
    assert 0 < score < 100


def test_skill_diversity_multiple_categories():
    skills = [
        _skill("Python", "language"),
        _skill("React", "framework"),
        _skill("Docker", "tool"),
        _skill("Postgres", "database"),
        _skill("AWS", "cloud"),
        _skill("Teamwork", "soft_skill"),
    ]
    score = _score_skill_diversity(skills)
    assert score >= 50  # maximum breadth achieved


# ── GitHub activity ──────────────────────────────────────


def test_github_activity_none():
    assert _score_github_activity(None) == 0


def test_github_activity_daily():
    gh = _github(commit_frequency=CommitFrequency.DAILY, public_repos=30)
    assert _score_github_activity(gh) == 100


def test_github_activity_sporadic():
    gh = _github(commit_frequency=CommitFrequency.SPORADIC, public_repos=1)
    score = _score_github_activity(gh)
    assert score < 20


# ── Repo quality ─────────────────────────────────────────


def test_repo_quality_none():
    assert _score_repo_quality(None) == 0


def test_repo_quality_rich_repos():
    repos = [
        RepoSummary(
            name=f"r{i}", description="d", stars=20, topics=["t"], has_readme=True
        )
        for i in range(5)
    ]
    gh = _github(
        notable_repos=repos,
        total_stars=100,
        top_languages={"Py": 40, "JS": 30, "Go": 15, "Rust": 10, "C": 5},
    )
    score = _score_repo_quality(gh)
    assert score >= 80


# ── Documentation ────────────────────────────────────────


def test_documentation_none():
    assert _score_documentation(None) == 0


def test_documentation_all_present():
    repos = [RepoSummary(name="r", description="d", has_readme=True)]
    gh = _github(notable_repos=repos)
    assert _score_documentation(gh) == 100


def test_documentation_missing_readme():
    repos = [RepoSummary(name="r", description="d", has_readme=False)]
    gh = _github(notable_repos=repos)
    score = _score_documentation(gh)
    assert score == 50


# ── Community ────────────────────────────────────────────


def test_community_none():
    assert _score_community(None) == 0


def test_community_high():
    gh = _github(followers=100, total_stars=100)
    assert _score_community(gh) == 100


# ── Composite score ──────────────────────────────────────


def test_composite_score_range():
    score = compute_developer_score(
        "Experience Education Skills", [_skill("Python")], _github()
    )
    assert isinstance(score, DeveloperScore)
    assert 0 <= score.overall <= 100
    assert "Score breakdown" in score.justification


def test_composite_score_no_github():
    score = compute_developer_score("Experience", [_skill("Python")], None)
    assert score.overall >= 0
    assert score.categories["github_activity"] == 0


def test_composite_score_empty():
    score = compute_developer_score("", [], None)
    assert score.overall == 0
