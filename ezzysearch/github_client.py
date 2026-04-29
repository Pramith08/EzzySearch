from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import date
from typing import Any

import requests

from ezzysearch.config import GITHUB_API_BASE_URL, GITHUB_API_VERSION, MAX_RESULTS_PER_PAGE
from ezzysearch.models import RepoResult, SearchResults


class GitHubAPIError(RuntimeError):
    """Raised when GitHub returns an unexpected API response."""


class GitHubRateLimitError(GitHubAPIError):
    def __init__(self, message: str, reset_at: str | None = None) -> None:
        super().__init__(message)
        self.reset_at = reset_at


@dataclass(frozen=True)
class SearchParams:
    query: str
    language: str = ""
    min_stars: int = 0
    updated_after: date | None = None
    include_archived: bool = False
    sort: str = ""
    order: str = "desc"
    per_page: int = 10


def build_repository_query(params: SearchParams) -> str:
    query = params.query.strip()
    if not query:
        raise ValueError("Search query cannot be empty.")

    terms = [query]

    language = params.language.strip()
    if language:
        terms.append(f"language:{language}")

    if params.min_stars > 0:
        terms.append(f"stars:>={params.min_stars}")

    if params.updated_after:
        terms.append(f"pushed:>={params.updated_after.isoformat()}")

    if not params.include_archived:
        terms.append("archived:false")

    return " ".join(terms)


class GitHubClient:
    def __init__(
        self,
        token: str | None = None,
        session: requests.Session | None = None,
        base_url: str = GITHUB_API_BASE_URL,
    ) -> None:
        self.token = token
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")

    def search_repositories(self, params: SearchParams) -> SearchResults:
        per_page = min(max(params.per_page, 1), MAX_RESULTS_PER_PAGE)
        query_params: dict[str, Any] = {
            "q": build_repository_query(params),
            "per_page": per_page,
        }

        if params.sort:
            query_params["sort"] = params.sort
            query_params["order"] = params.order

        payload = self._request_json("/search/repositories", params=query_params)
        repositories = tuple(RepoResult.from_api(item) for item in payload.get("items", ()))

        return SearchResults(
            total_count=int(payload.get("total_count") or 0),
            incomplete_results=bool(payload.get("incomplete_results")),
            repositories=repositories,
        )

    def get_repository(self, owner: str, repo: str) -> RepoResult | None:
        payload = self._request_json(f"/repos/{owner}/{repo}", allow_not_found=True)
        if payload is None:
            return None
        return RepoResult.from_api(payload)

    def fetch_readme(self, owner: str, repo: str) -> str | None:
        payload = self._request_json(f"/repos/{owner}/{repo}/readme", allow_not_found=True)
        if payload is None:
            return None

        content = payload.get("content")
        encoding = payload.get("encoding")
        if not content:
            return None

        if encoding == "base64":
            try:
                return base64.b64decode(content, validate=False).decode("utf-8", errors="replace")
            except (ValueError, TypeError):
                raise GitHubAPIError("GitHub returned an unreadable README response.")

        return str(content)

    def _request_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        allow_not_found: bool = False,
    ) -> dict[str, Any] | None:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, headers=self._headers(), params=params, timeout=20)
        except requests.RequestException as exc:
            raise GitHubAPIError(f"Could not reach GitHub API: {exc}") from exc

        if allow_not_found and response.status_code == 404:
            return None

        if response.status_code in {403, 429}:
            message = self._error_message(response)
            remaining = response.headers.get("x-ratelimit-remaining")
            if remaining == "0" or "rate limit" in message.lower():
                raise GitHubRateLimitError(message, response.headers.get("x-ratelimit-reset"))

        if response.status_code < 200 or response.status_code >= 300:
            raise GitHubAPIError(self._error_message(response))

        try:
            payload = response.json()
        except ValueError as exc:
            raise GitHubAPIError("GitHub returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise GitHubAPIError("GitHub returned an unexpected response shape.")

        return payload

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "EzzySearch/2.0",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        message = payload.get("message") if isinstance(payload, dict) else None
        return message or f"GitHub API request failed with HTTP {response.status_code}."
