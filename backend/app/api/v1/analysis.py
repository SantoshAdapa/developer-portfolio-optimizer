import asyncio
import logging
import uuid
from typing import cast

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    UploadFile,
)
from fastapi.responses import JSONResponse

from app.ai.embeddings import embed_and_store_chunks
from app.models.schemas import (
    AnalysisResponse,
    CareerRoadmap,
    GitHubSummary,
    ProjectIdea,
    Skill,
    Suggestion,
)
from app.services.github_service import analyze_github_profile, extract_username
from app.services.recommendation_service import (
    extract_skills_with_ai,
    generate_career_roadmap,
    generate_portfolio_suggestions,
    generate_project_ideas,
)
from app.services.resume_service import (
    cleanup_file,
    extract_text_from_pdf,
    save_upload,
)
from app.utils.text_chunker import chunk_text
from app.services.scoring_service import (
    build_score_breakdown,
    compute_career_direction,
    compute_developer_score,
    compute_market_demand,
    compute_portfolio_depth,
    compute_radar_scores,
    compute_skill_categories,
    compute_skill_gaps,
    extract_programming_languages,
    extract_skills_from_github,
    extract_skills_from_text,
    generate_ai_insights,
    generate_fallback_project_ideas,
    generate_fallback_roadmap,
    generate_fallback_suggestions,
    generate_learning_roadmap,
)
from app.db import store
from app.utils.rate_limit import check_rate_limit
from app.utils.validators import validate_github_url, validate_pdf_file

logger = logging.getLogger(__name__)
router = APIRouter()


_ANALYSIS_ID_PATTERN = r"^[a-f0-9]{12}$"


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: str = Path(pattern=_ANALYSIS_ID_PATTERN),
):
    """Retrieve a previously computed analysis by ID."""
    stored = store.load("analysis", analysis_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Job is still processing in the background
    if stored.get("status") == "processing":
        return JSONResponse(
            status_code=202,
            content={"analysis_id": analysis_id, "status": "processing"},
        )

    # Job failed
    if stored.get("status") == "failed":
        raise HTTPException(status_code=500, detail="Analysis failed")

    return AnalysisResponse(
        analysis_id=analysis_id,
        developer_score=stored["developer_score"],
        skills=stored.get("skills", []),
        skill_categories=stored.get("skill_categories", []),
        radar_scores=stored.get("radar_scores"),
        programming_languages=stored.get("programming_languages", []),
        ai_insights=stored.get("ai_insights"),
        score_breakdown=stored.get("score_breakdown"),
        portfolio_depth=stored.get("portfolio_depth"),
        skill_gap=stored.get("skill_gap"),
        learning_roadmap=stored.get("learning_roadmap"),
        market_demand=stored.get("market_demand"),
        career_direction=stored.get("career_direction"),
        github_summary=stored.get("github_summary"),
        portfolio_suggestions=stored.get("portfolio_suggestions", []),
        project_ideas=stored.get("project_ideas", []),
        career_roadmap=stored.get("career_roadmap"),
    )


@router.post("", dependencies=[Depends(check_rate_limit)])
async def run_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile | None = File(None),
    github_url: str = Form(""),
    resume_id: str = Form(""),
):
    """Full analysis pipeline: resume and/or GitHub."""
    # ── Require at least one input ─────────────────────
    if not file and not github_url and not resume_id:
        raise HTTPException(
            status_code=400,
            detail="Provide a resume file and/or a GitHub profile URL",
        )

    # ── Validate inputs ────────────────────────────────
    if file:
        pdf_error = validate_pdf_file(file.filename or "", file.content_type)
        if pdf_error:
            raise HTTPException(status_code=400, detail=pdf_error)

    if github_url:
        # Accept both URLs and plain usernames — skip URL validation for plain usernames
        stripped = github_url.strip().lstrip("@")
        if "github.com" in stripped or "/" in stripped:
            gh_error = validate_github_url(github_url)
            if gh_error:
                raise HTTPException(status_code=400, detail=gh_error)

    # ── Save & extract resume (must happen before request closes) ──
    resume_text = ""
    analysis_id: str | None = None
    prev_skills: list[Skill] = []

    # Try reusing a previously uploaded resume
    if resume_id and not file:
        prev = store.load("resume", resume_id)
        if prev:
            resume_text = prev.get("text", "")
            analysis_id = resume_id
            # Restore previously extracted skills
            raw_skills = prev.get("skills", [])
            for rs in raw_skills:
                if isinstance(rs, dict):
                    try:
                        prev_skills.append(Skill(**rs))
                    except Exception:
                        pass

    if file:
        try:
            analysis_id, file_path = await save_upload(file)
        except ValueError as e:
            raise HTTPException(status_code=413, detail=str(e))

        try:
            resume_text = extract_text_from_pdf(file_path)
        except ValueError as e:
            cleanup_file(file_path)
            raise HTTPException(status_code=422, detail=str(e))
        finally:
            cleanup_file(file_path)

    if not analysis_id:
        analysis_id = uuid.uuid4().hex[:12]

    # ── Save initial processing status ─────────────────
    store.save("analysis", analysis_id, {"status": "processing"})

    # ── Schedule heavy work in background ──────────────
    background_tasks.add_task(
        _run_analysis_job,
        analysis_id,
        resume_text,
        github_url,
        list(prev_skills),
    )

    return JSONResponse(
        status_code=202,
        content={"analysis_id": analysis_id, "status": "processing"},
    )


