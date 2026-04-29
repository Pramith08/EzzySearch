from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from ezzysearch.config import APP_NAME, DEFAULT_RESULTS_PER_PAGE, get_github_token
from ezzysearch.github_client import GitHubAPIError, GitHubClient, GitHubRateLimitError, SearchParams
from ezzysearch.models import RepoAnalysis, RepoResult, SearchResults
from ezzysearch.repo_analyzer import analyze_repo


SORT_OPTIONS = {
    "Best match": "",
    "Most stars": "stars",
    "Most forks": "forks",
    "Recently updated": "updated",
}
UPDATED_FILTERS = {
    "Any time": None,
    "Past 6 months": 180,
    "Past year": 365,
    "Past 2 years": 730,
}


def main() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon=":mag:", layout="wide")
    _ensure_state()
    token = _resolve_token()

    with st.sidebar:
        logo = Path("assets") / "EZ Logo.jpg"
        if logo.exists():
            st.image(str(logo), use_container_width=True)

        st.header("Search Filters")
        language = st.text_input("Language", placeholder="Python")
        min_stars = st.number_input("Minimum stars", min_value=0, value=0, step=10)
        sort_label = st.selectbox("Sort by", tuple(SORT_OPTIONS.keys()), index=0)
        updated_label = st.selectbox("Updated", tuple(UPDATED_FILTERS.keys()), index=0)
        per_page = st.slider("Results", min_value=5, max_value=30, value=DEFAULT_RESULTS_PER_PAGE, step=5)
        include_archived = st.checkbox("Include archived repos", value=False)

        st.divider()
        if token:
            st.success("GitHub token detected")
        else:
            st.info("Public API mode")

    st.title("EzzySearch")
    st.caption("Find, score, compare, and shortlist GitHub repositories without scraping GitHub pages.")

    search_tab, compare_tab, shortlist_tab = st.tabs(("Search", "Compare", "Shortlist"))

    with search_tab:
        _render_search(
            token=token,
            language=language,
            min_stars=int(min_stars),
            sort_label=sort_label,
            updated_label=updated_label,
            per_page=per_page,
            include_archived=include_archived,
        )

    with compare_tab:
        _render_compare(token)

    with shortlist_tab:
        _render_shortlist()


def _render_search(
    token: str | None,
    language: str,
    min_stars: int,
    sort_label: str,
    updated_label: str,
    per_page: int,
    include_archived: bool,
) -> None:
    with st.form("repo-search-form"):
        query = st.text_input("Topic or keyword", placeholder="machine learning, django, cybersecurity tools")
        submitted = st.form_submit_button("Search repositories", use_container_width=True)

    if not submitted and not st.session_state.last_query:
        st.info("Search for a topic to discover beginner-friendly repositories.")
        return

    if submitted:
        st.session_state.last_query = query.strip()

    query = st.session_state.last_query
    if not query:
        st.warning("Enter a topic or keyword before searching.")
        return

    direct_repo = _parse_repo_reference(query)
    if direct_repo:
        _render_direct_repo(direct_repo[0], direct_repo[1], token)
        return

    try:
        with st.spinner("Searching GitHub repositories..."):
            results = search_repositories_cached(
                query=query,
                language=language,
                min_stars=min_stars,
                sort=SORT_OPTIONS[sort_label],
                updated_days=UPDATED_FILTERS[updated_label],
                include_archived=include_archived,
                per_page=per_page,
                token=token,
            )
    except GitHubRateLimitError as exc:
        st.error(f"GitHub rate limit reached: {exc}")
        return
    except (GitHubAPIError, ValueError) as exc:
        st.error(str(exc))
        return

    if results.incomplete_results:
        st.warning("GitHub returned partial results. Try narrowing the query or filters.")

    st.subheader(f"{_format_count(results.total_count)} repositories found")
    if not results.repositories:
        _render_relaxed_fallback(query, token)
        return

    for repo in results.repositories:
        _render_repo_card(repo, token)


