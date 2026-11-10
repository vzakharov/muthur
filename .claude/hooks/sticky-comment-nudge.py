#!/usr/bin/env python3
"""`PreToolUse` hook on `Bash` and the GitHub MCP comment tools: deny, once, a
hand-built write of one of the loop's sticky PR comments — the squash proposal,
the finalize attestation or the review board's link — naming the
`scripts/pr-comment.sh` line that makes it instead.

The script is the one write of those comments that auto mode's approvals cover,
and the skills that name it are not the only way a session comes to touch them:
a relay's next step, an operator's ask, memory. A hook runs before the
classifier, so the agent is pointed at the script before any denial exists for
it to ask its operator a phrase about.

A write counts as sticky when either side of it provably is: its new body leads
with a marker, or the comment it edits already does. The body is read where the
command names it — inline, or a file it names literally; the edited comment is
fetched with `gh` when the call names it literally. Whatever the hook cannot
show passes, so a review reply or an ordinary comment is never refused. The
identical call again in the same session goes through — debugging the script,
say — with the classifier still behind it.

Fails open: an unreadable payload, an untokenisable command, an unreadable file,
a failed fetch or an unrecordable refusal lets the call through.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from session_state import first_sighting, project_root, state_file
from shell_words import WRAPPERS, program, simple_commands, tokens, unwrap

# The home of these markers is `scripts/pr-comment.sh`'s `case`, and
# `scripts/test_sticky_comment_nudge.py` keeps the two equal.
MARKERS = {
    "squash": "Proposed squash",
    "attestation": "<!-- finalize-attestation",
    "review-board": "<!-- review-board",
}
WHAT = {
    "squash": "the squash proposal",
    "attestation": "the finalize attestation",
    "review-board": "the review board's link",
}
LEAD_BYTES = 256
FETCH_SECONDS = 5

MCP_TOOLS = ("mcp__github__add_issue_comment", "mcp__github__update_issue_comment")
ISSUE_COMMENTS = re.compile(r"(?:^|/)issues/([^/]+)/comments/?$")
ONE_COMMENT = re.compile(r"(?:^|/)issues/comments/([^/]+)/?$")
NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
WRITES = ("POST", "PATCH")

# `gh api` options that take the following word as their argument.
API_VALUES = set(
    "-X --method -f --raw-field -F --field -H --header -q --jq -t --template "
    "--input -p --preview --hostname --cache".split()
)
# `gh pr comment` / `gh issue comment` options that take one.
COMMENT_VALUES = {"-b", "--body", "-F", "--body-file", "-R", "--repo"}
LAST_OWN_COMMENT = '[.comments[] | select(.viewerDidAuthor)] | last | .body // ""'


@dataclass
class Write:
    kind: str
    pr: str
    # The body's file when it leads with the marker, for the reason to name.
    file: Optional[Path]
    marked: bool


def kind_of(body: Optional[str]) -> Optional[str]:
    if body is None:
        return None
    return next((kind for kind, marker in MARKERS.items() if body.startswith(marker)), None)


def judge(
    body: Optional[str], edited: Optional[str], pr: str, file: Optional[Path]
) -> Optional[Write]:
    kind = kind_of(body) or kind_of(edited)
    if kind is None:
        return None
    marked = kind_of(body) == kind
    return Write(kind, pr, file if marked else None, marked)


def path_of(word: str, base: Path) -> Optional[Path]:
    """The file a word names, or None when only the shell could say which."""
    if not word or word == "-" or any(c in word for c in "$`*?"):
        return None
    return base / os.path.expanduser(word)


def lead(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        with path.open("rb") as f:
            return f.read(LEAD_BYTES).decode("utf-8", "replace")
    except OSError:
        return None


def fetch(args: list[str], cwd: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["gh", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=FETCH_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def options(
    args: list[str], takes_value: set[str]
) -> tuple[list[tuple[str, str]], list[str], set[str]]:
    """The valued options in order, the operands, and the bare flags of a `gh`
    subcommand's arguments, reading `--flag=value` and `-Xvalue` as well."""
    valued: list[tuple[str, str]] = []
    operands: list[str] = []
    flags: set[str] = set()
    i = 0
    while i < len(args):
        arg = args[i]
        flag, value = arg, None
        if arg.startswith("--") and "=" in arg:
            flag, value = arg.split("=", 1)
        elif not arg.startswith("--") and arg[:2] in takes_value and len(arg) > 2:
            flag, value = arg[:2], arg[2:]
        if flag in takes_value:
            if value is None:
                i += 1
                value = args[i] if i < len(args) else ""
            valued.append((flag, value))
        elif arg.startswith("-") and arg != "-":
            flags.add(arg)
        else:
            operands.append(arg)
        i += 1
    return valued, operands, flags


def api_write(args: list[str], base: Path) -> tuple[Optional[Write], Optional[str]]:
    """The sticky write a `gh api` call makes, and the PR number its path names."""
    valued, operands, _ = options(args, API_VALUES)
    if not operands:
        return None, None
    path = operands[0].split("?", 1)[0]
    listing, single = ISSUE_COMMENTS.search(path), ONE_COMMENT.search(path)
    pr = listing.group(1) if listing and listing.group(1).isdigit() else None
    fields = [(f, v) for f, v in valued if f in ("-f", "--raw-field", "-F", "--field")]
    methods = [value.upper() for flag, value in valued if flag in ("-X", "--method")]
    method = methods[-1] if methods else ("POST" if fields else "GET")
    if not (listing or single) or method not in WRITES:
        return None, pr

    body: Optional[str] = None
    file: Optional[Path] = None
    for flag, field in fields:
        key, _, value = field.partition("=")
        if key != "body":
            continue
        # Only `-F` reads `@<path>` as a file; `-f` sends it as written.
        if flag in ("-F", "--field") and value.startswith("@"):
            file = path_of(value[1:], base)
            body = lead(file)
        else:
            body, file = value, None

    edited = None
    if single and single.group(1).isdigit():
        edited = fetch(["api", path, "--jq", ".body"], base)
    return judge(body, edited, pr or "<n>", file), pr


