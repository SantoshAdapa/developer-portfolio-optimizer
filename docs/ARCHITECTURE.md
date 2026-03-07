# Developer Portfolio Optimizer — System Architecture

## 1. System Overview

An AI-powered SaaS application that analyzes a developer's resume and GitHub profile to provide actionable portfolio improvements, career roadmaps, and project suggestions.

**Tech Stack Summary:**

| Layer          | Technology                                  |
|----------------|---------------------------------------------|
| Frontend       | Next.js 14 (App Router), React, TailwindCSS, shadcn/ui, Framer Motion |
| Backend        | Python 3.12, FastAPI, async/await           |
| AI Engine      | Google Gemini API, Embeddings, RAG          |
| Vector Store   | ChromaDB                                    |
| External APIs  | GitHub REST API v3                          |
| Infrastructure | Docker, GitHub Actions, AWS EC2             |

---

## 2. System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Next.js App Router                                        │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐ │  │
│  │  │ Dashboard │ │  Upload   │ │ Analysis │ │   Roadmap   │ │  │
│  │  └──────────┘ └───────────┘ └──────────┘ └─────────────┘ │  │
│  │  TailwindCSS + shadcn/ui + Framer Motion                  │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS / REST
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  API Gateway  ──▶  Rate Limiter  ──▶  CORS Middleware    │    │
│  └──────────────────────────┬───────────────────────────────┘    │
│                              │                                    │
│  ┌───────────────────────────┼──────────────────────────────┐    │
│  │              SERVICE LAYER                                │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │    │
│  │  │ Resume Svc   │ │ GitHub Svc   │ │ Scoring Svc      │ │    │
│  │  │ - PDF parse  │ │ - Repo fetch │ │ - Weighted score │ │    │
│  │  │ - Skill ext  │ │ - Lang stats │ │ - Benchmarks     │ │    │
│  │  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘ │    │
│  │         │                │                   │            │    │
│  │  ┌──────┴────────────────┴───────────────────┴─────────┐ │    │
│  │  │             AI / RAG PIPELINE                        │ │    │
│  │  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐ │ │    │
│  │  │  │ Embeddings │ │ RAG Engine │ │ Gemini Client    │ │ │    │
│  │  │  │ (Gemini)   │ │ Retrieval  │ │ Prompt Templates │ │ │    │
│  │  │  └─────┬──────┘ └─────┬──────┘ └────────┬─────────┘ │ │    │
│  │  └────────┼───────────────┼─────────────────┼───────────┘ │    │
│  └───────────┼───────────────┼─────────────────┼─────────────┘    │
└──────────────┼───────────────┼─────────────────┼─────────────────┘
               │               │                 │
       ┌───────▼───────┐      │          ┌───────▼───────┐
       │   ChromaDB    │◀─────┘          │  Gemini API   │
       │ Vector Store  │                 │  (External)   │
       └───────────────┘                 └───────────────┘
                                                │
                                         ┌──────▼──────┐
                                         │ GitHub API  │
                                         │ (External)  │
                                         └─────────────┘
```

---

## 3. Backend Architecture

### 3.1 Layer Breakdown

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, lifespan events
│   ├── config.py                # Pydantic Settings (env vars)
│   ├── dependencies.py          # Dependency injection
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py        # Aggregate v1 router
│   │   │   ├── resume.py        # POST /upload, GET /skills
│   │   │   ├── github.py        # POST /github/analyze
│   │   │   ├── analysis.py      # POST /analyze, GET /score
│   │   │   └── recommendations.py  # GET /recommendations/*
│   │   └── middleware.py        # CORS, rate limiting, error handling
│   │
│   ├── services/
│   │   ├── resume_service.py    # PDF parsing, text extraction
│   │   ├── github_service.py    # GitHub API client
│   │   ├── scoring_service.py   # Developer score computation
│   │   └── recommendation_service.py  # Portfolio/career suggestions
│   │
│   ├── ai/
│   │   ├── gemini_client.py     # Gemini API wrapper (async)
│   │   ├── embeddings.py        # Text → vector embeddings
│   │   ├── rag_pipeline.py      # Retrieval-Augmented Generation
│   │   └── prompts/
│   │       ├── skill_extraction.py
│   │       ├── scoring.py
│   │       ├── portfolio_suggestions.py
│   │       ├── project_ideas.py
│   │       └── career_roadmap.py
│   │
│   ├── db/
│   │   ├── chroma_client.py     # ChromaDB connection + collections
│   │   └── vector_store.py      # Abstraction over ChromaDB ops
│   │
│   ├── models/
│   │   ├── schemas.py           # Pydantic request/response models
│   │   └── enums.py             # Skill categories, score levels
│   │
│   └── utils/
│       ├── pdf_parser.py        # PyMuPDF-based PDF extraction
│       ├── text_chunker.py      # Chunk text for embedding
│       └── validators.py        # GitHub URL validation, file checks
│
├── tests/
│   ├── conftest.py
│   ├── test_resume.py
│   ├── test_github.py
│   ├── test_analysis.py
│   └── test_ai_pipeline.py
│
├── requirements.txt
├── Dockerfile
└── pyproject.toml
```

