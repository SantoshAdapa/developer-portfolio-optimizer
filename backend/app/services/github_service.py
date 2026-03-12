import asyncio
import logging
import re
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.models.enums import CommitFrequency
from app.models.schemas import GitHubSummary, RepoSummary

logger = logging.getLogger(__name__)

# ── In-memory cache for GitHub analysis results ──────────────
# username → (GitHubSummary, timestamp)
_github_cache: dict[str, tuple[GitHubSummary, float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes

_GITHUB_USERNAME_RE = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$")


def extract_username(value: str) -> str:
    """Normalise a GitHub username or profile URL into a plain username.

    Handles:
      - Plain username: ``octocat``
      - With @: ``@octocat``
      - Full URL: ``https://github.com/octocat``
      - URL with trailing path: ``https://github.com/octocat/repo``
    """
    value = value.strip().rstrip("/")

    # Strip URL portion if present
    if "github.com" in value:
        parsed = urlparse(value if "://" in value else f"https://{value}")
        path = parsed.path.strip("/")
        username = path.split("/")[0] if path else ""
    else:
        username = value.lstrip("@")

    if not username:
        raise ValueError("Could not extract GitHub username from input")

    if not _GITHUB_USERNAME_RE.match(username):
        raise ValueError(f"Invalid GitHub username format: {username}")

    return username


def _build_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


async def _github_get(
    client: httpx.AsyncClient, url: str, **kwargs: Any
) -> httpx.Response:
    """Wrapper around client.get that handles GitHub rate-limit responses."""
    resp = await client.get(url, headers=_build_headers(), **kwargs)
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        logger.warning("GitHub API rate-limit hit for %s", url)
        token_hint = (
            " Set a GITHUB_TOKEN environment variable to increase the limit."
            if not settings.github_token
            else ""
        )
        raise httpx.HTTPStatusError(
            f"GitHub API rate limit exceeded.{token_hint}",
            request=resp.request,
            response=resp,
        )
    return resp


async def fetch_user_profile(username: str) -> dict:
    """Fetch basic GitHub user profile."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await _github_get(
            client,
            f"{settings.github_api_base}/users/{username}",
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_repos(username: str, max_repos: int = 30) -> list[dict]:
    """Fetch public repos sorted by most recently pushed."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await _github_get(
            client,
            f"{settings.github_api_base}/users/{username}/repos",
            params={
                "sort": "pushed",
                "direction": "desc",
                "per_page": min(max_repos, 100),
                "type": "owner",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_recent_commits(username: str, repo_name: str) -> list[dict]:
    """Fetch recent commits for a single repo (last 30)."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await _github_get(
            client,
            f"{settings.github_api_base}/repos/{username}/{repo_name}/commits",
            params={"per_page": 30},
        )
        if resp.status_code != 200:
            return []
        return resp.json()


def _compute_language_distribution(repos: list[dict]) -> dict[str, float]:
    """Compute language % across repos (by count of repos using each language)."""
    counter: Counter[str] = Counter()
    for repo in repos:
        lang = repo.get("language")
        if lang:
            counter[lang] += 1
    total = sum(counter.values()) or 1
    return {
        lang: round(count / total * 100, 1) for lang, count in counter.most_common(10)
    }


def _determine_commit_frequency(commit_dates: list[datetime]) -> CommitFrequency:
    """Classify commit cadence from a list of commit timestamps."""
    if not commit_dates:
        return CommitFrequency.SPORADIC

    now = datetime.now(timezone.utc)
    recent = [d for d in commit_dates if (now - d).days <= 90]

    if len(recent) == 0:
        return CommitFrequency.SPORADIC

    weeks_active = max(1, len({d.isocalendar()[:2] for d in recent}))
    avg_per_week = len(recent) / weeks_active

    if avg_per_week >= 5:
        return CommitFrequency.DAILY
    if avg_per_week >= 1:
        return CommitFrequency.WEEKLY
    if len(recent) >= 3:
        return CommitFrequency.MONTHLY
    return CommitFrequency.SPORADIC


async def fetch_repo_tree(
    username: str, repo_name: str, branch: str = "main"
) -> list[str]:
    """Fetch the file tree of a repo (recursive). Returns list of file paths."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await _github_get(
            client,
            f"{settings.github_api_base}/repos/{username}/{repo_name}/git/trees/{branch}",
            params={"recursive": "1"},
        )
        if resp.status_code != 200:
            # Retry with 'master' branch
            resp = await _github_get(
                client,
                f"{settings.github_api_base}/repos/{username}/{repo_name}/git/trees/master",
                params={"recursive": "1"},
            )
            if resp.status_code != 200:
                return []
        data = resp.json()
        return [
            item["path"] for item in data.get("tree", []) if item.get("type") == "blob"
        ]


async def fetch_file_content(username: str, repo_name: str, file_path: str) -> str:
    """Fetch the raw content of a specific file from a repo."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.github_api_base}/repos/{username}/{repo_name}/contents/{file_path}",
            headers={**_build_headers(), "Accept": "application/vnd.github.raw+json"},
        )
        if resp.status_code != 200:
            return ""
        return resp.text[:10000]  # Cap to prevent huge files


async def fetch_readme(username: str, repo_name: str) -> str:
    """Fetch the README content of a repo."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{settings.github_api_base}/repos/{username}/{repo_name}/readme",
            headers={**_build_headers(), "Accept": "application/vnd.github.raw+json"},
        )
        if resp.status_code != 200:
            return ""
        return resp.text[:8000]


# Files that reveal technology stack when present in a repo
_DEPENDENCY_FILES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "Pipfile",
    "Gemfile",
    "Cargo.toml",
    "go.mod",
    "build.gradle",
    "pom.xml",
    "composer.json",
    "pubspec.yaml",
]

