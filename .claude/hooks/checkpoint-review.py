#!/usr/bin/env python3
"""Hold a session on a model below Opus to the Opus checkpoint review at each
cutoff of `/plan`, `/go` and `/finalize`. `/handle` has no cutoff of its own: its lanes
load `/go` or `/plan`, which enter the gate by `skill_entry.py`'s Read route.

As a hook, on two events, each its own registration in `.claude/settings.json`:

- entering one of those skills, by any route `skill_entry.py` names, marks the
  cutoff **entered** in `tmp/checkpoint-review/<session>`, and on a weaker model
  delivers `checkpoint-review.md` the first time. A subagent's own entry — the
  reviewer opening skill files — marks nothing;
- `PreToolUse` on `Bash` denies the command that closes an entered cutoff while
  the session's serving model is weaker and the branch carries no passing
  review at its head — the `git mv` out of `*.draft.do-not-implement.md`
  (`plan`), the `git mv` to `*.completed.md` (`go`), `gh pr ready`
  (`finalize`).

The verdict lives in git, not in the session: the reviewer commits only on a
verdict that lets the session carry on (`go/review.md` § "The commit"), so the
gate opens when the branch carries such a commit and nothing since it needs
review — the diff from it to `HEAD`, as `scripts/floor.py` computes it, touches
only the loop's working artifacts. A session that skips the review, edits after
it, or fixes a vet failure or merge conflict after it finds the gate shut.

The serving model is the one the transcript records on the session's latest
reply. An entry is marked whatever the model, because a typed command in a
session's first prompt arrives before any reply records one; the gate, which
runs later, decides.

What the gate cannot see: whether the reviewer was Opus, or was launched from the
one line; and a `review(...)` commit the session wrote itself. It guards a
review skipped or outdated by later edits. The base is `origin/HEAD`'s branch,
else `main`, unfetched: a PR on another base reads a wider range, which still
finds the branch's newest review commit.

`MUTHUR_CHECKPOINT_REVIEW=off` makes it a no-op. The hook fails open — an
unreadable payload, transcript, state or repository is stderr and exit 0, never
a blocked turn.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterator, List, Optional

from session_state import project_root, state_file
from skill_entry import entered_skill


@functools.lru_cache(maxsize=None)
def floor_module() -> ModuleType:
    # `scripts/` is not on a hook's import path; the floor's lookup lives there so
    # that `/polish`, the reviewer and this gate share one copy of it. Loaded on
    # first use, so that a missing file fails open like any other unreadable input.
    path = Path(__file__).resolve().parents[2] / "scripts" / "floor.py"
    spec = importlib.util.spec_from_file_location("floor", path)
    if spec is None or spec.loader is None:
        raise OSError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SWITCH = "MUTHUR_CHECKPOINT_REVIEW"
HOOK = "checkpoint-review"
PROCEDURE = Path(".claude") / "skills" / "go" / "checkpoint-review.md"
CUTOFFS = {"plan": "plan", "go": "go", "implement": "go", "finalize": "finalize"}
# The verdicts the reviewer commits, `go/review.md` § "The commit".
REVIEWED = ("review(pass):", "review(fixed):", "review(fixed-relay):")
WEAKER = ("sonnet", "haiku")
CHUNK = 1 << 16
WORKING_ARTIFACTS = ("docs/issue/", "docs/pr/", "docs/remove-before-merging/")
PLANS = "docs/plans/"

# A closing command sits at command position: the start, or after `;`, `&&`,
# `||`, `|`, a newline or `(`, with optional `VAR=value` prefixes. A quoted
# string or heredoc body has its separators masked first (`masked`), so a commit
# message quoting `gh pr ready` is not that command.
POSITION = r"(?:^|[;&|\n(])\s*(?:\w+=\S*\s+)*"
CLOSES = {
    "plan": re.compile(POSITION + r"git\s+mv\b[^;&|\n]*\.draft\.do-not-implement\.md"),
    "go": re.compile(POSITION + r"git\s+mv\b[^;&|\n]*\.completed\.md\b"),
    "finalize": re.compile(POSITION + r"gh\s+pr\s+ready\b(?![^;&|\n]*--undo)"),
}
QUOTED = re.compile(r"\"(?:\\.|[^\"\\])*\"|'[^']*'", re.S)
HEREDOC = re.compile(r"(<<-?[ \t]*(['\"]?)(\w+)\2[^\n]*\n)(.*?)(\n[ \t]*\3[ \t]*(?:\n|$))", re.S)
SEPARATORS = re.compile(r"[;&|\n(]")


def say(message: str) -> None:
    print(f"{HOOK}: {message}", file=sys.stderr)


def lines_backwards(path: Path) -> Iterator[bytes]:
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        end = handle.tell()
        rest = b""
        while end > 0:
            start = max(0, end - CHUNK)
            handle.seek(start)
            block = handle.read(end - start) + rest
            end = start
            lines = block.split(b"\n")
            rest = lines.pop(0)
            yield from reversed(lines)
        yield rest


def serving_model(transcript: Path) -> Optional[str]:
    for line in lines_backwards(transcript):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        message = entry.get("message")
        model = message.get("model") if isinstance(message, dict) else None
        if isinstance(model, str) and model != "<synthetic>":
            return model
    return None


def weaker(payload: dict) -> bool:
    transcript = payload.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        return False
    try:
        model = serving_model(Path(transcript))
    except OSError as error:
        say(f"cannot read the transcript ({error}); treated as not weaker.")
        return False
    return model is not None and any(name in model.lower() for name in WEAKER)


def masked(command: str) -> str:
    def blank(match: "re.Match[str]") -> str:
        return SEPARATORS.sub(" ", match.group())

    command = QUOTED.sub(blank, command)
    return HEREDOC.sub(lambda m: m.group(1).rstrip("\n") + " " + SEPARATORS.sub(" ", m.group(4)) + m.group(5), command)


def base_ref(root: Path) -> str:
    floor = floor_module()
    try:
        return floor.git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip()
    except floor.GitError:
        return "origin/main"


def changes_since(root: Path, review: str, base: str) -> List[tuple]:
    """`(status, paths)` per change from the review commit to HEAD with the base
    merged in below the line, as `scripts/floor.py` computes it."""
    floor = floor_module()
    tree = floor.scope_start(root, base, review)
    tokens = floor.git(root, "diff", "--name-status", "-z", "-M", tree, "HEAD").split("\0")
    changes: List[tuple] = []
    index = 0
    while index < len(tokens) and tokens[index]:
        status = tokens[index]
        count = 2 if status[0] in "RC" else 1
        changes.append((status, tokens[index + 1 : index + 1 + count]))
        index += 1 + count
    return changes


def is_working_artifact(status: str, paths: List[str]) -> bool:
    if all(path.startswith(WORKING_ARTIFACTS) for path in paths):
        return True
    return all(path.startswith(PLANS) for path in paths) and status in ("D", "R100")


def review_gap(root: Path) -> Optional[str]:
    """Why the branch has no passing review at its head, or None when it has one."""
    base = base_ref(root)
    review = floor_module().find_floor(root, base, REVIEWED)
    if review is None:
        return "no checkpoint review has let this branch through"
    later = [paths for status, paths in changes_since(root, review[0], base) if not is_working_artifact(status, paths)]
    if later:
        return f"work changed after the last review ({later[0][0]})"
    return None


def load(state: Path) -> dict:
    try:
        data = json.loads(state.read_text())
    except FileNotFoundError:
        return {"entered": [], "delivered": False}
    if not isinstance(data, dict) or not isinstance(data.get("entered"), list):
        raise ValueError(f"{state} is not a checkpoint-review state")
    return data


def save(state: Path, data: dict) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(data))


def emit(event: str, fields: dict) -> None:
    json.dump({"hookSpecificOutput": {"hookEventName": event, **fields}}, sys.stdout)


def on_entry(payload: dict, root: Path, state: Path, skill: str) -> None:
    data = load(state)
    if skill not in data["entered"]:
        data["entered"].append(skill)
    deliver = not data.get("delivered") and weaker(payload)
    text = None
    if deliver:
        try:
            text = (root / PROCEDURE).read_text()
        except OSError as error:
            say(f"cannot read {PROCEDURE} ({error}); not delivered.")
        data["delivered"] = text is not None
    save(state, data)
    if text is not None:
        emit(
            payload["hook_event_name"],
            {
                "additionalContext": (
                    f"This session runs below Opus, so `/{skill}` ends in an Opus checkpoint review. "
                    f"The procedure is below — this is its read.\n\n===== {PROCEDURE} =====\n{text}"
                )
            },
        )


def on_bash(payload: dict, root: Path, state: Path) -> None:
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return
    command = masked(command)
    closing = [skill for skill, pattern in CLOSES.items() if pattern.search(command)]
    if not closing:
        return
    entered = [skill for skill in closing if skill in load(state)["entered"]]
    if not entered or not weaker(payload):
        return
    gap = review_gap(root)
    if gap is None:
        return
    emit(
        "PreToolUse",
        {
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"This command closes the `/{entered[0]}` cutoff, and {gap}. Run the checkpoint "
                f"review per `{PROCEDURE}` — it reviews what is missing — act on its verdict, and "
                f"run this command again."
            ),
        },
    )


def hook() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        say("unreadable payload; nothing checked.")
        return 0
    if not isinstance(payload, dict):
        return 0
    root = project_root(payload)
    if root is None:
        return 0
    state = state_file(root, HOOK, payload)
    if state is None:
        return 0
    try:
        if payload.get("hook_event_name") == "PreToolUse":
            if payload.get("tool_name") == "Bash":
                on_bash(payload, root, state)
            return 0
        if payload.get("agent_id"):
            return 0
        skill = CUTOFFS.get(entered_skill(payload, root) or "")
        if skill is not None:
            on_entry(payload, root, state, skill)
    except (OSError, ValueError) as error:
        say(f"{error}; nothing checked.")
    return 0


def main() -> int:
    if os.environ.get(SWITCH) == "off":
        return 0
    return hook()


if __name__ == "__main__":
    sys.exit(main())
