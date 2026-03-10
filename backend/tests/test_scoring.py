"""Tests for scoring_service — verifies sub-scores and composite score logic."""

from app.models.enums import CommitFrequency, Proficiency, SkillCategory
from app.models.schemas import DeveloperScore, GitHubSummary, RepoSummary, Skill
from app.services.scoring_service import (
    _score_community,
    _score_content_quality,
    _score_documentation,
    _score_formatting_quality,
    _score_github_activity,
    _score_impact_quantification,
    _score_keyword_density,
    _score_repo_quality,
    _score_resume_completeness,
    _score_skill_diversity,
    compute_developer_score,
    compute_radar_scores,
    compute_skill_categories,
    extract_programming_languages,
    extract_skills_from_text,
    generate_ai_insights,
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
    # All 10 categories should be present when both resume + GitHub are provided
    assert len(score.categories) == 10


def test_composite_score_no_github():
    """Without GitHub, only resume-based metrics should appear."""
    score = compute_developer_score("Experience", [_skill("Python")], None)
    assert score.overall >= 0
    # All 6 resume metrics should be present
    assert "resume_completeness" in score.categories
    assert "skill_diversity" in score.categories
    assert "content_quality" in score.categories
    assert "formatting_quality" in score.categories
    assert "impact_quantification" in score.categories
    assert "keyword_density" in score.categories
    assert "github_activity" not in score.categories
    assert "community" not in score.categories
    assert len(score.categories) == 6
    assert score.overall > 0


def test_composite_score_github_only():
    """Without resume, only GitHub-based metrics should appear."""
    score = compute_developer_score("", [], _github())
    assert score.overall > 0
    assert "github_activity" in score.categories
    assert "resume_completeness" not in score.categories


def test_composite_score_empty():
    score = compute_developer_score("", [], None)
    assert score.overall == 0
    assert len(score.categories) == 0


# ── New ATS sub-score tests ──────────────────────────────


def test_content_quality_empty():
    assert _score_content_quality("") == 0


def test_content_quality_rich():
    text = (
        "Developed scalable microservices. Implemented CI/CD pipelines. "
        "Designed and built RESTful APIs. Led a team of 5 engineers. "
        "email@example.com 555-1234 linkedin.com/in/dev\n"
        + "\n".join(["This is a detailed line with many words describing project work."] * 10)
    )
    score = _score_content_quality(text)
    assert score >= 50


def test_formatting_quality_empty():
    assert _score_formatting_quality("") == 0


def test_formatting_quality_structured():
    text = (
        "EXPERIENCE\n\n"
        "- Developed REST API\n"
        "- Managed cloud infrastructure\n"
        "- Led team standup meetings\n\n"
        "EDUCATION\n\n"
        "- B.S. Computer Science\n"
    )
    score = _score_formatting_quality(text)
    assert score > 0


def test_impact_quantification_empty():
    assert _score_impact_quantification("") == 0


def test_impact_quantification_numbers():
    text = "Increased revenue by 30%. Reduced latency by 200ms. Managed $50k budget over 2 years."
    score = _score_impact_quantification(text)
    assert score >= 40


def test_keyword_density_empty():
    assert _score_keyword_density("", []) == 0


def test_keyword_density_rich():
    text = "Agile scrum ci/cd devops microservices api rest graphql cloud testing deployment architecture"
    score = _score_keyword_density(text, [_skill("Python")])
    assert score >= 30


# ── Text-based skill extraction ──────────────────────────


def test_extract_skills_from_text_empty():
    assert extract_skills_from_text("") == []


def test_extract_skills_from_text_finds_skills():
    text = "Experienced with Python, React, Docker, PostgreSQL, and AWS."
    skills = extract_skills_from_text(text)
    names = {s.name.lower() for s in skills}
    assert "python" in names
    assert "react" in names
    assert "docker" in names


# ── Radar scores ─────────────────────────────────────────


def test_compute_radar_scores_empty():
    radar = compute_radar_scores([], "")
    assert radar.frontend == 0
    assert radar.backend == 0


def test_compute_radar_scores_with_skills():
    skills = [
        _skill("React", "framework"),
        _skill("Python", "language"),
        _skill("Docker", "tool"),
    ]
    radar = compute_radar_scores(skills, "react python docker fastapi")
    assert radar.frontend > 0
    assert radar.backend > 0
    assert radar.devops > 0


# ── Skill categories ─────────────────────────────────────


def test_compute_skill_categories():
    skills = [
        _skill("Python", "language"),
        _skill("Java", "language"),
        _skill("React", "framework"),
    ]
    cats = compute_skill_categories(skills)
    assert len(cats) == 2
    lang_cat = next(c for c in cats if c.category == "language")
    assert "Python" in lang_cat.skills
    assert "Java" in lang_cat.skills


# ── Programming languages ────────────────────────────────


def test_extract_programming_languages():
    skills = [_skill("Python", "language"), _skill("Java", "language")]
    langs = extract_programming_languages(skills, "python java")
    names = {lang.name for lang in langs}
    assert "Python" in names
    assert "Java" in names


# ── AI Insights ──────────────────────────────────────────


def test_generate_ai_insights():
    categories = {
        "resume_completeness": 77,
        "content_quality": 65,
        "skill_diversity": 50,
        "formatting_quality": 40,
        "impact_quantification": 20,
        "keyword_density": 55,
    }
    skills = [_skill("Python"), _skill("React", "framework")]
    insights = generate_ai_insights(categories, skills, None, 55)
    assert len(insights.strengths) > 0
    assert len(insights.career_potential) > 0
    assert len(insights.recommended_improvements) > 0
