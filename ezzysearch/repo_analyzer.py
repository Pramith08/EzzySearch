from __future__ import annotations

import re
from datetime import UTC, datetime

from ezzysearch.models import RepoAnalysis, RepoResult


INSTALL_PATTERNS = (
    r"\binstall\b",
    r"\binstallation\b",
    r"\bgetting started\b",
    r"\bsetup\b",
    r"\bquickstart\b",
)
USAGE_PATTERNS = (
    r"\busage\b",
    r"\bexample\b",
    r"\bhow to\b",
    r"\btutorial\b",
)


def analyze_repo(repo: RepoResult, readme_text: str | None, now: datetime | None = None) -> RepoAnalysis:
    now = now or datetime.now(UTC)
    readme = readme_text or ""
    readme_lower = readme.lower()
    days_since_push = _days_since(repo.pushed_at or repo.updated_at, now)

    checks = {
        "has_readme": bool(readme.strip()),
        "has_install_section": _matches_any(readme_lower, INSTALL_PATTERNS),
        "has_usage_examples": _matches_any(readme_lower, USAGE_PATTERNS),
        "has_license": bool(repo.license_name),
        "recently_updated": days_since_push is not None and days_since_push <= 365,
        "not_archived": not repo.archived,
        "has_topics": bool(repo.topics),
        "has_popularity_signal": repo.stars >= 10 or repo.forks >= 3,
        "readme_has_substance": len(readme.strip()) >= 400,
    }

    score = _score(checks, repo, days_since_push)
    strengths = _strengths(checks, repo, days_since_push)
    warnings = _warnings(checks, repo, days_since_push)

    return RepoAnalysis(
        score=score,
        level=_level(score),
        maintenance=_maintenance(repo, days_since_push),
        documentation=_documentation(checks),
        setup_clarity=_setup_clarity(checks),
        risk=_risk(repo, score, days_since_push),
        strengths=tuple(strengths),
        warnings=tuple(warnings),
        checks=checks,
    )


def _score(checks: dict[str, bool], repo: RepoResult, days_since_push: int | None) -> int:
    score = 0
    score += 20 if checks["has_readme"] else 0
    score += 12 if checks["readme_has_substance"] else 0
    score += 14 if checks["has_install_section"] else 0
    score += 14 if checks["has_usage_examples"] else 0
    score += 10 if checks["has_license"] else 0
    score += 10 if checks["not_archived"] else 0
    score += 5 if checks["has_topics"] else 0

    if days_since_push is not None:
        if days_since_push <= 180:
            score += 10
        elif days_since_push <= 365:
            score += 7
        elif days_since_push <= 730:
            score += 3

    if repo.stars >= 500:
        score += 5
    elif repo.stars >= 50:
        score += 4
    elif repo.stars >= 10:
        score += 2

    if repo.forks >= 20:
        score += 3
    elif repo.forks >= 3:
        score += 2

    return max(0, min(score, 100))


def _strengths(checks: dict[str, bool], repo: RepoResult, days_since_push: int | None) -> list[str]:
    strengths: list[str] = []
    if checks["has_readme"]:
        strengths.append("README is available")
    if checks["has_install_section"]:
        strengths.append("Setup instructions are detectable")
    if checks["has_usage_examples"]:
        strengths.append("Usage examples or tutorial language is detectable")
    if checks["has_license"]:
        strengths.append("License is declared")
    if checks["recently_updated"]:
        strengths.append("Repository was updated within the last year")
    if repo.stars >= 50:
        strengths.append("Popularity signal from stars")
    if repo.topics:
        strengths.append("Topics make the project easier to discover")
    if days_since_push is not None and days_since_push <= 30:
        strengths.append("Very recent activity")
    return strengths


def _warnings(checks: dict[str, bool], repo: RepoResult, days_since_push: int | None) -> list[str]:
    warnings: list[str] = []
    if repo.archived:
        warnings.append("Repository is archived")
    if not checks["has_readme"]:
        warnings.append("README was not available")
    elif not checks["readme_has_substance"]:
        warnings.append("README appears short")
    if not checks["has_install_section"]:
        warnings.append("Setup instructions were not detected")
    if not checks["has_usage_examples"]:
        warnings.append("Usage examples were not detected")
    if not checks["has_license"]:
        warnings.append("License was not declared")
    if days_since_push is None:
        warnings.append("Could not determine recent maintenance")
    elif days_since_push > 730:
        warnings.append("No push activity detected in the last two years")
    elif days_since_push > 365:
        warnings.append("No push activity detected in the last year")
    if repo.stars < 10 and repo.forks < 3:
        warnings.append("Low public adoption signal")
    return warnings


def _level(score: int) -> str:
    if score >= 80:
        return "Beginner friendly"
    if score >= 60:
        return "Usable with some caution"
    if score >= 40:
        return "Intermediate"
    return "Needs review"


def _maintenance(repo: RepoResult, days_since_push: int | None) -> str:
    if repo.archived:
        return "Archived"
    if days_since_push is None:
        return "Unknown"
    if days_since_push <= 180:
        return "Active"
    if days_since_push <= 365:
        return "Recently maintained"
    if days_since_push <= 730:
        return "Slow"
    return "Stale"


def _documentation(checks: dict[str, bool]) -> str:
    if checks["has_readme"] and checks["readme_has_substance"] and checks["has_usage_examples"]:
        return "Good"
    if checks["has_readme"] and checks["readme_has_substance"]:
        return "Basic"
    if checks["has_readme"]:
        return "Thin"
    return "Missing"


def _setup_clarity(checks: dict[str, bool]) -> str:
    if checks["has_install_section"] and checks["has_usage_examples"]:
        return "Clear"
    if checks["has_install_section"]:
        return "Partial"
    return "Unclear"


def _risk(repo: RepoResult, score: int, days_since_push: int | None) -> str:
    if repo.archived or score < 40:
        return "High"
    if days_since_push is not None and days_since_push > 730:
        return "High"
    if score < 65:
        return "Medium"
    return "Low"


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _days_since(timestamp: str, now: datetime) -> int | None:
    if not timestamp:
        return None

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return max((now - parsed).days, 0)