### 3.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Async everywhere** | FastAPI + `httpx.AsyncClient` for non-blocking GitHub/Gemini calls |
| **Service layer pattern** | Decouples business logic from API routes for testability |
| **Pydantic Settings** | Type-safe config from env vars with validation |
| **Prompt templates as modules** | Version-controllable, testable prompt engineering |
| **ChromaDB abstraction** | `vector_store.py` wraps ChromaDB so the DB can be swapped later |

### 3.3 Core Service Responsibilities

**Resume Service** — Accepts PDF upload, extracts text via PyMuPDF, normalizes content, delegates to AI layer for skill extraction.

**GitHub Service** — Async HTTP client that fetches user profile, repositories, language breakdown, commit frequency, and README quality via GitHub REST API.

**Scoring Service** — Computes a weighted developer score (0-100) based on: resume completeness, skill diversity, GitHub activity, repo quality, and documentation.

**Recommendation Service** — Orchestrates RAG pipeline to generate portfolio improvements, project ideas, and career roadmaps.

---

## 4. Frontend Architecture

### 4.1 Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout, providers, fonts
│   │   ├── page.tsx             # Landing / hero page
│   │   ├── upload/
│   │   │   └── page.tsx         # Resume upload + GitHub URL form
│   │   ├── analysis/
│   │   │   └── page.tsx         # Results dashboard
│   │   └── roadmap/
│   │       └── page.tsx         # Career roadmap view
│   │
│   ├── components/
│   │   ├── ui/                  # shadcn/ui primitives (button, card, etc.)
│   │   ├── upload/
│   │   │   ├── ResumeDropzone.tsx
│   │   │   └── GitHubUrlInput.tsx
│   │   ├── analysis/
│   │   │   ├── ScoreCard.tsx
│   │   │   ├── SkillsRadar.tsx
│   │   │   ├── RepoAnalysis.tsx
│   │   │   └── SuggestionList.tsx
│   │   ├── roadmap/
│   │   │   ├── RoadmapTimeline.tsx
│   │   │   └── ProjectIdeas.tsx
│   │   └── shared/
│   │       ├── Header.tsx
│   │       ├── Footer.tsx
│   │       └── LoadingState.tsx
│   │
│   ├── lib/
│   │   ├── api.ts               # Axios/fetch wrapper for backend calls
│   │   ├── constants.ts         # API base URL, routes
│   │   └── utils.ts             # Formatting, helpers
│   │
│   ├── hooks/
│   │   ├── useAnalysis.ts       # React Query hook for analysis data
│   │   └── useUpload.ts         # File upload with progress
│   │
│   └── types/
│       └── index.ts             # TypeScript interfaces matching API schemas
│
├── public/
│   └── assets/
├── tailwind.config.ts
├── next.config.js
├── package.json
├── Dockerfile
└── tsconfig.json
```

### 4.2 Page Flow

```
Landing Page  →  Upload Page  →  [Loading/Processing]  →  Analysis Dashboard
                                                              │
                                                              ├── Score Card
                                                              ├── Skills Radar Chart
                                                              ├── Repo Analysis
                                                              ├── Portfolio Suggestions
                                                              └── Career Roadmap ──→  Roadmap Page
