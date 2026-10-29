#!/usr/bin/env python3
"""Hold a session on a model below Opus to `checkpoint-review.md` at each cutoff
of `/plan`, `/go` and `/finalize`. `/handle` has no cutoff of its own: its lanes
load `/go` or `/plan`, which enter the gate by `skill_entry.py`'s Read route.

As a hook, on three events, each its own registration in `.claude/settings.json`:

- entering one of those skills, by any route `skill_entry.py` names, marks its
  review pending in `tmp/checkpoint-review/<session>`, and on a weaker model
  delivers `checkpoint-review.md` the first time;
- `PreToolUse` on `Bash` denies the command that closes a cutoff whose review
  is pending, while the session's serving model is weaker — the `git mv` out of
  `*.draft.do-not-implement.md` (`plan`), the `git mv` to `*.completed.md`
  (`go`), `gh pr ready` (`finalize`).

The serving model is the one the transcript records on the session's latest
reply. An entry is marked whatever the model, because a typed command in a
session's first prompt arrives before any reply records one; the gate, which
runs later, decides.

As a command, `checkpoint-review.py verdict <session> <skill> <verdict>`
records a verdict: any but `revise` clears that skill's review.

`MUTHUR_CHECKPOINT_REVIEW=off` makes both a no-op. The hook fails open — an
unreadable payload, transcript or state is stderr and exit 0, never a blocked
turn; the command fails loudly, being what the session runs on purpose.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Iterator, Optional

from session_state import project_root, state_file
from skill_entry import entered_skill

SWITCH = "MUTHUR_CHECKPOINT_REVIEW"
HOOK = "checkpoint-review"
PROCEDURE = Path(".claude") / "skills" / "go" / "checkpoint-review.md"
CUTOFFS = {"plan": "plan", "go": "go", "implement": "go", "finalize": "finalize"}
VERDICTS = ("pass", "revise", "fixed", "fixed-relay", "relay")
WEAKER = ("sonnet", "haiku")
CHUNK = 1 << 16

# A command chained after `;`, `&&` or a newline is its own command, so each
# pattern stops at the separators.
CLOSES = {
    "plan": re.compile(r"\bgit\s+mv\b[^;&|\n]*\.draft\.do-not-implement\.md"),
    "go": re.compile(r"\bgit\s+mv\b[^;&|\n]*\.completed\.md\b"),
    "finalize": re.compile(r"\bgh\s+pr\s+ready\b(?![^;&|\n]*--undo)"),
}


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


def load(state: Path) -> dict:
    try:
        data = json.loads(state.read_text())
    except FileNotFoundError:
        return {"pending": [], "delivered": False}
    if not isinstance(data, dict) or not isinstance(data.get("pending"), list):
        raise ValueError(f"{state} is not a checkpoint-review state")
    return data


def save(state: Path, data: dict) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(data))


def emit(event: str, fields: dict) -> None:
    json.dump({"hookSpecificOutput": {"hookEventName": event, **fields}}, sys.stdout)


def on_entry(payload: dict, root: Path, state: Path, skill: str) -> None:
    data = load(state)
    if skill not in data["pending"]:
        data["pending"].append(skill)
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
                    f"This session runs below Opus, so `/{skill}` ends in a checkpoint review. "
                    f"The procedure is below — this is its read. Your session id for its verdict "
                    f"command is `{payload['session_id']}`.\n\n===== {PROCEDURE} =====\n{text}"
                )
            },
        )


def on_bash(payload: dict, state: Path) -> None:
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return
    closing = [skill for skill, pattern in CLOSES.items() if pattern.search(command)]
    if not closing:
        return
    pending = [skill for skill in closing if skill in load(state)["pending"]]
    if not pending or not weaker(payload):
        return
    skill = pending[0]
    emit(
        "PreToolUse",
        {
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"The checkpoint review of `/{skill}` has not recorded a verdict, and this command "
                f"closes that cutoff. Run the review per `{PROCEDURE}`, then record its verdict with "
                f"`python3 .claude/hooks/checkpoint-review.py verdict {payload['session_id']} {skill} <verdict>`, "
                f"and run this command again."
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
                on_bash(payload, state)
            return 0
        skill = CUTOFFS.get(entered_skill(payload, root) or "")
        if skill is not None:
            on_entry(payload, root, state, skill)
    except (OSError, ValueError) as error:
        say(f"{error}; nothing checked.")
    return 0


def verdict(args: list) -> int:
    usage = f"usage: checkpoint-review.py verdict <session-id> <{'|'.join(sorted(set(CUTOFFS.values())))}> <{'|'.join(VERDICTS)}>"
    if len(args) != 3 or args[1] not in CUTOFFS or args[2] not in VERDICTS:
        print(usage, file=sys.stderr)
        return 2
    session, skill, given = args[0], CUTOFFS[args[1]], args[2]
    root = project_root({"cwd": os.getcwd()})
    state = state_file(root, HOOK, {"session_id": session}) if root else None
    if state is None:
        print(f"{HOOK}: no state can be kept for session {session!r} here.", file=sys.stderr)
        return 2
    data = load(state)
    if given != "revise" and skill in data["pending"]:
        data["pending"].remove(skill)
    save(state, data)
    still = "still pending" if skill in data["pending"] else "cleared"
    print(f"{HOOK}: {given} recorded for /{skill}; its review is {still}.")
    return 0


def main() -> int:
    if os.environ.get(SWITCH) == "off":
        return 0
    if sys.argv[1:2] == ["verdict"]:
        return verdict(sys.argv[2:])
    return hook()


if __name__ == "__main__":
    sys.exit(main())
