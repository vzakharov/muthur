"""The PR export the branch last committed — what the agent had already seen.

`/handle` Step 2 commits every export it reads, so the copy on the PR's head
branch is the record of the last look. The awaiting verdict counts a review or
comment that copy does not carry as new.

The copy comes off the local branch when the PR's head is checked out, its
commits being the newest and possibly unpushed; otherwise off the PR's head
commit through the contents API. The second route is the ordinary one for the
`/handle` hook, which runs at a session's first prompt while HEAD is still the
harness's auto-branch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, NamedTuple

from gh_export.api import request
from lib.github import AllRoutesFailed


class PreviousExport(NamedTuple):
    text: str
    # A short SHA, naming the commit the copy was read from.
    commit: str


def previous_export(
    md_path: Path, pr: dict[str, Any], repo: str, token: str
) -> PreviousExport | None:
    """`None` when the branch has never committed an export at `md_path`."""
    head = pr.get("head") or {}
    if head.get("ref") and _git("branch", "--show-current") == head.get("ref"):
        text = _git("show", f"HEAD:./{md_path.as_posix()}")
        sha = _git("rev-parse", "--short=7", "HEAD")
        return PreviousExport(text, sha or "HEAD") if text is not None else None

    sha = head.get("sha") or ""
    url = (
        f"https://api.github.com/repos/{repo}/contents/{md_path.as_posix()}"
        f"?ref={sha}"
    )
    try:
        body, _ = request(url, token, "application/vnd.github.raw")
    except AllRoutesFailed as exc:
        if any(f.status.startswith("404") for f in exc.failures):
            return None
        raise
    return PreviousExport(body.decode("utf-8"), sha[:7])


def _git(*args: str) -> str | None:
    """Stdout without its trailing newline, or `None` when git refuses —
    outside a repository, or for a path the commit does not carry."""
    done = subprocess.run(["git", *args], capture_output=True, text=True)
    return done.stdout.rstrip("\n") if done.returncode == 0 else None