```

### 4.3 Key Frontend Patterns

| Pattern | Implementation |
|---------|---------------|
| **Server Components** | Default for static content; data fetching at page level |
| **Client Components** | Interactive widgets: upload dropzone, charts, animations |
| **React Query** | Cache + async state for API calls, retry, loading states |
| **Framer Motion** | Page transitions, card reveals, score counter animations |
| **shadcn/ui** | Consistent, accessible component primitives |

---

## 5. Data Flow

### 5.1 End-to-End Flow

```
1. USER uploads resume (PDF) + enters GitHub URL
        │
2. FRONTEND sends multipart POST to /api/v1/analyze
        │
3. BACKEND receives request, validates inputs
        │
4. PARALLEL PROCESSING:
   ├── Resume Pipeline:
   │   a. Parse PDF → raw text
   │   b. Chunk text into segments (~512 tokens each)
   │   c. Generate embeddings via Gemini Embedding API
   │   d. Store vectors in ChromaDB (collection: "resumes")
   │   e. Extract skills via Gemini (structured output)
   │
   └── GitHub Pipeline:
       a. Fetch user profile (repos, followers, bio)
       b. Fetch top repositories (stars, forks, languages)
       c. Analyze language distribution
       d. Evaluate commit frequency & recency
       e. Assess README quality per repo
        │
5. RAG CONTEXT ASSEMBLY:
   a. Query ChromaDB with skill-related queries
   b. Retrieve top-k relevant resume chunks
   c. Combine: resume context + GitHub data + user query
        │
6. AI GENERATION (Gemini):
   a. Developer Score: weighted formula + LLM justification
   b. Portfolio Suggestions: based on gaps detected
   c. Project Ideas: based on skill level + trending tech
   d. Career Roadmap: 3/6/12-month actionable plan
        │
7. RESPONSE: structured JSON returned to frontend
        │
8. FRONTEND renders interactive dashboard with animations
```

### 5.2 Data Storage

| Store | Purpose | Retention |
|-------|---------|-----------|
| ChromaDB `resumes` collection | Resume embeddings + metadata | Per-session (TTL: 24h) |
| ChromaDB `skills` collection | Skill taxonomy embeddings | Persistent (pre-loaded) |
| Local filesystem `/uploads/` | Temporary PDF storage | Deleted after processing |

---

## 6. API Route Design

### 6.1 Route Table

All routes are prefixed with `/api/v1`.

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| `POST` | `/analyze` | Full analysis pipeline | `multipart: resume (PDF) + github_url (string)` | `AnalysisResponse` |
| `POST` | `/resume/upload` | Upload & parse resume only | `multipart: file (PDF)` | `ResumeResponse` |
| `GET`  | `/resume/{id}/skills` | Get extracted skills | — | `SkillsResponse` |
| `POST` | `/github/analyze` | Analyze GitHub profile only | `{ "github_url": "..." }` | `GitHubAnalysis` |
| `GET`  | `/score/{analysis_id}` | Get developer score | — | `ScoreResponse` |
| `GET`  | `/recommendations/{analysis_id}/portfolio` | Portfolio suggestions | — | `PortfolioSuggestions` |
| `GET`  | `/recommendations/{analysis_id}/projects` | Project ideas | — | `ProjectIdeas` |
| `GET`  | `/recommendations/{analysis_id}/roadmap` | Career roadmap | — | `CareerRoadmap` |
| `GET`  | `/health` | Health check | — | `{ "status": "ok" }` |

### 6.2 Response Schemas (Pydantic)

```python
class AnalysisResponse(BaseModel):
    analysis_id: str
    developer_score: DeveloperScore
    skills: list[Skill]
    github_summary: GitHubSummary
    portfolio_suggestions: list[Suggestion]
    project_ideas: list[ProjectIdea]
    career_roadmap: CareerRoadmap

class DeveloperScore(BaseModel):
    overall: int                      # 0-100
    categories: dict[str, int]        # e.g., {"skills": 85, "github": 72}
    justification: str

class Skill(BaseModel):
    name: str
    category: SkillCategory           # enum: language, framework, tool, soft_skill
    proficiency: str                   # beginner, intermediate, advanced
    source: str                        # "resume" | "github" | "both"

