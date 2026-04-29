from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RepoResult:
    name: str
    full_name: str
    owner: str
    url: str
    description: str
    stars: int
    forks: int
    open_issues: int
    language: str
    license_name: str
    topics: tuple[str, ...]
    updated_at: str
    pushed_at: str
    archived: bool
    default_branch: str

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "RepoResult":
        owner = item.get("owner") or {}
        license_info = item.get("license") or {}

        return cls(
            name=str(item.get("name") or ""),
            full_name=str(item.get("full_name") or ""),
            owner=str(owner.get("login") or ""),
            url=str(item.get("html_url") or ""),
            description=str(item.get("description") or ""),
            stars=int(item.get("stargazers_count") or 0),
            forks=int(item.get("forks_count") or 0),
            open_issues=int(item.get("open_issues_count") or 0),
            language=str(item.get("language") or ""),
            license_name=str(license_info.get("name") or ""),
            topics=tuple(str(topic) for topic in item.get("topics") or ()),
            updated_at=str(item.get("updated_at") or ""),
            pushed_at=str(item.get("pushed_at") or ""),
            archived=bool(item.get("archived")),
            default_branch=str(item.get("default_branch") or "main"),
        )


@dataclass(frozen=True)
class SearchResults:
    total_count: int
    incomplete_results: bool
    repositories: tuple[RepoResult, ...]


@dataclass(frozen=True)
class RepoAnalysis:
    score: int
    level: str
    maintenance: str
    documentation: str
    setup_clarity: str
    risk: str
    strengths: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    checks: dict[str, bool] = field(default_factory=dict)
