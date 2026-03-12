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
    "github_activity": 0.15,
    "repo_quality": 0.15,
    "documentation": 0.10,
    "community": 0.10,
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
_GITHUB_METRICS = {"github_activity", "repo_quality", "documentation", "community"}

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
    """Extract skills from GitHub profile data: languages, topics, and repo metadata.

    Uses top_languages (with percentage-based proficiency), repo topics,
    and repo descriptions to build a skill list when no resume is available.
    """
    skills: list[Skill] = []
    seen: set[str] = set()

    # 1. From top_languages (percentage → proficiency)
    for lang, pct in github.top_languages.items():
        lang_lower = lang.lower()
        canonical = _KNOWN_LANGUAGES.get(lang_lower)
        if not canonical:
            # Try title-case key (GitHub returns e.g. "Python", "JavaScript")
            canonical = _KNOWN_LANGUAGES.get(lang_lower, lang)
        key = canonical.lower()
        if key in seen:
            continue
        seen.add(key)

        if pct >= 30:
            prof = Proficiency.ADVANCED
        elif pct >= 12:
            prof = Proficiency.INTERMEDIATE
        else:
            prof = Proficiency.BEGINNER

        skills.append(
            Skill(
                name=canonical,
                category=SkillCategory.LANGUAGE,
                proficiency=prof,
                source="github",
            )
        )

    # 2. From repo topics → match against _KNOWN_SKILLS
    all_topics: set[str] = set()
    for repo in github.notable_repos:
        for topic in repo.topics:
            all_topics.add(topic.lower().replace("-", " "))

    _category_map = {
        "language": SkillCategory.LANGUAGE,
        "framework": SkillCategory.FRAMEWORK,
        "tool": SkillCategory.TOOL,
        "database": SkillCategory.DATABASE,
        "cloud": SkillCategory.CLOUD,
    }

    for category, skill_list in _KNOWN_SKILLS.items():
        for skill_name in skill_list:
            if skill_name in seen:
                continue
            # Match topic exactly or as substring of topic
            matched = any(
                skill_name == topic or skill_name in topic for topic in all_topics
            )
            if not matched:
                continue
            display = _DISPLAY_NAME_MAP.get(skill_name, skill_name.title())
            seen.add(skill_name)
            skills.append(
                Skill(
                    name=display,
                    category=_category_map.get(category, SkillCategory.TOOL),
                    proficiency=Proficiency.INTERMEDIATE,
                    source="github",
                )
            )

    # 3. From repo languages (not captured in top_languages)
    for repo in github.notable_repos:
        if repo.language:
            lang_lower = repo.language.lower()
            canonical = _KNOWN_LANGUAGES.get(lang_lower, repo.language)
            key = canonical.lower()
            if key not in seen:
                seen.add(key)
                skills.append(
                    Skill(
                        name=canonical,
                        category=SkillCategory.LANGUAGE,
                        proficiency=Proficiency.BEGINNER,
                        source="github",
                    )
                )

    # 4. Detect frameworks/tools from repo descriptions and names
    repo_text_parts: list[str] = []
    for repo in github.notable_repos:
        if repo.description:
            repo_text_parts.append(repo.description.lower())
        repo_text_parts.append(repo.name.lower().replace("-", " ").replace("_", " "))
    repo_text = " ".join(repo_text_parts)

    for category, skill_list in _KNOWN_SKILLS.items():
        if category == "language":
            continue  # Already handled above
        for skill_name in skill_list:
            if skill_name in seen or len(skill_name) <= 2:
                continue
            if _skill_present_in_text(skill_name, repo_text):
                display = _DISPLAY_NAME_MAP.get(skill_name, skill_name.title())
                seen.add(skill_name)
                skills.append(
                    Skill(
                        name=display,
                        category=_category_map.get(category, SkillCategory.TOOL),
                        proficiency=Proficiency.INTERMEDIATE,
                        source="github",
                    )
                )

    return skills


