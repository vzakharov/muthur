#!/usr/bin/env python3
"""Wire every attached repository's hooks into a multi-repo cloud session.

A cloud session with several repositories attached starts in their common
parent and reads hooks only from the parent's `.claude/settings.json`, which no
repository carries — so none of their hooks run. This writes that file from the
hooks each repository's own `.claude/settings.json` declares, each command run
with `CLAUDE_PROJECT_DIR` set to its own repository, then runs the
`SessionStart` hooks at once: the settings watcher picks the file up for every
later event, but the session has already started.

Run by the user-level `SessionStart` hook the environment setup script installs
(`docs/adopting/web-remote.md`), or by the agent per
`.claude/rules/multi-repo.md` where that hook is missing. In a single-repo
session it exits 0 and writes nothing, since the repository's hooks already run.

Usage: multi-repo-hooks.py [--primary <repo>] [--run-session-start]

`--primary` names the repository session-wide hooks run from — the session's
first source, which only the agent can read (`get_session`); absent, the
alphabetically first repository carrying the hook. `--run-session-start` runs
the `SessionStart` hooks even when the file on disk is already current, which
otherwise means Claude Code loaded it at this start and runs them itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

from lib.session import Session

ANCHOR = Path(__file__).resolve().parent.parent
PROJECT_DIR_VAR = re.compile(r"\$\{?CLAUDE_PROJECT_DIR\}?")

# Hooks whose effect belongs to their own repository — or which check that a
# path lies inside `CLAUDE_PROJECT_DIR`, so exactly one copy acts — run once per
# repository carrying them. A cost row lands in each repository, as does the
# estimate its vet run checks; a cross-repo sum counts a shared session more
# than once, which is the accepted cost of keeping each ledger whole.
PER_REPO = frozenset(
    {
        ".claude/hooks/install-deps.sh",
        "scripts/muthur-sync.sh",
        ".claude/hooks/format-md.sh",
        ".claude/hooks/file-tools-nudge.py",
        ".claude/costs/hooks/stop-session-cost.sh",
        ".claude/costs/hooks/stage-cost-row.sh",
        ".claude/costs/hooks/estimate-notice.sh",
    }
)
# A bare `#12` in a prompt names no repository, so exporting it in each would
# take three different threads. `/take-issue` and `/handle` export on their own
# when the hook has not.
SKIPPED = frozenset(
    {
        ".claude/hooks/prompt-issue-export.sh",
        ".claude/hooks/prompt-handle-pr-export.sh",
    }
)
# Everything else is session-wide and runs once.

STAMP = "multi-repo-hooks.sha256"


def hook_key(command: str) -> str:
    """The repo-relative script a hook command runs: its classification key."""
    stripped = PROJECT_DIR_VAR.sub("", command, count=1).lstrip("/")
    return shlex.split(stripped)[0] if stripped else ""


def localize(command: str, repo: Path) -> str:
    # The variable is spelled out rather than left to the prefix, because the
    # shell expands a command's arguments before a `VAR=value cmd` prefix applies.
    quoted = shlex.quote(str(repo))
    return f"CLAUDE_PROJECT_DIR={quoted} " + PROJECT_DIR_VAR.sub(quoted, command)


def repo_hooks(repo: Path) -> dict[str, list[dict]]:
    path = repo / ".claude" / "settings.json"
    if not path.is_file():
        return {}
    hooks = json.loads(path.read_text()).get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path}: `hooks` is not an object")
    return hooks


def build(session: Session, primary: Path | None) -> dict:
    """The parent's settings: every repository's hooks, sorted per PER_REPO/SKIPPED."""
    order = sorted(session.repos, key=lambda r: (r != primary, r.name))
    taken: set[tuple[str, str | None, str]] = set()
    events: dict[str, list[dict]] = {}
    for repo in order:
        for event, groups in repo_hooks(repo).items():
            for group in groups:
                matcher = group.get("matcher")
                kept = []
                for hook in group.get("hooks", []):
                    command = hook.get("command", "")
                    key = hook_key(command)
                    if key in SKIPPED:
                        continue
                    if key not in PER_REPO:
                        once = (event, matcher, PROJECT_DIR_VAR.sub("", command))
                        if once in taken:
                            continue
                        taken.add(once)
                    kept.append({**hook, "command": localize(command, repo)})
                if kept:
                    entry = {"matcher": matcher} if matcher is not None else {}
                    events.setdefault(event, []).append({**entry, "hooks": kept})
    return {"hooks": events}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def write(session: Session, settings: dict) -> bool:
    """Write the parent's settings; True when the file on disk changed.

    A settings file there that this script did not write — no stamp, or a stamp
    that no longer matches — is someone's own, and is refused, never replaced.
    """
    directory = session.root / ".claude"
    target, stamp = directory / "settings.json", directory / STAMP
    text = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
    if target.exists():
        current = target.read_text()
        if not stamp.is_file() or stamp.read_text().strip() != digest(current):
            raise FileExistsError(
                f"{target} exists and was not written by this script; "
                "merge its hooks by hand or move it aside, then rerun."
            )
        if current == text:
            return False
    directory.mkdir(exist_ok=True)
    target.write_text(text)
    stamp.write_text(digest(text) + "\n")
    return True


def transcript_path(root: Path, session_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(root))
    return str(Path.home() / ".claude" / "projects" / slug / f"{session_id}.jsonl")


def start_payload(session: Session, received: str) -> str:
    """The SessionStart payload the hooks read: the one Claude Code sent, when
    a hook ran this script, else one built to the same shape."""
    try:
        sent = json.loads(received) if received.strip() else None
    except ValueError:
        sent = None
    if isinstance(sent, dict) and sent.get("hook_event_name") == "SessionStart":
        return json.dumps({**sent, "source": "startup"})
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    return json.dumps(
        {
            "session_id": session_id,
            "transcript_path": transcript_path(session.root, session_id),
            "cwd": str(session.root),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )


def run_session_start(session: Session, settings: dict, payload: str) -> bool:
    """Run the `startup` SessionStart hooks, relaying what each adds to context.

    Every hook runs whatever an earlier one did; True only when all succeeded.
    """
    ok = True
    for group in settings["hooks"].get("SessionStart", []):
        matcher = group.get("matcher")
        if matcher and not re.fullmatch(matcher, "startup"):
            continue
        for hook in group["hooks"]:
            command = hook["command"]
            try:
                result = subprocess.run(
                    ["bash", "-c", command],
                    input=payload,
                    capture_output=True,
                    text=True,
                    cwd=session.root,
                    timeout=hook.get("timeout", 600),
                )
            except subprocess.TimeoutExpired:
                ok = False
                print(f"multi-repo-hooks: `{command}` timed out", file=sys.stderr)
                continue
            print(context_of(result.stdout), end="")
            if result.returncode != 0:
                ok = False
                print(
                    f"multi-repo-hooks: `{command}` exited "
                    f"{result.returncode}: {result.stderr.strip()}",
                    file=sys.stderr,
                )
    return ok


def context_of(stdout: str) -> str:
    """What a hook's stdout adds to the session's context, as plain text.

    A hook answers either with text, which Claude Code takes as is, or with the
    JSON shape `.claude/hooks/lib.sh`'s `emit_context` writes.
    """
    try:
        parsed = json.loads(stdout)
    except ValueError:
        return stdout
    ctx = parsed.get("hookSpecificOutput", {}).get("additionalContext")
    return ctx + "\n" if isinstance(ctx, str) else stdout


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--primary")
    parser.add_argument("--run-session-start", action="store_true")
    args = parser.parse_args(argv)

    session = Session.detect(ANCHOR)
    if not session.multi_repo:
        return 0
    primary = session.repo_named(args.primary) if args.primary else None
    settings = build(session, primary)
    changed = write(session, settings)
    print(
        f"multi-repo-hooks: {session.root}/.claude/settings.json "
        f"{'written' if changed else 'already current'} for {session.names}."
    )
    if changed or args.run_session_start:
        received = "" if sys.stdin.isatty() else sys.stdin.read()
        payload = start_payload(session, received)
        return 0 if run_session_start(session, settings, payload) else 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except (FileExistsError, ValueError) as exc:
        print(f"multi-repo-hooks: {exc}", file=sys.stderr)
        sys.exit(1)
