"""Scoring service — computes a weighted developer score from resume + GitHub data.

Scoring philosophy
──────────────────
Each sub-score (0-100) is computed from observable signals and then combined
with a weighted average into a composite score.  Thresholds are calibrated so
that a typical mid-career developer with a reasonable GitHub presence scores
around 55-70, while an exceptional profile caps near 100.

Base weights (before redistribution)
─────────────────────────────────────
  resume_completeness  0.15   Resume structure matters, but less than code.
  skill_diversity      0.20   Breadth + depth of skills shown.
  github_activity      0.20   Commit cadence and repo count.
  repo_quality         0.25   Stars, language diversity, topic tagging.
  documentation        0.10   README and description presence.
  community            0.10   Followers + stars as community signal.

When only a subset of data sources are available (e.g. resume-only or
GitHub-only), weights are redistributed proportionally among the
applicable metrics so the overall score remains meaningful.
"""

from __future__ import annotations

import math
import re

from app.models.enums import CommitFrequency, Proficiency, SkillCategory
from app.models.schemas import (
    AiInsights,
    CareerDirectionResult,
    CareerPathSuggestion,
    DeveloperScore,
    GitHubSummary,
    LearningResource,
    LearningRoadmapResult,
    LearningStep,
    MarketDemandResult,
    MarketSkillDemand,
    PortfolioDepthScore,
    ProgrammingLanguageScore,
    RadarScores,
    ScoreBreakdown,
    Skill,
    SkillCategoryBreakdown,
    SkillGapResult,
    SkillMatch,
)

# ── Weight configuration ─────────────────────────────────

# Base weight configuration.
# When all data sources are available these sum to 1.0.
# When only a subset is available, weights are redistributed
# proportionally among the applicable metrics.
WEIGHTS = {
    "resume_completeness": 0.10,
    "content_quality": 0.10,
    "skill_diversity": 0.12,
    "formatting_quality": 0.06,
    "impact_quantification": 0.06,
    "keyword_density": 0.06,
    "github_activity": 0.12,
    "repo_quality": 0.12,
    "documentation": 0.08,
    "community": 0.08,
    "technology_depth": 0.10,
}

# Which data source each metric depends on.
_RESUME_METRICS = {
    "resume_completeness",
    "content_quality",
    "skill_diversity",
    "formatting_quality",
    "impact_quantification",
    "keyword_density",
}
_GITHUB_METRICS = {
    "github_activity",
    "repo_quality",
    "documentation",
    "community",
    "technology_depth",
}

# Resume sections we look for (case-insensitive substrings).
# 9 sections total → each contributes ~11% toward the 0-100 score.
_RESUME_SECTIONS = [
    "summary",
    "objective",
    "experience",
    "work",
    "education",
    "skills",
    "technologies",
    "projects",
    "certifications",
]
# Action verbs indicating quality resume content.
_ACTION_VERBS = [
    "developed",
    "implemented",
    "designed",
    "built",
    "created",
    "managed",
    "led",
    "architected",
    "optimized",
    "improved",
    "increased",
    "reduced",
    "deployed",
    "automated",
    "integrated",
    "delivered",
    "launched",
    "maintained",
    "collaborated",
    "coordinated",
    "mentored",
    "analyzed",
    "engineered",
    "configured",
    "established",
    "streamlined",
    "migrated",
    "resolved",
    "troubleshot",
    "tested",
    "refactored",
    "scaled",
]

# Industry keywords for keyword density scoring.
_INDUSTRY_KEYWORDS = [
    "agile",
    "scrum",
    "ci/cd",
    "devops",
    "microservices",
    "api",
    "rest",
    "graphql",
    "cloud",
    "distributed",
    "scalable",
    "performance",
    "security",
    "testing",
    "unit test",
    "integration",
    "deployment",
    "architecture",
    "design patterns",
    "oop",
    "functional",
    "full-stack",
    "full stack",
    "frontend",
    "backend",
    "machine learning",
    "data science",
    "artificial intelligence",
    "deep learning",
    "nlp",
    "computer vision",
    "big data",
    "analytics",
    "database",
    "version control",
    "git",
    "open source",
    "containerization",
]

# Mapping from radar chart category to skill keywords.
_RADAR_SKILL_MAP = {
    "frontend": [
        "react",
        "next.js",
        "nextjs",
        "vue",
        "vue.js",
        "angular",
        "svelte",
        "html",
        "css",
        "tailwind",
        "tailwindcss",
        "bootstrap",
        "sass",
        "less",
        "webpack",
        "vite",
        "jquery",
        "redux",
        "gatsby",
        "nuxt",
        "nuxt.js",
        "material ui",
        "chakra",
        "styled-components",
        "framer motion",
        "responsive design",
        "web design",
        "ui/ux",
        "figma",
        "javascript",
        "typescript",
    ],
    "backend": [
        "fastapi",
        "django",
        "flask",
        "express",
        "express.js",
        "node",
        "node.js",
        "nodejs",
        "spring",
        "spring boot",
        "rails",
        "ruby on rails",
        "laravel",
        "asp.net",
        ".net",
        "gin",
        "fiber",
        "actix",
        "rocket",
        "rest api",
        "graphql",
        "grpc",
        "microservices",
        "nest.js",
        "nestjs",
        "koa",
        "hapi",
        "fastify",
        "java",
        "python",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "c#",
    ],
    "data": [
        "sql",
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "elasticsearch",
        "sqlite",
        "cassandra",
        "dynamodb",
        "firebase",
        "supabase",
        "prisma",
        "sqlalchemy",
        "pandas",
        "numpy",
        "data analysis",
        "etl",
        "data pipeline",
        "apache spark",
        "kafka",
        "rabbitmq",
        "neo4j",
        "oracle",
        "mariadb",
        "data engineering",
        "data warehouse",
    ],
    "ml_ai": [
        "tensorflow",
        "pytorch",
        "keras",
        "scikit-learn",
        "sklearn",
        "opencv",
        "nlp",
        "machine learning",
        "deep learning",
        "neural network",
        "huggingface",
        "transformers",
        "bert",
        "gpt",
        "llm",
        "computer vision",
        "reinforcement learning",
        "xgboost",
        "lightgbm",
        "artificial intelligence",
        "data science",
        "feature engineering",
        "model training",
        "langchain",
        "rag",
    ],
    "devops": [
        "docker",
        "kubernetes",
        "k8s",
        "ci/cd",
        "jenkins",
        "github actions",
        "gitlab ci",
        "terraform",
        "ansible",
        "aws",
        "amazon web services",
        "azure",
        "gcp",
        "google cloud",
        "heroku",
        "vercel",
        "netlify",
        "linux",
        "nginx",
        "apache",
        "prometheus",
        "grafana",
        "helm",
        "cloudformation",
        "pulumi",
        "digitalocean",
        "cloudflare",
    ],
    "testing": [
        "jest",
        "pytest",
        "mocha",
        "cypress",
        "selenium",
        "playwright",
        "unit test",
        "unit testing",
        "integration testing",
        "test-driven",
        "tdd",
        "bdd",
        "testing",
        "junit",
        "rspec",
        "vitest",
        "enzyme",
        "testing library",
        "coverage",
        "qa",
    ],
}

# Known programming languages for extraction.
_KNOWN_LANGUAGES = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "matlab": "MATLAB",
    "perl": "Perl",
    "haskell": "Haskell",
    "elixir": "Elixir",
    "dart": "Dart",
    "lua": "Lua",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "shell": "Shell/Bash",
    "bash": "Shell/Bash",
    "powershell": "PowerShell",
    "objective-c": "Objective-C",
}

# Known skills for text-based fallback extraction.
_KNOWN_SKILLS: dict[str, list[str]] = {
    "language": [
        "python",
        "javascript",
        "typescript",
        "java",
        "c++",
        "c#",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "matlab",
        "perl",
        "haskell",
        "elixir",
        "dart",
        "lua",
        "sql",
        "html",
        "css",
        "shell",
        "bash",
        "powershell",
    ],
    "framework": [
        "react",
        "next.js",
        "nextjs",
        "vue",
        "vue.js",
        "angular",
        "svelte",
        "django",
        "flask",
        "fastapi",
        "express",
        "express.js",
        "spring",
        "spring boot",
        "rails",
        "ruby on rails",
        "laravel",
        ".net",
        "asp.net",
        "flutter",
        "react native",
        "electron",
        "gatsby",
        "nuxt",
        "nuxt.js",
        "nest.js",
        "nestjs",
        "tailwind",
        "tailwindcss",
        "bootstrap",
        "material ui",
        "jquery",
        "redux",
    ],
    "tool": [
        "docker",
        "kubernetes",
        "git",
        "github",
        "gitlab",
        "jenkins",
        "terraform",
        "ansible",
        "webpack",
        "vite",
        "babel",
        "eslint",
        "prettier",
        "jira",
        "confluence",
        "figma",
        "postman",
        "nginx",
        "apache",
        "prometheus",
        "grafana",
        "helm",
        "github actions",
        "ci/cd",
        "circleci",
    ],
    "database": [
        "postgresql",
        "postgres",
        "mysql",
        "mongodb",
        "redis",
        "elasticsearch",
        "sqlite",
        "cassandra",
        "dynamodb",
        "firebase",
        "supabase",
        "neo4j",
        "oracle",
        "mariadb",
    ],
    "cloud": [
        "aws",
        "amazon web services",
        "azure",
        "gcp",
        "google cloud",
        "heroku",
        "vercel",
        "netlify",
        "digitalocean",
        "cloudflare",
    ],
}

# ── Sub-score functions ──────────────────────────────────


def _score_resume_completeness(resume_text: str) -> int:
    """0-100 based on how many standard resume sections are present."""
    if not resume_text:
        return 0
    lower = resume_text.lower()
    found = sum(1 for s in _RESUME_SECTIONS if s in lower)
    return min(100, int(found / len(_RESUME_SECTIONS) * 100))


def _score_skill_diversity(skills: list[Skill]) -> int:
    """0-100 based on breadth of skill categories.

    Breadth (50 pts): fraction of the 6 possible SkillCategory values covered.
    Depth  (50 pts): unique skill count, capped at 20 for full marks.
    """
    if not skills:
        return 0
    categories = {s.category for s in skills}
    unique_skills = len(skills)

    # 6 possible categories: language, framework, tool, database, cloud, soft_skill
    breadth = len(categories) / 6 * 50

    # Cap at 20 skills — more than 20 doesn't add score (avoids inflation)
    depth = min(unique_skills / 20, 1.0) * 50

    return min(100, int(breadth + depth))


def _score_github_activity(github: GitHubSummary | None) -> int:
    """0-100 based on commit frequency and repo count.

    Frequency (50 pts): daily=50, weekly=35, monthly=20, sporadic=5.
    Repo count (50 pts): linear up to 30 repos for full marks.
    """
    if not github:
        return 0

    freq_scores = {
        CommitFrequency.DAILY: 50,
        CommitFrequency.WEEKLY: 35,
        CommitFrequency.MONTHLY: 20,
        CommitFrequency.SPORADIC: 5,
    }
    freq_score = freq_scores.get(github.commit_frequency, 5)

    # Repo count contribution (cap at 30 repos for full marks)
    repo_score = min(github.public_repos / 30, 1.0) * 50

    return min(100, int(freq_score + repo_score))


def _score_repo_quality(github: GitHubSummary | None) -> int:
    """0-100 based on stars, language diversity, and topics usage.

    Stars       (35 pts): linear up to 100 total stars.
    Languages   (30 pts): unique languages, capped at 5 for full marks.
    Topics      (35 pts): fraction of repos that have topic tags.
    """
    if not github or not github.notable_repos:
        return 0

    repos = github.notable_repos

    # Stars (log-scale, cap at 100 total stars for full marks on this component)
    star_score = min(github.total_stars / 100, 1.0) * 35

    # Language diversity (more languages = better portfolio)
    lang_count = len(github.top_languages)
    lang_score = min(lang_count / 5, 1.0) * 30

    # Topics/tags usage (signal of well-maintained repos)
    repos_with_topics = sum(1 for r in repos if r.topics)
    topic_ratio = repos_with_topics / len(repos) if repos else 0
    topic_score = topic_ratio * 35

    return min(100, int(star_score + lang_score + topic_score))


def _score_documentation(github: GitHubSummary | None) -> int:
    """0-100 based on README presence and descriptions across repos."""
    if not github or not github.notable_repos:
        return 0

    repos = github.notable_repos
    has_readme = sum(1 for r in repos if r.has_readme)
    has_desc = sum(1 for r in repos if r.description)

    readme_pct = has_readme / len(repos) * 50
    desc_pct = has_desc / len(repos) * 50

    return min(100, int(readme_pct + desc_pct))


def _score_community(github: GitHubSummary | None) -> int:
    """0-100 based on followers and stars as community signals.

    Followers (50 pts): linear up to 50 followers.
    Stars     (50 pts): linear up to 50 total stars.
    """
    if not github:
        return 0

    # Followers (cap at 50 for full marks on this piece)
    follower_score = min(github.followers / 50, 1.0) * 50

    # Total stars as community validation
    star_score = min(github.total_stars / 50, 1.0) * 50

    return min(100, int(follower_score + star_score))


