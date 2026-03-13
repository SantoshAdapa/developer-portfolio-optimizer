"""Job Description matching service.

Supports three matching modes:
1. **JD text** – paste a full job description; skills are extracted with AI
   then matched semantically against the developer's skill set.
2. **Role template** – pick a predefined role (ML Engineer, Backend Developer,
   etc.); the template's required/preferred skills are used.
3. **Experience level** – pick a seniority tier; generic expectations are
   compared against the profile.

All modes use the normalisation dictionary and (when available) embedding-
based semantic similarity so that "NLP" matches "Natural Language Processing".
"""

from __future__ import annotations

import logging

from app.ai.skill_matcher import match_skills_sync, SkillMatchResult
from app.data.role_templates import (
    EXPERIENCE_LEVELS,
    ROLE_TEMPLATES,
    compute_domain_distribution,
)
from app.data.skill_normalization import normalize_skill
from app.models.schemas import Skill
from app.services.scoring_service import extract_skills_from_text

logger = logging.getLogger(__name__)

_PROF_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}


# ── Async version with semantic (embedding) matching ─────────


async def match_job_description_semantic(
    developer_skills: list[Skill],
    jd_text: str | None = None,
    role_key: str | None = None,
    experience_level: str | None = None,
) -> dict:
    """Main entry point – choose mode based on which argument is supplied."""
    from app.ai.skill_matcher import match_skills_semantic  # async import

    # Determine required skill names
    required_skills: dict[str, str] = {}
    preferred_skills: dict[str, str] = {}
    label = ""

    if role_key and role_key in ROLE_TEMPLATES:
        tmpl = ROLE_TEMPLATES[role_key]
        required_skills = dict(tmpl["required"])
        preferred_skills = dict(tmpl.get("preferred", {}))
        label = tmpl["label"]

    elif experience_level and experience_level in EXPERIENCE_LEVELS:
        lvl = EXPERIENCE_LEVELS[experience_level]
        label = lvl["label"]
        # For experience levels, use developer's own skill names as check
        # and measure breadth rather than specific skills
        return _match_experience_level(developer_skills, experience_level)

    elif jd_text:
        jd_extracted = extract_skills_from_text(jd_text)
        if not jd_extracted:
            return _empty_result(
                "No skills could be extracted from the job description."
            )
        for sk in jd_extracted:
            canon = normalize_skill(sk.name)
            prof = (
                sk.proficiency.value
                if hasattr(sk.proficiency, "value")
                else str(sk.proficiency)
            )
            required_skills[canon] = prof
        label = "Job Description"
    else:
        return _empty_result("No job description, role, or experience level provided.")

    # Collect developer skill names (canonical)
    dev_skill_names = [normalize_skill(s.name) for s in developer_skills]
    dev_skill_map = {normalize_skill(s.name).lower(): s for s in developer_skills}

    # --- Semantic matching for required skills ---
    all_req_names = list(required_skills.keys())
    try:
        req_results = await match_skills_semantic(all_req_names, dev_skill_names)
    except Exception:
        logger.warning("Semantic matching failed, using sync fallback")
        req_results = match_skills_sync(all_req_names, dev_skill_names)

    matched, partial, missing = _classify_results(
        req_results, required_skills, dev_skill_map
    )

    # --- Preferred skills (bonus) ---
    pref_matched: list[dict] = []
    if preferred_skills:
        pref_names = list(preferred_skills.keys())
        try:
            pref_results = await match_skills_semantic(pref_names, dev_skill_names)
        except Exception:
            pref_results = match_skills_sync(pref_names, dev_skill_names)

        for r in pref_results:
            if r.matched_to is not None:
                dev_sk = dev_skill_map.get(normalize_skill(r.matched_to).lower())
                dev_prof = _get_prof(dev_sk)
                pref_matched.append(
                    {
                        "skill": normalize_skill(r.skill),
                        "status": "matched",
                        "proficiency": dev_prof,
                        "required_level": preferred_skills.get(r.skill, "intermediate"),
                        "match_type": r.match_type,
                    }
                )

    # --- Scoring (weighted) ---
    # Required skills weight = 3, Preferred skills weight = 2
    REQUIRED_WEIGHT = 3
    PREFERRED_WEIGHT = 2
    total_req = len(required_skills)
    total_pref = len(preferred_skills)

    total_weight = total_req * REQUIRED_WEIGHT + total_pref * PREFERRED_WEIGHT
    matched_weight = (
        (len(matched) * REQUIRED_WEIGHT)
        + (len(partial) * 0.5 * REQUIRED_WEIGHT)
        + (len(pref_matched) * PREFERRED_WEIGHT)
    )
    pct = int((matched_weight / total_weight) * 100) if total_weight else 0
    pct = max(0, min(100, pct))

    # Confidence
    if len(matched) + len(partial) >= total_req * 0.7:
        confidence = "high"
    elif len(matched) + len(partial) >= total_req * 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    # Domain distribution
    domain_dist = compute_domain_distribution(dev_skill_names)

    summary = _build_summary(pct, matched, partial, missing, pref_matched, label)

    # Recommended skills to learn (from missing + partial)
    recommended = [s["skill"] for s in missing[:10]]
    if partial:
        recommended.extend(s["skill"] for s in partial[:5])

    return {
        "match_percentage": pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "partial_skills": partial,
        "preferred_matched": pref_matched,
        "confidence": confidence,
        "label": label,
        "domain_distribution": domain_dist,
        "summary": summary,
        "recommended_skills": recommended,
    }