def _render_direct_repo(owner: str, repo_name: str, token: str | None) -> None:
    try:
        with st.spinner(f"Loading {owner}/{repo_name}..."):
            repo = get_repository_cached(owner, repo_name, token)
    except GitHubRateLimitError as exc:
        st.error(f"GitHub rate limit reached: {exc}")
        return
    except GitHubAPIError as exc:
        st.error(str(exc))
        return

    if not repo:
        st.info(f"No repository found for `{owner}/{repo_name}`.")
        return

    st.subheader("Exact repository")
    _render_repo_card(repo, token)


def _render_relaxed_fallback(query: str, token: str | None) -> None:
    st.info("No repositories matched the current filters. Showing unfiltered name matches below.")
    try:
        fallback = search_repositories_cached(
            query=f"{query} in:name",
            language="",
            min_stars=0,
            sort="",
            updated_days=None,
            include_archived=False,
            per_page=10,
            token=token,
        )
    except (GitHubAPIError, ValueError) as exc:
        st.warning(f"Could not load relaxed fallback results: {exc}")
        return

    if not fallback.repositories:
        st.info("No relaxed fallback matches were found either.")
        return

    st.subheader(f"{_format_count(fallback.total_count)} unfiltered matches")
    for repo in fallback.repositories:
        _render_repo_card(repo, token)


def _render_repo_card(repo: RepoResult, token: str | None) -> None:
    with st.container(border=True):
        left, right = st.columns((4, 1))
        with left:
            st.markdown(f"### [{repo.full_name}]({repo.url})")
            st.write(repo.description or "No description provided.")
            st.caption(_repo_caption(repo))
        with right:
            st.metric("Stars", _format_count(repo.stars))
            st.metric("Forks", _format_count(repo.forks))

        topic_text = ", ".join(repo.topics[:8]) if repo.topics else "No topics"
        st.caption(f"Topics: {topic_text}")

        actions = st.columns((1, 1, 3))
        if actions[0].button("Analyze", key=f"analyze:{repo.full_name}", use_container_width=True):
            st.session_state.analysis_requested.add(repo.full_name)
        if actions[1].button("Shortlist", key=f"shortlist:{repo.full_name}", use_container_width=True):
            st.session_state.shortlist[repo.full_name] = repo
            st.toast(f"Added {repo.full_name}")

        if repo.full_name in st.session_state.analysis_requested:
            _render_analysis(repo, token)


def _render_analysis(repo: RepoResult, token: str | None) -> None:
    try:
        with st.spinner(f"Reading README for {repo.full_name}..."):
            readme = fetch_readme_cached(repo.owner, repo.name, token)
    except GitHubRateLimitError as exc:
        st.error(f"GitHub rate limit reached while fetching README: {exc}")
        return
    except GitHubAPIError as exc:
        st.error(str(exc))
        return

    analysis = analyze_repo(repo, readme)
    _analysis_summary(analysis)

    with st.expander("README preview"):
        if readme:
            st.markdown(_trim_readme(readme))
            if len(readme) > 3000:
                st.caption("Preview trimmed to the first 3,000 characters.")
        else:
            st.info("README was not available through the GitHub API.")


def _analysis_summary(analysis: RepoAnalysis) -> None:
    cols = st.columns(4)
    cols[0].metric("Beginner score", f"{analysis.score}/100")
    cols[1].metric("Maintenance", analysis.maintenance)
    cols[2].metric("Docs", analysis.documentation)
    cols[3].metric("Risk", analysis.risk)
    st.progress(analysis.score / 100)
    st.caption(f"{analysis.level} | Setup clarity: {analysis.setup_clarity}")

    if analysis.strengths:
        st.success("Strengths: " + "; ".join(analysis.strengths[:4]))
    if analysis.warnings:
        st.warning("Watchouts: " + "; ".join(analysis.warnings[:4]))