def _score_technology_depth(github: GitHubSummary | None) -> int:
    """0-100 based on technology stack depth detected from repos.

    Measures how many distinct technologies, frameworks, and tools
    are actively used across repositories, detected from dependency files,
    config files, file tree analysis, and README content.

    Components:
      Unique technologies (40 pts): distinct techs from deep analysis
      Framework diversity  (25 pts): different frameworks detected
      Config maturity      (20 pts): presence of config/tooling files
      Stack completeness   (15 pts): coverage across categories
    """
    if not github or not github.notable_repos:
        return 0

    repos = github.notable_repos

    # Collect all detected technologies across repos
    all_techs: set[str] = set()
    all_config_files: set[str] = set()
    repos_with_tests = 0
    repos_with_ci = 0
    repos_with_docker = 0

    for repo in repos:
        for tech in repo.detected_technologies:
            all_techs.add(tech)
        for cf in repo.config_files:
            all_config_files.add(cf)
        if repo.has_tests:
            repos_with_tests += 1
        if repo.has_ci:
            repos_with_ci += 1
        if repo.has_docker:
            repos_with_docker += 1

    # Also count top_languages
    for lang in github.top_languages:
        all_techs.add(lang)

    # Unique technologies (40 pts) — log scale, 15+ techs for full marks
    tech_count = len(all_techs)
    if tech_count >= 15:
        tech_score = 40
    elif tech_count >= 8:
        tech_score = int(25 + (tech_count - 8) / 7 * 15)
    elif tech_count >= 3:
        tech_score = int(10 + (tech_count - 3) / 5 * 15)
    else:
        tech_score = tech_count * 3

    # Framework diversity (25 pts) — different frameworks/libraries
    _frameworks = {
        "React",
        "Next.js",
        "Vue",
        "Nuxt.js",
        "Angular",
        "Svelte",
        "Django",
        "Flask",
        "FastAPI",
        "Express.js",
        "NestJS",
        "Spring Boot",
        "TailwindCSS",
        "Bootstrap",
        "Material UI",
        "TensorFlow",
        "PyTorch",
        "Scikit-learn",
        "Keras",
        "Prisma",
        "SQLAlchemy",
        "Sequelize",
        "TypeORM",
    }
    detected_frameworks = all_techs & _frameworks
    framework_score = min(25, len(detected_frameworks) * 6)

    # Config maturity (20 pts) — tooling sophistication
    config_score = 0
    if all_config_files:
        config_score += min(10, len(all_config_files) * 2)
    if repos_with_tests > 0:
        config_score += 4
    if repos_with_ci > 0:
        config_score += 3
    if repos_with_docker > 0:
        config_score += 3
    config_score = min(20, config_score)

    # Stack completeness (15 pts) — covers frontend, backend, data, devops, etc.
    _category_techs = {
        "frontend": {
            "React",
            "Vue",
            "Angular",
            "Svelte",
            "Next.js",
            "HTML",
            "CSS",
            "JavaScript",
            "TypeScript",
            "TailwindCSS",
            "Bootstrap",
        },
        "backend": {
            "Python",
            "Java",
            "Go",
            "Rust",
            "Node.js",
            "Django",
            "Flask",
            "FastAPI",
            "Express.js",
            "NestJS",
            "Spring Boot",
            "Ruby",
            "PHP",
        },
        "data": {
            "PostgreSQL",
            "MongoDB",
            "MySQL",
            "Redis",
            "SQLite",
            "Elasticsearch",
            "Pandas",
            "NumPy",
            "SQL",
            "Firebase",
            "Prisma",
            "SQLAlchemy",
        },
        "ml_ai": {
            "TensorFlow",
            "PyTorch",
            "Scikit-learn",
            "OpenCV",
            "Keras",
            "Hugging Face Transformers",
            "LangChain",
            "XGBoost",
            "LightGBM",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "Computer Vision",
        },
        "devops": {
            "Docker",
            "Kubernetes",
            "Terraform",
            "AWS",
            "GitHub Actions",
            "CI/CD",
            "Jenkins",
            "Ansible",
            "Nginx",
            "Heroku",
            "Vercel",
        },
    }
    categories_covered = sum(
        1 for cat_techs in _category_techs.values() if all_techs & cat_techs
    )
    completeness_score = min(15, categories_covered * 3)

    return min(100, tech_score + framework_score + config_score + completeness_score)


# ── ATS Sub-score functions ──────────────────────────────


def _score_content_quality(resume_text: str) -> int:
    """0-100 based on content richness: word count, action verbs, detail."""
    if not resume_text:
        return 0
    lower = resume_text.lower()
    words = lower.split()
    word_count = len(words)
    score = 0

    # Word count (max 25 pts)
    if word_count >= 400:
        score += 25
    elif word_count >= 200:
        score += 18
    elif word_count >= 100:
        score += 10
    elif word_count >= 50:
        score += 5

    # Action verb usage (max 25 pts)
    action_count = sum(1 for verb in _ACTION_VERBS if verb in lower)
    score += min(25, action_count * 3)

    # Sentence variety (max 15 pts)
    sentences = [
        s.strip() for s in re.split(r"[.!?]", resume_text) if len(s.strip()) > 10
    ]
    score += min(15, len(sentences) * 2)

    # Contact info (max 10 pts)
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text))
    has_phone = bool(re.search(r"[\d\-()+\s]{7,}", resume_text))
    has_linkedin = "linkedin" in lower
    score += min(10, (int(has_email) + int(has_phone) + int(has_linkedin)) * 4)

    # Detailed descriptions (max 25 pts)
    detailed_lines = sum(
        1 for line in resume_text.split("\n") if len(line.split()) >= 8
    )
    score += min(25, detailed_lines * 3)

    return min(100, score)


def _score_formatting_quality(resume_text: str) -> int:
    """0-100 based on resume structure: bullets, headings, spacing."""
    if not resume_text:
        return 0
    lines = resume_text.split("\n")
    score = 0

    # Bullet points (max 25 pts)
    bullet_lines = sum(
        1
        for line in lines
        if line.strip().startswith(("\u2022", "-", "*", "\u2013", "\u25ba", "\u25aa"))
    )
    score += min(25, bullet_lines * 3)

    # Headings — short, prominent lines (max 20 pts)
    heading_count = sum(
        1
        for line in lines
        if line.strip()
        and len(line.strip().split()) <= 5
        and (
            line.strip().isupper()
            or line.strip().istitle()
            or line.strip().endswith(":")
        )
    )
    score += min(20, heading_count * 4)

    # Spacing / separators (max 15 pts)
    empty_lines = sum(1 for line in lines if not line.strip())
    non_empty = len(lines) - empty_lines
    if non_empty > 0 and 2 <= empty_lines <= non_empty:
        score += 15
    elif empty_lines > 0:
        score += 8

    # Readable line lengths (max 20 pts)
    readable = sum(
        1 for line in lines if 5 <= len(line.strip()) <= 120 and line.strip()
    )
    total_non_empty = max(1, sum(1 for line in lines if line.strip()))
    score += int(readable / total_non_empty * 20)

    # Section-like patterns (max 20 pts)
    section_pattern = re.compile(r"^[A-Z][A-Za-z\s&/]+:?\s*$", re.MULTILINE)
    sections = section_pattern.findall(resume_text)
    score += min(20, len(sections) * 4)

    return min(100, score)


def _score_impact_quantification(resume_text: str) -> int:
    """0-100 based on measurable outcomes: numbers, percentages, metrics."""
    if not resume_text:
        return 0
    score = 0

    # Numbers and metrics (max 40 pts)
    numbers = re.findall(r"\b\d+[%+]?\b", resume_text)
    score += min(40, len(numbers) * 4)

    # Percentage mentions (max 25 pts)
    percentages = re.findall(r"\d+\s*%", resume_text)
    score += min(25, len(percentages) * 8)

    # Dollar/revenue mentions (max 20 pts)
    money = re.findall(
        r"[$\u20ac\u00a3]\s*[\d,.]+|revenue|budget|cost|savings",
        resume_text.lower(),
    )
    score += min(20, len(money) * 7)

    # Time-based achievements (max 15 pts)
    time_refs = re.findall(r"\b\d+\s*(?:year|month|week|day)s?\b", resume_text.lower())
    score += min(15, len(time_refs) * 5)

    return min(100, score)


def _score_keyword_density(resume_text: str, skills: list[Skill]) -> int:
    """0-100 based on industry keywords and skill mentions in text."""
    if not resume_text:
        return 0
    lower = resume_text.lower()
    score = 0

    # Industry keywords (max 50 pts)
    keyword_count = sum(1 for kw in _INDUSTRY_KEYWORDS if kw in lower)
    score += min(50, keyword_count * 4)

    # Skill keywords from extracted skills (max 30 pts)
    skill_in_text = sum(1 for s in skills if s.name.lower() in lower)
    score += min(30, skill_in_text * 3)

    # Technical terms density (max 20 pts)
    tech_terms = re.findall(
        r"\b(?:algorithm|data structure|api|sdk|framework|library|platform|"
        r"architecture|system|application|software|engineering)\b",
        lower,
    )
    score += min(20, len(tech_terms) * 3)

    return min(100, score)


# ── Main scoring function ────────────────────────────────


def compute_developer_score(
    resume_text: str,
    skills: list[Skill],
    github: GitHubSummary | None,
) -> DeveloperScore:
    """Compute the weighted composite developer score.

    Uses ATS-style resume evaluation with 6 resume-based sub-scores and
    4 GitHub-based sub-scores.  Weights are redistributed based on
    available data sources so unused metrics are excluded, not penalised.
    """

    all_scores = {
        "resume_completeness": _score_resume_completeness(resume_text),
        "content_quality": _score_content_quality(resume_text),
        "skill_diversity": _score_skill_diversity(skills),
        "formatting_quality": _score_formatting_quality(resume_text),
        "impact_quantification": _score_impact_quantification(resume_text),
        "keyword_density": _score_keyword_density(resume_text, skills),
        "github_activity": _score_github_activity(github),
        "repo_quality": _score_repo_quality(github),
        "documentation": _score_documentation(github),
        "community": _score_community(github),
        "technology_depth": _score_technology_depth(github),
    }

    # Determine which metrics are applicable based on available data
    has_resume = bool(resume_text)
    has_github = github is not None

    active_keys: set[str] = set()
    if has_resume:
        active_keys |= _RESUME_METRICS
    if has_github:
        active_keys |= _GITHUB_METRICS

    # Build redistributed weights (sum to 1.0 over active keys only)
    active_weights = {k: WEIGHTS[k] for k in active_keys}
    total_weight = sum(active_weights.values()) or 1.0
    normalized = {k: v / total_weight for k, v in active_weights.items()}

    # Compute overall from active metrics only
    overall = int(sum(all_scores[k] * normalized[k] for k in normalized))
    overall = max(0, min(100, overall))

    # Only include active categories in the response
    categories = {k: all_scores[k] for k in sorted(active_keys)}

    # Build human-readable justification
    parts: list[str] = []
    for key in sorted(active_keys, key=lambda k: all_scores[k], reverse=True):
        s = all_scores[key]
        label = key.replace("_", " ").title()
        if s >= 75:
            parts.append(f"{label}: strong ({s}/100)")
        elif s >= 40:
            parts.append(f"{label}: moderate ({s}/100)")
        else:
            parts.append(f"{label}: needs improvement ({s}/100)")

    justification = "Score breakdown \u2014 " + "; ".join(parts) + "."

    return DeveloperScore(
        overall=overall,
        categories=categories,
        justification=justification,
    )


# ── Text-based skill extraction fallback ─────────────────

# Display name overrides for text-extracted skills.
_DISPLAY_NAME_MAP = {
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    "nestjs": "Nest.js",
    "nest.js": "Nest.js",
    "nuxtjs": "Nuxt.js",
    "nuxt.js": "Nuxt.js",
    "tailwindcss": "TailwindCSS",
    "tailwind": "TailwindCSS",
    "fastapi": "FastAPI",
    "graphql": "GraphQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "dynamodb": "DynamoDB",
    "neo4j": "Neo4j",
    "elasticsearch": "Elasticsearch",
    "sqlite": "SQLite",
    "ci/cd": "CI/CD",
    "k8s": "Kubernetes",
    "github actions": "GitHub Actions",
    "github": "GitHub",
    "gitlab": "GitLab",
    "aws": "AWS",
    "gcp": "GCP",
    "digitalocean": "DigitalOcean",
    "cloudflare": "Cloudflare",
    "react native": "React Native",
    "spring boot": "Spring Boot",
    "ruby on rails": "Ruby on Rails",
    "asp.net": "ASP.NET",
    "material ui": "Material UI",
    "amazon web services": "AWS",
    "google cloud": "Google Cloud",
    "c++": "C++",
    "c#": "C#",
}


def _skill_present_in_text(skill_name: str, text_lower: str) -> bool:
    """Check if a skill name appears in text as a distinct term, not a substring.

    Uses word-boundary matching to avoid false positives like
    'express' matching 'expressed' or 'expression'.
    """
    # Special characters in skill names need escaping for regex
    escaped = re.escape(skill_name)
    # For multi-word skills (e.g. "spring boot"), match the full phrase
    # For single-word skills, require word boundaries
    pattern = rf"(?<![\w\-]){escaped}(?![\w\-])"
    return bool(re.search(pattern, text_lower))


