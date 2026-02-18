import re
from typing import Optional
import urllib.parse


REPO_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/?$",
    re.IGNORECASE,
)
REPO_SSH_RE = re.compile(
    r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+)$",
    re.IGNORECASE,
)
REPO_SLUG_RE = re.compile(r"^(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)$")


def normalize_repo_slug(value: object) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None

    match = REPO_URL_RE.match(raw)
    if match:
        repo = match.group("repo")
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"{match.group('owner')}/{repo}"

    match = REPO_SSH_RE.match(raw)
    if match:
        repo = match.group("repo")
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"{match.group('owner')}/{repo}"

    match = REPO_SLUG_RE.match(raw)
    if match:
        return f"{match.group('owner')}/{match.group('repo')}"

    return None


def choose_repo_slug_from_env(
    dashboard_repo: object,
    github_repository: object,
    github_actions: object,
) -> Optional[str]:
    configured = normalize_repo_slug(dashboard_repo)
    current = normalize_repo_slug(github_repository)
    actions_enabled = str(github_actions or "").strip().lower() == "true"

    if configured and current:
        if actions_enabled and configured != current:
            # GitHub Actions always runs for the current repository; prefer it when stale
            # DASHBOARD_REPO lags behind a renamed fork.
            return current
        return configured

    return configured or current


def pages_url_from_slug(slug: str) -> str:
    owner, repo = slug.split("/", 1)
    if repo.lower() == f"{owner.lower()}.github.io":
        return f"https://{owner}.github.io/"
    return f"https://{owner}.github.io/{repo}/"


def normalize_dashboard_url(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if not re.match(r"^[a-z][a-z0-9+.-]*://", raw, flags=re.IGNORECASE):
        raw = f"https://{raw.lstrip('/')}"

    parsed = urllib.parse.urlparse(raw)
    scheme = str(parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        return ""

    host = str(parsed.netloc or "").strip()
    if not host:
        return ""

    path = str(parsed.path or "/")
    if not path.startswith("/"):
        path = f"/{path}"
    if not path.endswith("/") and not parsed.query:
        path = f"{path}/"

    return urllib.parse.urlunparse((scheme, host, path, "", parsed.query, ""))
