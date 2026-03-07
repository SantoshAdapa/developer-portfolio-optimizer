"""Benchmark service — compares a developer score against predefined archetypes."""

import json
from pathlib import Path

from app.models.schemas import DeveloperScore


_BENCHMARKS_PATH = Path(__file__).resolve().parent.parent / "data" / "benchmarks.json"

_benchmarks_cache: dict | None = None


def _load_benchmarks() -> dict:
    global _benchmarks_cache
    if _benchmarks_cache is None:
        with open(_BENCHMARKS_PATH, "r", encoding="utf-8") as f:
            _benchmarks_cache = json.load(f)
    return _benchmarks_cache


def _fit_score(categories: dict[str, int], archetype: dict) -> float:
    """Return 0-100 indicating how well the developer fits this archetype.

    For each dimension the score falls within [min, max] → full credit,
    below min → partial, above max → partial (over-qualified).
    """
    ranges = archetype["expected_ranges"]
    total = 0.0
    count = 0

    for dim, rng in ranges.items():
        val = categories.get(dim, 0)
        low, high = rng["min"], rng["max"]

        if low <= val <= high:
            total += 100.0
        elif val < low:
            total += max(0.0, (val / low) * 100) if low > 0 else 100.0
        else:
            # Above max — still a decent fit, just over-qualified
            overshoot = val - high
            total += max(50.0, 100.0 - overshoot)

        count += 1

    return round(total / count, 1) if count else 0.0


def _percentile(score: int, all_averages: list[int]) -> int:
    """Estimate a percentile given the archetype average distribution."""
    below = sum(1 for avg in all_averages if score >= avg)
    return int(below / len(all_averages) * 100) if all_averages else 50


def evaluate_against_benchmarks(developer_score: DeveloperScore) -> dict:
    """Compare a developer's score against all predefined archetypes.

    Returns closest archetype, percentile, per-archetype fit scores, and details.
    """
    data = _load_benchmarks()
    archetypes = data["archetypes"]

    benchmark_scores: dict[str, float] = {}
    all_averages: list[int] = []

    for key, archetype in archetypes.items():
        fit = _fit_score(developer_score.categories, archetype)
        benchmark_scores[key] = fit
        all_averages.append(archetype["average_overall"])

    # Closest archetype = highest fit score
    closest_archetype = max(benchmark_scores, key=benchmark_scores.get)  # type: ignore[arg-type]

    # Percentile among archetype averages
    score_percentile = _percentile(developer_score.overall, all_averages)

    # Build detail list for each archetype
    archetype_details: list[dict] = []
    for key, archetype in archetypes.items():
        archetype_details.append(
            {
                "key": key,
                "label": archetype["label"],
                "description": archetype["description"],
                "average_overall": archetype["average_overall"],
                "fit_score": benchmark_scores[key],
            }
        )

    return {
        "closest_archetype": closest_archetype,
        "closest_archetype_label": archetypes[closest_archetype]["label"],
        "score_percentile": score_percentile,
        "developer_overall": developer_score.overall,
        "benchmark_scores": benchmark_scores,
        "archetype_details": archetype_details,
    }