def extract_skills_from_github(github: GitHubSummary) -> list[Skill]:
    """Extract skills from GitHub profile data using deep repository analysis.

    Sources (in priority order):
    1. Detected technologies from dependency files (package.json, requirements.txt)
    2. Detected technologies from file tree analysis (extensions, config files)
    3. Detected technologies from README content parsing
    4. top_languages (with percentage-based proficiency)
    5. Repo topics matched against known skills
    6. Repo descriptions and names
    """
    skills: list[Skill] = []
    seen: set[str] = set()

    # ── Technology-to-skill category mapping ──────────────
    _tech_category_map: dict[str, tuple[str, str]] = {
        # (canonical_name, SkillCategory)
        # Languages
        "python": ("Python", "language"),
        "javascript": ("JavaScript", "language"),
        "typescript": ("TypeScript", "language"),
        "java": ("Java", "language"),
        "go": ("Go", "language"),
        "rust": ("Rust", "language"),
        "ruby": ("Ruby", "language"),
        "php": ("PHP", "language"),
        "swift": ("Swift", "language"),
        "kotlin": ("Kotlin", "language"),
        "scala": ("Scala", "language"),
        "dart": ("Dart", "language"),
        "c": ("C", "language"),
        "c++": ("C++", "language"),
        "c#": ("C#", "language"),
        "r": ("R", "language"),
        "html": ("HTML", "language"),
        "css": ("CSS", "language"),
        "sql": ("SQL", "language"),
        "shell/bash": ("Shell/Bash", "language"),
        "lua": ("Lua", "language"),
        "perl": ("Perl", "language"),
        "jupyter notebook": ("Jupyter Notebook", "language"),
        # Frameworks
        "react": ("React", "framework"),
        "next.js": ("Next.js", "framework"),
        "vue": ("Vue", "framework"),
        "nuxt.js": ("Nuxt.js", "framework"),
        "angular": ("Angular", "framework"),
        "svelte": ("Svelte", "framework"),
        "django": ("Django", "framework"),
        "flask": ("Flask", "framework"),
        "fastapi": ("FastAPI", "framework"),
        "express.js": ("Express.js", "framework"),
        "nestjs": ("NestJS", "framework"),
        "spring boot": ("Spring Boot", "framework"),
        "tailwindcss": ("TailwindCSS", "framework"),
        "bootstrap": ("Bootstrap", "framework"),
        "material ui": ("Material UI", "framework"),
        "styled components": ("Styled Components", "framework"),
        "redux": ("Redux", "framework"),
        "zustand": ("Zustand", "framework"),
        "electron": ("Electron", "framework"),
        "react native": ("React Native", "framework"),
        "flutter": ("Flutter", "framework"),
        # ML/AI frameworks
        "tensorflow": ("TensorFlow", "framework"),
        "pytorch": ("PyTorch", "framework"),
        "keras": ("Keras", "framework"),
        "scikit-learn": ("Scikit-learn", "framework"),
        "opencv": ("OpenCV", "framework"),
        "pandas": ("Pandas", "framework"),
        "numpy": ("NumPy", "framework"),
        "matplotlib": ("Matplotlib", "framework"),
        "seaborn": ("Seaborn", "framework"),
        "scipy": ("SciPy", "framework"),
        "hugging face transformers": ("Hugging Face", "framework"),
        "langchain": ("LangChain", "framework"),
        "xgboost": ("XGBoost", "framework"),
        "lightgbm": ("LightGBM", "framework"),
        "spacy": ("spaCy", "framework"),
        "nltk": ("NLTK", "framework"),
        "streamlit": ("Streamlit", "framework"),
        "gradio": ("Gradio", "framework"),
        # Databases
        "postgresql": ("PostgreSQL", "database"),
        "mongodb": ("MongoDB", "database"),
        "mysql": ("MySQL", "database"),
        "redis": ("Redis", "database"),
        "sqlite": ("SQLite", "database"),
        "elasticsearch": ("Elasticsearch", "database"),
        "firebase": ("Firebase", "database"),
        "prisma": ("Prisma", "database"),
        "sqlalchemy": ("SQLAlchemy", "database"),
        "sequelize": ("Sequelize", "database"),
        "typeorm": ("TypeORM", "database"),
        # Tools
        "docker": ("Docker", "tool"),
        "docker compose": ("Docker Compose", "tool"),
        "kubernetes": ("Kubernetes", "tool"),
        "terraform": ("Terraform", "tool"),
        "ansible": ("Ansible", "tool"),
        "nginx": ("Nginx", "tool"),
        "github actions": ("GitHub Actions", "tool"),
        "ci/cd": ("CI/CD", "tool"),
        "jenkins": ("Jenkins", "tool"),
        "git": ("Git", "tool"),
        "eslint": ("ESLint", "tool"),
        "prettier": ("Prettier", "tool"),
        "webpack": ("Webpack", "tool"),
        "vite": ("Vite", "tool"),
        "jest": ("Jest", "tool"),
        "pytest": ("pytest", "tool"),
        "cypress": ("Cypress", "tool"),
        "selenium": ("Selenium", "tool"),
        "playwright": ("Playwright", "tool"),
        "storybook": ("Storybook", "tool"),
        "make": ("Make", "tool"),
        # Cloud
        "aws": ("AWS", "cloud"),
        "google cloud": ("Google Cloud", "cloud"),
        "azure": ("Azure", "cloud"),
        "heroku": ("Heroku", "cloud"),
        "vercel": ("Vercel", "cloud"),
        "netlify": ("Netlify", "cloud"),
    }

    # Build a reverse lookup for case-insensitive matching
    _tech_lookup: dict[str, tuple[str, str]] = {}
    for key, val in _tech_category_map.items():
        _tech_lookup[key.lower()] = val

    # ── Helper to add skill ──────────────────────────────
    def _add_skill(
        name: str, category: str, proficiency: Proficiency, source: str = "github"
    ) -> None:
        key = name.lower()
        if key in seen:
            return
        seen.add(key)
        skills.append(
            Skill(
                name=name,
                category=SkillCategory(category),
                proficiency=proficiency,
                source=source,
            )
        )

    # ── 1. From detected_technologies (deep analysis) ────
    # Count how many repos use each technology to estimate proficiency
    tech_repo_count: dict[str, int] = {}
    for repo in github.notable_repos:
        for tech in repo.detected_technologies:
            tech_lower = tech.lower()
            tech_repo_count[tech_lower] = tech_repo_count.get(tech_lower, 0) + 1

    for tech_lower, count in tech_repo_count.items():
        lookup = _tech_lookup.get(tech_lower)
        if not lookup:
            continue
        name, category = lookup
        # Proficiency based on how many repos use this tech
        if count >= 4:
            prof = Proficiency.ADVANCED
        elif count >= 2:
            prof = Proficiency.INTERMEDIATE
        else:
            prof = Proficiency.BEGINNER
        _add_skill(name, category, prof)

    # ── 2. From top_languages (percentage-based proficiency) ──
    for lang, pct in github.top_languages.items():
        lang_lower = lang.lower()
        canonical = _KNOWN_LANGUAGES.get(lang_lower, lang)
        lookup = _tech_lookup.get(canonical.lower())
        category = lookup[1] if lookup else "language"

        if pct >= 30:
            prof = Proficiency.ADVANCED
        elif pct >= 12:
            prof = Proficiency.INTERMEDIATE
        else:
            prof = Proficiency.BEGINNER

        _add_skill(canonical, category, prof)

    # ── 3. From repo topics → match against known skills ──
    all_topics: set[str] = set()
    for repo in github.notable_repos:
        for topic in repo.topics:
            all_topics.add(topic.lower().replace("-", " "))

    for topic in all_topics:
        lookup = _tech_lookup.get(topic)
        if lookup:
            name, category = lookup
            _add_skill(name, category, Proficiency.INTERMEDIATE)
            continue
        # Also try matching known skills
        for cat_name, skill_list in _KNOWN_SKILLS.items():
            for skill_name in skill_list:
                if skill_name == topic or topic in skill_name or skill_name in topic:
                    display = _DISPLAY_NAME_MAP.get(skill_name, skill_name.title())
                    _category_map = {
                        "language": SkillCategory.LANGUAGE,
                        "framework": SkillCategory.FRAMEWORK,
                        "tool": SkillCategory.TOOL,
                        "database": SkillCategory.DATABASE,
                        "cloud": SkillCategory.CLOUD,
                    }
                    cat = _category_map.get(cat_name, SkillCategory.TOOL)
                    _add_skill(display, cat, Proficiency.INTERMEDIATE)
                    break

    # ── 4. From individual repo languages ─────────────────
    for repo in github.notable_repos:
        if repo.language:
            lang_lower = repo.language.lower()
            canonical = _KNOWN_LANGUAGES.get(lang_lower, repo.language)
            _add_skill(canonical, "language", Proficiency.BEGINNER)

    # ── 5. From repo descriptions and names ───────────────
    repo_text_parts: list[str] = []
    for repo in github.notable_repos:
        if repo.description:
            repo_text_parts.append(repo.description.lower())
        repo_text_parts.append(repo.name.lower().replace("-", " ").replace("_", " "))
    repo_text = " ".join(repo_text_parts)

    for category, skill_list in _KNOWN_SKILLS.items():
        if category == "language":
            continue
        for skill_name in skill_list:
            if skill_name in seen or len(skill_name) <= 2:
                continue
            if _skill_present_in_text(skill_name, repo_text):
                display = _DISPLAY_NAME_MAP.get(skill_name, skill_name.title())
                _add_skill(display, category, Proficiency.INTERMEDIATE)

    # ── 6. Detect domain-specific skills from repo indicators ──
    has_ml_repos = any(
        any(
            t.lower()
            in (
                "tensorflow",
                "pytorch",
                "scikit-learn",
                "keras",
                "opencv",
                "machine learning",
                "deep learning",
                "nlp",
                "computer vision",
                "xgboost",
                "lightgbm",
                "hugging face transformers",
            )
            for t in repo.detected_technologies
        )
        for repo in github.notable_repos
    )
    if has_ml_repos:
        _add_skill("Machine Learning", "framework", Proficiency.INTERMEDIATE)

    has_testing = any(repo.has_tests for repo in github.notable_repos)
    if has_testing:
        _add_skill("Testing", "tool", Proficiency.INTERMEDIATE)

    has_ci = any(repo.has_ci for repo in github.notable_repos)
    if has_ci:
        _add_skill("CI/CD", "tool", Proficiency.INTERMEDIATE)

    has_docker = any(repo.has_docker for repo in github.notable_repos)
    if has_docker:
        _add_skill("Docker", "tool", Proficiency.INTERMEDIATE)

    return skills


def extract_resume_projects(resume_text: str) -> list[dict]:
    """Extract structured project information from resume text.

    Parses resume into individual projects (from Projects, Experience, Work
    sections) and for each project extracts:
      - name: project title
      - description: the full text block for this project
      - technologies: technologies detected in this project's description
      - domain: classified domain (web, api, data, ml, mobile, devops, library)
      - complexity_signals: count of architecture/complexity indicators

    This mirrors the per-repo analysis done for GitHub, producing a unified
    structure that downstream functions can consume identically.
    """
    if not resume_text:
        return []

    lines = resume_text.split("\n")
    projects: list[dict] = []

    # ── Step 1: Split text into section blocks ────────────
    sections = _split_into_sections(lines)

    # ── Step 2: Extract projects from relevant sections ───
    project_sections = ["projects", "experience", "work", "professional experience",
                        "work experience", "project experience"]
    for section_name, section_lines in sections:
        if not any(ps in section_name.lower() for ps in project_sections):
            continue
        section_projects = _extract_projects_from_section(section_lines)
        projects.extend(section_projects)

    # ── Step 3: If no projects found structurally, try the whole text ──
    if not projects:
        projects = _extract_projects_from_flat_text(resume_text)

    # ── Step 4: Enrich each project with technology and domain analysis ──
    for proj in projects:
        desc_lower = proj["description"].lower()
        proj["technologies"] = _detect_technologies_in_text(desc_lower)
        proj["domain"] = _classify_project_domain(proj["technologies"], desc_lower)
        proj["complexity_signals"] = _count_complexity_signals(desc_lower)

    return projects


def _split_into_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Split resume lines into named sections based on heading detection."""
    sections: list[tuple[str, list[str]]] = []
    current_name = "header"
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append(line)
            continue

        # Detect section headings
        words = stripped.split()
        no_bullet = not stripped.startswith(
            ("\u2022", "-", "*", "\u2013")
        )
        is_letter_only = stripped[0].isupper() and all(
            c.isalpha() or c.isspace() or c in "&/-:"
            for c in stripped.rstrip(":")
        )
        is_heading = (
            len(words) <= 6
            and len(stripped) <= 60
            and (
                stripped.isupper()
                or stripped.istitle()
                or stripped.endswith(":")
                or is_letter_only
            )
            and no_bullet
        )

        if is_heading and len(stripped) > 2:
            if current_lines:
                sections.append((current_name, current_lines))
            current_name = stripped.rstrip(":")
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_name, current_lines))

    return sections


def _extract_projects_from_section(section_lines: list[str]) -> list[dict]:
    """Extract individual projects from a section's lines.

    Uses heuristics: project titles are non-bullet lines that appear before
    bullet-point descriptions, or lines with a date range / pipe separator.
    """
    projects: list[dict] = []
    current_name = ""
    current_desc_lines: list[str] = []

    for line in section_lines:
        stripped = line.strip()
        if not stripped:
            continue

        is_bullet = stripped.startswith(
            ("\u2022", "-", "*", "\u2013", "\u25ba", "\u25aa")
        )

        # Detect project/job title: non-bullet, has uppercase start, not too long
        is_title = (
            not is_bullet
            and len(stripped) <= 120
            and stripped[0].isupper()
            and not stripped.startswith(("http", "www"))
        )

        # Check for date patterns (common in experience entries)
        has_date = bool(re.search(
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
            r"january|february|march|april|june|july|august|september|"
            r"october|november|december|present|current|\d{4})\b",
            stripped.lower(),
        ))

        # A title line or a line with dates starts a new project entry
        if is_title and (has_date or len(stripped.split()) <= 12) and not is_bullet:
            # Save previous project
            if current_name and current_desc_lines:
                desc = "\n".join(current_desc_lines)
                projects.append({"name": current_name, "description": desc})
            elif current_desc_lines and not current_name:
                # First block without a clear title
                desc = "\n".join(current_desc_lines)
                projects.append({"name": "Project", "description": desc})

            current_name = stripped
            current_desc_lines = []
        else:
            current_desc_lines.append(stripped)

    # Save last project
    if current_name and current_desc_lines:
        desc = "\n".join(current_desc_lines)
        projects.append({"name": current_name, "description": desc})
    elif current_desc_lines:
        desc = "\n".join(current_desc_lines)
        projects.append({"name": "Project", "description": desc})

    return projects


def _extract_projects_from_flat_text(resume_text: str) -> list[dict]:
    """Fallback: extract projects from unstructured text using action verb patterns."""
    lower = resume_text.lower()
    project_patterns = re.findall(
        r"((?:built|developed|created|designed|implemented|launched|deployed)\s+"
        r"(?:a\s+|an\s+|the\s+)?[A-Za-z][\w\s\-,/()]{10,200}?)(?:\.|$|\n)",
        lower,
    )

    projects: list[dict] = []
    seen: set[str] = set()
    for match in project_patterns:
        key = match.strip()[:40]
        if key in seen:
            continue
        seen.add(key)
        # Grab surrounding context (200 chars before and after)
        idx = lower.find(match)
        ctx_start = max(0, idx - 200)
        ctx_end = min(len(lower), idx + len(match) + 200)
        context = resume_text[ctx_start:ctx_end]
        projects.append({"name": match.strip()[:60].title(), "description": context})

    # If still nothing, treat the whole resume as one project block
    if not projects and len(resume_text.strip()) > 50:
        projects.append({"name": "Resume", "description": resume_text})

    return projects


# Technology detection for resume text (shared with GitHub pipeline)
_TECHNOLOGY_PATTERNS: dict[str, str] = {
    # ML/AI
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "keras": "keras",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "opencv": "opencv",
    "pandas": "pandas",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "scipy": "scipy",
    "xgboost": "xgboost",
    "lightgbm": "lightgbm",
    "huggingface": "hugging face transformers",
    "hugging face": "hugging face transformers",
    "transformers": "hugging face transformers",
    "langchain": "langchain",
    "spacy": "spacy",
    "nltk": "nltk",
    "streamlit": "streamlit",
    "gradio": "gradio",
    "machine learning": "machine learning",
    "deep learning": "deep learning",
    "neural network": "neural network",
    "computer vision": "computer vision",
    "natural language processing": "nlp",
    "nlp": "nlp",
    "reinforcement learning": "reinforcement learning",
    "model training": "model training",
    "feature engineering": "feature engineering",
    # Frontend
    "react": "react",
    "next.js": "next.js",
    "nextjs": "next.js",
    "vue": "vue",
    "vue.js": "vue",
    "angular": "angular",
    "svelte": "svelte",
    "tailwind": "tailwindcss",
    "tailwindcss": "tailwindcss",
    "bootstrap": "bootstrap",
    "material ui": "material ui",
    "styled-components": "styled components",
    "redux": "redux",
    "gatsby": "gatsby",
    "nuxt": "nuxt.js",
    "framer motion": "framer motion",
    "responsive design": "responsive design",
    "figma": "figma",
    # Backend
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "express": "express.js",
    "express.js": "express.js",
    "nest.js": "nestjs",
    "nestjs": "nestjs",
    "spring boot": "spring boot",
    "spring": "spring",
    "rails": "ruby on rails",
    "ruby on rails": "ruby on rails",
    "laravel": "laravel",
    "asp.net": "asp.net",
    ".net": ".net",
    "rest api": "rest api",
    "graphql": "graphql",
    "grpc": "grpc",
    "microservices": "microservices",
    # Databases
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "sqlite": "sqlite",
    "cassandra": "cassandra",
    "dynamodb": "dynamodb",
    "firebase": "firebase",
    "supabase": "supabase",
    "neo4j": "neo4j",
    "prisma": "prisma",
    "sqlalchemy": "sqlalchemy",
    # Languages
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "c\\+\\+": "c++",
    "c#": "c#",
    "golang": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala",
    "dart": "dart",
    "html": "html",
    "css": "css",
    "sql": "sql",
    # DevOps / Tools
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "terraform": "terraform",
    "ansible": "ansible",
    "ci/cd": "ci/cd",
    "jenkins": "jenkins",
    "github actions": "github actions",
    "gitlab ci": "gitlab ci",
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "heroku": "heroku",
    "vercel": "vercel",
    "netlify": "netlify",
    "nginx": "nginx",
    "linux": "linux",
    # Testing
    "jest": "jest",
    "pytest": "pytest",
    "cypress": "cypress",
    "selenium": "selenium",
    "playwright": "playwright",
    "unit test": "unit testing",
    "unit testing": "unit testing",
    "integration testing": "integration testing",
    "test-driven": "tdd",
    "tdd": "tdd",
}


def _detect_technologies_in_text(text_lower: str) -> list[str]:
    """Detect technologies mentioned in a text block using word-boundary matching.

    Returns canonical technology names found in the text.
    """
    found: set[str] = set()
    for pattern, canonical in _TECHNOLOGY_PATTERNS.items():
        if len(pattern) <= 2:
            continue
        if _skill_present_in_text(pattern, text_lower):
            found.add(canonical)
    return sorted(found)


# Domain classification based on detected technologies
_DOMAIN_TECH_MAP: dict[str, set[str]] = {
    "ml": {
        "tensorflow", "pytorch", "keras", "scikit-learn", "opencv", "xgboost",
        "lightgbm", "hugging face transformers", "langchain", "spacy", "nltk",
        "machine learning", "deep learning", "neural network", "computer vision",
        "nlp", "reinforcement learning", "model training", "feature engineering",
        "streamlit", "gradio",
    },
    "data": {
        "pandas", "numpy", "matplotlib", "seaborn", "scipy", "sql", "postgresql",
        "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "cassandra",
        "dynamodb", "firebase", "supabase", "neo4j", "prisma", "sqlalchemy",
    },
    "web": {
        "react", "next.js", "vue", "angular", "svelte", "tailwindcss", "bootstrap",
        "material ui", "styled components", "redux", "gatsby", "nuxt.js",
        "framer motion", "responsive design", "html", "css", "figma",
    },
    "api": {
        "fastapi", "django", "flask", "express.js", "nestjs", "spring boot",
        "spring", "ruby on rails", "laravel", "asp.net", ".net", "rest api",
        "graphql", "grpc", "microservices",
    },
    "devops": {
        "docker", "kubernetes", "terraform", "ansible", "ci/cd", "jenkins",
        "github actions", "gitlab ci", "aws", "azure", "gcp", "heroku",
        "vercel", "netlify", "nginx", "linux",
    },
    "mobile": {
        "react native", "flutter", "swift", "kotlin", "dart",
    },
    "testing": {
        "jest", "pytest", "cypress", "selenium", "playwright", "unit testing",
        "integration testing", "tdd",
    },
}


def _classify_project_domain(technologies: list[str], description: str) -> str:
    """Classify a project's primary domain based on its technologies and description."""
    tech_set = set(technologies)
    domain_scores: dict[str, int] = {}

    for domain, domain_techs in _DOMAIN_TECH_MAP.items():
        overlap = tech_set & domain_techs
        domain_scores[domain] = len(overlap)

    # Also check description for domain keywords
    domain_keywords = {
        "ml": ["machine learning", "deep learning", "neural", "model", "training",
               "prediction", "classification",
               "regression", "detection",
               "recognition", "computer vision",
               "nlp", "ai",
               "artificial intelligence"],
        "data": ["data analysis", "data pipeline",
                 "etl", "analytics", "dashboard",
                 "data warehouse",
                 "data engineering",
                 "visualization", "reporting"],
        "web": ["website", "web app", "frontend",
                "landing page", "ui",
                "user interface",
                "responsive", "single page",
                "spa"],
        "api": ["api", "backend", "server",
                "endpoint", "microservice",
                "rest", "authentication",
                "authorization"],
        "devops": ["deploy", "infrastructure",
                   "pipeline", "container",
                   "cloud", "monitoring",
                   "automation",
                   "provisioning"],
        "mobile": ["mobile", "ios", "android",
                   "app store",
                   "cross-platform"],
    }

    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in description:
                domain_scores[domain] = domain_scores.get(domain, 0) + 1

    if not domain_scores or max(domain_scores.values()) == 0:
        return "general"
    return max(domain_scores, key=lambda k: domain_scores[k])


