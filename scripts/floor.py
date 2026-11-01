#!/usr/bin/env python3
"""Print where a branch-local pass's scope starts: the branch's own change since
the newest commit that pass left, or its whole change when it has left none.

Usage:
  python3 scripts/floor.py [--full] [--base BRANCH] TYPE...

TYPE is a commit subject's first token, exactly — `polish:`, `review(pass):` —
and the **floor** is the newest commit in `origin/<base>..HEAD` whose subject
opens with one of them. Two lines go to stdout:

  floor <sha> <subject>        or   floor none
  from <ref>

`git diff <ref>` is the scope, uncommitted edits to tracked files included.
`--full` ignores the floor and starts at the base, as a branch with none does.

The base is `--base`, else the PR's base branch from `gh`, else the branch
`origin/HEAD` names, else `main`, and it is fetched first: `origin/<base>` in a
working copy is as old as the clone, and a range against a stale one reads every
commit the base has landed since as this branch's work.

With a floor, `<ref>` is the floor merged with the base commit the branch has
taken in, never the floor itself. A branch that merges its base after the floor
carries everything the base landed in between, which the base's own PRs already
reviewed; the virtual merge puts it below the line, so what remains is the
branch's own commits since the floor on either side of the merge, plus the
merge's conflict resolutions — text written at merge time that nobody has read.
Where the real merge conflicted, the virtual one holds the conflict markers and
the diff shows the resolution against them. With no base merge since the floor,
`<ref>` is the floor's own tree.

The lookup's range being two-dot is what keeps it honest without bookkeeping: a
marked commit the base carries is never a floor, and one a rebase, amend or reset
rewrote away cannot come back as one.

`.claude/hooks/checkpoint-review.py` imports `origin_head`, `find_floor` and
`scope_start`, without `gh` or the fetch: a hook does not reach the network.

Exit status is non-zero when git cannot answer — the fetch, a ref, the merge.
Stdlib only — no third-party deps. Python 3.9+.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NoReturn, Optional, Sequence, Tuple


class GitError(ValueError):
    pass


def git(root: Path, *args: str, ok: Tuple[int, ...] = (0,)) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode not in ok:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip() or result.returncode}")
    return result.stdout


def find_floor(root: Path, base: str, types: Sequence[str]) -> Optional[Tuple[str, str]]:
    """The newest `(sha, subject)` in `base..HEAD` whose subject's first token is
    one of `types`, or None."""
    for line in git(root, "log", f"{base}..HEAD", "--format=%H %s").splitlines():
        sha, _, subject = line.partition(" ")
        if subject.split(" ", 1)[0] in types:
            return sha, subject
    return None


def scope_start(root: Path, base: str, floor: Optional[str]) -> str:
    merge_base = git(root, "merge-base", "HEAD", base).strip()
    if floor is None:
        return merge_base
    # merge-tree exits 1 on a conflict, the case the virtual merge exists for, and
    # also on a ref it cannot read; the cat-file check tells the two apart.
    merged = git(root, "merge-tree", "--write-tree", "--name-only", floor, merge_base, ok=(0, 1))
    tree = merged.splitlines()[0] if merged else ""
    git(root, "cat-file", "-e", f"{tree}^{{tree}}")
    return tree


def pr_base(root: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "--json", "baseRefName", "--jq", ".baseRefName"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def origin_head(root: Path) -> str:
    """The branch `origin/HEAD` names, else `main` — the base when no PR names one."""
    try:
        return git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip().removeprefix("origin/")
    except GitError:
        return "main"


def default_base(root: Path) -> str:
    found = pr_base(root)
    return found if found is not None else origin_head(root)


def _die(message: str) -> NoReturn:
    print(f"floor: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print where a branch-local pass's scope starts.")
    parser.add_argument("types", nargs="+", metavar="TYPE", help="a commit subject's first token, exactly")
    parser.add_argument("--full", action="store_true", help="ignore the floor and start at the base")
    parser.add_argument("--base", help="the branch this work merges into (default: the PR's base)")
    args = parser.parse_args()

    root = Path.cwd()
    try:
        base = args.base or default_base(root)
        git(root, "fetch", "--quiet", "origin", base)
        ref = f"origin/{base}"
        floor = find_floor(root, ref, args.types)
        start = scope_start(root, ref, None if args.full or floor is None else floor[0])
    except GitError as error:
        _die(str(error))
    print(f"floor {floor[0]} {floor[1]}" if floor else "floor none")
    print(f"from {start}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
