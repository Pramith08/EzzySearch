from __future__ import annotations

import os


APP_NAME = "EzzySearch"
GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_RESULTS_PER_PAGE = 10
MAX_RESULTS_PER_PAGE = 30


def get_github_token() -> str | None:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    return token or None