_COMPLEXITY_TERMS = [
    "architecture", "scalable", "distributed", "microservice", "caching",
    "queue", "concurrent", "async", "real-time", "optimization",
    "algorithm", "encryption", "authentication", "authorization",
    "rate limit", "load balanc", "database design", "system design",
    "pipeline", "multi-threaded", "parallel", "clustering",
    "api gateway", "message broker", "event-driven", "websocket",
    "oauth", "jwt", "rbac", "ssl", "https",
]


def _count_complexity_signals(text_lower: str) -> int:
    """Count architecture and complexity signals in text."""
    return sum(1 for term in _COMPLEXITY_TERMS if term in text_lower)


def extract_skills_from_text(resume_text: str) -> list[Skill]:
    """Extract skills from resume text using project-aware technology detection.

    Extracts structured projects from the resume and detects technologies
    per project, then aggregates into skills with proficiency based on
    frequency across projects and contextual signals.
    """
    if not resume_text:
        return []

    lower = resume_text.lower()
    skills: list[Skill] = []
    seen: set[str] = set()

    # ── Extract structured projects and detect technologies per project ──
    projects = extract_resume_projects(resume_text)
    tech_project_count: dict[str, int] = {}
    for proj in projects:
        for tech in proj.get("technologies", []):
            tech_project_count[tech] = tech_project_count.get(tech, 0) + 1

    # ── Build the GitHub-style tech category lookup ──────
    # Reuse the same _tech_category_map pattern from extract_skills_from_github
    _resume_tech_lookup: dict[str, tuple[str, str]] = {
        # ML/AI
        "tensorflow": ("TensorFlow", "framework"),
        "pytorch": ("PyTorch", "framework"),
        "keras": ("Keras", "framework"),
        "scikit-learn": ("Scikit-learn", "framework"),
        "opencv": ("OpenCV", "framework"),
        "pandas": ("Pandas", "framework"),
        "numpy": ("NumPy", "framework"),
        "matplotlib": ("Matplotlib", "framework"),
        "seaborn": ("Seaborn", "framework"),
        "scipy": ("SciPy", "framework"),
        "xgboost": ("XGBoost", "framework"),
        "lightgbm": ("LightGBM", "framework"),
        "hugging face transformers": ("Hugging Face", "framework"),
        "langchain": ("LangChain", "framework"),
        "spacy": ("spaCy", "framework"),
        "nltk": ("NLTK", "framework"),
        "streamlit": ("Streamlit", "framework"),
        "gradio": ("Gradio", "framework"),
        "machine learning": ("Machine Learning", "framework"),
        "deep learning": ("Deep Learning", "framework"),
        "neural network": ("Neural Networks", "framework"),
        "computer vision": ("Computer Vision", "framework"),
        "nlp": ("NLP", "framework"),
        "reinforcement learning": ("Reinforcement Learning", "framework"),
        "model training": ("Model Training", "framework"),
        "feature engineering": ("Feature Engineering", "framework"),
        # Frontend
        "react": ("React", "framework"),
        "next.js": ("Next.js", "framework"),
        "vue": ("Vue", "framework"),
        "angular": ("Angular", "framework"),
        "svelte": ("Svelte", "framework"),
        "tailwindcss": ("TailwindCSS", "framework"),
        "bootstrap": ("Bootstrap", "framework"),
        "material ui": ("Material UI", "framework"),
        "styled components": ("Styled Components", "framework"),
        "redux": ("Redux", "framework"),
        "gatsby": ("Gatsby", "framework"),
        "nuxt.js": ("Nuxt.js", "framework"),
        "framer motion": ("Framer Motion", "framework"),
        "responsive design": ("Responsive Design", "framework"),
        "figma": ("Figma", "tool"),
        # Backend
        "fastapi": ("FastAPI", "framework"),
        "django": ("Django", "framework"),
        "flask": ("Flask", "framework"),
        "express.js": ("Express.js", "framework"),
        "nestjs": ("NestJS", "framework"),
        "spring boot": ("Spring Boot", "framework"),
        "spring": ("Spring", "framework"),
        "ruby on rails": ("Ruby on Rails", "framework"),
        "laravel": ("Laravel", "framework"),
        "asp.net": ("ASP.NET", "framework"),
        ".net": (".NET", "framework"),
        "rest api": ("REST API", "framework"),
        "graphql": ("GraphQL", "framework"),
        "grpc": ("gRPC", "framework"),
        "microservices": ("Microservices", "framework"),
        # Databases
        "postgresql": ("PostgreSQL", "database"),
        "mysql": ("MySQL", "database"),
        "mongodb": ("MongoDB", "database"),
        "redis": ("Redis", "database"),
        "elasticsearch": ("Elasticsearch", "database"),
        "sqlite": ("SQLite", "database"),
        "cassandra": ("Cassandra", "database"),
        "dynamodb": ("DynamoDB", "database"),
        "firebase": ("Firebase", "database"),
        "supabase": ("Supabase", "database"),
        "neo4j": ("Neo4j", "database"),
        "prisma": ("Prisma", "database"),
        "sqlalchemy": ("SQLAlchemy", "database"),
        # Languages
        "python": ("Python", "language"),
        "javascript": ("JavaScript", "language"),
        "typescript": ("TypeScript", "language"),
        "java": ("Java", "language"),
        "c++": ("C++", "language"),
        "c#": ("C#", "language"),
        "go": ("Go", "language"),
        "rust": ("Rust", "language"),
        "ruby": ("Ruby", "language"),
        "php": ("PHP", "language"),
        "swift": ("Swift", "language"),
        "kotlin": ("Kotlin", "language"),
        "scala": ("Scala", "language"),
        "dart": ("Dart", "language"),
        "html": ("HTML", "language"),
        "css": ("CSS", "language"),
        "sql": ("SQL", "language"),
        # DevOps / Tools
        "docker": ("Docker", "tool"),
        "kubernetes": ("Kubernetes", "tool"),
        "terraform": ("Terraform", "tool"),
        "ansible": ("Ansible", "tool"),
        "ci/cd": ("CI/CD", "tool"),
        "jenkins": ("Jenkins", "tool"),
        "github actions": ("GitHub Actions", "tool"),
        "gitlab ci": ("GitLab CI", "tool"),
        "aws": ("AWS", "cloud"),
        "azure": ("Azure", "cloud"),
        "gcp": ("GCP", "cloud"),
        "heroku": ("Heroku", "cloud"),
        "vercel": ("Vercel", "cloud"),
        "netlify": ("Netlify", "cloud"),
        "nginx": ("Nginx", "tool"),
        "linux": ("Linux", "tool"),
        # Testing
        "jest": ("Jest", "tool"),
        "pytest": ("pytest", "tool"),
        "cypress": ("Cypress", "tool"),
        "selenium": ("Selenium", "tool"),
        "playwright": ("Playwright", "tool"),
        "unit testing": ("Unit Testing", "tool"),
        "integration testing": ("Integration Testing", "tool"),
        "tdd": ("TDD", "tool"),
    }

    # ── Add skills from project-detected technologies ──
    for tech, count in sorted(
        tech_project_count.items(), key=lambda x: -x[1]
    ):
        lookup = _resume_tech_lookup.get(tech)
        if not lookup:
            continue
        name, category = lookup
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        # Proficiency based on how many projects use this tech
        if count >= 3:
            prof = Proficiency.ADVANCED
        elif count >= 2:
            prof = Proficiency.INTERMEDIATE
        else:
            # Single project: use contextual analysis for proficiency
            prof = _estimate_proficiency_from_text(tech, resume_text)

        skills.append(
            Skill(
                name=name,
                category=SkillCategory(category),
                proficiency=prof,
                source="resume",
            )
        )

    # ── Also check the full resume text for skills not found in projects ──
    # (e.g. skills listed in a Skills section without project context)
    section_weights = _detect_section_context(resume_text)
    for category, skill_list in _KNOWN_SKILLS.items():
        for skill_name in skill_list:
            if len(skill_name) <= 2:
                continue
            if not _skill_present_in_text(skill_name, lower):
                continue

            display = _DISPLAY_NAME_MAP.get(skill_name, skill_name.title())
            key = display.lower()
            if key in seen:
                continue
            seen.add(key)

            proficiency = _estimate_proficiency_from_text(
                skill_name, resume_text, section_weights
            )
            skills.append(
                Skill(
                    name=display,
                    category=SkillCategory(category),
                    proficiency=proficiency,
                    source="resume",
                )
            )

    return skills


def _detect_section_context(resume_text: str) -> dict[str, float]:
    """Identify which sections exist and return a weight map for skill context."""
    lower = resume_text.lower()
    weights: dict[str, float] = {}
    # Sections where skill mentions carry higher weight
    high_weight = ["experience", "work", "projects", "professional"]
    medium_weight = ["skills", "technologies", "technical"]
    low_weight = ["education", "coursework", "certifications", "summary"]

    for section in high_weight:
        if section in lower:
            weights[section] = 1.5
    for section in medium_weight:
        if section in lower:
            weights[section] = 1.0
    for section in low_weight:
        if section in lower:
            weights[section] = 0.6
    return weights


def _estimate_proficiency_from_text(
    skill_name: str,
    resume_text: str,
    section_weights: dict[str, float] | None = None,
) -> Proficiency:
    """Estimate proficiency from contextual signals in resume text.

    Uses multiple signals:
    - Frequency of mention (more mentions = higher proficiency)
    - Surrounding action verbs and context clues
    - Duration indicators (years of experience)
    - Section importance (skills in experience section > education section)
    """
    lower = resume_text.lower()
    skill_lower = skill_name.lower()

    # Count frequency of mentions
    frequency = lower.count(skill_lower)

    # Gather context around all occurrences
    contexts: list[str] = []
    start = 0
    while True:
        idx = lower.find(skill_lower, start)
        if idx == -1:
            break
        ctx_start = max(0, idx - 200)
        ctx_end = min(len(lower), idx + len(skill_lower) + 200)
        contexts.append(lower[ctx_start:ctx_end])
        start = idx + 1

    if not contexts:
        return Proficiency.INTERMEDIATE

    combined_context = " ".join(contexts)

    # Score accumulator
    score = 0

    # Frequency signal: 1 mention = 1pt, 2-3 = 3pt, 4+ = 5pt
    if frequency >= 4:
        score += 5
    elif frequency >= 2:
        score += 3
    else:
        score += 1

    # Advanced context clues
    advanced_clues = [
        "expert",
        "advanced",
        "senior",
        "lead",
        "architect",
        "extensive",
        "deep",
        "strong",
        "proficient",
        "mastered",
        "5+",
        "4+",
        "3+ years",
        "led",
        "architected",
        "designed",
        "built from scratch",
        "production",
        "scaled",
        "enterprise",
    ]
    advanced_matches = sum(1 for clue in advanced_clues if clue in combined_context)
    score += advanced_matches * 2

    # Beginner context clues (subtract)
    beginner_clues = [
        "basic",
        "beginner",
        "learning",
        "familiar",
        "exposure",
        "coursework",
        "course",
        "intro",
        "introduction",
        "hobby",
        "personal project",
    ]
    beginner_matches = sum(1 for clue in beginner_clues if clue in combined_context)
    score -= beginner_matches * 2

    # Duration indicators
    year_patterns = re.findall(
        r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience)?",
        combined_context,
    )
    if year_patterns:
        max_years = max(int(y) for y in year_patterns)
        if max_years >= 3:
            score += 4
        elif max_years >= 1:
            score += 2

    # Action verb proximity (skill near action verbs = experience indicator)
    action_nearby = sum(1 for verb in _ACTION_VERBS if verb in combined_context)
    if action_nearby >= 3:
        score += 3
    elif action_nearby >= 1:
        score += 1

    # Section context weighting
    if section_weights:
        in_experience = any(
            sec in combined_context
            for sec in ["experience", "work", "professional", "projects"]
        )
        in_education = any(
            sec in combined_context for sec in ["education", "coursework", "academic"]
        )
        if in_experience:
            score += 2
        if in_education and not in_experience:
            score -= 1

    # Classify
    if score >= 7:
        return Proficiency.ADVANCED
    elif score <= 1:
        return Proficiency.BEGINNER
    return Proficiency.INTERMEDIATE