# ── Sync fallback (used by old endpoint) ─────────────────────


def match_job_description(
    jd_text: str,
    developer_skills: list[Skill],
) -> dict:
    """Synchronous JD match using normalisation + alias matching."""
    jd_skills = extract_skills_from_text(jd_text)
    if not jd_skills:
        return _empty_result("No skills could be extracted from the job description.")

    dev_skill_names = [normalize_skill(s.name) for s in developer_skills]
    dev_skill_map = {normalize_skill(s.name).lower(): s for s in developer_skills}

    required: dict[str, str] = {}
    for sk in jd_skills:
        canon = normalize_skill(sk.name)
        prof = (
            sk.proficiency.value
            if hasattr(sk.proficiency, "value")
            else str(sk.proficiency)
        )
        required[canon] = prof

    results = match_skills_sync(list(required.keys()), dev_skill_names)
    matched, partial, missing = _classify_results(results, required, dev_skill_map)

    total = len(required)
    pct = int(((len(matched) + len(partial) * 0.5) / total) * 100) if total else 0
    pct = max(0, min(100, pct))

    confidence = "high" if pct >= 70 else ("medium" if pct >= 40 else "low")

    summary = _build_summary(pct, matched, partial, missing, [], "Job Description")

    return {
        "match_percentage": pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "partial_skills": partial,
        "preferred_matched": [],
        "confidence": confidence,
        "label": "Job Description",
        "domain_distribution": compute_domain_distribution(dev_skill_names),
        "summary": summary,
        "recommended_skills": [s["skill"] for s in missing[:10]],
    }


# ── Experience-level matching ────────────────────────────────


def _match_experience_level(
    developer_skills: list[Skill],
    level_key: str,
) -> dict:
    """Compare a developer's profile against an experience-level expectation.

    Uses skill count and proficiency level to compute a meaningful score.
    Only counts unique skills (by canonical name). Skills below the expected
    proficiency are classified as partial matches.
    """
    lvl = EXPERIENCE_LEVELS[level_key]
    expected_count = lvl["expected_skills"]
    expected_prof = lvl["expected_proficiency"]

    prof_rank_map = {"beginner": 0, "intermediate": 1, "advanced": 2}
    expected_rank = prof_rank_map.get(expected_prof, 0)

    # Deduplicate skills by canonical name, keeping highest proficiency
    best_skill: dict[str, tuple[Skill, int]] = {}
    for s in developer_skills:
        p = (
            s.proficiency.value
            if hasattr(s.proficiency, "value")
            else str(s.proficiency)
        )
        skill_rank = prof_rank_map.get(p, 0)
        canon = normalize_skill(s.name).lower()
        if canon not in best_skill or skill_rank > best_skill[canon][1]:
            best_skill[canon] = (s, skill_rank)

    matched_details: list[dict] = []
    below_prof_details: list[dict] = []

    for canon, (s, skill_rank) in best_skill.items():
        p = (
            s.proficiency.value
            if hasattr(s.proficiency, "value")
            else str(s.proficiency)
        )
        entry = {
            "skill": normalize_skill(s.name),
            "status": "matched" if skill_rank >= expected_rank else "partial",
            "proficiency": p,
            "required_level": expected_prof,
            "match_type": "exact",
        }
        if skill_rank >= expected_rank:
            matched_details.append(entry)
        else:
            below_prof_details.append(entry)

    unique_count = len(best_skill)
    meeting_prof = len(matched_details)

    # Skill count score: what fraction of expected skills do you have?
    skill_count_score = min(100, int(unique_count / max(expected_count, 1) * 100))
    # Proficiency score: what fraction of your skills meet the bar?
    prof_score = (
        min(100, int(meeting_prof / max(unique_count, 1) * 100))
        if unique_count > 0
        else 0
    )
    # Combined: 50% breadth + 50% proficiency depth
    pct = int(skill_count_score * 0.5 + prof_score * 0.5)
    pct = max(0, min(100, pct))

    confidence = "high" if pct >= 70 else ("medium" if pct >= 40 else "low")

    dev_names = [normalize_skill(s.name) for s in developer_skills]
    summary = (
        f"For {lvl['label']} level: you have {unique_count} unique skills "
        f"(expected ~{expected_count}). "
        f"{meeting_prof} skills meet the {expected_prof} proficiency bar."
    )

    return {
        "match_percentage": pct,
        "matched_skills": matched_details,
        "missing_skills": [],
        "partial_skills": below_prof_details,
        "preferred_matched": [],
        "confidence": confidence,
        "label": lvl["label"],
        "domain_distribution": compute_domain_distribution(dev_names),
        "summary": summary,
        "recommended_skills": [p["skill"] for p in below_prof_details[:5]],
    }


