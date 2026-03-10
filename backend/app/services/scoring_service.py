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

import re

from app.models.enums import CommitFrequency, Proficiency
from app.models.schemas import (
    AiInsights,
    DeveloperScore,
    GitHubSummary,
    ProgrammingLanguageScore,
    RadarScores,
    ScoreBreakdown,
    Skill,
    SkillCategoryBreakdown,
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
    "docs": [
        "readme",
        "documentation",
        "technical writing",
        "api docs",
        "swagger",
        "openapi",
        "jsdoc",
        "sphinx",
        "mkdocs",
        "confluence",
        "wiki",
        "storybook",
        "typedoc",
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


def extract_skills_from_text(resume_text: str) -> list[Skill]:
    """Extract skills from resume text using keyword matching.

    Used as a fallback when AI extraction produces few or no results.
    """
    if not resume_text:
        return []

    lower = resume_text.lower()
    skills: list[Skill] = []
    seen: set[str] = set()

    for category, skill_list in _KNOWN_SKILLS.items():
        for skill_name in skill_list:
            # Skip very short names to avoid false positives
            if len(skill_name) <= 2:
                continue
            if skill_name not in lower:
                continue

            display = _DISPLAY_NAME_MAP.get(skill_name, skill_name.title())
            key = display.lower()
            if key in seen:
                continue
            seen.add(key)

            proficiency = _estimate_proficiency_from_text(skill_name, resume_text)
            skills.append(
                Skill(
                    name=display,
                    category=category,
                    proficiency=proficiency,
                    source="resume",
                )
            )

    return skills


def _estimate_proficiency_from_text(skill_name: str, resume_text: str) -> Proficiency:
    """Estimate proficiency from surrounding context in resume text."""
    lower = resume_text.lower()
    idx = lower.find(skill_name.lower())
    if idx == -1:
        return Proficiency.INTERMEDIATE

    start = max(0, idx - 200)
    end = min(len(lower), idx + len(skill_name) + 200)
    context = lower[start:end]

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
    ]
    if any(clue in context for clue in advanced_clues):
        return Proficiency.ADVANCED

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
    ]
    if any(clue in context for clue in beginner_clues):
        return Proficiency.BEGINNER

    return Proficiency.INTERMEDIATE


# ── Radar score computation ──────────────────────────────


def compute_radar_scores(skills: list[Skill], resume_text: str) -> RadarScores:
    """Compute radar chart scores from detected skills and resume text."""
    lower = resume_text.lower() if resume_text else ""
    scores: dict[str, int] = {}

    for category, keywords in _RADAR_SKILL_MAP.items():
        matched_skills = [
            s for s in skills if any(kw in s.name.lower() for kw in keywords)
        ]
        text_matches = sum(1 for kw in keywords if kw in lower)
        prof_bonus = sum(
            3
            if s.proficiency == Proficiency.ADVANCED
            else 1
            if s.proficiency == Proficiency.INTERMEDIATE
            else 0
            for s in matched_skills
        )
        raw = len(matched_skills) * 15 + text_matches * 5 + prof_bonus * 5
        scores[category] = min(100, raw)

    return RadarScores(**scores)


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
    """Extract programming languages from skills and resume text."""
    languages: dict[str, ProgrammingLanguageScore] = {}

    # From extracted skills
    for skill in skills:
        key = skill.name.lower()
        if skill.category == "language" and key in _KNOWN_LANGUAGES:
            canonical = _KNOWN_LANGUAGES[key]
            if canonical not in languages:
                languages[canonical] = ProgrammingLanguageScore(
                    name=canonical,
                    proficiency=skill.proficiency,
                    confidence=0.9,
                    context=f"Detected from {skill.source}",
                )

    # From resume text (fallback for non-obvious names)
    if resume_text:
        lower = resume_text.lower()
        for key, canonical in _KNOWN_LANGUAGES.items():
            if canonical in languages or len(key) <= 2:
                continue
            if key not in lower:
                continue
            prof = _estimate_proficiency_from_text(key, resume_text)
            languages[canonical] = ProgrammingLanguageScore(
                name=canonical,
                proficiency=prof,
                confidence=0.6,
                context="Detected from resume text",
            )

    order = {"advanced": 0, "intermediate": 1, "beginner": 2}
    return sorted(
        languages.values(),
        key=lambda x: (order.get(x.proficiency, 1), -x.confidence),
    )


# ── AI Insights generation ──────────────────────────────


def generate_ai_insights(
    categories: dict[str, int],
    skills: list[Skill],
    github: GitHubSummary | None,
    overall: int,
) -> AiInsights:
    """Generate structured insights from scoring results."""
    strengths: list[str] = []
    weaknesses: list[str] = []
    improvements: list[str] = []

    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    for name, value in sorted_cats:
        label = name.replace("_", " ").title()
        if value >= 70:
            strengths.append(f"Strong {label.lower()} ({value}/100)")
        elif value >= 50:
            strengths.append(f"Good {label.lower()} ({value}/100)")
        if len(strengths) >= 3:
            break

    for name, value in reversed(sorted_cats):
        label = name.replace("_", " ").title()
        if value < 50:
            weaknesses.append(f"{label} needs improvement ({value}/100)")
        if len(weaknesses) >= 3:
            break

    # Skill-based insights
    tech_skills = [s for s in skills if s.category != "soft_skill"]
    advanced_skills = [s for s in tech_skills if s.proficiency == "advanced"]
    skill_categories = {s.category for s in tech_skills}

    if len(advanced_skills) >= 3:
        names = ", ".join(s.name for s in advanced_skills[:3])
        strengths.append(f"Deep expertise in {names}")
    if len(skill_categories) >= 4:
        strengths.append(
            f"Well-rounded skill set across {len(skill_categories)} categories"
        )

    if len(tech_skills) < 5:
        weaknesses.append("Limited technical skills detected")
        improvements.append("Add more technical skills and tools to your resume")

    if not any(s.category == "cloud" for s in skills):
        improvements.append(
            "Consider adding cloud platform experience (AWS, Azure, GCP)"
        )
    if categories.get("impact_quantification", 0) < 40:
        improvements.append(
            "Add measurable impact metrics (percentages, numbers, revenue)"
        )
    if categories.get("formatting_quality", 0) < 50:
        improvements.append(
            "Improve resume formatting with clear headings and bullet points"
        )
    if github is None:
        improvements.append("Link a GitHub profile to showcase code and projects")

    # Career potential
    if overall >= 75:
        career = (
            "Strong profile suited for senior engineering roles. "
            "Consider leadership opportunities and open-source contributions."
        )
    elif overall >= 55:
        career = (
            "Solid foundation for mid-level positions. "
            "Deepen one specialty and build 2-3 showcase projects to reach senior level."
        )
    elif overall >= 35:
        career = (
            "Growing developer profile with clear potential. "
            "Build more projects, contribute to open source, and expand your skill set."
        )
    else:
        career = (
            "Early-career profile with room for growth. "
            "Focus on building projects and gaining practical experience."
        )

    return AiInsights(
        strengths=strengths[:5],
        weaknesses=weaknesses[:5],
        career_potential=career,
        recommended_improvements=improvements[:5],
    )


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