# Config files whose mere presence indicates a technology
_CONFIG_FILE_TECH_MAP: dict[str, list[str]] = {
    "Dockerfile": ["Docker"],
    "docker-compose.yml": ["Docker", "Docker Compose"],
    "docker-compose.yaml": ["Docker", "Docker Compose"],
    ".dockerignore": ["Docker"],
    "Jenkinsfile": ["Jenkins", "CI/CD"],
    "Makefile": ["Make"],
    "nginx.conf": ["Nginx"],
    "webpack.config.js": ["Webpack", "JavaScript"],
    "webpack.config.ts": ["Webpack", "TypeScript"],
    "vite.config.js": ["Vite", "JavaScript"],
    "vite.config.ts": ["Vite", "TypeScript"],
    "tsconfig.json": ["TypeScript"],
    "jest.config.js": ["Jest", "Testing"],
    "jest.config.ts": ["Jest", "Testing"],
    "pytest.ini": ["pytest", "Testing"],
    "setup.cfg": ["Python"],
    ".eslintrc.js": ["ESLint"],
    ".eslintrc.json": ["ESLint"],
    ".prettierrc": ["Prettier"],
    "tailwind.config.js": ["TailwindCSS"],
    "tailwind.config.ts": ["TailwindCSS"],
    "next.config.js": ["Next.js", "React"],
    "next.config.mjs": ["Next.js", "React"],
    "nuxt.config.js": ["Nuxt.js", "Vue"],
    "nuxt.config.ts": ["Nuxt.js", "Vue"],
    "angular.json": ["Angular", "TypeScript"],
    "svelte.config.js": ["Svelte"],
    ".babelrc": ["Babel"],
    "babel.config.js": ["Babel"],
    "rollup.config.js": ["Rollup"],
    "gulpfile.js": ["Gulp"],
    "Procfile": ["Heroku"],
    "vercel.json": ["Vercel"],
    "netlify.toml": ["Netlify"],
    "terraform.tf": ["Terraform"],
    "serverless.yml": ["Serverless Framework"],
    "cdk.json": ["AWS CDK"],
    "app.yaml": ["Google App Engine"],
    "fly.toml": ["Fly.io"],
    ".travis.yml": ["Travis CI", "CI/CD"],
    "appveyor.yml": ["AppVeyor", "CI/CD"],
    "tox.ini": ["tox", "Testing"],
    "manage.py": ["Django"],
}