def extract_skills_from_text(resume_text: str) -> list[Skill]:
    """Extract skills from resume text using keyword matching with contextual analysis.

    Used as a fallback when AI extraction produces few or no results.
    Uses frequency, surrounding context, and section importance to determine
    proficiency rather than simple keyword presence.
    Applies word-boundary matching to avoid false positives.
    """
    if not resume_text:
        return []

    lower = resume_text.lower()
    skills: list[Skill] = []
    seen: set[str] = set()

    # Detect resume sections for section-aware weighting
    section_weights = _detect_section_context(resume_text)

    for category, skill_list in _KNOWN_SKILLS.items():
        for skill_name in skill_list:
            # Skip very short names to avoid false positives
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

    Uses a weighted approach:
    - Skills matched in project/experience context score higher than
      simple keyword presence in text.
    - Each skill contributes to only its primary category to avoid
      double-counting (e.g., Python only counts under backend, not data).
    - Proficiency level affects the contribution.
    - GitHub languages and topics contribute when resume text is absent.
    """
    lower = resume_text.lower() if resume_text else ""
    scores: dict[str, float] = {cat: 0.0 for cat in _RADAR_SKILL_MAP}

    # Track which skills have already been assigned to a category
    assigned_skills: set[str] = set()

    # First pass: assign each skill to its best-matching category
    # based on both keyword match and skill object category
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
            continue

        # Pick the best category: prefer the one aligned with skill.category
        best_cat = matching_cats[0]
        if len(matching_cats) > 1:
            hints = skill_category_hints.get(skill.category, set())
            for cat in matching_cats:
                if cat in hints:
                    best_cat = cat
                    break

        # Proficiency-weighted contribution
        prof_weight = {
            Proficiency.ADVANCED: 20,
            Proficiency.INTERMEDIATE: 14,
            Proficiency.BEGINNER: 8,
        }
        scores[best_cat] += prof_weight.get(skill.proficiency, 14)
        assigned_skills.add(skill_lower)

    # Second pass: only count text mentions that appear in project/experience
    # context AND pass word-boundary matching (prevents false inflation)
    project_context = _has_project_context(lower)

    for cat, keywords in _RADAR_SKILL_MAP.items():
        for kw in keywords:
            if len(kw) <= 2:
                continue
            if kw in assigned_skills:
                continue
            # Only count keywords that are genuinely present as distinct terms
            if not _skill_present_in_text(kw, lower):
                continue
            # Only add score if the keyword appears in project/experience context
            if project_context.get(kw, False):
                scores[cat] += 5

    # Third pass: GitHub languages and topics (when no resume text available)
    if github:
        for lang, pct in github.top_languages.items():
            lang_lower = lang.lower()
            if lang_lower in assigned_skills:
                continue
            for cat, keywords in _RADAR_SKILL_MAP.items():
                if lang_lower in keywords:
                    # Weight by language percentage
                    if pct >= 30:
                        scores[cat] += 15
                    elif pct >= 12:
                        scores[cat] += 10
                    else:
                        scores[cat] += 5
                    assigned_skills.add(lang_lower)
                    break

        # Repo topics
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

    # Normalize to 0-100 with diminishing returns
    final: dict[str, int] = {}
    for cat, raw in scores.items():
        # Use log-based scaling: first few skills matter most
        if raw <= 0:
            final[cat] = 0
        else:
            # Scale so ~60 raw points = 80/100, ~100 raw = 95/100
            normalized = min(100, int(40 * math.log(1 + raw / 10)))
            final[cat] = normalized

    return RadarScores(**final)


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
    """Analyze portfolio depth based on actual project detection, tech diversity, and complexity."""
    lower = resume_text.lower() if resume_text else ""

    # Accurate project count via structural analysis
    project_count = _count_distinct_projects(resume_text, github)

    # Technology diversity (0-100)
    unique_techs: set[str] = set()
    for skill in skills:
        unique_techs.add(skill.name.lower())
    if github:
        for lang in github.top_languages:
            unique_techs.add(lang.lower())
    tech_div = min(100, len(unique_techs) * 7)

    # Complexity score (0-100): action verbs, architecture terms, scale indicators
    complexity_terms = [
        "architecture",
        "scalable",
        "distributed",
        "microservice",
        "caching",
        "queue",
        "concurrent",
        "async",
        "real-time",
        "optimization",
        "algorithm",
        "encryption",
        "authentication",
        "authorization",
        "rate limit",
        "load balanc",
        "database design",
        "system design",
    ]
    complexity_hits = sum(1 for term in complexity_terms if term in lower)
    complexity = min(100, complexity_hits * 12)

    # Deployment signals (0-100)
    deploy_hits = sum(1 for sig in _DEPLOYMENT_SIGNALS if sig in lower)
    if github:
        if github.commit_frequency in ("daily", "weekly"):
            deploy_hits += 2
        repos_with_topics = sum(1 for r in github.notable_repos if r.topics)
        deploy_hits += repos_with_topics
    deployment = min(100, deploy_hits * 10)

    # Project type balance (0-100): how many different types of projects
    types_found: set[str] = set()
    for ptype, keywords in _PROJECT_TYPES.items():
        if any(kw in lower for kw in keywords):
            types_found.add(ptype)
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
