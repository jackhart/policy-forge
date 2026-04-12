"""Fetch and manage policy documents from the tau2-bench repo."""

from pathlib import Path
from urllib.request import urlopen

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

REPO = "sierra-research/tau2-bench"
DEFAULT_TAG = "main"

SOURCES = {
    "airline": "data/tau2/domains/airline/policy.md",
    "retail": "data/tau2/domains/retail/policy.md",
}


def raw_url(repo_path: str, tag: str = DEFAULT_TAG) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{tag}/{repo_path}"


def fetch(domain: str, tag: str = DEFAULT_TAG) -> Path:
    """Fetch a policy doc from tau2-bench and cache it locally.

    Returns the local path. Skips download if the file already exists
    (delete it manually to re-fetch).
    """
    if domain not in SOURCES:
        raise ValueError(f"Unknown domain {domain!r}, expected one of {list(SOURCES)}")

    repo_path = SOURCES[domain]
    dest = DATA_DIR / domain / "policy.md"

    if dest.exists():
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    url = raw_url(repo_path, tag)
    with urlopen(url) as resp:
        dest.write_bytes(resp.read())

    return dest


def policy_text(domain: str, tag: str = DEFAULT_TAG) -> str:
    """Fetch the policy doc and return its text."""
    return fetch(domain, tag).read_text()
