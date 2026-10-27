"""Whether a branch is finalized: its PR's attestation names a SHA, and nothing
after that SHA touches more than the ledger's rows.

GitHub is asked until the answer is yes; the yes is cached in
`tmp/costs/finalized/<branch>`, and while the cached SHA still holds, later
turns read only the local log. A work commit after it, or a history that no
longer contains it, sends the question back to GitHub.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, Tuple

from lib.github import Client, GitHubError
from lib.ledger_branch import PREFIX, resolve, run
from lib.rows import ROOT
from lib.shape import ShapeError, read_object, required

# `revoked` and a marker with no SHA are attestations that no longer hold.
MARKER = re.compile(r"<!-- finalize-attestation(?: ([0-9a-f]{40}|revoked))? -->")
ORIGIN = re.compile(r"([^/:]+)/([^/]+?)(?:\.git)?/?$")

QUERY = """
query($owner: String!, $name: String!, $branch: String!) {
  repository(owner: $owner, name: $name) {
    pullRequests(headRefName: $branch, first: 1, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes { comments(last: 100) { nodes { body } } }
    }
  }
}
"""


def cache_path(branch: str) -> Path:
    return ROOT / "tmp" / "costs" / "finalized" / branch


def origin_repo() -> Optional[Tuple[str, str]]:
    done = run("remote", "get-url", "origin")
    found = ORIGIN.search(done.stdout.decode().strip()) if done.returncode == 0 else None
    return (found.group(1), found.group(2)) if found else None


def attested(client: Client, owner: str, name: str, branch: str) -> Optional[str]:
    """The SHA the latest PR from `branch` was attested at, if it was."""
    data = client.call(QUERY, {"owner": owner, "name": name, "branch": branch})
    repo = required(read_object, data, "repository", "attestation query")
    pulls = required(read_object, repo, "pullRequests", "attestation query").get("nodes") or []
    if not pulls:
        return None
    comments = required(read_object, pulls[0], "comments", "attestation query").get("nodes") or []
    marks = [found for comment in comments for found in MARKER.finditer(str(comment.get("body", "")))]
    sha = marks[-1].group(1) if marks else None
    return sha if sha not in (None, "revoked") else None


def holds(sha: str) -> bool:
    """HEAD still contains `sha`, and every commit since touches only rows."""
    if resolve(sha) is None or run("merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
        return False
    since = run("log", "--format=%H", f"{sha}..HEAD", "--", ".", f":(exclude){PREFIX}")
    return since.returncode == 0 and since.stdout.strip() == b""


def finalized(branch: str, client: Client) -> bool:
    cache = cache_path(branch)
    cached = cache.read_text(encoding="utf-8").strip() if cache.exists() else None
    if cached and holds(cached):
        return True
    cache.unlink(missing_ok=True)
    repo = origin_repo()
    if repo is None:
        return False
    try:
        sha = attested(client, *repo, branch)
    except (GitHubError, ShapeError, ValueError):
        # A query that fails counts as not finalized: the commit carries its
        # display copy and the next one asks again. The operator approved this
        # fallback for this call site alone: its worst case is a row on a
        # finalized branch, which reaches the trunk only if the branch merges
        # after it, and which the report counts once either way.
        return False
    if sha is None or not holds(sha):
        return False
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(sha + "\n", encoding="utf-8")
    return True