# ── Radar score computation ──────────────────────────────


def compute_radar_scores(
    skills: list[Skill],
    resume_text: str,
    github: GitHubSummary | None = None,
) -> RadarScores:
    """Compute radar chart scores from detected skills, resume text, and GitHub data.

    Uses project-level technology detection:
    - Resume projects are parsed and technologies are detected per project,
      then each technology is mapped to its radar category.
    - GitHub repos contribute via detected_technologies, languages, and topics.
    - Skills from the skills list contribute with proficiency-based weighting.
    - Each technology contributes to only its primary radar category.
    """
    scores: dict[str, float] = {cat: 0.0 for cat in _RADAR_SKILL_MAP}
    assigned_skills: set[str] = set()

    # ── Project-level analysis for resume text ────────────
    # This is the key improvement: detect technologies per project and
    # use _DOMAIN_TECH_MAP (shared with GitHub pipeline) for accurate
    # category assignment instead of flat keyword matching.
    if resume_text:
        projects = extract_resume_projects(resume_text)
        # Aggregate project technologies with per-project multiplier
        for proj in projects:
            techs = proj.get("technologies", [])
            for tech in techs:
                tech_lower = tech.lower()
                if tech_lower in assigned_skills:
                    continue

                # Map technology to radar category using _DOMAIN_TECH_MAP
                best_cat = _map_tech_to_radar_category(tech_lower)
                if best_cat:
                    # Technologies found in project context get high weight
                    scores[best_cat] += 15
                    assigned_skills.add(tech_lower)

    # ── Skills-based scoring ──────────────────────────────
    skill_category_hints = {
        "language": {"backend", "frontend"},
        "framework": {"backend", "frontend", "data"},
        "tool": {"devops"},
        "database": {"data"},
        "cloud": {"devops"},
    }

    for skill in skills:
        skill_lower = skill.name.lower()
        if skill_lower in assigned_skills:
            continue

        # Find which radar categories this skill matches
        matching_cats: list[str] = []
        for cat, keywords in _RADAR_SKILL_MAP.items():
            if any(kw == skill_lower or kw in skill_lower for kw in keywords):
                matching_cats.append(cat)

        if not matching_cats:
            # Try domain tech map as fallback
            best_cat = _map_tech_to_radar_category(skill_lower)
            if best_cat:
                matching_cats = [best_cat]

        if not matching_cats:
            continue

        # Pick the best category: prefer the one aligned with skill.category
        best_cat = matching_cats[0]
        if len(matching_cats) > 1:
            hints = skill_category_hints.get(skill.category, set())
            for cat in matching_cats:
                if cat in hints:
                    best_cat = cat
                    break

        prof_weight = {
            Proficiency.ADVANCED: 20,
            Proficiency.INTERMEDIATE: 14,
            Proficiency.BEGINNER: 8,
        }
        scores[best_cat] += prof_weight.get(skill.proficiency, 14)
        assigned_skills.add(skill_lower)

    # ── GitHub-specific signals ───────────────────────────
    if github:
        for lang, pct in github.top_languages.items():
            lang_lower = lang.lower()
            if lang_lower in assigned_skills:
                continue
            for cat, keywords in _RADAR_SKILL_MAP.items():
                if lang_lower in keywords:
                    if pct >= 30:
                        scores[cat] += 15
                    elif pct >= 12:
                        scores[cat] += 10
                    else:
                        scores[cat] += 5
                    assigned_skills.add(lang_lower)
                    break

        for repo in github.notable_repos:
            for topic in repo.topics:
                topic_lower = topic.lower().replace("-", " ")
                if topic_lower in assigned_skills:
                    continue
                for cat, keywords in _RADAR_SKILL_MAP.items():
                    if topic_lower in keywords or any(
                        kw in topic_lower for kw in keywords if len(kw) > 2
                    ):
                        scores[cat] += 5
                        assigned_skills.add(topic_lower)
                        break

        for repo in github.notable_repos:
            for tech in repo.detected_technologies:
                tech_lower = tech.lower()
                if tech_lower in assigned_skills:
                    continue
                best_cat = _map_tech_to_radar_category(tech_lower)
                if best_cat:
                    scores[best_cat] += 8
                    assigned_skills.add(tech_lower)
                else:
                    for cat, keywords in _RADAR_SKILL_MAP.items():
                        if tech_lower in keywords or any(
                            kw == tech_lower for kw in keywords
                        ):
                            scores[cat] += 8
                            assigned_skills.add(tech_lower)
                            break

    # Normalize to 0-100 with diminishing returns
    final: dict[str, int] = {}
    for cat, raw in scores.items():
        if raw <= 0:
            final[cat] = 0
        else:
            normalized = min(100, int(40 * math.log(1 + raw / 10)))
            final[cat] = normalized

    return RadarScores(**final)


def _map_tech_to_radar_category(tech_lower: str) -> str | None:
    """Map a technology name to its primary radar chart category.

    Uses _DOMAIN_TECH_MAP (shared between resume and GitHub pipelines)
    for consistent category assignment.
    """
    # Direct mapping from domain to radar category
    _domain_to_radar = {
        "ml": "ml_ai",
        "data": "data",
        "web": "frontend",
        "api": "backend",
        "devops": "devops",
        "mobile": "frontend",
        "testing": "testing",
    }

    for domain, techs in _DOMAIN_TECH_MAP.items():
        if tech_lower in techs:
            return _domain_to_radar.get(domain)

    # Also check _RADAR_SKILL_MAP directly
    for cat, keywords in _RADAR_SKILL_MAP.items():
        if tech_lower in keywords:
            return cat

    return None


def _has_project_context(text: str) -> dict[str, bool]:
    """Check which keywords appear near project/experience context indicators."""
    context_indicators = [
        "built",
        "developed",
        "implemented",
        "deployed",
        "created",
        "designed",
        "architected",
        "project",
        "production",
        "application",
    ]
    result: dict[str, bool] = {}
    for cat_keywords in _RADAR_SKILL_MAP.values():
        for kw in cat_keywords:
            if len(kw) <= 2:
                continue
            idx = text.find(kw)
            if idx == -1:
                continue
            ctx_start = max(0, idx - 150)
            ctx_end = min(len(text), idx + len(kw) + 150)
            context = text[ctx_start:ctx_end]
            result[kw] = any(ind in context for ind in context_indicators)
    return result


# ── Skill category grouping ─────────────────────────────


def compute_skill_categories(skills: list[Skill]) -> list[SkillCategoryBreakdown]:
    """Group skills by category with computed scores."""
    groups: dict[str, list[str]] = {}
    for s in skills:
        groups.setdefault(s.category, []).append(s.name)

    return [
        SkillCategoryBreakdown(
            category=cat,
            skills=names,
            score=min(100, len(names) * 15 + 10),
        )
        for cat, names in sorted(groups.items())
    ]


# ── Programming language extraction ─────────────────────


def extract_programming_languages(
    skills: list[Skill],
    resume_text: str,
) -> list[ProgrammingLanguageScore]:
    """Extract programming languages from skills and resume text with contextual confidence."""
    languages: dict[str, ProgrammingLanguageScore] = {}
    lower = resume_text.lower() if resume_text else ""

    # From extracted skills (higher base confidence)
    for skill in skills:
        key = skill.name.lower()
        if skill.category == "language" and key in _KNOWN_LANGUAGES:
            canonical = _KNOWN_LANGUAGES[key]
            if canonical not in languages:
                confidence = _compute_language_confidence(
                    key, resume_text, skill.source
                )
                proficiency = _reconcile_proficiency_confidence(
                    skill.proficiency, confidence
                )
                languages[canonical] = ProgrammingLanguageScore(
                    name=canonical,
                    proficiency=proficiency,
                    confidence=confidence,
                    context=f"Detected from {skill.source}",
                )

    # From resume text (fallback for non-obvious names)
    if resume_text:
        for key, canonical in _KNOWN_LANGUAGES.items():
            if canonical in languages or len(key) <= 2:
                continue
            if not _skill_present_in_text(key, lower):
                continue
            prof = _estimate_proficiency_from_text(key, resume_text)
            confidence = _compute_language_confidence(key, resume_text, "resume_text")
            prof = _reconcile_proficiency_confidence(prof, confidence)
            languages[canonical] = ProgrammingLanguageScore(
                name=canonical,
                proficiency=prof,
                confidence=confidence,
                context="Detected from resume text",
            )

    order = {"advanced": 0, "intermediate": 1, "beginner": 2}
    return sorted(
        languages.values(),
        key=lambda x: (order.get(x.proficiency, 1), -x.confidence),
    )


def _compute_language_confidence(lang_key: str, resume_text: str, source: str) -> float:
    """Compute confidence score for a programming language based on evidence strength."""
    if not resume_text:
        return 0.5

    lower = resume_text.lower()
    confidence = 0.3  # base

    # Frequency of mentions
    count = lower.count(lang_key)
    if count >= 5:
        confidence += 0.3
    elif count >= 3:
        confidence += 0.2
    elif count >= 2:
        confidence += 0.1

    # Appears in skills/technical section
    skill_section = _extract_section_text(
        lower, ["skills", "technologies", "technical"]
    )
    if lang_key in skill_section:
        confidence += 0.15

    # Appears in experience/project context
    exp_section = _extract_section_text(lower, ["experience", "work", "projects"])
    if lang_key in exp_section:
        confidence += 0.15

    # Source bonus
    if source == "both":
        confidence += 0.1
    elif source == "resume":
        confidence += 0.05

    return round(min(1.0, confidence), 2)


def _reconcile_proficiency_confidence(
    proficiency: Proficiency, confidence: float
) -> Proficiency:
    """Ensure proficiency and confidence are logically consistent.

    Rules:
    - Advanced proficiency requires confidence >= 0.55
    - Beginner proficiency should not have confidence > 0.75
    - Low confidence (< 0.4) caps proficiency at intermediate
    """
    if proficiency == Proficiency.ADVANCED and confidence < 0.55:
        return Proficiency.INTERMEDIATE
    if proficiency == Proficiency.BEGINNER and confidence > 0.75:
        return Proficiency.INTERMEDIATE
    if confidence < 0.4 and proficiency == Proficiency.ADVANCED:
        return Proficiency.INTERMEDIATE
    return proficiency


def _extract_section_text(text: str, section_headers: list[str]) -> str:
    """Extract rough section text by finding headers and taking text until next header."""
    result: list[str] = []
    lines = text.split("\n")
    in_section = False
    for line in lines:
        stripped = line.strip().lower()
        if any(h in stripped for h in section_headers) and len(stripped.split()) <= 5:
            in_section = True
            continue
        if in_section:
            # Stop at next section header
            if (
                stripped
                and len(stripped.split()) <= 5
                and (stripped.isupper() or stripped.istitle() or stripped.endswith(":"))
            ):
                in_section = False
                continue
            result.append(line)
    return " ".join(result)


# ── AI Insights generation ──────────────────────────────


