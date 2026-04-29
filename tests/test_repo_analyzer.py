from __future__ import annotations

from datetime import UTC, datetime

from ezzysearch.models import RepoResult
from ezzysearch.repo_analyzer import analyze_repo


def make_repo(**overrides: object) -> RepoResult:
    values = {
        "name": "demo",
        "full_name": "octo/demo",
        "owner": "octo",
        "url": "https://github.com/octo/demo",
        "description": "Demo repo",
        "stars": 100,
        "forks": 10,
        "open_issues": 3,
        "language": "Python",
        "license_name": "MIT License",
        "topics": ("streamlit", "github"),
        "updated_at": "2026-04-01T00:00:00Z",
        "pushed_at": "2026-04-01T00:00:00Z",
        "archived": False,
        "default_branch": "main",
    }
    values.update(overrides)
    return RepoResult(**values)


def test_beginner_friendly_repo_scores_high() -> None:
    readme = """
    # Demo

    ## Installation
    Install the package with pip.

    ## Usage
    Run the example command to start the demo.

    This README includes enough detail for a beginner to understand the project,
    install it locally, run an example, and decide whether it is worth opening.
    """

    analysis = analyze_repo(make_repo(), readme, now=datetime(2026, 4, 29, tzinfo=UTC))

    assert analysis.score >= 80
    assert analysis.level == "Beginner friendly"
    assert analysis.risk == "Low"
    assert analysis.checks["has_install_section"] is True
    assert analysis.checks["has_usage_examples"] is True


def test_archived_repo_with_no_readme_scores_low() -> None:
    repo = make_repo(
        stars=1,
        forks=0,
        license_name="",
        topics=(),
        archived=True,
        pushed_at="2021-01-01T00:00:00Z",
    )

    analysis = analyze_repo(repo, None, now=datetime(2026, 4, 29, tzinfo=UTC))

    assert analysis.score < 40
    assert analysis.maintenance == "Archived"
    assert analysis.risk == "High"
    assert "README was not available" in analysis.warnings


def test_thin_readme_warns_about_missing_setup_and_usage() -> None:
    analysis = analyze_repo(make_repo(), "# Demo", now=datetime(2026, 4, 29, tzinfo=UTC))

    assert analysis.documentation == "Thin"
    assert "Setup instructions were not detected" in analysis.warnings
    assert "Usage examples were not detected" in analysis.warnings
