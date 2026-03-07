from pydantic import BaseModel, Field, HttpUrl

from app.models.enums import CommitFrequency, Priority, Proficiency, SkillCategory


# ── Request Models ───────────────────────────────────────

class GitHubAnalyzeRequest(BaseModel):
    github_url: HttpUrl


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