# Directory patterns that indicate technologies
_DIR_TECH_MAP: dict[str, list[str]] = {
    ".github/workflows": ["GitHub Actions", "CI/CD"],
    ".circleci": ["CircleCI", "CI/CD"],
    "terraform": ["Terraform", "Infrastructure as Code"],
    "kubernetes": ["Kubernetes"],
    "k8s": ["Kubernetes"],
    "helm": ["Helm", "Kubernetes"],
    "ansible": ["Ansible"],
    ".storybook": ["Storybook", "Testing"],
    "cypress": ["Cypress", "Testing"],
    "__tests__": ["Testing"],
    "tests": ["Testing"],
    "test": ["Testing"],
    "spec": ["Testing"],
    "migrations": ["Database Migrations"],
    "prisma": ["Prisma", "Database"],
    "graphql": ["GraphQL"],
    "proto": ["gRPC", "Protocol Buffers"],
    "notebooks": ["Jupyter", "Data Science"],
    "models": ["ML/AI models"],
}


def _detect_technologies_from_tree(
    file_paths: list[str],
) -> tuple[list[str], list[str], dict[str, bool]]:
    """Analyze a repo's file tree to detect technologies.

    Returns (detected_technologies, config_files_found, indicators).
    """
    detected: set[str] = set()
    config_found: list[str] = []
    indicators = {
        "has_ci": False,
        "has_docker": False,
        "has_tests": False,
    }

    for path in file_paths:
        filename = path.rsplit("/", 1)[-1] if "/" in path else path

        # Check config files
        if filename in _CONFIG_FILE_TECH_MAP:
            detected.update(_CONFIG_FILE_TECH_MAP[filename])
            config_found.append(filename)

        # Check dependency files
        if filename in _DEPENDENCY_FILES:
            config_found.append(filename)

        # Check directory patterns
        for dir_pattern, techs in _DIR_TECH_MAP.items():
            if dir_pattern in path:
                detected.update(techs)

        # Detect from file extensions
        if path.endswith(".py"):
            detected.add("Python")
        elif path.endswith((".js", ".mjs", ".cjs")):
            detected.add("JavaScript")
        elif path.endswith((".ts", ".tsx")):
            detected.add("TypeScript")
        elif path.endswith(".jsx"):
            detected.add("JavaScript")
            detected.add("React")
        elif path.endswith(".vue"):
            detected.add("Vue")
            detected.add("JavaScript")
        elif path.endswith(".svelte"):
            detected.add("Svelte")
        elif path.endswith(".java"):
            detected.add("Java")
        elif path.endswith((".rb", ".erb")):
            detected.add("Ruby")
        elif path.endswith(".go"):
            detected.add("Go")
        elif path.endswith(".rs"):
            detected.add("Rust")
        elif path.endswith(".swift"):
            detected.add("Swift")
        elif path.endswith(".kt"):
            detected.add("Kotlin")
        elif path.endswith(".scala"):
            detected.add("Scala")
        elif path.endswith(".dart"):
            detected.add("Dart")
        elif path.endswith(".php"):
            detected.add("PHP")
        elif path.endswith((".css", ".scss", ".sass", ".less")):
            detected.add("CSS")
        elif path.endswith(".html"):
            detected.add("HTML")
        elif path.endswith((".sh", ".bash")):
            detected.add("Shell/Bash")
        elif path.endswith((".yml", ".yaml")) and "docker" in path.lower():
            detected.add("Docker")
        elif path.endswith(".sql"):
            detected.add("SQL")
        elif path.endswith(".ipynb"):
            detected.add("Jupyter Notebook")
            detected.add("Python")
        elif path.endswith(".r") or path.endswith(".R"):
            detected.add("R")
        elif path.endswith((".c", ".h")):
            detected.add("C")
        elif path.endswith((".cpp", ".cc", ".hpp")):
            detected.add("C++")

        # Detect React from JSX/TSX
        if path.endswith(".tsx"):
            detected.add("React")

    # Set indicators
    indicators["has_ci"] = any(
        ".github/workflows" in p
        or ".circleci" in p
        or "Jenkinsfile" in p
        or ".travis.yml" in p
        for p in file_paths
    )
    indicators["has_docker"] = any(
        p.rsplit("/", 1)[-1]
        in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml")
        for p in file_paths
    )
    indicators["has_tests"] = any(
        "test" in p.lower() and p.endswith((".py", ".js", ".ts", ".java", ".rb", ".go"))
        for p in file_paths
    )

    return sorted(detected), config_found, indicators