class GitHubSummary(BaseModel):
    username: str
    public_repos: int
    top_languages: dict[str, float]   # language → percentage
    total_stars: int
    commit_frequency: str             # "daily", "weekly", "monthly", "sporadic"
    notable_repos: list[RepoSummary]

class Suggestion(BaseModel):
    area: str
    current_state: str
    recommendation: str
    priority: str                      # "high", "medium", "low"
    impact: str

class ProjectIdea(BaseModel):
    title: str
    description: str
    tech_stack: list[str]
    difficulty: str
    estimated_time: str
    skills_developed: list[str]

class CareerRoadmap(BaseModel):
    current_level: str
    target_role: str
    milestones: list[Milestone]

class Milestone(BaseModel):
    timeframe: str                     # "1-3 months", "3-6 months", etc.
    goals: list[str]
    skills_to_learn: list[str]
    actions: list[str]
```

---

## 7. AI Analysis Pipeline — How It Works

### 7.1 Pipeline Overview

The AI layer uses a **Retrieval-Augmented Generation (RAG)** architecture to ground Gemini's responses in the developer's actual data rather than generic advice.

```
┌─────────────────────────────────────────────────────────┐
│                   AI ANALYSIS PIPELINE                   │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌───────────────────┐  │
│  │  INGEST  │───▶│  EMBED   │───▶│  STORE (ChromaDB) │  │
│  │ PDF text │    │ Gemini   │    │  Vector chunks    │  │
│  └──────────┘    │ Embedding│    └─────────┬─────────┘  │
│                  └──────────┘              │             │
│                                            ▼             │
│  ┌──────────┐    ┌──────────┐    ┌───────────────────┐  │
│  │  QUERY   │───▶│ RETRIEVE │◀───│  Similarity       │  │
│  │ Context  │    │ top-k    │    │  Search            │  │
│  └──────────┘    └────┬─────┘    └───────────────────┘  │
│                       │                                  │
│                       ▼                                  │
│              ┌─────────────────┐                        │
│              │    AUGMENT      │                        │
│              │ Resume chunks + │                        │
│              │ GitHub data +   │                        │
│              │ Prompt template │                        │
│              └────────┬────────┘                        │
│                       │                                  │
│                       ▼                                  │
│              ┌─────────────────┐                        │
│              │   GENERATE      │                        │
│              │ Gemini API call │                        │
│              │ Structured JSON │                        │
│              └─────────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Step-by-Step Breakdown

**Step 1 — Ingest & Chunk**
- PDF text is extracted using PyMuPDF (`fitz`)
- Text is split into overlapping chunks (~512 tokens, 50-token overlap) to preserve context across chunk boundaries
- Each chunk gets metadata: `{source: "resume", section: "experience", chunk_index: 3}`

**Step 2 — Embed & Store**
- Each chunk is converted to a vector embedding using Gemini's `text-embedding-004` model
- Vectors are stored in ChromaDB with their metadata
- This enables semantic search over the resume content

**Step 3 — GitHub Data Collection**
- Runs in parallel with resume processing
- Fetches: repos, languages, commit history, stars, READMEs
- Structures data into a normalized `GitHubProfile` object

**Step 4 — RAG Retrieval**
- For each analysis task (scoring, suggestions, roadmap), a task-specific query is embedded
- ChromaDB performs cosine similarity search to find the most relevant resume chunks
- Top-k chunks (k=5) are returned as grounding context

**Step 5 — Prompt Assembly**
- A structured prompt is assembled from:
  - **System prompt**: role definition + output format instructions
  - **Retrieved context**: relevant resume sections
  - **GitHub data**: structured profile summary
  - **Task instructions**: specific to the analysis type (scoring vs. roadmap vs. suggestions)
- Gemini is instructed to return **structured JSON** matching the Pydantic schemas

**Step 6 — Generation & Parsing**
- Gemini generates a response grounded in actual developer data
- Response is parsed into Pydantic models for type safety
- Fallback: if JSON parsing fails, a retry with stricter formatting instructions is attempted

### 7.3 Scoring Algorithm

The developer score is a weighted composite:

