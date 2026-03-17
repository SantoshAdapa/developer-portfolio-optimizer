<div align="center">

# Developer Portfolio Optimizer

**AI-powered resume and GitHub profile analysis for developers**

An intelligent full-stack application that evaluates a developer's resume and GitHub presence using Google Gemini, RAG pipelines, and vector embeddings — then delivers actionable scores, portfolio suggestions, project ideas, and career roadmaps.

[![CI](https://github.com/SantoshAdapa/developer-portfolio-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/SantoshAdapa/developer-portfolio-optimizer/actions/workflows/ci.yml)
[![Deploy](https://github.com/SantoshAdapa/developer-portfolio-optimizer/actions/workflows/deploy.yml/badge.svg)](https://github.com/SantoshAdapa/developer-portfolio-optimizer/actions/workflows/deploy.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Next.js 14](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

[Features](#-key-features) &bull; [Architecture](#-system-architecture) &bull; [Quick Start](#-quick-start) &bull; [Demo](#-demo) &bull; [Deployment](#-deployment)

</div>

---

## Overview

Developer Portfolio Optimizer uses a **Retrieval-Augmented Generation (RAG)** pipeline to ground AI analysis in a developer's actual data — not generic advice. Upload a resume PDF and provide a GitHub username: the system parses the resume, generates vector embeddings, fetches GitHub repository data, and sends enriched context to Google Gemini to produce a comprehensive developer analysis.

The result is an interactive dashboard with a developer score (0-100), skill radar charts, portfolio improvement suggestions, recommended project ideas, career direction analysis, job description matching, and a personalized learning roadmap.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Resume Analysis** | PDF upload with text extraction, chunking, and embedding via Gemini's `text-embedding-004` model |
| **GitHub Profile Analysis** | Repository fetching, language distribution, commit frequency, README quality, CI/CD detection |
| **Developer Score** | Weighted composite score (0-100) across resume quality, skill diversity, GitHub activity, repo quality, and documentation |
| **RAG Pipeline** | Retrieval-Augmented Generation using ChromaDB vector search for context-grounded AI responses |
| **Skill Radar Charts** | Visual breakdown across frontend, backend, data, ML/AI, DevOps, and testing domains |
| **Portfolio Suggestions** | Prioritized recommendations with current state assessment and expected impact |
| **Project Ideas** | AI-generated project suggestions with tech stack, difficulty level, and estimated time |
| **Career Roadmap** | Milestone-based roadmap with timeframes, goals, and skills to learn |
| **Job Description Matching** | Match your profile against job descriptions or predefined role templates |
| **Benchmarking** | Compare your score against developer archetype benchmarks |
| **Profile Comparison** | Side-by-side comparison of two developer analyses |
| **Export Report** | Download analysis results as a shareable report |
| **Demo Mode** | Try the tool with pre-loaded sample profiles without uploading your own data |

---

## Demo

The application features a three-step workflow:

1. **Landing Page** — Animated hero section with an overview of capabilities
2. **Analyze Page** — Upload a resume PDF, enter a GitHub username, and run the analysis (or try Demo Mode)
3. **Results Dashboard** — Interactive panels for scores, skills, suggestions, roadmaps, and more

> **Demo Mode**: Click "Try Demo" on the analyze page to see the full analysis pipeline in action using a sample developer profile.

### Screenshots

<details>
<summary>Click to expand screenshots</summary>

<!-- Replace these placeholders with actual screenshots -->

| Page | Screenshot |
|------|-----------|
| Landing Page | ![Landing Page](docs/screenshots/landing.png) |
| Analysis Page | ![Analysis Page](docs/screenshots/analyze.png) |
| Results — Score Overview | ![Score Overview](docs/screenshots/score-overview.png) |
| Results — Skill Radar | ![Skill Radar](docs/screenshots/skill-radar.png) |
| Results — Suggestions | ![Suggestions](docs/screenshots/suggestions.png) |
| Results — Career Roadmap | ![Career Roadmap](docs/screenshots/career-roadmap.png) |

</details>

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Next.js 14 (App Router)                                   │  │
│  │  React + TailwindCSS + shadcn/ui + Framer Motion           │  │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐ │  │
│  │  │ Landing  │ │  Analyze  │ │ Results  │ │  Compare    │ │  │
│  │  └──────────┘ └───────────┘ └──────────┘ └─────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP / REST
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                    NGINX Reverse Proxy                            │
│            /api/* → Backend    /* → Frontend                     │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                             │
│                                                                   │
│  API Layer ──► Auth Middleware ──► Rate Limiting ──► CORS         │
│       │                                                           │
│  ┌────┴──────────────────────────────────────────────────────┐   │
│  │                    SERVICE LAYER                            │   │
│  │  Resume Service │ GitHub Service │ Scoring │ Recommendations│   │
│  │  Comparison     │ Benchmarks     │ JD Match                 │   │
│  └────┬──────────────────────────────────────────────────────┘   │
│       │                                                           │
│  ┌────┴──────────────────────────────────────────────────────┐   │
│  │               AI / RAG PIPELINE                             │   │
│  │  Embeddings (Gemini) → ChromaDB → Retrieval → Generation   │   │
│  │  Prompt Templates: scoring, skills, suggestions, roadmap    │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────┬───────────────────────────────────┬──────────────────┘
            │                                   │
    ┌───────▼───────┐                   ┌───────▼───────┐
    │   ChromaDB    │                   │  Gemini API   │
    │ Vector Store  │                   │  (Google AI)  │
    └───────────────┘                   └───────────────┘
                                                │
                                        ┌───────▼───────┐
                                        │  GitHub API   │
                                        │  (REST v3)    │
                                        └───────────────┘
```

### Data Flow

```
1. Upload resume (PDF) + enter GitHub username
2. Backend parses PDF → chunks text → generates embeddings → stores in ChromaDB
3. GitHub Service fetches repos, languages, commit history (in parallel)
4. RAG pipeline queries ChromaDB for relevant resume chunks
5. Context (resume chunks + GitHub data + skills) is assembled
6. Gemini generates structured JSON: scores, suggestions, roadmap
7. Frontend renders interactive dashboard with animated visualizations
```

---

## Tech Stack

### Frontend

| Technology | Purpose |
|-----------|---------|
| [Next.js 14](https://nextjs.org/) | App Router, SSR, file-based routing |
| [React 18](https://react.dev/) | Component architecture |
| [TailwindCSS](https://tailwindcss.com/) | Utility-first styling |
| [shadcn/ui](https://ui.shadcn.com/) | Accessible UI primitives (Radix-based) |
| [Framer Motion](https://www.framer.com/motion/) | Page transitions, animations |
| [Recharts](https://recharts.org/) | Radar charts, data visualizations |
| [TanStack Query](https://tanstack.com/query) | Server state management, caching |
| [Lucide React](https://lucide.dev/) | Icon library |

### Backend

| Technology | Purpose |
|-----------|---------|
| [Python 3.12](https://python.org/) | Runtime |
| [FastAPI](https://fastapi.tiangolo.com/) | Async REST API framework |
| [Pydantic v2](https://docs.pydantic.dev/) | Request/response validation, settings |
| [Google Generative AI](https://ai.google.dev/) | Gemini API client (LLM + embeddings) |
| [ChromaDB](https://www.trychroma.com/) | Vector database for RAG |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | PDF text extraction |
| [HTTPX](https://www.python-httpx.org/) | Async HTTP client for GitHub API |
| [Prometheus](https://prometheus.io/) | Metrics instrumentation (`/metrics`) |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| [Docker](https://docker.com/) | Containerization (multi-stage builds) |
| [Docker Compose](https://docs.docker.com/compose/) | Multi-service orchestration |
| [Nginx](https://nginx.org/) | Reverse proxy, gzip, static caching |
| [GitHub Actions](https://github.com/features/actions) | CI/CD pipeline |
| [AWS EC2](https://aws.amazon.com/ec2/) | Production deployment |

---

## Project Structure

```
developer-portfolio-optimizer/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middleware, health check
│   │   ├── config.py                # Pydantic Settings (env vars)
│   │   ├── api/v1/
│   │   │   ├── router.py            # Aggregate v1 router with auth
│   │   │   ├── resume.py            # POST /resume/upload
│   │   │   ├── github.py            # POST /github/analyze
│   │   │   ├── analysis.py          # POST /analyze
│   │   │   ├── recommendations.py   # GET /recommendations/*
│   │   │   ├── compare.py           # POST /compare
│   │   │   ├── benchmarks.py        # GET /benchmarks
│   │   │   └── jd_match.py          # POST /jd-match
│   │   ├── services/
│   │   │   ├── resume_service.py    # PDF parsing, skill extraction
│   │   │   ├── github_service.py    # GitHub API client
│   │   │   ├── scoring_service.py   # Developer score computation
│   │   │   ├── recommendation_service.py
│   │   │   ├── comparison_service.py
│   │   │   ├── benchmark_service.py
│   │   │   └── jd_match_service.py
│   │   ├── ai/
│   │   │   ├── gemini_client.py     # Gemini API wrapper (async)
│   │   │   ├── embeddings.py        # Text → vector embeddings
│   │   │   ├── rag_pipeline.py      # Retrieve → Augment → Generate
│   │   │   ├── skill_matcher.py     # Skill normalization & matching
│   │   │   └── prompts/             # Versioned prompt templates
│   │   ├── db/
│   │   │   ├── chroma_client.py     # ChromaDB connection manager
│   │   │   ├── vector_store.py      # Vector CRUD operations
│   │   │   └── store.py             # SQLite persistence layer
│   │   ├── models/
│   │   │   ├── schemas.py           # Pydantic request/response models
│   │   │   └── enums.py             # Skill categories, proficiency levels
│   │   └── utils/
│   │       ├── pdf_parser.py        # PDF text extraction
│   │       ├── text_chunker.py      # Chunk text for embedding
│   │       ├── validators.py        # Input validation
│   │       ├── auth.py              # API key authentication
│   │       └── rate_limit.py        # Rate limiting
│   ├── tests/                       # pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx               # Root layout, providers
│   │   ├── page.tsx                 # Landing page
│   │   ├── analyze/page.tsx         # Upload & analysis form
│   │   ├── results/[analysis_id]/   # Results dashboard
│   │   ├── compare/page.tsx         # Profile comparison
│   │   └── job-match/page.tsx       # JD matching
│   ├── components/
│   │   ├── ui/                      # shadcn/ui primitives
│   │   ├── landing/                 # Hero, how-it-works, CTA
│   │   ├── upload/                  # File uploader, GitHub input
│   │   ├── analysis/                # Score meter, timeline, AI explanation
│   │   ├── results/                 # Score, skills, suggestions, roadmap panels
│   │   ├── charts/                  # Skill radar chart
│   │   ├── comparison/              # Side-by-side comparison
│   │   ├── benchmark/               # Archetype benchmarking
│   │   └── layout/                  # Navbar, footer, particle background
│   ├── hooks/                       # React Query hooks
│   ├── services/api.ts              # Backend API client
│   ├── lib/                         # Utils, constants, providers
│   ├── types/index.ts               # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
│
├── infra/
│   └── nginx.conf                   # Reverse proxy configuration
│
├── .github/workflows/
│   ├── ci.yml                       # Lint, test, build pipeline
│   └── deploy.yml                   # Automated EC2 deployment
│
├── docs/
│   └── ARCHITECTURE.md              # Detailed system design
│
├── docker-compose.yml               # 4-service orchestration
├── .env.example                     # Environment variable template
└── .gitignore
```

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose** (recommended)
- Or for local development:
  - Python 3.12+
  - Node.js 20+
  - A running ChromaDB instance

### Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google AI API key ([Get one here](https://aistudio.google.com/apikey)) |
| `GITHUB_TOKEN` | Yes | GitHub personal access token for API access |
| `GEMINI_MODEL` | No | Model to use (default: `gemini-2.0-flash`) |
| `CHROMA_HOST` | No | ChromaDB host (default: `chromadb`) |
| `CHROMA_PORT` | No | ChromaDB port (default: `8000`) |
| `BACKEND_PORT` | No | Backend port (default: `8000`) |
| `FRONTEND_PORT` | No | Frontend port (default: `3000`) |
| `UPLOAD_DIR` | No | Upload directory (default: `/app/uploads`) |
| `MAX_FILE_SIZE_MB` | No | Max upload size (default: `10`) |
| `API_KEY` | No | API key for request authentication (empty = disabled) |
| `ENCRYPTION_KEY` | No | Fernet key for PII encryption at rest |
| `ALLOWED_ORIGINS` | No | CORS origins, comma-separated (default: `http://localhost:3000`) |

---

## Docker Setup

The recommended way to run the application:

```bash
# Clone the repository
git clone https://github.com/SantoshAdapa/developer-portfolio-optimizer.git
cd developer-portfolio-optimizer

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and GITHUB_TOKEN

# Build and start all services
docker compose up --build
```

This starts four containers:

| Container | Port | Description |
|-----------|------|-------------|
| `dpo-nginx` | `80` | Nginx reverse proxy (routes `/api/*` to backend, `/*` to frontend) |
| `dpo-frontend` | `3000` | Next.js application |
| `dpo-backend` | `8000` | FastAPI application |
| `dpo-chromadb` | internal | ChromaDB vector database |

Access the application at **http://localhost**.

### Resource Limits

Each container has configured memory and CPU limits:

| Service | Memory | CPUs |
|---------|--------|------|
| Nginx | 128 MB | 0.25 |
| Frontend | 512 MB | 1.0 |
| Backend | 512 MB | 1.0 |
| ChromaDB | 512 MB | 0.5 |

---

## Running Locally (Without Docker)

<details>
<summary>Backend</summary>

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start ChromaDB (in a separate terminal or as a background process)
chroma run --host 0.0.0.0 --port 8000

# Start the backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at http://localhost:8000/docs (Swagger UI).

</details>

<details>
<summary>Frontend</summary>

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Open http://localhost:3000 in your browser.

</details>

---

## API Endpoints

All routes are prefixed with `/api/v1` and protected by optional API key authentication.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/resume/upload` | Upload and parse a resume PDF |
| `POST` | `/github/analyze` | Analyze a GitHub profile |
| `POST` | `/analyze` | Run full analysis pipeline |
| `GET` | `/recommendations/{id}/portfolio` | Portfolio improvement suggestions |
| `GET` | `/recommendations/{id}/projects` | AI-generated project ideas |
| `GET` | `/recommendations/{id}/roadmap` | Career roadmap |
| `POST` | `/compare` | Compare two developer profiles |
| `GET` | `/benchmarks/{id}` | Benchmark against archetypes |
| `POST` | `/jd-match` | Match profile against a job description |
| `GET` | `/health` | Health check (SQLite, ChromaDB, Gemini, disk) |

---

## CI/CD Pipeline

### CI (`ci.yml`)

Triggered on pushes and pull requests to `main`:

```
Lint & Type Check ──► Tests ──► Docker Build
   (ruff, mypy)     (pytest)    (buildx cache)
```

- **Ruff** — Linting and format checking
- **Mypy** — Static type analysis
- **pytest** — Backend test suite
- **Docker Buildx** — Image build with GitHub Actions cache

### Deployment (`deploy.yml`)

Triggered automatically when CI succeeds on `main`:

```
CI Passes ──► SSH to EC2 ──► Pull & Build ──► Rolling Restart ──► Health Check
```

1. SSH into EC2 using stored secrets
2. Pull latest code and rebuild Docker images
3. Tag images with commit SHA for rollback capability
4. Rolling restart: backend first, then frontend, then nginx
5. Health checks on both services — automatic rollback on failure

---

## Deployment

### AWS EC2 Setup

The application is designed for deployment on an AWS EC2 instance with Docker:

1. **Launch an EC2 instance** (Ubuntu recommended, t3.medium or larger)
2. **Install Docker and Docker Compose** on the instance
3. **Clone the repository** and configure `.env`
4. **Configure GitHub Secrets** for automated deployment:
   - `EC2_HOST` — Instance public IP
   - `EC2_USER` — SSH username
   - `EC2_SSH_KEY` — Private SSH key
   - `GEMINI_API_KEY` — Google AI API key
5. Push to `main` — CI/CD handles the rest

### Architecture in Production

```
Internet ──► EC2 Instance
               │
               ├── Nginx (port 80) ──► reverse proxy
               │     ├── /api/*  → FastAPI (port 8000)
               │     └── /*      → Next.js (port 3000)
               │
               ├── FastAPI Backend
               │     └── ChromaDB (internal)
               │
               └── ChromaDB Vector Store
```

---

## How the AI Pipeline Works

### RAG (Retrieval-Augmented Generation)

The system doesn't rely on generic AI responses. Instead, it uses a RAG pipeline to ground every recommendation in the developer's actual resume content and GitHub activity:

```
PDF Upload                    GitHub Username
    │                              │
    ▼                              ▼
Parse & Chunk Text          Fetch Repos & Stats
    │                              │
    ▼                              │
Generate Embeddings                │
(Gemini text-embedding-004)        │
    │                              │
    ▼                              │
Store in ChromaDB                  │
    │                              │
    ▼                              ▼
Similarity Search ──► Context Assembly ──► Gemini Generation
(top-k chunks)        (resume + GitHub     (structured JSON)
                       + prompt template)
```

### Scoring Algorithm

The developer score is a weighted composite across measurable signals:

| Component | Weight | Signals |
|-----------|--------|---------|
| Resume Completeness | 15% | Sections present (summary, experience, education, skills, projects) |
| Skill Diversity | 20% | Breadth across languages, frameworks, tools, cloud |
| GitHub Activity | 20% | Commit frequency, recency, consistency |
| Repository Quality | 25% | Stars, READMEs, tests, CI config, Docker usage |
| Documentation | 10% | README quality per repo |
| Community Engagement | 10% | Followers, PRs, issues, contributions |

---

## Future Improvements

- [ ] **LinkedIn Integration** — Import professional experience directly from LinkedIn
- [ ] **Real-time Collaboration** — Share and compare analyses with team members
- [ ] **Custom Role Templates** — Create and save custom job description templates
- [ ] **Historical Tracking** — Track portfolio score changes over time
- [ ] **PDF Report Generation** — Export analysis as a styled PDF document
- [ ] **Multi-language Resume Support** — Parse resumes in languages other than English
- [ ] **LeetCode / HackerRank Integration** — Incorporate competitive programming data
- [ ] **Webhook Notifications** — Get notified when your portfolio score changes
- [ ] **Team Dashboard** — Aggregate analysis for engineering teams or bootcamp cohorts
- [ ] **Fine-tuned Models** — Use fine-tuned models for more accurate skill extraction

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

```bash
# Run backend tests
cd backend && pytest tests/ -v

# Run backend linting
ruff check . && ruff format --check . && mypy app/ --ignore-missing-imports

# Run frontend linting
cd frontend && npm run lint
```

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">

Built with [FastAPI](https://fastapi.tiangolo.com/) + [Next.js](https://nextjs.org/) + [Gemini](https://ai.google.dev/) + [ChromaDB](https://www.trychroma.com/)

</div>