def _parse_package_json_deps(content: str) -> list[str]:
    """Extract dependency names from package.json content."""
    import json

    techs: list[str] = []
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return techs

    # Map well-known npm packages to technology names
    _NPM_TECH_MAP = {
        "react": "React",
        "react-dom": "React",
        "next": "Next.js",
        "vue": "Vue",
        "nuxt": "Nuxt.js",
        "@angular/core": "Angular",
        "svelte": "Svelte",
        "express": "Express.js",
        "fastify": "Fastify",
        "koa": "Koa",
        "hapi": "Hapi",
        "nestjs": "NestJS",
        "@nestjs/core": "NestJS",
        "tailwindcss": "TailwindCSS",
        "bootstrap": "Bootstrap",
        "sass": "Sass",
        "less": "Less",
        "webpack": "Webpack",
        "vite": "Vite",
        "rollup": "Rollup",
        "jest": "Jest",
        "mocha": "Mocha",
        "cypress": "Cypress",
        "playwright": "Playwright",
        "vitest": "Vitest",
        "mongoose": "MongoDB",
        "pg": "PostgreSQL",
        "mysql2": "MySQL",
        "prisma": "Prisma",
        "@prisma/client": "Prisma",
        "sequelize": "Sequelize",
        "typeorm": "TypeORM",
        "graphql": "GraphQL",
        "apollo-server": "GraphQL",
        "@apollo/client": "GraphQL",
        "axios": "Axios",
        "redux": "Redux",
        "@reduxjs/toolkit": "Redux",
        "zustand": "Zustand",
        "mobx": "MobX",
        "socket.io": "WebSockets",
        "ws": "WebSockets",
        "tensorflow": "TensorFlow",
        "@tensorflow/tfjs": "TensorFlow",
        "firebase": "Firebase",
        "firebase-admin": "Firebase",
        "aws-sdk": "AWS",
        "@aws-sdk/client-s3": "AWS",
        "docker-compose": "Docker",
        "eslint": "ESLint",
        "prettier": "Prettier",
        "storybook": "Storybook",
        "@storybook/react": "Storybook",
        "three": "Three.js",
        "d3": "D3.js",
        "chart.js": "Chart.js",
        "recharts": "Recharts",
        "framer-motion": "Framer Motion",
        "styled-components": "Styled Components",
        "@emotion/react": "Emotion CSS",
        "electron": "Electron",
    }

    for section in ("dependencies", "devDependencies"):
        deps = data.get(section, {})
        if isinstance(deps, dict):
            for pkg in deps:
                pkg_lower = pkg.lower()
                if pkg_lower in _NPM_TECH_MAP:
                    techs.append(_NPM_TECH_MAP[pkg_lower])
                elif pkg.startswith("@types/"):
                    techs.append("TypeScript")

    return techs


def _parse_requirements_txt(content: str) -> list[str]:
    """Extract technology names from requirements.txt."""
    techs: list[str] = []

    _PIP_TECH_MAP = {
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "uvicorn": "FastAPI",
        "starlette": "FastAPI",
        "sqlalchemy": "SQLAlchemy",
        "alembic": "SQLAlchemy",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "scipy": "SciPy",
        "matplotlib": "Matplotlib",
        "seaborn": "Seaborn",
        "scikit-learn": "Scikit-learn",
        "sklearn": "Scikit-learn",
        "tensorflow": "TensorFlow",
        "torch": "PyTorch",
        "pytorch": "PyTorch",
        "keras": "Keras",
        "opencv-python": "OpenCV",
        "cv2": "OpenCV",
        "pillow": "Pillow",
        "pil": "Pillow",
        "requests": "Requests",
        "httpx": "HTTPX",
        "beautifulsoup4": "BeautifulSoup",
        "bs4": "BeautifulSoup",
        "scrapy": "Scrapy",
        "selenium": "Selenium",
        "playwright": "Playwright",
        "celery": "Celery",
        "redis": "Redis",
        "pymongo": "MongoDB",
        "motor": "MongoDB",
        "psycopg2": "PostgreSQL",
        "asyncpg": "PostgreSQL",
        "mysql-connector-python": "MySQL",
        "pymysql": "MySQL",
        "boto3": "AWS",
        "botocore": "AWS",
        "google-cloud-storage": "Google Cloud",
        "azure-storage-blob": "Azure",
        "docker": "Docker",
        "docker-compose": "Docker",
        "pytest": "pytest",
        "unittest": "Testing",
        "transformers": "Hugging Face Transformers",
        "langchain": "LangChain",
        "openai": "OpenAI",
        "spacy": "spaCy",
        "nltk": "NLTK",
        "pydantic": "Pydantic",
        "marshmallow": "Marshmallow",
        "graphene": "GraphQL",
        "strawberry-graphql": "GraphQL",
        "click": "Click CLI",
        "typer": "Typer CLI",
        "streamlit": "Streamlit",
        "gradio": "Gradio",
        "jupyter": "Jupyter",
        "notebook": "Jupyter",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "catboost": "CatBoost",
    }

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Extract package name (before ==, >=, <=, ~=, etc.)
        pkg = (
            line.split("==")[0]
            .split(">=")[0]
            .split("<=")[0]
            .split("~=")[0]
            .split("[")[0]
            .strip()
            .lower()
        )
        if pkg in _PIP_TECH_MAP:
            techs.append(_PIP_TECH_MAP[pkg])

    return techs


