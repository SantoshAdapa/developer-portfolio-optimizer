"""Comparison service — compares two developer analysis results."""

from app.models.schemas import DeveloperScore, GitHubSummary, Skill


COMPARISON_DIMENSIONS = [
    "skill_diversity",
    "github_activity",
    "repo_quality",
    "documentation",
    "community",
]

# Extra resume-only dimensions used when GitHub data is absent
_RESUME_DIMENSIONS = [
    "resume_completeness",
    "content_quality",
    "formatting_quality",
    "impact_quantification",
    "keyword_density",
]


def _skill_names(skills: list[Skill]) -> set[str]:
    return {s.name.lower() for s in skills}


def _build_developer_summary(
    score: DeveloperScore,
    skills: list[Skill],
    github: GitHubSummary | None,
    label: str,
) -> dict:
    """Create a short summary dict for one developer."""
    top_skills = sorted(
        skills,
        key=lambda s: (
            {"advanced": 3, "intermediate": 2, "beginner": 1}.get(s.proficiency.value if hasattr(s.proficiency, "value") else str(s.proficiency), 0)
        ),
        reverse=True,
    )[:8]
    summary: dict = {
        "label": label,
        "overall_score": score.overall,
        "top_skills": [s.name for s in top_skills],
        "skill_count": len(skills),
    }
    if github:
        summary["github_username"] = github.username
        summary["public_repos"] = github.public_repos
        summary["total_stars"] = github.total_stars
        summary["top_languages"] = list(github.top_languages.keys())[:5]
    return summary


def _compare_projects(
    github_a: GitHubSummary | None,
    github_b: GitHubSummary | None,
) -> dict:
    """Compare notable projects / repos between two developers."""
    repos_a = github_a.notable_repos if github_a else []
    repos_b = github_b.notable_repos if github_b else []

    def _repo_info(repos: list) -> list[dict]:
        return [
            {
                "name": r.name,
                "language": r.language,
                "stars": r.stars,
                "technologies": r.detected_technologies[:5] if r.detected_technologies else [],
                "has_ci": r.has_ci,
                "has_tests": r.has_tests,
            }
            for r in repos[:6]
        ]

    return {
        "developer_a_projects": _repo_info(repos_a),
        "developer_b_projects": _repo_info(repos_b),
        "developer_a_project_count": len(repos_a),
        "developer_b_project_count": len(repos_b),
    }


def _compare_strengths_weaknesses(
    score_a: DeveloperScore,
    score_b: DeveloperScore,
    skills_a: list[Skill],
    skills_b: list[Skill],
) -> dict:
    """Identify strengths and weaknesses for each developer."""
    all_dims = list(score_a.categories.keys() | score_b.categories.keys())

    strengths_a: list[str] = []
    weaknesses_a: list[str] = []
    strengths_b: list[str] = []
    weaknesses_b: list[str] = []

    for dim in all_dims:
        val_a = score_a.categories.get(dim, 0)
        val_b = score_b.categories.get(dim, 0)
        dim_label = dim.replace("_", " ").title()

        if val_a > val_b + 5:
            strengths_a.append(dim_label)
            weaknesses_b.append(dim_label)
        elif val_b > val_a + 5:
            strengths_b.append(dim_label)
            weaknesses_a.append(dim_label)

    # Unique skill strengths
    names_a = _skill_names(skills_a)
    names_b = _skill_names(skills_b)
    unique_a = names_a - names_b
    unique_b = names_b - names_a

    if unique_a:
        strengths_a.append(f"{len(unique_a)} unique skill(s)")
    if unique_b:
        strengths_b.append(f"{len(unique_b)} unique skill(s)")

    return {
        "developer_a": {"strengths": strengths_a, "weaknesses": weaknesses_a},
        "developer_b": {"strengths": strengths_b, "weaknesses": weaknesses_b},
    }