def comment_write(noun: str, args: list[str], base: Path) -> Optional[Write]:
    """The sticky write a `gh pr comment` or `gh issue comment` makes."""
    valued, operands, flags = options(args, COMMENT_VALUES)
    given = dict(valued)
    text = given.get("-b", given.get("--body"))
    named = given.get("-F", given.get("--body-file"))
    if text is None and named is None:
        return None
    file = path_of(named, base) if text is None and named is not None else None
    body = text if text is not None else lead(file)

    edited = None
    if "--edit-last" in flags:
        repo = given.get("-R", given.get("--repo"))
        view = [noun, "view", *operands[:1], *(["-R", repo] if repo else [])]
        edited = fetch([*view, "--json", "comments", "--jq", LAST_OWN_COMMENT], base)
    pr = operands[0] if operands and operands[0].isdigit() else "<n>"
    return judge(body, edited, pr, file)


def moved(base: Path, args: list[str]) -> Path:
    target = path_of(args[0], base) if args and not args[0].startswith("-") else None
    return target if target is not None and target.is_dir() else base


def bash_write(command: str, base: Path) -> Optional[Write]:
    pr: Optional[str] = None
    for simple in simple_commands(tokens(command)):
        run = program(simple.words)
        while run is not None and run[0] in WRAPPERS:
            run = program(unwrap(*run))
        if run is None:
            continue
        name, args = run
        found: Optional[Write] = None
        if name == "cd":
            base = moved(base, args)
        elif name == "gh" and args[:1] == ["api"]:
            found, named = api_write(args[1:], base)
            pr = named or pr
        elif name == "gh" and args[:1] in (["pr"], ["issue"]) and args[1:2] == ["comment"]:
            found = comment_write(args[0], args[2:], base)
        if found is not None:
            # A write by comment id takes its PR from the lookup chained before it.
            if found.pr == "<n>" and pr:
                found.pr = pr
            return found
    return None


def mcp_write(tool: str, given: dict, base: Path) -> Optional[Write]:
    body = given.get("body")
    if not isinstance(body, str):
        return None
    edited = None
    pr = "<n>"
    if tool == "mcp__github__update_issue_comment":
        owner, repo = str(given.get("owner")), str(given.get("repo"))
        comment = str(given.get("comment_id"))
        if NAME.match(owner) and NAME.match(repo) and comment.isdigit():
            path = f"repos/{owner}/{repo}/issues/comments/{comment}"
            edited = fetch(["api", path, "--jq", ".body"], base)
    else:
        number = str(given.get("issue_number")).removesuffix(".0")
        pr = number if number.isdigit() else "<n>"
    return judge(body, edited, pr, None)


def shown(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root.resolve()))
    except ValueError:
        return str(resolved)


def reason(write: Write, via: str, root: Path) -> str:
    kind, marker = write.kind, MARKERS[write.kind]
    file = shown(write.file, root) if write.file else "<file>"
    if not write.marked:
        body = (
            f" Its new body does not lead with `{marker}`, and an edit that drops the "
            "marker leaves the comment where neither the script nor the skills that "
            "look for it can find it again; the file the script takes must lead with it."
        )
    elif write.file is None:
        body = (
            " The script takes the body from a file, so write it to one first — for "
            "the squash proposal, the working file `/squash-message` keeps."
        )
    else:
        body = ""
    number = " `<n>` is the PR's number." if write.pr == "<n>" else ""
    return (
        f"This {via} writes {WHAT[kind]}, the PR comment leading with `{marker}`, by "
        "hand. `scripts/pr-comment.sh` is the one write of it that auto mode's "
        f"approvals cover: it finds the comment, then edits or posts it.{body} Run it "
        "from the repository root, spelled exactly so, with no `cd … &&` or anything "
        "else chained in front, since the approvals match the command's text:\n\n"
        f"scripts/pr-comment.sh {kind} {write.pr} {file}\n\n"
        f"Put `--update-only` after `{kind}` when it must refresh the comment and "
        f"never create one.{number} If this hand-built write is genuinely what you "
        "mean — debugging the script, say — make the identical call again and it "
        "goes through."
    )


def say(message: str) -> None:
    print(f"sticky-comment-nudge: {message}", file=sys.stderr)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
        tool, given = payload["tool_name"], payload["tool_input"]
    except (ValueError, KeyError, TypeError):
        say("unreadable payload; call allowed.")
        return 0
    if not isinstance(given, dict) or (tool != "Bash" and tool not in MCP_TOOLS):
        return 0
    root = project_root(payload)
    if root is None:
        return 0
    state = state_file(root, "sticky-comment-nudge", payload)
    if state is None:
        return 0

    cwd = payload.get("cwd")
    base = Path(cwd) if isinstance(cwd, str) and Path(cwd).is_dir() else root
    try:
        if tool == "Bash":
            command = given.get("command")
            if not isinstance(command, str):
                return 0
            found, call, via = bash_write(command, base), command, "`gh` command"
        else:
            found = mcp_write(tool, given, base)
            call, via = tool + json.dumps(given, sort_keys=True), f"`{tool}` call"
    except (ValueError, OSError, RuntimeError):
        return 0
    if found is None or not first_sighting(state, call):
        return 0

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason(found, via, root),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
