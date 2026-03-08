"""Scoring service — computes a weighted developer score from resume + GitHub data."""

from app.models.enums import CommitFrequency
from app.models.schemas import DeveloperScore, GitHubSummary, Skill

# ── Weight configuration ─────────────────────────────────

WEIGHTS = {
    "resume_completeness": 0.15,
    "skill_diversity": 0.20,
    "github_activity": 0.20,
    "repo_quality": 0.25,
    "documentation": 0.10,
    "community": 0.10,
}

# Resume sections we look for (case-insensitive substrings)
_RESUME_SECTIONS = [
    "summary",
    "objective",
    "experience",
    "work",
    "education",
    "skills",
    "technologies",
    "projects",
    "certifications",
]


# ── Sub-score functions ──────────────────────────────────


def _score_resume_completeness(resume_text: str) -> int:
    """0-100 based on how many standard resume sections are present."""
    if not resume_text:
        return 0
    lower = resume_text.lower()
    found = sum(1 for s in _RESUME_SECTIONS if s in lower)
    return min(100, int(found / len(_RESUME_SECTIONS) * 100))


def _score_skill_diversity(skills: list[Skill]) -> int:
    """0-100 based on breadth of skill categories."""
    if not skills:
        return 0
    categories = {s.category for s in skills}
    unique_skills = len(skills)

    # Breadth: how many categories covered (out of 6 possible)
    breadth = len(categories) / 6 * 50

    # Depth: raw skill count (cap at 20 for full marks)
    depth = min(unique_skills / 20, 1.0) * 50

    return min(100, int(breadth + depth))


def _score_github_activity(github: GitHubSummary | None) -> int:
    """0-100 based on commit frequency and repo count."""
    if not github:
        return 0

    freq_scores = {
        CommitFrequency.DAILY: 50,
        CommitFrequency.WEEKLY: 35,
        CommitFrequency.MONTHLY: 20,
        CommitFrequency.SPORADIC: 5,
    }
    freq_score = freq_scores.get(github.commit_frequency, 5)

    # Repo count contribution (cap at 30 repos for full marks)
    repo_score = min(github.public_repos / 30, 1.0) * 50

    return min(100, int(freq_score + repo_score))


def _score_repo_quality(github: GitHubSummary | None) -> int:
    """0-100 based on stars, language diversity, and topics usage."""
    if not github or not github.notable_repos:
        return 0

    repos = github.notable_repos

    # Stars (log-scale, cap at 100 total stars for full marks on this component)
    star_score = min(github.total_stars / 100, 1.0) * 35

    # Language diversity (more languages = better portfolio)
    lang_count = len(github.top_languages)
    lang_score = min(lang_count / 5, 1.0) * 30

    # Topics/tags usage (signal of well-maintained repos)
    repos_with_topics = sum(1 for r in repos if r.topics)
    topic_ratio = repos_with_topics / len(repos) if repos else 0
    topic_score = topic_ratio * 35

    return min(100, int(star_score + lang_score + topic_score))


def _score_documentation(github: GitHubSummary | None) -> int:
    """0-100 based on README presence and descriptions across repos."""
    if not github or not github.notable_repos:
        return 0

    repos = github.notable_repos
    has_readme = sum(1 for r in repos if r.has_readme)
    has_desc = sum(1 for r in repos if r.description)

    readme_pct = has_readme / len(repos) * 50
    desc_pct = has_desc / len(repos) * 50

    return min(100, int(readme_pct + desc_pct))


def _score_community(github: GitHubSummary | None) -> int:
    """0-100 based on followers and stars as community signals."""
    if not github:
        return 0

    # Followers (cap at 50 for full marks on this piece)
    follower_score = min(github.followers / 50, 1.0) * 50

    # Total stars as community validation
    star_score = min(github.total_stars / 50, 1.0) * 50

    return min(100, int(follower_score + star_score))


# ── Main scoring function ────────────────────────────────


def compute_developer_score(
    resume_text: str,
    skills: list[Skill],
    github: GitHubSummary | None,
) -> DeveloperScore:
    """Compute the weighted composite developer score."""

    categories = {
        "resume_completeness": _score_resume_completeness(resume_text),
        "skill_diversity": _score_skill_diversity(skills),
        "github_activity": _score_github_activity(github),
        "repo_quality": _score_repo_quality(github),
        "documentation": _score_documentation(github),
        "community": _score_community(github),
    }

    overall = int(sum(categories[k] * WEIGHTS[k] for k in WEIGHTS))
    overall = max(0, min(100, overall))

    # Build human-readable justification
    parts: list[str] = []
    for key, score in categories.items():
        label = key.replace("_", " ").title()
        if score >= 75:
            parts.append(f"{label}: strong ({score}/100)")
        elif score >= 40:
            parts.append(f"{label}: moderate ({score}/100)")
        else:
            parts.append(f"{label}: needs improvement ({score}/100)")

    justification = "Score breakdown — " + "; ".join(parts) + "."

    return DeveloperScore(
        overall=overall,
        categories=categories,
        justification=justification,
    )
