# EzzySearch

EzzySearch is a Streamlit app for discovering and comparing GitHub repositories. It uses the GitHub REST API instead of browser scraping, then scores each repository for beginner friendliness using metadata and README signals.

EzzySearch is not affiliated with GitHub.

## Features

- Search public GitHub repositories by topic or keyword.
- Open an exact repository by entering `owner/repo` or a GitHub repository URL.
- Filter by language, stars, recency, and archived status.
- Sort by best match, stars, forks, or recent updates.
- Analyze a repository's README and metadata.
- Score beginner friendliness, documentation quality, maintenance, setup clarity, and risk.
- Shortlist repositories and export the shortlist as Markdown.
- Compare 2-4 shortlisted repositories.

## Project Structure

```text
main.py                    Streamlit dashboard entrypoint
assets/                    Logo and static assets
ezzysearch/config.py       App configuration
ezzysearch/github_client.py GitHub REST API client
ezzysearch/models.py       Shared data models
ezzysearch/repo_analyzer.py Rule-based beginner-friendliness analyzer
tests/                     Unit tests with mocked API responses
```

## Setup

```bash
git clone https://github.com/Pramith08/EzzySearch.git
cd EzzySearch
python -m pip install -r requirements.txt
```

Optional: set a GitHub token to get higher API limits.

```powershell
$env:GITHUB_TOKEN="your_token_here"
```

## Run

```bash
streamlit run main.py
```

## Test

```bash
python -m pytest -q
```

## Notes

- The app does not scrape GitHub web pages.
- API results are cached in Streamlit to reduce repeated requests.
- README previews are loaded only when a user chooses to analyze a repository.
- If strict filters return no repositories, EzzySearch offers relaxed name matches.
- Full repository content remains on GitHub; EzzySearch links back to original repositories.