# ── Helpers ──────────────────────────────────────────────────


def _classify_results(
    results: list[SkillMatchResult],
    required_levels: dict[str, str],
    dev_skill_map: dict[str, Skill],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Classify semantic match results into matched / partial / missing."""
    matched: list[dict] = []
    partial: list[dict] = []
    missing: list[dict] = []

    for r in results:
        req_level = required_levels.get(r.skill, "intermediate")
        if r.matched_to is None:
            missing.append(
                {
                    "skill": normalize_skill(r.skill),
                    "status": "gap",
                    "proficiency": "",
                    "required_level": req_level,
                    "match_type": "none",
                }
            )
        else:
            dev_sk = dev_skill_map.get(normalize_skill(r.matched_to).lower())
            dev_prof = _get_prof(dev_sk)
            dev_rank = _PROF_RANK.get(dev_prof, 0)
            req_rank = _PROF_RANK.get(req_level, 0)

            if dev_rank >= req_rank:
                matched.append(
                    {
                        "skill": normalize_skill(r.skill),
                        "status": "matched",
                        "proficiency": dev_prof,
                        "required_level": req_level,
                        "match_type": r.match_type,
                    }
                )
            else:
                partial.append(
                    {
                        "skill": normalize_skill(r.skill),
                        "status": "partial",
                        "proficiency": dev_prof,
                        "required_level": req_level,
                        "match_type": r.match_type,
                    }
                )

    return matched, partial, missing


def _get_prof(skill: Skill | None) -> str:
    if skill is None:
        return "beginner"
    p = skill.proficiency
    return p.value if hasattr(p, "value") else str(p)


def _build_summary(
    pct: int,
    matched: list[dict],
    partial: list[dict],
    missing: list[dict],
    pref_matched: list[dict],
    label: str,
) -> str:
    total = len(matched) + len(partial) + len(missing)
    parts = [
        f"You match {pct}% for {label} ({len(matched)}/{total} required skills fully matched)."
    ]
    if pref_matched:
        parts.append(f"{len(pref_matched)} preferred skill(s) matched.")
    if partial:
        names = ", ".join(s["skill"] for s in partial[:5])
        parts.append(f"{len(partial)} skill(s) need leveling up: {names}.")
    if missing:
        names = ", ".join(s["skill"] for s in missing[:5])
        extra = f" and {len(missing) - 5} more" if len(missing) > 5 else ""
        parts.append(f"Key gaps: {names}{extra}.")
    return " ".join(parts)


def _empty_result(summary: str) -> dict:
    return {
        "match_percentage": 0,
        "matched_skills": [],
        "missing_skills": [],
        "partial_skills": [],
        "preferred_matched": [],
        "confidence": "low",
        "label": "",
        "domain_distribution": {},
        "summary": summary,
        "recommended_skills": [],
    }