def _parse_readme_technologies(readme: str) -> list[str]:
    """Detect technologies mentioned in README content."""
    techs: list[str] = []
    lower = readme.lower()

    _README_TECH_MAP = {
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "keras": "Keras",
        "opencv": "OpenCV",
        "scikit-learn": "Scikit-learn",
        "sklearn": "Scikit-learn",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "matplotlib": "Matplotlib",
        "react": "React",
        "next.js": "Next.js",
        "vue.js": "Vue",
        "angular": "Angular",
        "svelte": "Svelte",
        "express": "Express.js",
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "spring boot": "Spring Boot",
        "node.js": "Node.js",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "terraform": "Terraform",
        "ansible": "Ansible",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "mysql": "MySQL",
        "sqlite": "SQLite",
        "elasticsearch": "Elasticsearch",
        "graphql": "GraphQL",
        "rest api": "REST API",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "Google Cloud",
        "heroku": "Heroku",
        "vercel": "Vercel",
        "netlify": "Netlify",
        "hugging face": "Hugging Face",
        "langchain": "LangChain",
        "openai": "OpenAI",
        "streamlit": "Streamlit",
        "selenium": "Selenium",
        "playwright": "Playwright",
        "tailwindcss": "TailwindCSS",
        "tailwind css": "TailwindCSS",
        "bootstrap": "Bootstrap",
        "material ui": "Material UI",
        "styled-components": "Styled Components",
        "jwt": "JWT Authentication",
        "oauth": "OAuth",
        "websocket": "WebSockets",
        "socket.io": "WebSockets",
        "apache spark": "Apache Spark",
        "kafka": "Kafka",
        "rabbitmq": "RabbitMQ",
        "celery": "Celery",
        "nginx": "Nginx",
        "github actions": "GitHub Actions",
        "jenkins": "Jenkins",
        "ci/cd": "CI/CD",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "natural language processing": "NLP",
        "nlp": "NLP",
        "computer vision": "Computer Vision",
        "neural network": "Neural Networks",
        "reinforcement learning": "Reinforcement Learning",
    }

    for keyword, tech in _README_TECH_MAP.items():
        if keyword in lower:
            techs.append(tech)

    return techs