```
Developer Score = (
    Resume Completeness     × 0.15 +
    Skill Diversity         × 0.20 +
    GitHub Activity         × 0.20 +
    Repository Quality      × 0.25 +
    Documentation Quality   × 0.10 +
    Community Engagement    × 0.10
) × 100
```

Each sub-score is computed from measurable signals:
- **Resume Completeness**: sections present (summary, experience, education, skills, projects)
- **Skill Diversity**: breadth across categories (languages, frameworks, tools, cloud)
- **GitHub Activity**: commit frequency, recency, consistency
- **Repository Quality**: stars, READMEs, tests, CI config, clean code signals
- **Documentation**: README quality score per repo
- **Community Engagement**: PRs, issues, followers, contributions to other repos

---

## 8. Project Structure (Complete)

```
developer-portfolio-optimizer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── middleware.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py
│   │   │       ├── resume.py
│   │   │       ├── github.py
│   │   │       ├── analysis.py
│   │   │       └── recommendations.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── resume_service.py
│   │   │   ├── github_service.py
│   │   │   ├── scoring_service.py
│   │   │   └── recommendation_service.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── gemini_client.py
│   │   │   ├── embeddings.py
│   │   │   ├── rag_pipeline.py
│   │   │   └── prompts/
│   │   │       ├── __init__.py
│   │   │       ├── skill_extraction.py
│   │   │       ├── scoring.py
│   │   │       ├── portfolio_suggestions.py
│   │   │       ├── project_ideas.py
│   │   │       └── career_roadmap.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── chroma_client.py
│   │   │   └── vector_store.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py
│   │   │   └── enums.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── pdf_parser.py
│   │       ├── text_chunker.py
│   │       └── validators.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_resume.py
│   │   ├── test_github.py
│   │   ├── test_analysis.py
│   │   └── test_ai_pipeline.py
│   ├── uploads/
│   │   └── .gitkeep
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── upload/
│   │   │   │   └── page.tsx
│   │   │   ├── analysis/
│   │   │   │   └── page.tsx
│   │   │   └── roadmap/
│   │   │       └── page.tsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── upload/
│   │   │   │   ├── ResumeDropzone.tsx
│   │   │   │   └── GitHubUrlInput.tsx
│   │   │   ├── analysis/
│   │   │   │   ├── ScoreCard.tsx
│   │   │   │   ├── SkillsRadar.tsx
│   │   │   │   ├── RepoAnalysis.tsx
│   │   │   │   └── SuggestionList.tsx
│   │   │   ├── roadmap/
│   │   │   │   ├── RoadmapTimeline.tsx
│   │   │   │   └── ProjectIdeas.tsx
│   │   │   └── shared/
│   │   │       ├── Header.tsx
│   │   │       ├── Footer.tsx
│   │   │       └── LoadingState.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── constants.ts
│   │   │   └── utils.ts
│   │   ├── hooks/
│   │   │   ├── useAnalysis.ts
│   │   │   └── useUpload.ts
│   │   └── types/
│   │       └── index.ts
│   ├── public/
│   │   └── assets/
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── package.json
│   ├── Dockerfile
│   └── tsconfig.json
│
├── infra/
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── .github/
│       └── workflows/
│           ├── ci.yml
│           └── deploy.yml
│
├── docs/
│   └── ARCHITECTURE.md
│
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## 9. Infrastructure

### 9.1 Docker Compose

Three services:
- **backend**: FastAPI on port 8000
- **frontend**: Next.js on port 3000
- **chromadb**: ChromaDB on port 8001

### 9.2 CI/CD (GitHub Actions)

**CI Pipeline** (`ci.yml`):
1. Lint & type-check (backend: `ruff`, `mypy`; frontend: `eslint`, `tsc`)
2. Run unit tests (`pytest`, `vitest`)
3. Build Docker images
4. Security scan (`trivy`)

**Deploy Pipeline** (`deploy.yml`):
1. Build & push images to ECR
2. SSH into EC2 instance
3. Pull latest images
4. `docker compose up -d`
5. Health check verification

### 9.3 Environment Variables

```env
# AI
GEMINI_API_KEY=

# GitHub
GITHUB_TOKEN=

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8001

# App
BACKEND_PORT=8000
FRONTEND_PORT=3000
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE_MB=10

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```
