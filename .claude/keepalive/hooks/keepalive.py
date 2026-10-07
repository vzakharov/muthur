#!/usr/bin/env python3
"""`Stop` (with `asyncRewake`) + `UserPromptSubmit` hook: keep an idle
session's one-hour prompt cache warm by waking the model shortly before it
expires. `.claude/keepalive/CLAUDE.md` carries the contract.

Exit 2 is the wake, its stderr the model's instruction; any other exit wakes
nothing. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# The ledger's lib is reached by path, as its own scripts reach it.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "costs"))

from lib.restart import TTL_1H, epoch, read_history

WAKE = 2
DEFAULT_WAKES = 5
DEFAULT_LEAD = 300
MARK = "Cache keepalive, "


@dataclass(frozen=True)
class State:
    """`tmp/keepalive/` under the project: the wakes spent this idle spell, and
    the token of the one sleeper still entitled to fire."""

    dir: Path
    session: str

    @property
    def file(self) -> Path:
        return self.dir / f"{self.session}.json"

    @property
    def period_knob(self) -> Path:
        return self.dir / "period"

    def read(self) -> Dict[str, Any]:
        try:
            return json.loads(self.file.read_text())
        except (OSError, ValueError):
            return {}

    def write(self, data: Dict[str, Any]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps(data))


def message(wake: int, wakes: int, idle_minutes: int) -> str:
    if wake < wakes:
        return (
            f"{MARK}wake {wake} of {wakes}: the session has been idle about"
            f" {idle_minutes} min, and this turn exists only to keep its prompt cache warm."
            " Reply in the conversation's language with one line of at most seven words"
            f" saying so (e.g. «🕯 кеш продлён, {wake}/{wakes}»), and nothing else: no tools."
        )
    return (
        f"{MARK}last wake ({wake} of {wakes}): the session has been idle about"
        f" {idle_minutes} min. Run `/relay` per `.claude/skills/relay/SKILL.md`"
        " § \"Without a successor\": commit the summary, start no session, and end the"
        " reply with the `/relay take <branch>` line. The cache stays warm about an hour"
        " more; nothing wakes the session after this."
    )


def delay(state: State, transcript: Path, lead: int) -> Optional[float]:
    """Seconds until this sleeper fires, or None when there is nothing to keep
    warm: no transcript yet, or a five-minute cache no sane rate can bridge."""
    try:
        return float(state.period_knob.read_text())
    except (OSError, ValueError):
        pass
    history = read_history(transcript) if transcript.is_file() else None
    if history is None or history.ttl != TTL_1H:
        return None
    now = time.time()
    # The TTL runs from the request's start, which the response's timestamp
    # follows; `lead` absorbs the gap.
    anchor = min(epoch(history.last.timestamp) or now, now)
    return max(0.0, anchor + history.ttl - lead - now)


def on_stop(state: State, transcript: Path, wakes: int, lead: int) -> int:
    data = state.read()
    spent = int(data.get("wakes", 0))
    if spent >= wakes:
        return 0
    seconds = delay(state, transcript, lead)
    if seconds is None:
        return 0
    token = uuid.uuid4().hex
    state.write({"wakes": spent, "token": token})
    time.sleep(seconds)
    data = state.read()
    if data.get("token") != token:
        return 0
    wake = int(data.get("wakes", 0)) + 1
    state.write({"wakes": wake, "token": None})
    print(message(wake, wakes, round((seconds + lead) / 60)), file=sys.stderr)
    return WAKE


def on_prompt(state: State, prompt: str) -> None:
    # A wake reaches `UserPromptSubmit` too, carrying its own instruction, and
    # resetting on it would never let the spell end.
    if MARK in prompt:
        return
    if state.file.exists():
        state.write({"wakes": 0, "token": None})


def setting(name: str, default: int) -> Optional[int]:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"keepalive: {name} must be a whole number; nothing armed.", file=sys.stderr)
        return None


def main() -> int:
    if os.environ.get("CACHE_KEEPALIVE") == "off":
        return 0
    wakes = setting("CACHE_KEEPALIVE_WAKES", DEFAULT_WAKES)
    lead = setting("CACHE_KEEPALIVE_LEAD", DEFAULT_LEAD)
    if wakes is None or lead is None:
        return 0
    event = json.load(sys.stdin)
    session = event.get("session_id") or ""
    if not session or "/" in session or session.startswith("."):
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ROOT)
    state = State(project / "tmp" / "keepalive", session)
    kind = event.get("hook_event_name")
    if kind == "Stop":
        return on_stop(state, Path(event.get("transcript_path") or ""), wakes, lead)
    if kind == "UserPromptSubmit":
        on_prompt(state, event.get("prompt") or "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
