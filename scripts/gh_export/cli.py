"""Argument parsing for `scripts/export-github-item.py`."""

from __future__ import annotations

import re

from lib.github import detect_origin_repo, die

USAGE = (
    "Usage: python3 scripts/export-github-item.py "
    "<number|https://github.com/OWNER/REPO/issues/N"
    "|https://github.com/OWNER/REPO/pull/N> [--repo OWNER/REPO] [--include-resolved]"
)


def parse_args(argv: list[str]) -> tuple[int, str, bool]:
    """`(number, OWNER/REPO, include_resolved)`. `--include-resolved` keeps
    resolved review threads, which a PR export drops by default."""
    rest = [a for a in argv[1:] if a != "--"]
    repo_flag: str | None = None
    include_resolved = False
    nums: list[int] = []
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--repo" and i + 1 < len(rest):
            repo_flag = rest[i + 1]
            i += 2
            continue
        if arg == "--include-resolved":
            include_resolved = True
            i += 1
            continue
        m_url = re.match(
            r"^https://github\.com/([^/]+)/([^/]+)/(?:issues|pull)/(\d+)/?$",
            arg.strip(),
            re.IGNORECASE,
        )
        if m_url:
            repo_flag = f"{m_url.group(1)}/{m_url.group(2)}"
            nums.append(int(m_url.group(3)))
            i += 1
            continue
        m_num = re.match(r"^#?(\d+)$", arg)
        if m_num:
            nums.append(int(m_num.group(1)))
        i += 1

    if len(nums) != 1:
        die(USAGE)

    if repo_flag is None:
        repo_flag = detect_origin_repo()
        if repo_flag is None:
            die(
                "Could not determine OWNER/REPO. Pass --repo OWNER/REPO, give a full "
                "issue or PR URL, or run from a checkout whose `origin` is a "
                "github.com repo."
            )

    parts = repo_flag.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        die("--repo and item URLs must use OWNER/REPO (e.g. octocat/hello-world).")

    return nums[0], repo_flag, include_resolved
