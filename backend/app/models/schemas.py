from pydantic import BaseModel, Field

from app.models.enums import CommitFrequency, Priority, Proficiency, SkillCategory


# ── Request Models ───────────────────────────────────────


class GitHubAnalyzeRequest(BaseModel):
    github_username: str


# ── Shared Sub-Models ────────────────────────────────────


class Skill(BaseModel):
    name: str
    category: SkillCategory
    proficiency: Proficiency
    source: str = Field(description="resume | github | both")


class RepoSummary(BaseModel):
    name: str
    description: str | None = None
    language: str | None = None
    stars: int = 0
    forks: int = 0
    has_readme: bool = False
    topics: list[str] = []


class GitHubSummary(BaseModel):
    username: str
    avatar_url: str | None = None
    bio: str | None = None
    public_repos: int = 0
    followers: int = 0
    top_languages: dict[str, float] = Field(
        default_factory=dict, description="language → percentage"
    )
    total_stars: int = 0
    commit_frequency: CommitFrequency = CommitFrequency.SPORADIC
    notable_repos: list[RepoSummary] = []


class DeveloperScore(BaseModel):
    overall: int = Field(ge=0, le=100)
    categories: dict[str, int] = Field(
        default_factory=dict,
        description="e.g. {'resume': 80, 'github': 72, 'skills': 85}",
    )
    justification: str = ""


class Suggestion(BaseModel):
    area: str
    current_state: str
    recommendation: str
    priority: Priority
    impact: str


class ProjectIdea(BaseModel):
    title: str
    description: str
    tech_stack: list[str] = []
    difficulty: str = ""
    estimated_time: str = ""
    skills_developed: list[str] = []


class Milestone(BaseModel):
    timeframe: str
    goals: list[str] = []
    skills_to_learn: list[str] = []
    actions: list[str] = []


class CareerRoadmap(BaseModel):
    current_level: str = ""
    target_role: str = ""
    milestones: list[Milestone] = []


class ProgrammingLanguageScore(BaseModel):
    name: str
    proficiency: Proficiency
    confidence: float = Field(ge=0, le=1)
    context: str = ""


class SkillCategoryBreakdown(BaseModel):
    category: str
    skills: list[str] = []
    score: int = Field(ge=0, le=100)


class RadarScores(BaseModel):
    frontend: int = 0
    backend: int = 0
    data: int = 0
    ml_ai: int = 0
    devops: int = 0
    docs: int = 0


class AiInsights(BaseModel):
    strengths: list[str] = []
    weaknesses: list[str] = []
    career_potential: str = ""
    recommended_improvements: list[str] = []


class ScoreBreakdown(BaseModel):
    resume_completeness: int = 0
    content_quality: int = 0
    skill_diversity: int = 0
    formatting_quality: int = 0
    impact_quantification: int = 0
    keyword_density: int = 0
    github_activity: int | None = None
    repo_quality: int | None = None
    documentation: int | None = None
    community: int | None = None


# ── Response Models ──────────────────────────────────────


class ResumeUploadResponse(BaseModel):
    analysis_id: str
    filename: str
    extracted_text_preview: str = Field(
        default="", description="First 500 chars of extracted text"
    )
    skills: list[Skill] = []


class GitHubAnalysisResponse(BaseModel):
    analysis_id: str
    summary: GitHubSummary


class AnalysisResponse(BaseModel):
    analysis_id: str
    developer_score: DeveloperScore
    skills: list[Skill] = []
    skill_categories: list[SkillCategoryBreakdown] = []
    radar_scores: RadarScores | None = None
    programming_languages: list[ProgrammingLanguageScore] = []
    ai_insights: AiInsights | None = None
    score_breakdown: ScoreBreakdown | None = None
    github_summary: GitHubSummary | None = None
    portfolio_suggestions: list[Suggestion] = []
    project_ideas: list[ProjectIdea] = []
    career_roadmap: CareerRoadmap | None = None


class PortfolioSuggestionsResponse(BaseModel):
    analysis_id: str
    suggestions: list[Suggestion] = []


class ProjectIdeasResponse(BaseModel):
    analysis_id: str
    project_ideas: list[ProjectIdea] = []


class CareerRoadmapResponse(BaseModel):
    analysis_id: str
    roadmap: CareerRoadmap


# ── Comparison & Benchmarking ────────────────────────────


class CompareRequest(BaseModel):
    analysis_id_a: str = Field(pattern=r"^[a-f0-9]{12}$")
    analysis_id_b: str = Field(pattern=r"^[a-f0-9]{12}$")


class DimensionComparison(BaseModel):
    dimension: str
    developer_a: int
    developer_b: int
    difference: int


class SkillGapEntry(BaseModel):
    skill: str
    present_in: str = Field(description="developer_a | developer_b")


class CompareResponse(BaseModel):
    analysis_id_a: str
    analysis_id_b: str
    score_difference: int
    dimension_comparison: list[DimensionComparison] = []
    skill_gap: list[SkillGapEntry] = []
    github_activity_diff: int = 0
    winner: str = Field(description="developer_a | developer_b | tie")
    summary: str = ""


class ArchetypeDetail(BaseModel):
    key: str
    label: str
    description: str
    average_overall: int
    fit_score: float


class BenchmarkResponse(BaseModel):
    analysis_id: str
    closest_archetype: str
    closest_archetype_label: str
    score_percentile: int
    developer_overall: int
    benchmark_scores: dict[str, float] = Field(
        default_factory=dict,
        description="archetype_key → fit_score (0-100)",
    )
    archetype_details: list[ArchetypeDetail] = []