def generate_ai_insights(
    categories: dict[str, int],
    skills: list[Skill],
    github: GitHubSummary | None,
    overall: int,
    resume_text: str = "",
) -> AiInsights:
    """Generate structured insights from scoring results.

    Produces domain-specific insights based on radar score distribution,
    skill composition, and detected gaps rather than generic category labels.
    Key strength is determined by project usage frequency, not just proficiency labels.
    """
    strengths: list[str] = []
    weaknesses: list[str] = []
    improvements: list[str] = []

    # ── Skill composition analysis ──────────────────────
    tech_skills = [s for s in skills if s.category != "soft_skill"]
    advanced_skills = [s for s in tech_skills if s.proficiency == "advanced"]
    intermediate_skills = [s for s in tech_skills if s.proficiency == "intermediate"]
    beginner_skills = [s for s in tech_skills if s.proficiency == "beginner"]
    skill_cats = {s.category for s in tech_skills}

    # Domain detection: what kind of developer is this?
    has_frontend = any(
        s.name.lower() in _RADAR_SKILL_MAP.get("frontend", []) for s in skills
    )
    has_backend = any(
        s.name.lower() in _RADAR_SKILL_MAP.get("backend", []) for s in skills
    )
    has_ml = any(s.name.lower() in _RADAR_SKILL_MAP.get("ml_ai", []) for s in skills)
    has_devops = any(
        s.name.lower() in _RADAR_SKILL_MAP.get("devops", []) for s in skills
    )

    # ── Determine key strength based on project context frequency ──
    # Instead of using proficiency labels, count how often each skill
    # appears in project/experience context to find the actual strongest skill
    key_skill = _detect_key_strength(tech_skills, resume_text)

    # If no resume text but GitHub data exists, derive key strength from GitHub
    if not key_skill and github:
        if github.top_languages:
            top_lang = max(
                github.top_languages,
                key=lambda k: github.top_languages[k],
            )
            key_skill = f"Strong project experience in {top_lang}"

    # ── Strengths ───────────────────────────────────────
    if key_skill:
        strengths.append(key_skill)

    if has_frontend and has_backend:
        strengths.append("Full-stack capability spanning frontend and backend")
    elif has_frontend:
        strengths.append("Solid frontend development foundation")
    elif has_backend:
        strengths.append("Strong backend engineering skills")

    if has_ml:
        strengths.append("Machine learning and AI expertise — a high-demand specialty")

    if len(skill_cats) >= 4:
        strengths.append(
            f"Versatile skill set across {len(skill_cats)} technology categories"
        )

    if github and github.total_stars >= 50:
        strengths.append(
            f"Community-validated work with {github.total_stars} GitHub stars"
        )
    elif github and github.commit_frequency in ("daily", "weekly"):
        strengths.append("Consistent coding activity showing dedication")

    if github and github.public_repos >= 10:
        strengths.append(
            f"Active builder with {github.public_repos} public repositories"
        )

    if github and len(github.top_languages) >= 3:
        langs = ", ".join(list(github.top_languages.keys())[:4])
        strengths.append(f"Multi-language proficiency across {langs}")

    if categories.get("content_quality", 0) >= 70:
        strengths.append("Well-crafted resume with strong content quality")

    if github and categories.get("documentation", 0) >= 70:
        strengths.append("Well-documented repositories with READMEs and descriptions")

    # Fallback: ensure at least one strength
    if not strengths and tech_skills:
        names = ", ".join(s.name for s in tech_skills[:3])
        strengths.append(f"Technical foundation in {names}")
    elif not strengths and github:
        strengths.append(
            f"Active GitHub presence with {github.public_repos} repositories"
        )

    # ── Weaknesses ──────────────────────────────────────
    if len(tech_skills) < 5:
        weaknesses.append(
            f"Only {len(tech_skills)} technical skills detected — consider showcasing more"
        )

    if not any(s.category == "cloud" for s in skills):
        weaknesses.append("No cloud platform skills detected (AWS, Azure, GCP)")

    if not any(s.category == "database" for s in skills):
        weaknesses.append("No database technologies listed")

    if not has_devops:
        weaknesses.append("Missing DevOps and infrastructure skills")

    if resume_text and categories.get("impact_quantification", 0) < 40:
        weaknesses.append("Resume lacks measurable impact metrics and numbers")

    if resume_text and categories.get("formatting_quality", 0) < 50:
        weaknesses.append("Resume formatting could be more structured and scannable")

    if not resume_text and github:
        weaknesses.append(
            "No resume linked — adding a resume strengthens your profile analysis"
        )

    if github and github.total_stars < 5 and github.public_repos >= 3:
        weaknesses.append(
            "Low repository stars — improve READMEs and documentation to attract attention"
        )

    if github and github.commit_frequency in ("sporadic", "monthly"):
        weaknesses.append(
            "Inconsistent commit activity — regular contributions strengthen your profile"
        )

    if len(advanced_skills) == 0 and len(tech_skills) > 0:
        weaknesses.append("No skills at advanced proficiency level detected")

    if len(beginner_skills) > len(intermediate_skills) + len(advanced_skills):
        weaknesses.append(
            "Most skills are at beginner level — focus on deepening core competencies"
        )

    if not any(s.category == "framework" for s in skills):
        weaknesses.append(
            "No frameworks detected — frameworks demonstrate practical project experience"
        )

    # Fallback: always provide at least one weakness/improvement opportunity
    if not weaknesses:
        if len(intermediate_skills) > len(advanced_skills):
            weaknesses.append(
                "Several skills at intermediate level — deepening 2-3 to advanced "
                "would strengthen your profile significantly"
            )
        elif not github:
            weaknesses.append(
                "No GitHub profile linked — public code contributions "
                "add significant credibility"
            )
        else:
            weaknesses.append(
                "Consider expanding into adjacent technology areas to broaden "
                "your engineering versatility"
            )

    # ── Improvements ────────────────────────────────────
    if not any(s.category == "cloud" for s in skills):
        improvements.append(
            "Add cloud platform experience — deploy a project on AWS, Azure, or GCP"
        )

    if resume_text and categories.get("impact_quantification", 0) < 40:
        improvements.append(
            "Quantify achievements: add percentages, revenue impact, and user counts"
        )

    if resume_text and categories.get("formatting_quality", 0) < 50:
        improvements.append(
            "Restructure resume with clear headings, bullet points, and consistent formatting"
        )

    if github is None:
        improvements.append(
            "Link a GitHub profile to showcase your code, contributions, and projects"
        )

    if not resume_text:
        improvements.append(
            "Upload a resume to enable deeper skill analysis and career insights"
        )

    if not has_devops:
        improvements.append(
            "Learn Docker and CI/CD — they're expected in most engineering roles"
        )

    if github and github.total_stars < 10:
        improvements.append(
            "Add comprehensive READMEs with screenshots, setup instructions, and demos"
        )

    if github and len(github.top_languages) < 3:
        improvements.append(
            "Diversify your tech stack — explore projects in different languages"
        )

    if len(intermediate_skills) > len(advanced_skills) * 2 and len(tech_skills) > 3:
        improvements.append(
            "Deepen expertise: focus on advancing 2-3 core skills from intermediate to advanced"
        )

    # If they have ML but no deployment skills
    if has_ml and not has_devops:
        improvements.append(
            "Bridge ML and production: learn MLOps tools like Docker, K8s, or cloud ML services"
        )

    # Fallback: always provide at least one improvement
    if not improvements:
        improvements.append(
            "Build a showcase project combining multiple skills to demonstrate "
            "end-to-end engineering capability"
        )

    # ── Career potential ────────────────────────────────
    if overall >= 80:
        career = (
            "Exceptional profile positioned for senior/staff engineering roles. "
            "Consider technical leadership, open-source contributions, and conference talks."
        )
    elif overall >= 65:
        career = (
            "Strong foundation for senior engineering roles. "
            "Deepen one specialty area and build 2-3 impressive showcase projects "
            "to accelerate career growth."
        )
    elif overall >= 50:
        career = (
            "Solid mid-level profile with clear growth trajectory. "
            "Focus on quantifying impact, expanding cloud skills, and "
            "contributing to open-source projects."
        )
    elif overall >= 35:
        career = (
            "Growing developer profile with visible potential. "
            "Build end-to-end projects, gain production experience, "
            "and expand your technical toolkit."
        )
    else:
        career = (
            "Early-career profile with room for rapid growth. "
            "Start with focused project building, online courses, "
            "and contributing to beginner-friendly open-source projects."
        )

    return AiInsights(
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        career_potential=career,
        recommended_improvements=improvements[:6],
    )


def _detect_key_strength(skills: list[Skill], resume_text: str) -> str | None:
    """Determine the developer's key strength from project context frequency.

    Instead of relying solely on proficiency labels (which can be unreliable),
    this counts how frequently each skill appears in project/experience
    descriptions and weights by action verb proximity.
    """
    if not skills or not resume_text:
        return None

    lower = resume_text.lower()
    # Extract project/experience section text for focused analysis
    project_text = _extract_section_text(
        lower, ["projects", "experience", "work", "professional"]
    )
    if not project_text:
        project_text = lower

    skill_scores: list[tuple[str, float]] = []
    for skill in skills:
        skill_lower = skill.name.lower()
        # Count mentions in project/experience context
        freq = project_text.count(skill_lower)
        if freq == 0:
            continue

        score = float(freq)
        # Bonus for action verb proximity (indicates active usage)
        for verb in _ACTION_VERBS[:15]:  # check top action verbs
            if verb in project_text:
                # Check if verb is near the skill mention
                idx = project_text.find(skill_lower)
                if idx != -1:
                    ctx = project_text[max(0, idx - 100) : idx + len(skill_lower) + 100]
                    if verb in ctx:
                        score += 0.5

        # Proficiency bonus (but not dominant)
        if skill.proficiency == Proficiency.ADVANCED:
            score += 1.0
        elif skill.proficiency == Proficiency.INTERMEDIATE:
            score += 0.5

        skill_scores.append((skill.name, score))

    if not skill_scores:
        # Fall back to proficiency-based if no project context
        advanced = [s for s in skills if s.proficiency == Proficiency.ADVANCED]
        if advanced:
            return f"Strong proficiency in {advanced[0].name}"
        if skills:
            return f"Technical foundation in {skills[0].name}"
        return None

    # Sort by score descending
    skill_scores.sort(key=lambda x: x[1], reverse=True)
    top_skill = skill_scores[0][0]

    # If top 2-3 skills are close in score, mention multiple
    if len(skill_scores) >= 2 and skill_scores[1][1] >= skill_scores[0][1] * 0.7:
        top_names = [s[0] for s in skill_scores[:2]]
        return f"Strong project experience in {' and '.join(top_names)}"

    return f"Deep project experience in {top_skill}"


# ── Score breakdown builder ──────────────────────────────


def build_score_breakdown(
    categories: dict[str, int],
    has_github: bool,
) -> ScoreBreakdown:
    """Build a structured score breakdown from category scores."""
    return ScoreBreakdown(
        resume_completeness=categories.get("resume_completeness", 0),
        content_quality=categories.get("content_quality", 0),
        skill_diversity=categories.get("skill_diversity", 0),
        formatting_quality=categories.get("formatting_quality", 0),
        impact_quantification=categories.get("impact_quantification", 0),
        keyword_density=categories.get("keyword_density", 0),
        github_activity=categories.get("github_activity") if has_github else None,
        repo_quality=categories.get("repo_quality") if has_github else None,
        documentation=categories.get("documentation") if has_github else None,
        community=categories.get("community") if has_github else None,
        technology_depth=categories.get("technology_depth") if has_github else None,
    )


# ── Portfolio Depth Score ────────────────────────────────

# Project-type indicators detected in resume text.
_PROJECT_INDICATORS = [
    "project",
    "application",
    "app",
    "website",
    "platform",
    "system",
    "tool",
    "library",
    "package",
    "service",
    "api",
    "dashboard",
    "pipeline",
    "bot",
    "cli",
    "extension",
    "plugin",
    "mobile app",
    "web app",
    "microservice",
]

_DEPLOYMENT_SIGNALS = [
    "deployed",
    "production",
    "live",
    "hosted",
    "published",
    "released",
    "launched",
    "aws",
    "azure",
    "gcp",
    "heroku",
    "vercel",
    "netlify",
    "docker",
    "kubernetes",
    "ci/cd",
]

_PROJECT_TYPES = {
    "web": ["website", "web app", "web application", "frontend", "full-stack", "saas"],
    "api": ["api", "rest", "graphql", "microservice", "backend", "server"],
    "data": [
        "data pipeline",
        "etl",
        "analytics",
        "dashboard",
        "data science",
        "ml",
        "machine learning",
    ],
    "mobile": ["mobile", "ios", "android", "react native", "flutter"],
    "devops": ["ci/cd", "infrastructure", "terraform", "docker", "kubernetes"],
    "library": ["library", "package", "npm", "pypi", "gem", "open source", "cli"],
}


