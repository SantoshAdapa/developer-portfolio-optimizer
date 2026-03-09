import asyncio
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.models.enums import CommitFrequency
from app.models.schemas import GitHubSummary, RepoSummary


def extract_username(github_url: str) -> str:
    """Extract GitHub username from a profile URL."""
    path = urlparse(str(github_url)).path.strip("/")
    # Take first segment only (handles trailing slashes, extra paths)
    username = path.split("/")[0]
    if not username:
        raise ValueError("Could not extract GitHub username from URL")
    return username


def _build_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


async def fetch_user_profile(username: str) -> dict:
    """Fetch basic GitHub user profile."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.github_api_base}/users/{username}",
            headers=_build_headers(),
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_repos(username: str, max_repos: int = 30) -> list[dict]:
    """Fetch public repos sorted by most recently pushed."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.github_api_base}/users/{username}/repos",
            headers=_build_headers(),
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
        resp = await client.get(
            f"{settings.github_api_base}/repos/{username}/{repo_name}/commits",
            headers=_build_headers(),
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


async def analyze_github_profile(username: str) -> GitHubSummary:
    """Full GitHub profile analysis — fetches profile, repos, and commits."""

    # Parallel fetch: profile + repos
    profile_data, repos_data = await asyncio.gather(
        fetch_user_profile(username),
        fetch_repos(username),
    )

    # Build repo summaries
    notable_repos: list[RepoSummary] = []
    for repo in repos_data[:15]:
        notable_repos.append(
            RepoSummary(
                name=repo.get("name", ""),
                description=repo.get("description"),
                language=repo.get("language"),
                stars=repo.get("stargazers_count", 0),
                forks=repo.get("forks_count", 0),
                has_readme=repo.get("description") is not None,  # heuristic
                topics=repo.get("topics", []),
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

    return GitHubSummary(
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