async def _run_analysis_job(
    analysis_id: str,
    resume_text: str,
    github_url: str,
    prev_skills: list[Skill],
) -> None:
    """Execute the heavy analysis pipeline in the background."""
    try:
        github_summary: GitHubSummary | None = None

        # ── Parallel: skills extraction + GitHub analysis + embed chunks ──
        coros: list = []
        coro_labels: list[str] = []

        if resume_text:
            resume_chunks = chunk_text(resume_text)
            coros.append(extract_skills_with_ai(resume_text))
            coro_labels.append("skills")
            coros.append(embed_and_store_chunks(analysis_id, resume_chunks))
            coro_labels.append("embed")

        if github_url:
            try:
                gh_username = extract_username(github_url)
                coros.append(analyze_github_profile(gh_username))
                coro_labels.append("github")
            except ValueError as e:
                logger.warning("Invalid GitHub input: %s — %s", github_url, e)

        raw_results = (
            await asyncio.gather(*coros, return_exceptions=True) if coros else []
        )
        result_map = dict(zip(coro_labels, raw_results))

        # Unpack skills
        skills: list[Skill] = list(prev_skills)
        if "skills" in result_map:
            if isinstance(result_map["skills"], BaseException):
                logger.exception(
                    "Skill extraction failed", exc_info=result_map["skills"]
                )
            else:
                skills = cast(list[Skill], result_map["skills"])

        # Fallback: text-based skill extraction if AI produced few results
        if len(skills) < 5 and resume_text:
            text_skills = extract_skills_from_text(resume_text)
            existing_names = {s.name.lower() for s in skills}
            for ts in text_skills:
                if ts.name.lower() not in existing_names:
                    skills.append(ts)
                    existing_names.add(ts.name.lower())

        # Unpack embedding result — log but don't block
        if "embed" in result_map and isinstance(result_map["embed"], BaseException):
            logger.warning("Embedding storage failed: %s", result_map["embed"])

        # Unpack GitHub
        if "github" in result_map:
            if isinstance(result_map["github"], BaseException):
                logger.exception(
                    "GitHub analysis failed", exc_info=result_map["github"]
                )
            else:
                github_summary = cast(GitHubSummary, result_map["github"])

        # Extract skills from GitHub data (languages, topics, repo metadata)
        if github_summary:
            github_skills = extract_skills_from_github(github_summary)
            existing_names = {s.name.lower() for s in skills}
            for gs in github_skills:
                if gs.name.lower() not in existing_names:
                    skills.append(gs)
                    existing_names.add(gs.name.lower())
                else:
                    for s in skills:
                        if s.name.lower() == gs.name.lower() and s.source == "resume":
                            s.source = "both"
                            break

        # ── Scoring ────────────────────────────────────────
        developer_score = compute_developer_score(resume_text, skills, github_summary)

        # ── Enhanced analysis data ───────────────────────
        radar_scores = compute_radar_scores(skills, resume_text, github_summary)
        skill_categories = compute_skill_categories(skills)
        programming_languages = extract_programming_languages(skills, resume_text)
        score_breakdown = build_score_breakdown(
            developer_score.categories, github_summary is not None
        )
        ai_insights = generate_ai_insights(
            developer_score.categories,
            skills,
            github_summary,
            developer_score.overall,
            resume_text,
        )

        # ── Career intelligence features ──────────────────
        portfolio_depth = compute_portfolio_depth(skills, resume_text, github_summary)
        skill_gap = compute_skill_gaps(skills, resume_text)
        learning_roadmap = generate_learning_roadmap(skill_gap)
        market_demand = compute_market_demand(skills, resume_text)
        career_direction = compute_career_direction(skills, resume_text, radar_scores)

        # ── AI recommendations (parallel, with RAG) ────────
        suggestion_coro = generate_portfolio_suggestions(
            resume_text, skills, github_summary, analysis_id
        )
        project_coro = generate_project_ideas(skills, github_summary, analysis_id)
        roadmap_coro = generate_career_roadmap(
            resume_text, skills, github_summary, analysis_id
        )

        rec_results = await asyncio.gather(
            suggestion_coro, project_coro, roadmap_coro, return_exceptions=True
        )

        portfolio_suggestions: list[Suggestion] = (
            cast(list[Suggestion], rec_results[0])
            if not isinstance(rec_results[0], BaseException)
            else []
        )
        project_ideas: list[ProjectIdea] = (
            cast(list[ProjectIdea], rec_results[1])
            if not isinstance(rec_results[1], BaseException)
            else []
        )
        career_roadmap: CareerRoadmap | None = (
            cast(CareerRoadmap, rec_results[2])
            if not isinstance(rec_results[2], BaseException)
            else None
        )

        for i, r in enumerate(rec_results):
            if isinstance(r, BaseException):
                logger.exception("Recommendation generation %d failed", i, exc_info=r)

        # ── Local fallbacks when AI recommendations are empty ──
        if not portfolio_suggestions:
            portfolio_suggestions = generate_fallback_suggestions(
                skill_gap, skills, career_direction
            )
        if not project_ideas:
            project_ideas = generate_fallback_project_ideas(
                skill_gap, skills, career_direction
            )
        if not career_roadmap or not career_roadmap.milestones:
            career_roadmap = generate_fallback_roadmap(
                skill_gap, career_direction, skills
            )

        # ── Persist completed results ──────────────────────
        store.save(
            "analysis",
            analysis_id,
            {
                "status": "completed",
                "resume_text": resume_text,
                "skills": skills,
                "skill_categories": skill_categories,
                "radar_scores": radar_scores,
                "programming_languages": programming_languages,
                "ai_insights": ai_insights,
                "score_breakdown": score_breakdown,
                "portfolio_depth": portfolio_depth,
                "skill_gap": skill_gap,
                "learning_roadmap": learning_roadmap,
                "market_demand": market_demand,
                "career_direction": career_direction,
                "github_summary": github_summary,
                "developer_score": developer_score,
                "portfolio_suggestions": portfolio_suggestions,
                "project_ideas": project_ideas,
                "career_roadmap": career_roadmap,
            },
        )
    except Exception:
        logger.exception("Background analysis job %s failed", analysis_id)
        store.save(
            "analysis",
            analysis_id,
            {"status": "failed"},
        )