def _count_distinct_projects(resume_text: str, github: GitHubSummary | None) -> int:
    """Count distinct projects from resume structure rather than keyword frequency.

    Looks for:
    - Entries in a "Projects" section (each project title/heading = 1 project)
    - Distinct project names mentioned with action verbs
    - GitHub repos as separate signal (not double-counted with resume)
    """
    if not resume_text:
        return github.public_repos if github else 0

    lower = resume_text.lower()
    lines = resume_text.split("\n")
    project_count = 0

    # Method 1: Count entries in project/experience sections structurally
    in_project_section = False
    for line in lines:
        stripped = line.strip()
        stripped_lower = stripped.lower()

        # Detect project section headers
        if (
            len(stripped.split()) <= 4
            and any(
                h in stripped_lower
                for h in ["project", "portfolio", "experience", "work"]
            )
            and (
                stripped_lower.endswith(":") or stripped.isupper() or stripped.istitle()
            )
        ):
            in_project_section = True
            continue

        # Detect next section (exit project section)
        if (
            in_project_section
            and stripped
            and len(stripped.split()) <= 4
            and (
                stripped_lower.endswith(":") or stripped.isupper() or stripped.istitle()
            )
            and not any(
                h in stripped_lower
                for h in ["project", "portfolio", "experience", "work"]
            )
        ):
            in_project_section = False
            continue

        # In project section: count lines that look like project titles
        # (non-bullet, non-empty, not too long, looks like a heading)
        if (
            in_project_section
            and stripped
            and not stripped.startswith(
                ("\u2022", "-", "*", "\u2013", "\u25ba", "\u25aa")
            )
        ):
            words = stripped.split()
            # Project titles are typically 1-8 words, often title-cased
            if 1 <= len(words) <= 10 and (
                stripped.istitle()
                or stripped[0].isupper()
                or any(
                    ind in stripped_lower
                    for ind in ["app", "system", "platform", "tool", "bot"]
                )
            ):
                project_count += 1

    # Method 2: If structural analysis found nothing, use pattern matching
    # Look for "Built/Developed/Created X" patterns as distinct project indicators
    if project_count == 0:
        project_patterns = re.findall(
            r"(?:built|developed|created|designed|implemented|launched)\s+"
            r"(?:a\s+|an\s+|the\s+)?"
            r"[A-Za-z][A-Za-z\s-]{2,30}(?:app|application|system|platform|website|"
            r"tool|dashboard|pipeline|service|api|bot|library)",
            lower,
        )
        # Deduplicate similar names
        seen_projects: set[str] = set()
        for match in project_patterns:
            # Normalize to check for duplicates
            key = re.sub(r"\s+", " ", match.strip())[:30]
            if key not in seen_projects:
                seen_projects.add(key)
                project_count += 1

    # Method 3: Absolute minimum — count bullet clusters after project-like headings
    if project_count == 0:
        # Count how many times "project" appears as a distinct concept
        project_mentions = len(re.findall(r"\bproject\b", lower))
        # Be conservative: each 2-3 mentions likely refers to the same project
        project_count = max(1, project_mentions // 2) if project_mentions > 0 else 0

    # Add GitHub repos as distinct signal (take the higher count)
    if github:
        # Don't simply add — take max to avoid double-counting
        project_count = max(project_count, min(github.public_repos, 20))

    return project_count


def compute_portfolio_depth(
    skills: list[Skill],
    resume_text: str,
    github: GitHubSummary | None,
) -> PortfolioDepthScore:
    """Analyze portfolio depth based on actual project detection, tech diversity, and complexity.

    Uses structured project extraction from resume text (same intelligence
    as GitHub repo analysis) for accurate project counting, complexity
    scoring, and project type classification.
    """
    lower = resume_text.lower() if resume_text else ""

    # ── Structured project extraction from resume ─────────
    resume_projects = extract_resume_projects(resume_text) if resume_text else []

    # Accurate project count
    project_count = len(resume_projects)
    if github:
        project_count = max(project_count, min(github.public_repos, 20))

    # Technology diversity (0-100) — from project-detected technologies
    unique_techs: set[str] = set()
    for proj in resume_projects:
        for tech in proj.get("technologies", []):
            unique_techs.add(tech)
    for skill in skills:
        unique_techs.add(skill.name.lower())
    if github:
        for lang in github.top_languages:
            unique_techs.add(lang.lower())
        for repo in github.notable_repos:
            for tech in repo.detected_technologies:
                unique_techs.add(tech.lower())
    tech_div = min(100, len(unique_techs) * 7)

    # Complexity score (0-100) — from project-level complexity signals
    total_complexity_hits = 0
    for proj in resume_projects:
        total_complexity_hits += proj.get("complexity_signals", 0)
        # Technologies count contributes to complexity
        tech_count = len(proj.get("technologies", []))
        if tech_count >= 5:
            total_complexity_hits += 2
        elif tech_count >= 3:
            total_complexity_hits += 1

    # GitHub-based complexity signals
    if github:
        for repo in github.notable_repos:
            # File count as complexity proxy
            if repo.file_count >= 50:
                total_complexity_hits += 2
            elif repo.file_count >= 20:
                total_complexity_hits += 1

            # Config file diversity → architectural maturity
            if len(repo.config_files) >= 3:
                total_complexity_hits += 2
            elif len(repo.config_files) >= 1:
                total_complexity_hits += 1

            # CI/CD, Docker, tests → production-grade complexity
            if repo.has_ci:
                total_complexity_hits += 1
            if repo.has_docker:
                total_complexity_hits += 1
            if repo.has_tests:
                total_complexity_hits += 1

            # Multiple technologies in single repo → complex project
            if len(repo.detected_technologies) >= 5:
                total_complexity_hits += 2
            elif len(repo.detected_technologies) >= 3:
                total_complexity_hits += 1

            # Complexity from descriptions and README
            desc = (repo.description or "").lower()
            readme = repo.readme_content.lower() if repo.readme_content else ""
            combined = desc + " " + readme
            total_complexity_hits += sum(
                1 for term in _COMPLEXITY_TERMS if term in combined
            )

    complexity = min(100, total_complexity_hits * 8)

    # Deployment signals (0-100)
    deploy_hits = sum(1 for sig in _DEPLOYMENT_SIGNALS if sig in lower)
    if github:
        if github.commit_frequency in ("daily", "weekly"):
            deploy_hits += 2
        repos_with_topics = sum(1 for r in github.notable_repos if r.topics)
        deploy_hits += repos_with_topics
        # Count repos with actual deployment indicators
        for repo in github.notable_repos:
            if repo.has_docker:
                deploy_hits += 2
            if repo.has_ci:
                deploy_hits += 2
            deploy_techs = {
                "Docker",
                "Kubernetes",
                "Heroku",
                "Vercel",
                "Netlify",
                "AWS",
                "Google Cloud",
                "Azure",
                "Nginx",
                "Terraform",
            }
            for tech in repo.detected_technologies:
                if tech in deploy_techs:
                    deploy_hits += 1
    deployment = min(100, deploy_hits * 8)

    # Project type balance (0-100): how many different types of projects
    types_found: set[str] = set()

    # Detect project types from structured resume projects
    _domain_to_ptype = {
        "ml": "data", "data": "data", "web": "web", "api": "api",
        "devops": "devops", "mobile": "mobile", "testing": "library",
    }
    for proj in resume_projects:
        domain = proj.get("domain", "general")
        ptype = _domain_to_ptype.get(domain)
        if ptype:
            types_found.add(ptype)
        # Also check technologies for project type
        proj_techs = set(proj.get("technologies", []))
        if proj_techs & _DOMAIN_TECH_MAP.get("web", set()):
            types_found.add("web")
        if proj_techs & _DOMAIN_TECH_MAP.get("api", set()):
            types_found.add("api")
        if proj_techs & _DOMAIN_TECH_MAP.get("ml", set()):
            types_found.add("data")
        if proj_techs & _DOMAIN_TECH_MAP.get("devops", set()):
            types_found.add("devops")
        if proj_techs & _DOMAIN_TECH_MAP.get("mobile", set()):
            types_found.add("mobile")

    # Fallback: keyword matching on full text
    for ptype, keywords in _PROJECT_TYPES.items():
        if any(kw in lower for kw in keywords):
            types_found.add(ptype)

    # Also detect project types from GitHub repo data
    if github:
        for repo in github.notable_repos:
            desc = (repo.description or "").lower()
            name = repo.name.lower().replace("-", " ").replace("_", " ")
            readme = repo.readme_content.lower()[:500] if repo.readme_content else ""
            combined = desc + " " + name + " " + readme + " " + " ".join(repo.topics)

            for ptype, keywords in _PROJECT_TYPES.items():
                if any(kw in combined for kw in keywords):
                    types_found.add(ptype)

            # Also detect by technologies
            repo_techs = {t.lower() for t in repo.detected_technologies}
            if repo_techs & {
                "react",
                "vue",
                "angular",
                "svelte",
                "next.js",
                "html",
                "css",
                "tailwindcss",
            }:
                types_found.add("web")
            if repo_techs & {
                "django",
                "flask",
                "fastapi",
                "express.js",
                "nestjs",
                "spring boot",
            }:
                types_found.add("api")
            if repo_techs & {
                "tensorflow",
                "pytorch",
                "scikit-learn",
                "keras",
                "opencv",
                "pandas",
                "numpy",
            }:
                types_found.add("data")
            if repo_techs & {"react native", "flutter", "swift", "kotlin"}:
                types_found.add("mobile")
            if repo_techs & {
                "docker",
                "kubernetes",
                "terraform",
                "ansible",
                "ci/cd",
                "github actions",
            }:
                types_found.add("devops")

    type_balance = min(100, len(types_found) * 20)

    # Overall portfolio depth
    overall = int(
        tech_div * 0.25
        + complexity * 0.25
        + deployment * 0.20
        + type_balance * 0.20
        + min(100, project_count * 10) * 0.10
    )
    overall = max(0, min(100, overall))

    # Summary
    parts: list[str] = []
    if project_count >= 10:
        parts.append(f"Rich portfolio with {project_count}+ projects")
    elif project_count >= 5:
        parts.append(f"Solid portfolio with {project_count} projects")
    elif project_count >= 2:
        parts.append(f"Portfolio with {project_count} projects")
    elif project_count == 1:
        parts.append("Portfolio with 1 project")
    else:
        parts.append("No distinct projects detected")

    if len(types_found) >= 3:
        parts.append(f"spanning {len(types_found)} project types")
    if len(unique_techs) >= 8:
        parts.append(f"using {len(unique_techs)} technologies")

    summary = "; ".join(parts).capitalize() + "."

    return PortfolioDepthScore(
        overall=overall,
        project_count=project_count,
        technology_diversity=tech_div,
        complexity_score=complexity,
        deployment_signals=deployment,
        project_type_balance=type_balance,
        summary=summary,
    )


# ── Skill Gap Analysis Engine ───────────────────────────

# Target role skill templates.
_ROLE_TEMPLATES: dict[str, dict[str, str]] = {
    "frontend_engineer": {
        "javascript": "advanced",
        "typescript": "advanced",
        "react": "advanced",
        "html": "intermediate",
        "css": "intermediate",
        "tailwind": "intermediate",
        "webpack": "intermediate",
        "git": "intermediate",
        "testing": "intermediate",
        "responsive design": "intermediate",
    },
    "backend_engineer": {
        "python": "advanced",
        "sql": "advanced",
        "rest api": "intermediate",
        "docker": "intermediate",
        "git": "intermediate",
        "postgresql": "intermediate",
        "redis": "intermediate",
        "linux": "intermediate",
        "testing": "intermediate",
        "ci/cd": "intermediate",
    },
    "fullstack_engineer": {
        "javascript": "advanced",
        "typescript": "intermediate",
        "react": "intermediate",
        "node.js": "intermediate",
        "sql": "intermediate",
        "git": "intermediate",
        "docker": "intermediate",
        "html": "intermediate",
        "css": "intermediate",
        "rest api": "intermediate",
    },
    "ml_engineer": {
        "python": "advanced",
        "tensorflow": "intermediate",
        "pytorch": "intermediate",
        "scikit-learn": "intermediate",
        "pandas": "intermediate",
        "sql": "intermediate",
        "docker": "intermediate",
        "git": "intermediate",
        "linux": "intermediate",
        "statistics": "intermediate",
    },
    "devops_engineer": {
        "docker": "advanced",
        "kubernetes": "advanced",
        "terraform": "intermediate",
        "aws": "intermediate",
        "linux": "advanced",
        "ci/cd": "advanced",
        "git": "intermediate",
        "python": "intermediate",
        "bash": "intermediate",
        "monitoring": "intermediate",
    },
    "data_engineer": {
        "python": "advanced",
        "sql": "advanced",
        "apache spark": "intermediate",
        "kafka": "intermediate",
        "docker": "intermediate",
        "aws": "intermediate",
        "git": "intermediate",
        "postgresql": "intermediate",
        "data pipeline": "intermediate",
        "etl": "intermediate",
    },
}

_ROLE_DISPLAY_NAMES: dict[str, str] = {
    "frontend_engineer": "Frontend Engineer",
    "backend_engineer": "Backend Engineer",
    "fullstack_engineer": "Fullstack Engineer",
    "ml_engineer": "ML Engineer",
    "devops_engineer": "DevOps Engineer",
    "data_engineer": "Data Engineer",
}

_PROF_ORDER = {"advanced": 3, "intermediate": 2, "beginner": 1, "": 0}


def compute_skill_gaps(
    skills: list[Skill],
    resume_text: str,
    target_role: str | None = None,
) -> SkillGapResult:
    """Compare detected skills against a target role template.

    If no target_role is given, automatically selects the best-fit role.
    """
    skill_map: dict[str, str] = {}
    for s in skills:
        skill_map[s.name.lower()] = s.proficiency

    # Also check resume text for keywords
    lower = resume_text.lower() if resume_text else ""

    # Auto-detect best role if not specified
    if not target_role or target_role not in _ROLE_TEMPLATES:
        target_role = _auto_detect_role(skills, resume_text)

    template = _ROLE_TEMPLATES[target_role]
    role_display = _ROLE_DISPLAY_NAMES.get(
        target_role, target_role.replace("_", " ").title()
    )

    matched: list[SkillMatch] = []
    missing: list[SkillMatch] = []
    partial: list[SkillMatch] = []

    for req_skill, req_level in template.items():
        # Check if user has this skill (with fuzzy matching)
        user_prof = _find_skill_match(req_skill, skill_map, lower)

        display_name = _DISPLAY_NAME_MAP.get(req_skill, req_skill.title())

        if user_prof is None:
            missing.append(
                SkillMatch(
                    skill=display_name,
                    status="gap",
                    proficiency="",
                    required_level=req_level,
                )
            )
        elif _PROF_ORDER.get(user_prof, 0) >= _PROF_ORDER.get(req_level, 0):
            matched.append(
                SkillMatch(
                    skill=display_name,
                    status="matched",
                    proficiency=user_prof,
                    required_level=req_level,
                )
            )
        else:
            partial.append(
                SkillMatch(
                    skill=display_name,
                    status="partial",
                    proficiency=user_prof,
                    required_level=req_level,
                )
            )

    total = len(template)
    match_pct = int((len(matched) + len(partial) * 0.5) / total * 100) if total else 0

    summary_parts: list[str] = [f"{match_pct}% match for {role_display}"]
    if matched:
        summary_parts.append(f"{len(matched)} skills fully matched")
    if partial:
        summary_parts.append(f"{len(partial)} skills need leveling up")
    if missing:
        summary_parts.append(f"{len(missing)} skills to learn")

    return SkillGapResult(
        target_role=role_display,
        match_percentage=match_pct,
        matched_skills=matched,
        missing_skills=missing,
        partial_skills=partial,
        summary=". ".join(summary_parts) + ".",
    )


def _auto_detect_role(skills: list[Skill], resume_text: str) -> str:
    """Auto-detect the best-fit target role based on current skills."""
    lower = resume_text.lower() if resume_text else ""
    skill_names = {s.name.lower() for s in skills}

    scores: dict[str, float] = {}
    for role, template in _ROLE_TEMPLATES.items():
        role_score = 0.0
        for req_skill in template:
            if _find_skill_match(
                req_skill, {s: "intermediate" for s in skill_names}, lower
            ):
                role_score += 1
        scores[role] = role_score / len(template)

    return max(scores, key=lambda k: scores[k]) if scores else "fullstack_engineer"


def _find_skill_match(
    target: str,
    skill_map: dict[str, str],
    resume_lower: str,
) -> str | None:
    """Find if a target skill matches any user skill (with aliases)."""
    # Direct match
    if target in skill_map:
        return skill_map[target]

    # Alias matching
    aliases: dict[str, list[str]] = {
        "node.js": ["nodejs", "node"],
        "react": ["react.js", "reactjs"],
        "vue": ["vue.js", "vuejs"],
        "postgresql": ["postgres"],
        "kubernetes": ["k8s"],
        "testing": ["unit test", "pytest", "jest", "mocha", "testing"],
        "rest api": ["rest", "restful", "api"],
        "ci/cd": ["github actions", "jenkins", "gitlab ci", "circleci"],
        "bash": ["shell"],
        "monitoring": ["prometheus", "grafana", "datadog"],
        "statistics": ["data analysis", "data science"],
        "responsive design": ["css", "tailwind", "bootstrap"],
    }

    check_targets = [target]
    if target in aliases:
        check_targets.extend(aliases[target])

    for alias in check_targets:
        if alias in skill_map:
            return skill_map[alias]

    # Check resume text as last resort
    for alias in check_targets:
        if len(alias) > 2 and alias in resume_lower:
            return "beginner"

    return None


# ── Learning Roadmap ─────────────────────────────────────

_LEARNING_RESOURCES: dict[str, list[LearningResource]] = {
    "python": [
        LearningResource(
            name="Python.org tutorial", url="https://docs.python.org/3/tutorial/"
        ),
        LearningResource(
            name="Automate the Boring Stuff", url="https://automatetheboringstuff.com/"
        ),
        LearningResource(name="Real Python", url="https://realpython.com/"),
    ],
    "javascript": [
        LearningResource(
            name="MDN Web Docs",
            url="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        ),
        LearningResource(name="JavaScript.info", url="https://javascript.info/"),
        LearningResource(
            name="freeCodeCamp",
            url="https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/",
        ),
    ],
    "typescript": [
        LearningResource(
            name="TypeScript Handbook",
            url="https://www.typescriptlang.org/docs/handbook/",
        ),
        LearningResource(
            name="TypeScript Deep Dive", url="https://basarat.gitbook.io/typescript/"
        ),
    ],
    "react": [
        LearningResource(name="React.dev", url="https://react.dev/learn"),
        LearningResource(
            name="React Tutorial", url="https://react.dev/learn/tutorial-tic-tac-toe"
        ),
        LearningResource(name="Next.js Learn", url="https://nextjs.org/learn"),
    ],
    "docker": [
        LearningResource(
            name="Docker Getting Started", url="https://docs.docker.com/get-started/"
        ),
        LearningResource(
            name="Docker Curriculum", url="https://docker-curriculum.com/"
        ),
        LearningResource(
            name="Play with Docker", url="https://labs.play-with-docker.com/"
        ),
    ],
    "kubernetes": [
        LearningResource(
            name="Kubernetes.io tutorials", url="https://kubernetes.io/docs/tutorials/"
        ),
        LearningResource(
            name="KodeKloud",
            url="https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners/",
        ),
        LearningResource(
            name="Kubernetes the Hard Way",
            url="https://github.com/kelseyhightower/kubernetes-the-hard-way",
        ),
    ],
    "aws": [
        LearningResource(name="AWS Skill Builder", url="https://skillbuilder.aws/"),
        LearningResource(name="AWS Documentation", url="https://docs.aws.amazon.com/"),
        LearningResource(
            name="AWS Well-Architected",
            url="https://aws.amazon.com/architecture/well-architected/",
        ),
    ],
    "sql": [
        LearningResource(name="SQLBolt", url="https://sqlbolt.com/"),
        LearningResource(
            name="Mode SQL Tutorial", url="https://mode.com/sql-tutorial/"
        ),
        LearningResource(
            name="PostgreSQL Tutorial", url="https://www.postgresqltutorial.com/"
        ),
    ],
    "git": [
        LearningResource(name="Pro Git book", url="https://git-scm.com/book/en/v2"),
        LearningResource(
            name="Learn Git Branching", url="https://learngitbranching.js.org/"
        ),
        LearningResource(name="GitHub Skills", url="https://skills.github.com/"),
    ],
    "terraform": [
        LearningResource(
            name="Terraform Learn",
            url="https://developer.hashicorp.com/terraform/tutorials",
        ),
        LearningResource(
            name="HashiCorp tutorials", url="https://developer.hashicorp.com/tutorials"
        ),
    ],
    "ci/cd": [
        LearningResource(
            name="GitHub Actions docs", url="https://docs.github.com/en/actions"
        ),
        LearningResource(
            name="CI/CD with GitHub Actions",
            url="https://docs.github.com/en/actions/use-cases-and-examples/building-and-testing",
        ),
    ],
    "testing": [
        LearningResource(
            name="pytest documentation", url="https://docs.pytest.org/en/stable/"
        ),
        LearningResource(
            name="Testing Best Practices", url="https://testingjavascript.com/"
        ),
    ],
    "tensorflow": [
        LearningResource(
            name="TensorFlow tutorials", url="https://www.tensorflow.org/tutorials"
        ),
        LearningResource(
            name="Coursera ML Specialization",
            url="https://www.coursera.org/specializations/machine-learning-introduction",
        ),
    ],
    "pytorch": [
        LearningResource(
            name="PyTorch tutorials", url="https://pytorch.org/tutorials/"
        ),
        LearningResource(name="Fast.ai course", url="https://course.fast.ai/"),
    ],
    "linux": [
        LearningResource(name="Linux Journey", url="https://linuxjourney.com/"),
        LearningResource(
            name="OverTheWire Bandit", url="https://overthewire.org/wargames/bandit/"
        ),
    ],
    "scikit-learn": [
        LearningResource(
            name="Scikit-Learn documentation",
            url="https://scikit-learn.org/stable/tutorial/",
        ),
        LearningResource(
            name="Scikit-Learn User Guide",
            url="https://scikit-learn.org/stable/user_guide.html",
        ),
    ],
    "pandas": [
        LearningResource(
            name="Pandas documentation",
            url="https://pandas.pydata.org/docs/getting_started/",
        ),
        LearningResource(
            name="Kaggle Pandas course", url="https://www.kaggle.com/learn/pandas"
        ),
    ],
    "statistics": [
        LearningResource(
            name="Khan Academy Statistics",
            url="https://www.khanacademy.org/math/statistics-probability",
        ),
        LearningResource(
            name="Think Stats", url="https://greenteapress.com/thinkstats2/html/"
        ),
    ],
}

_SKILL_LEARNING_WEEKS: dict[str, int] = {
    "beginner_to_intermediate": 6,
    "intermediate_to_advanced": 10,
    "none_to_beginner": 4,
    "none_to_intermediate": 8,
}


def _get_resources(skill_name: str) -> list[LearningResource]:
    """Get learning resources for a skill, with fallback to generic resources."""
    skill_lower = skill_name.lower()
    if skill_lower in _LEARNING_RESOURCES:
        return _LEARNING_RESOURCES[skill_lower]
    # Fallback: link to a documentation search
    safe_name = skill_name.replace(" ", "+")
    return [
        LearningResource(
            name=f"{skill_name} official documentation",
            url=f"https://devdocs.io/search?q={safe_name}",
        ),
        LearningResource(
            name=f"Learn {skill_name}",
            url=f"https://www.freecodecamp.org/news/search/?query={safe_name}",
        ),
    ]


def generate_learning_roadmap(
    skill_gap: SkillGapResult,
) -> LearningRoadmapResult:
    """Generate a structured learning roadmap from skill gap analysis."""
    steps: list[LearningStep] = []
    order = 1

    # First: partial skills (already have some knowledge, faster to level up)
    for sm in skill_gap.partial_skills:
        current = sm.proficiency or "beginner"
        target = sm.required_level or "intermediate"
        key = f"{current}_to_{target}"
        weeks = _SKILL_LEARNING_WEEKS.get(key, 6)
        resources = _get_resources(sm.skill)

        steps.append(
            LearningStep(
                order=order,
                skill=sm.skill,
                current_level=current,
                target_level=target,
                resources=resources[:3],
                estimated_weeks=weeks,
            )
        )
        order += 1

    # Then: missing skills (need to learn from scratch)
    for sm in skill_gap.missing_skills:
        target = sm.required_level or "intermediate"
        key = f"none_to_{target}"
        weeks = _SKILL_LEARNING_WEEKS.get(key, 8)
        resources = _get_resources(sm.skill)

        steps.append(
            LearningStep(
                order=order,
                skill=sm.skill,
                current_level="none",
                target_level=target,
                resources=resources[:3],
                estimated_weeks=weeks,
            )
        )
        order += 1

    total_weeks = sum(s.estimated_weeks for s in steps)

    summary = (
        f"Learning roadmap for {skill_gap.target_role}: "
        f"{len(steps)} skills to develop over approximately {total_weeks} weeks."
    )

    return LearningRoadmapResult(
        target_role=skill_gap.target_role,
        steps=steps,
        total_estimated_weeks=total_weeks,
        summary=summary,
    )


# ── Market Demand Analysis ───────────────────────────────

# Simplified market demand data (in production, this would come from an API/dataset)
_MARKET_DEMAND: dict[str, tuple[str, str]] = {
    # (demand_level, trend)
    "python": ("high", "rising"),
    "javascript": ("high", "stable"),
    "typescript": ("high", "rising"),
    "react": ("high", "stable"),
    "next.js": ("high", "rising"),
    "node.js": ("high", "stable"),
    "docker": ("high", "rising"),
    "kubernetes": ("high", "rising"),
    "aws": ("high", "stable"),
    "azure": ("high", "rising"),
    "gcp": ("medium", "rising"),
    "terraform": ("high", "rising"),
    "go": ("high", "rising"),
    "rust": ("medium", "rising"),
    "java": ("high", "stable"),
    "c#": ("high", "stable"),
    "sql": ("high", "stable"),
    "postgresql": ("high", "stable"),
    "mongodb": ("medium", "stable"),
    "redis": ("medium", "stable"),
    "graphql": ("medium", "stable"),
    "ci/cd": ("high", "rising"),
    "git": ("high", "stable"),
    "linux": ("high", "stable"),
    "tensorflow": ("medium", "stable"),
    "pytorch": ("high", "rising"),
    "machine learning": ("high", "rising"),
    "deep learning": ("high", "rising"),
    "llm": ("high", "rising"),
    "langchain": ("medium", "rising"),
    "fastapi": ("medium", "rising"),
    "django": ("medium", "stable"),
    "flask": ("medium", "stable"),
    "vue": ("medium", "stable"),
    "angular": ("medium", "declining"),
    "svelte": ("medium", "rising"),
    "tailwind": ("high", "rising"),
    "ruby": ("low", "declining"),
    "php": ("medium", "declining"),
    "perl": ("low", "declining"),
    "jquery": ("low", "declining"),
}


def compute_market_demand(
    skills: list[Skill],
    resume_text: str,
) -> MarketDemandResult:
    """Compare user skills against market demand data."""
    lower = resume_text.lower() if resume_text else ""
    user_skills: set[str] = set()
    for s in skills:
        user_skills.add(s.name.lower())

    high_demand_matches: list[MarketSkillDemand] = []
    missing_high_demand: list[MarketSkillDemand] = []

    for skill_key, (demand, trend) in _MARKET_DEMAND.items():
        has_skill = skill_key in user_skills or (
            len(skill_key) > 2 and skill_key in lower
        )
        display = _DISPLAY_NAME_MAP.get(skill_key, skill_key.title())

        entry = MarketSkillDemand(
            skill=display,
            demand_level=demand,
            trend=trend,
            user_has=has_skill,
        )

        if has_skill and demand in ("high", "medium"):
            high_demand_matches.append(entry)
        elif not has_skill and demand == "high":
            missing_high_demand.append(entry)

    # Sort: high-demand rising first
    trend_order = {"rising": 0, "stable": 1, "declining": 2}
    high_demand_matches.sort(key=lambda x: trend_order.get(x.trend, 1))
    missing_high_demand.sort(key=lambda x: trend_order.get(x.trend, 1))

    # Market readiness score
    total_high = sum(1 for _, (d, _) in _MARKET_DEMAND.items() if d == "high")
    matched_high = sum(1 for m in high_demand_matches if m.demand_level == "high")
    readiness = int(matched_high / max(1, total_high) * 100)

    summary_parts: list[str] = [f"{readiness}% market readiness"]
    if high_demand_matches:
        summary_parts.append(f"{len(high_demand_matches)} in-demand skills matched")
    if missing_high_demand:
        rising_missing = [m for m in missing_high_demand if m.trend == "rising"]
        if rising_missing:
            names = ", ".join(m.skill for m in rising_missing[:3])
            summary_parts.append(f"trending skills to learn: {names}")

    return MarketDemandResult(
        high_demand_matches=high_demand_matches[:10],
        missing_high_demand=missing_high_demand[:10],
        market_readiness=readiness,
        summary=". ".join(summary_parts) + ".",
    )


# ── Career Direction Engine ──────────────────────────────

_CAREER_PATHS: dict[str, dict[str, list[str] | str]] = {
    "Frontend Engineer": {
        "matching": [
            "javascript",
            "typescript",
            "react",
            "vue",
            "angular",
            "html",
            "css",
            "tailwind",
            "next.js",
            "svelte",
        ],
        "to_develop": [
            "system design",
            "testing",
            "performance optimization",
            "accessibility",
        ],
        "description": "Build user interfaces and interactive web experiences",
    },
    "Backend Engineer": {
        "matching": [
            "python",
            "java",
            "go",
            "rust",
            "node.js",
            "sql",
            "postgresql",
            "redis",
            "docker",
            "rest api",
        ],
        "to_develop": [
            "system design",
            "distributed systems",
            "message queues",
            "caching",
        ],
        "description": "Design and build server-side systems, APIs, and data processing",
    },
    "Fullstack Engineer": {
        "matching": [
            "javascript",
            "typescript",
            "react",
            "node.js",
            "python",
            "sql",
            "html",
            "css",
            "docker",
            "git",
        ],
        "to_develop": ["devops", "cloud", "system design", "mobile development"],
        "description": "Work across the entire stack from frontend to backend and deployment",
    },
    "ML Engineer": {
        "matching": [
            "python",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "pandas",
            "numpy",
            "machine learning",
            "deep learning",
        ],
        "to_develop": [
            "mlops",
            "distributed training",
            "model serving",
            "data engineering",
        ],
        "description": "Build and deploy machine learning models at scale",
    },
    "DevOps Engineer": {
        "matching": [
            "docker",
            "kubernetes",
            "terraform",
            "aws",
            "linux",
            "ci/cd",
            "bash",
            "python",
            "git",
        ],
        "to_develop": [
            "security",
            "networking",
            "cost optimization",
            "site reliability",
        ],
        "description": "Automate infrastructure, deployments, and operational processes",
    },
    "Data Engineer": {
        "matching": [
            "python",
            "sql",
            "apache spark",
            "kafka",
            "aws",
            "docker",
            "postgresql",
            "etl",
        ],
        "to_develop": [
            "data modeling",
            "stream processing",
            "data governance",
            "orchestration",
        ],
        "description": "Build data pipelines and infrastructure for analytics and ML",
    },
    "Mobile Developer": {
        "matching": [
            "react native",
            "flutter",
            "swift",
            "kotlin",
            "dart",
            "javascript",
            "typescript",
        ],
        "to_develop": [
            "app store optimization",
            "push notifications",
            "offline-first",
            "animation",
        ],
        "description": "Build native and cross-platform mobile applications",
    },
    "Cloud Architect": {
        "matching": [
            "aws",
            "azure",
            "gcp",
            "terraform",
            "kubernetes",
            "docker",
            "linux",
            "networking",
        ],
        "to_develop": [
            "cost optimization",
            "compliance",
            "disaster recovery",
            "multi-cloud",
        ],
        "description": "Design and manage cloud infrastructure at enterprise scale",
    },
}


def compute_career_direction(
    skills: list[Skill],
    resume_text: str,
    radar_scores: RadarScores | None = None,
) -> CareerDirectionResult:
    """Suggest career paths based on skill distribution and radar scores."""
    skill_names = {s.name.lower() for s in skills}
    lower = resume_text.lower() if resume_text else ""

    career_paths: list[CareerPathSuggestion] = []

    for role, config in _CAREER_PATHS.items():
        matching_skills: list[str] = []
        for skill_key in config["matching"]:
            display = _DISPLAY_NAME_MAP.get(skill_key, skill_key.title())
            if skill_key in skill_names or (len(skill_key) > 2 and skill_key in lower):
                matching_skills.append(display)

        fit = int(len(matching_skills) / max(1, len(config["matching"])) * 100)

        # Boost fit based on radar scores
        if radar_scores:
            if role in ("Frontend Engineer",) and radar_scores.frontend >= 50:
                fit = min(100, fit + 10)
            elif role in ("Backend Engineer",) and radar_scores.backend >= 50:
                fit = min(100, fit + 10)
            elif role in ("ML Engineer",) and radar_scores.ml_ai >= 50:
                fit = min(100, fit + 10)
            elif (
                role in ("DevOps Engineer", "Cloud Architect")
                and radar_scores.devops >= 50
            ):
                fit = min(100, fit + 10)
            elif role in ("Data Engineer",) and radar_scores.data >= 50:
                fit = min(100, fit + 10)

        skills_to_develop: list[str] = []
        for dev_skill in config["to_develop"]:
            if dev_skill.lower() not in skill_names:
                skills_to_develop.append(dev_skill.title())

        career_paths.append(
            CareerPathSuggestion(
                role=role,
                fit_score=fit,
                matching_skills=matching_skills,
                skills_to_develop=skills_to_develop[:4],
                description=str(config["description"]),
            )
        )

    # Sort by fit score descending
    career_paths.sort(key=lambda x: x.fit_score, reverse=True)

    primary = career_paths[0].role if career_paths else "General Software Engineer"

    top_paths = career_paths[:3]
    summary = f"Best fit: {primary} ({top_paths[0].fit_score}% match). "
    if len(top_paths) > 1:
        alt = ", ".join(p.role for p in top_paths[1:3])
        summary += f"Also suited for: {alt}."

    return CareerDirectionResult(
        primary_direction=primary,
        career_paths=career_paths,
        summary=summary,
    )
