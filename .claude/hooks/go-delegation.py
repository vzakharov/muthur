#!/usr/bin/env python3
"""Deliver `/go`'s delegation procedure the first time `/go` enters a session.

`.claude/skills/go/SKILL.md` points at `delegation.md` only conditionally, so
that `MUTHUR_DELEGATION=off` leaves `/go` reading as if delegation had never
been written. This hook saves the agent the round trip: it prints
`delegation.md` and `delegation-model-capabilities.md` as additional context
when `/go`'s body arrives, or that of its redirect `implement`, by any of the
routes `skill_entry.py` names.

Once per session: a marker under `tmp/go-delegation/` keeps a later entry
silent, the files being in context already. Fails open — an unreadable payload
or a missing file is stderr and exit 0, never a failed turn.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from session_state import project_root, state_file
from skill_entry import entered_skill

SWITCH = "MUTHUR_DELEGATION"
SKILLS = {"go", "implement"}
SKILL_DIR = Path(".claude") / "skills" / "go"
FILES = ("delegation.md", "delegation-model-capabilities.md")


def say(message: str) -> None:
    print(f"go-delegation: {message}", file=sys.stderr)


def brief(root: Path) -> Optional[str]:
    parts = []
    for name in FILES:
        path = root / SKILL_DIR / name
        try:
            parts.append(f"===== {SKILL_DIR / name} =====\n{path.read_text()}")
        except OSError as error:
            say(f"cannot read {path} ({error}); no delegation brief delivered.")
            return None
    return (
        "/go's delegation is on in this session, so its procedure and the model "
        "notes are below — this is their read, and Step 2 follows them.\n\n"
        + "\n".join(parts)
    )


def main() -> int:
    if os.environ.get(SWITCH) == "off":
        return 0
    try:
        payload = json.loads(sys.stdin.read())
    except ValueError:
        say("unreadable payload; no delegation brief delivered.")
        return 0
    if not isinstance(payload, dict):
        return 0
    root = project_root(payload)
    if root is None:
        return 0
    marker = state_file(root, "go-delegation", payload)
    if marker is None or entered_skill(payload, root) not in SKILLS:
        return 0
    if marker.exists():
        return 0
    text = brief(root)
    if text is None:
        return 0
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch()
    except OSError as error:
        say(f"cannot record the delivery in {marker} ({error}); it may repeat.")

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": payload["hook_event_name"],
                "additionalContext": text,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