def _render_compare(token: str | None) -> None:
    shortlisted = list(st.session_state.shortlist.values())
    if len(shortlisted) < 2:
        st.info("Shortlist at least two repositories from the Search tab to compare them.")
        return

    selected_names = st.multiselect(
        "Choose 2-4 repositories",
        options=[repo.full_name for repo in shortlisted],
        default=[repo.full_name for repo in shortlisted[:2]],
        max_selections=4,
    )
    selected = [repo for repo in shortlisted if repo.full_name in selected_names]

    if len(selected) < 2:
        st.warning("Select at least two repositories.")
        return

    rows = []
    for repo in selected:
        try:
            readme = fetch_readme_cached(repo.owner, repo.name, token)
        except GitHubAPIError:
            readme = None
        analysis = analyze_repo(repo, readme)
        rows.append(
            {
                "Repository": repo.full_name,
                "Score": analysis.score,
                "Level": analysis.level,
                "Maintenance": analysis.maintenance,
                "Docs": analysis.documentation,
                "Risk": analysis.risk,
                "Stars": repo.stars,
                "Forks": repo.forks,
                "Language": repo.language or "Unknown",
                "License": repo.license_name or "Unknown",
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_shortlist() -> None:
    shortlisted = list(st.session_state.shortlist.values())
    if not shortlisted:
        st.info("Your shortlist is empty.")
        return

    for repo in shortlisted:
        cols = st.columns((4, 1))
        cols[0].markdown(f"[{repo.full_name}]({repo.url})")
        if cols[1].button("Remove", key=f"remove:{repo.full_name}", use_container_width=True):
            st.session_state.shortlist.pop(repo.full_name, None)
            st.rerun()

    st.download_button(
        "Export shortlist as Markdown",
        data=_shortlist_markdown(shortlisted),
        file_name="ezzysearch-shortlist.md",
        mime="text/markdown",
        use_container_width=True,
    )


@st.cache_data(ttl=900, show_spinner=False)
def search_repositories_cached(
    query: str,
    language: str,
    min_stars: int,
    sort: str,
    updated_days: int | None,
    include_archived: bool,
    per_page: int,
    token: str | None,
) -> SearchResults:
    updated_after = date.today() - timedelta(days=updated_days) if updated_days else None
    client = GitHubClient(token=token)
    return client.search_repositories(
        SearchParams(
            query=query,
            language=language,
            min_stars=min_stars,
            updated_after=updated_after,
            include_archived=include_archived,
            sort=sort,
            per_page=per_page,
        )
    )


@st.cache_data(ttl=900, show_spinner=False)
def get_repository_cached(owner: str, repo: str, token: str | None) -> RepoResult | None:
    client = GitHubClient(token=token)
    return client.get_repository(owner, repo)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_readme_cached(owner: str, repo: str, token: str | None) -> str | None:
    client = GitHubClient(token=token)
    return client.fetch_readme(owner, repo)


def _ensure_state() -> None:
    st.session_state.setdefault("last_query", "")
    st.session_state.setdefault("shortlist", {})
    st.session_state.setdefault("analysis_requested", set())


def _resolve_token() -> str | None:
    token = get_github_token()
    if token:
        return token

    try:
        secret_token = st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        secret_token = ""

    return str(secret_token).strip() or None


def _parse_repo_reference(query: str) -> tuple[str, str] | None:
    value = query.strip()
    url_match = re.fullmatch(r"https?://github\.com/([^/\s]+)/([^/\s#?]+).*", value)
    if url_match:
        return url_match.group(1), _strip_git_suffix(url_match.group(2))

    shorthand_match = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", value)
    if shorthand_match:
        return shorthand_match.group(1), _strip_git_suffix(shorthand_match.group(2))

    return None


def _strip_git_suffix(repo: str) -> str:
    return repo[:-4] if repo.endswith(".git") else repo


def _repo_caption(repo: RepoResult) -> str:
    details = [
        repo.language or "Unknown language",
        repo.license_name or "No license",
        f"Updated {repo.updated_at[:10]}" if repo.updated_at else "Updated unknown",
    ]
    if repo.archived:
        details.append("Archived")
    return " | ".join(details)


def _format_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _trim_readme(readme: str) -> str:
    return readme[:3000]


def _shortlist_markdown(repos: list[RepoResult]) -> str:
    lines = ["# EzzySearch Shortlist", ""]
    for repo in repos:
        lines.extend(
            [
                f"## {repo.full_name}",
                f"- URL: {repo.url}",
                f"- Description: {repo.description or 'No description provided.'}",
                f"- Stars: {repo.stars}",
                f"- Forks: {repo.forks}",
                f"- Language: {repo.language or 'Unknown'}",
                f"- License: {repo.license_name or 'Unknown'}",
                "",
            ]
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