def compare_profiles(
    score_a: DeveloperScore,
    skills_a: list[Skill],
    score_b: DeveloperScore,
    skills_b: list[Skill],
    github_a: GitHubSummary | None = None,
    github_b: GitHubSummary | None = None,
) -> dict:
    """Compare two developer profiles across all scoring dimensions.

    Returns a comparison dict suitable for the API response.
    """

    # ── Score difference ───────────────────────────────────
    score_difference = score_a.overall - score_b.overall

    # ── Choose dimensions based on available data ──────────
    # If both have GitHub-related scores, use full set; otherwise fallback to resume dims
    has_github_scores = any(
        score_a.categories.get(d, 0) > 0 or score_b.categories.get(d, 0) > 0
        for d in COMPARISON_DIMENSIONS
    )
    dims = COMPARISON_DIMENSIONS if has_github_scores else _RESUME_DIMENSIONS

    # ── Per-dimension comparison ───────────────────────────
    dimension_comparison: list[dict] = []
    a_wins = 0
    b_wins = 0

    for dim in dims:
        val_a = score_a.categories.get(dim, 0)
        val_b = score_b.categories.get(dim, 0)
        diff = val_a - val_b
        dimension_comparison.append(
            {
                "dimension": dim,
                "developer_a": val_a,
                "developer_b": val_b,
                "difference": diff,
            }
        )
        if val_a > val_b:
            a_wins += 1
        elif val_b > val_a:
            b_wins += 1

    # ── Skill gap ──────────────────────────────────────────
    names_a = _skill_names(skills_a)
    names_b = _skill_names(skills_b)

    skill_gap = sorted(
        [{"skill": s, "present_in": "developer_a"} for s in names_a - names_b]
        + [{"skill": s, "present_in": "developer_b"} for s in names_b - names_a],
        key=lambda x: x["skill"],
    )

    # ── Winner ─────────────────────────────────────────────
    if score_a.overall > score_b.overall:
        winner = "developer_a"
    elif score_b.overall > score_a.overall:
        winner = "developer_b"
    else:
        winner = "tie"

    # ── Summary ────────────────────────────────────────────
    abs_diff = abs(score_difference)
    if winner == "tie":
        summary = (
            "Both developers have identical overall scores. "
            f"Developer A leads in {a_wins} dimension(s), "
            f"Developer B leads in {b_wins}."
        )
    else:
        leader = "Developer A" if winner == "developer_a" else "Developer B"
        summary = (
            f"{leader} scores {abs_diff} points higher overall. "
            f"Developer A leads in {a_wins} dimension(s), "
            f"Developer B leads in {b_wins}. "
            f"There are {len(skill_gap)} skill differences between the profiles."
        )

    # ── Extended fields ────────────────────────────────────
    developer_a_summary = _build_developer_summary(score_a, skills_a, github_a, "Developer A")
    developer_b_summary = _build_developer_summary(score_b, skills_b, github_b, "Developer B")
    project_comparison = _compare_projects(github_a, github_b)
    strengths_weaknesses = _compare_strengths_weaknesses(score_a, score_b, skills_a, skills_b)

    # Shared vs unique skills
    shared_skills = sorted(names_a & names_b)
    skill_comparison = {
        "shared_skills": shared_skills,
        "developer_a_unique": sorted(names_a - names_b),
        "developer_b_unique": sorted(names_b - names_a),
        "developer_a_total": len(skills_a),
        "developer_b_total": len(skills_b),
    }

    # Build final insights
    insights: list[str] = [summary]
    if shared_skills:
        insights.append(
            f"Both developers share {len(shared_skills)} common skill(s): "
            + ", ".join(shared_skills[:8])
            + ("..." if len(shared_skills) > 8 else "")
            + "."
        )
    if github_a and github_b:
        star_diff = (github_a.total_stars or 0) - (github_b.total_stars or 0)
        if abs(star_diff) > 0:
            star_leader = "Developer A" if star_diff > 0 else "Developer B"
            insights.append(f"{star_leader} has {abs(star_diff)} more GitHub stars.")

    return {
        "score_difference": score_difference,
        "dimension_comparison": dimension_comparison,
        "skill_gap": skill_gap,
        "github_activity_diff": (
            score_a.categories.get("github_activity", 0)
            - score_b.categories.get("github_activity", 0)
        ),
        "winner": winner,
        "summary": summary,
        "developer_a_summary": developer_a_summary,
        "developer_b_summary": developer_b_summary,
        "skill_comparison": skill_comparison,
        "project_comparison": project_comparison,
        "strengths_weaknesses": strengths_weaknesses,
        "insights": insights,
    }
