"""Comparison service — compares two developer analysis results."""

from app.models.schemas import DeveloperScore, Skill


COMPARISON_DIMENSIONS = [
    "skill_diversity",
    "github_activity",
    "repo_quality",
    "documentation",
    "community",
]


def _skill_names(skills: list[Skill]) -> set[str]:
    return {s.name.lower() for s in skills}


def compare_profiles(
    score_a: DeveloperScore,
    skills_a: list[Skill],
    score_b: DeveloperScore,
    skills_b: list[Skill],
) -> dict:
    """Compare two developer profiles across all scoring dimensions.

    Returns a comparison dict suitable for the API response.
    """

    # ── Score difference ───────────────────────────────────
    score_difference = score_a.overall - score_b.overall

    # ── Per-dimension comparison ───────────────────────────
    dimension_comparison: list[dict] = []
    a_wins = 0
    b_wins = 0

    for dim in COMPARISON_DIMENSIONS:
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
        [
            {"skill": s, "present_in": "developer_a"}
            for s in names_a - names_b
        ]
        + [
            {"skill": s, "present_in": "developer_b"}
            for s in names_b - names_a
        ],
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
    }
