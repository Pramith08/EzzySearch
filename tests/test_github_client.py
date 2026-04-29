from __future__ import annotations

import base64
from datetime import date

import pytest

from ezzysearch.github_client import (
    GitHubClient,
    GitHubRateLimitError,
    SearchParams,
    build_repository_query,
)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, headers: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self) -> dict:
        return self._payload


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls = []

    def get(self, url: str, headers: dict, params: dict | None = None, timeout: int = 20) -> FakeResponse:
        self.calls.append({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return self.response


def test_build_repository_query_includes_filters() -> None:
    params = SearchParams(
        query="streamlit dashboard",
        language="Python",
        min_stars=50,
        updated_after=date(2026, 1, 1),
        include_archived=False,
    )

    query = build_repository_query(params)

    assert "streamlit dashboard" in query
    assert "language:Python" in query
    assert "stars:>=50" in query
    assert "pushed:>=2026-01-01" in query
    assert "archived:false" in query


def test_search_repositories_parses_api_response() -> None:
    session = FakeSession(
        FakeResponse(
            200,
            {
                "total_count": 1,
                "incomplete_results": False,
                "items": [
                    {
                        "name": "demo",
                        "full_name": "octo/demo",
                        "owner": {"login": "octo"},
                        "html_url": "https://github.com/octo/demo",
                        "description": "Demo repo",
                        "stargazers_count": 120,
                        "forks_count": 8,
                        "open_issues_count": 2,
                        "language": "Python",
                        "license": {"name": "MIT License"},
                        "topics": ["streamlit", "github"],
                        "updated_at": "2026-04-01T00:00:00Z",
                        "pushed_at": "2026-04-01T00:00:00Z",
                        "archived": False,
                        "default_branch": "main",
                    }
                ],
            },
        )
    )
    client = GitHubClient(session=session)

    results = client.search_repositories(SearchParams(query="demo", sort="stars", per_page=5))

    assert results.total_count == 1
    assert results.repositories[0].full_name == "octo/demo"
    assert results.repositories[0].stars == 120
    assert session.calls[0]["params"]["sort"] == "stars"
    assert session.calls[0]["params"]["per_page"] == 5


def test_fetch_readme_decodes_base64_content() -> None:
    readme = "# Demo\n\nInstall with pip."
    encoded = base64.b64encode(readme.encode()).decode()
    session = FakeSession(FakeResponse(200, {"content": encoded, "encoding": "base64"}))
    client = GitHubClient(session=session)

    assert client.fetch_readme("octo", "demo") == readme


def test_get_repository_parses_api_response() -> None:
    session = FakeSession(
        FakeResponse(
            200,
            {
                "name": "demo",
                "full_name": "octo/demo",
                "owner": {"login": "octo"},
                "html_url": "https://github.com/octo/demo",
                "description": "Demo repo",
                "stargazers_count": 120,
                "forks_count": 8,
                "open_issues_count": 2,
                "language": "Python",
                "license": {"name": "MIT License"},
                "topics": ["streamlit", "github"],
                "updated_at": "2026-04-01T00:00:00Z",
                "pushed_at": "2026-04-01T00:00:00Z",
                "archived": False,
                "default_branch": "main",
            },
        )
    )
    client = GitHubClient(session=session)

    repo = client.get_repository("octo", "demo")

    assert repo is not None
    assert repo.full_name == "octo/demo"
    assert session.calls[0]["url"].endswith("/repos/octo/demo")


def test_fetch_readme_returns_none_for_missing_readme() -> None:
    session = FakeSession(FakeResponse(404, {"message": "Not Found"}))
    client = GitHubClient(session=session)

    assert client.fetch_readme("octo", "missing") is None


def test_rate_limit_response_raises_specific_error() -> None:
    session = FakeSession(
        FakeResponse(
            403,
            {"message": "API rate limit exceeded"},
            {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1770000000"},
        )
    )
    client = GitHubClient(session=session)

    with pytest.raises(GitHubRateLimitError) as exc:
        client.search_repositories(SearchParams(query="demo"))

    assert exc.value.reset_at == "1770000000"
