#!/usr/bin/env python3
"""Print the attached repository a branch, `#N` or GitHub URL belongs to.

A skill acting on a branch, PR or issue runs this first in a session with
several repositories attached (`.claude/rules/multi-repo.md`), then works in the
path it prints. In a single-repo session it prints that repository without
looking, so a skill can call it whatever the mode.

Usage: find-repo.py <branch | #N | https://github.com/<owner>/<repo>/...>

- A branch is looked up with `git ls-remote` on each repository's `origin`.
- A URL is matched against each repository's `origin`, with no network call.
- `#N` is asked of each repository's GitHub API (`issues/N` answers for a PR
  too) through `gh`, which in a cloud session is the shim that gets past the
  proxy.

Exit 0 with the path on stdout when exactly one repository matches; 1 when none
does; 2 when several do, naming them — the session's own auto-branch exists in
every attached repository, and a number can be taken in each, so the caller
asks the operator rather than picking; 3 when a lookup itself failed, since a
repository that could not be asked is not one known to lack the target.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from lib.github import detect_origin_repo
from lib.session import Session

ANCHOR = Path(__file__).resolve().parent.parent
GITHUB_URL = re.compile(r"^https://github\.com/([^/]+)/([^/#?]+)")
NUMBER = re.compile(r"^#(\d+)$")


def has_branch(repo: Path, branch: str) -> bool:
    out = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return bool(out.strip())


def has_number(repo: Path, number: str) -> bool:
    origin = detect_origin_repo(repo)
    if origin is None:
        return False
    result = subprocess.run(
        ["gh", "api", f"repos/{origin}/issues/{number}", "--silent"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    if "HTTP 404" in result.stderr:
        return False
    raise RuntimeError(f"`gh api repos/{origin}/issues/{number}`: {result.stderr.strip()}")


def matches(session: Session, target: str) -> list[Path]:
    url = GITHUB_URL.match(target)
    if url:
        wanted = f"{url.group(1)}/{url.group(2).removesuffix('.git')}".lower()
        return [r for r in session.repos if (detect_origin_repo(r) or "").lower() == wanted]
    number = NUMBER.match(target)
    if number:
        return [r for r in session.repos if has_number(r, number.group(1))]
    return [r for r in session.repos if has_branch(r, target)]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.split("\n\n")[2], file=sys.stderr)
        return 64
    target = argv[0]
    session = Session.detect(ANCHOR)
    if not session.multi_repo:
        print(session.repos[0])
        return 0
    found = matches(session, target)
    if len(found) == 1:
        print(found[0])
        return 0
    if not found:
        print(
            f"find-repo: {target} is in none of the attached repositories: "
            + session.names,
            file=sys.stderr,
        )
        return 1
    print(
        f"find-repo: {target} is in several attached repositories: "
        + ", ".join(r.name for r in found),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        detail = getattr(exc, "stderr", None) or str(exc)
        print(f"find-repo: {detail.strip()}", file=sys.stderr)
        sys.exit(3)