async def _deep_analyze_repo(username: str, repo: dict) -> dict:
    """Perform deep analysis on a single repo: tree, dependency files, README."""
    repo_name = repo.get("name", "")
    default_branch = repo.get("default_branch", "main")

    # Fetch tree and README in parallel
    tree_paths, readme = await asyncio.gather(
        fetch_repo_tree(username, repo_name, default_branch),
        fetch_readme(username, repo_name),
    )

    detected: list[str] = []
    config_files: list[str] = []
    indicators: dict[str, bool] = {
        "has_ci": False,
        "has_docker": False,
        "has_tests": False,
    }

    if tree_paths:
        detected_from_tree, config_files, indicators = _detect_technologies_from_tree(
            tree_paths
        )
        detected.extend(detected_from_tree)

        # Fetch dependency file contents for deeper analysis
        dep_files_to_fetch: list[str] = []
        for cf in config_files:
            if cf in ("package.json", "requirements.txt"):
                dep_files_to_fetch.append(cf)

        if dep_files_to_fetch:
            dep_results = await asyncio.gather(
                *[
                    fetch_file_content(username, repo_name, f)
                    for f in dep_files_to_fetch[:2]
                ],
            )
            for dep_file, content in zip(dep_files_to_fetch[:2], dep_results):
                if not content:
                    continue
                if dep_file == "package.json":
                    detected.extend(_parse_package_json_deps(content))
                elif dep_file == "requirements.txt":
                    detected.extend(_parse_requirements_txt(content))

    # Parse README for technology mentions
    if readme:
        detected.extend(_parse_readme_technologies(readme))

    # Deduplicate
    unique_detected = sorted(set(detected))

    return {
        "readme_content": readme[:3000],
        "detected_technologies": unique_detected,
        "config_files": config_files,
        "file_count": len(tree_paths),
        "has_ci": indicators["has_ci"],
        "has_docker": indicators["has_docker"],
        "has_tests": indicators["has_tests"],
    }


async def analyze_github_profile(username: str) -> GitHubSummary:
    """Full GitHub profile analysis — fetches profile, repos, commits, and deep repo analysis.

    Results are cached for 5 minutes to avoid repeated API calls.
    """
    # Check cache first
    cached = _github_cache.get(username.lower())
    if cached is not None:
        summary, ts = cached
        if (time.monotonic() - ts) < _CACHE_TTL_SECONDS:
            logger.info("Returning cached GitHub analysis for %s", username)
            return summary

    # Parallel fetch: profile + repos
    profile_data, repos_data = await asyncio.gather(
        fetch_user_profile(username),
        fetch_repos(username),
    )

    # Deep-analyze top 8 repos in parallel
    top_repos = repos_data[:8]
    deep_results = await asyncio.gather(
        *[_deep_analyze_repo(username, repo) for repo in top_repos],
        return_exceptions=True,
    )

    # Build repo summaries with deep analysis data
    notable_repos: list[RepoSummary] = []
    for i, repo in enumerate(repos_data[:15]):
        deep_data: dict[str, Any] = {}
        if i < len(deep_results) and not isinstance(deep_results[i], BaseException):
            deep_data = deep_results[i]  # type: ignore[assignment]

        notable_repos.append(
            RepoSummary(
                name=repo.get("name", ""),
                description=repo.get("description"),
                language=repo.get("language"),
                stars=repo.get("stargazers_count", 0),
                forks=repo.get("forks_count", 0),
                has_readme=bool(deep_data.get("readme_content"))
                or repo.get("size", 0) > 0,
                topics=repo.get("topics", []),
                readme_content=deep_data.get("readme_content", ""),
                detected_technologies=deep_data.get("detected_technologies", []),
                config_files=deep_data.get("config_files", []),
                file_count=deep_data.get("file_count", 0),
                has_ci=deep_data.get("has_ci", False),
                has_docker=deep_data.get("has_docker", False),
                has_tests=deep_data.get("has_tests", False),
            )
        )

    # Compute aggregate stats
    total_stars = sum(r.get("stargazers_count", 0) for r in repos_data)
    top_languages = _compute_language_distribution(repos_data)

    # Sample commits from top 5 repos for frequency analysis
    top_repo_names = [r["name"] for r in repos_data[:5]]
    commit_results = await asyncio.gather(
        *[fetch_recent_commits(username, name) for name in top_repo_names]
    )

    commit_dates: list[datetime] = []
    for commits in commit_results:
        for c in commits:
            date_str = c.get("commit", {}).get("committer", {}).get("date", "")
            if date_str:
                try:
                    commit_dates.append(
                        datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    )
                except ValueError:
                    continue

    commit_frequency = _determine_commit_frequency(commit_dates)

    result = GitHubSummary(
        username=username,
        avatar_url=profile_data.get("avatar_url"),
        bio=profile_data.get("bio"),
        public_repos=profile_data.get("public_repos", 0),
        followers=profile_data.get("followers", 0),
        top_languages=top_languages,
        total_stars=total_stars,
        commit_frequency=commit_frequency,
        notable_repos=notable_repos,
    )

    # Store in cache
    _github_cache[username.lower()] = (result, time.monotonic())

    return result
