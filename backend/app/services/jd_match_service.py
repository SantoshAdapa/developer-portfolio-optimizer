"""Job Description matching service.

Extracts required skills from a job description, then compares them against
a developer's analysed skill set to produce a match score and breakdown.
"""

from __future__ import annotations

from app.models.schemas import Skill
from app.services.scoring_service import extract_skills_from_text


def match_job_description(
    jd_text: str,
    developer_skills: list[Skill],
) -> dict:
    """Compare *developer_skills* against skills required by *jd_text*.

    Returns a dict with:
      - match_percentage  (0-100)
      - matched_skills    list[dict]
      - missing_skills    list[dict]
      - partial_skills    list[dict]
      - summary           str
    """

    # 1. Extract "required" skills from the JD using the same NLP pipeline
    jd_skills = extract_skills_from_text(jd_text)
    if not jd_skills:
        return {
            "match_percentage": 0,
            "matched_skills": [],
            "missing_skills": [],
            "partial_skills": [],
            "summary": "No skills could be extracted from the job description.",
        }

    # 2. Build normalised look-ups for the developer's skills
    dev_map: dict[str, Skill] = {}
    for sk in developer_skills:
        dev_map[sk.name.lower()] = sk

    _PROF_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}

    matched: list[dict] = []
    partial: list[dict] = []
    missing: list[dict] = []

    for jd_sk in jd_skills:
        key = jd_sk.name.lower()
        dev_sk = dev_map.get(key)
        if dev_sk is None:
            missing.append(
                {
                    "skill": jd_sk.name,
                    "status": "gap",
                    "proficiency": "",
                    "required_level": jd_sk.proficiency.value
                    if hasattr(jd_sk.proficiency, "value")
                    else str(jd_sk.proficiency),
                }
            )
        else:
            dev_prof = (
                dev_sk.proficiency.value
                if hasattr(dev_sk.proficiency, "value")
                else str(dev_sk.proficiency)
            )
            jd_prof = (
                jd_sk.proficiency.value
                if hasattr(jd_sk.proficiency, "value")
                else str(jd_sk.proficiency)
            )
            dev_rank = _PROF_RANK.get(dev_prof, 0)
            jd_rank = _PROF_RANK.get(jd_prof, 0)

            if dev_rank >= jd_rank:
                matched.append(
                    {
                        "skill": jd_sk.name,
                        "status": "matched",
                        "proficiency": dev_prof,
                        "required_level": jd_prof,
                    }
                )
            else:
                partial.append(
                    {
                        "skill": jd_sk.name,
                        "status": "partial",
                        "proficiency": dev_prof,
                        "required_level": jd_prof,
                    }
                )

    total = len(matched) + len(partial) + len(missing)
    if total == 0:
        pct = 0
    else:
        # Full matches count 1, partial 0.5, missing 0
        pct = int(((len(matched) + len(partial) * 0.5) / total) * 100)

    summary_parts: list[str] = []
    summary_parts.append(
        f"You match {pct}% of the required skills ({len(matched)}/{total} fully matched)."
    )
    if partial:
        summary_parts.append(
            f"{len(partial)} skill(s) need improvement: "
            + ", ".join(s["skill"] for s in partial)
            + "."
        )
    if missing:
        top_missing = [s["skill"] for s in missing[:5]]
        summary_parts.append(
            f"Key gaps: {', '.join(top_missing)}"
            + ("." if len(missing) <= 5 else f" and {len(missing) - 5} more.")
        )

    return {
        "match_percentage": pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "partial_skills": partial,
        "summary": " ".join(summary_parts),
    }
