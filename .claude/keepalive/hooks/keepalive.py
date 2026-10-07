#!/usr/bin/env python3
"""Keep an idle session's one-hour prompt cache warm. Two entry points,
`.claude/keepalive/CLAUDE.md` carrying the contract:

- `UserPromptSubmit` hook (no arguments, the event on stdin): ends the idle
  spell on an operator prompt, and tells the model whether to start or stop a
  watcher and how to answer a wake.
- `keepalive.py watch <session_id> <transcript_path>`: the watcher, run as a
  background Bash task. It exits once the cache is `lead` seconds from expiry,
  and that exit is the wake.

Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# The ledger's lib is reached by path, as its own scripts reach it.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "costs"))

from lib.restart import TTL_1H, epoch, read_history

DEFAULT_WAKES = 5
DEFAULT_LEAD = 300
POLL = 30
# The Bash tool's cap on a background command, in seconds. The watcher exits
# under it, since reaching it stops the watcher with a notice of its own.
BASH_CAP = 7200
LIFETIME = BASH_CAP - 200
# Opens the watcher's task description, so a wake's notice — and a restart's
# list of stopped tasks — carries it into `UserPromptSubmit`, which must not
# read either as the operator coming back.
MARK = "Cache keepalive"
TASK = f"{MARK} watcher"
HOOK = Path(__file__).resolve()


@dataclass(frozen=True)
class State:
    """`tmp/keepalive/` under the project: the wakes spent this idle spell,
    the running watcher's pid, and whether it exited as a wake."""

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


def running(pid: Any) -> bool:
    """A live watcher of this hook — a pid alone may have been reused since a
    container restart."""
    try:
        cmdline = Path(f"/proc/{int(pid)}/cmdline").read_bytes()
    except (OSError, TypeError, ValueError):
        return False
    return str(HOOK).encode() in cmdline and b"watch" in cmdline


# --- The watcher --------------------------------------------------------------


def deadline(transcript: Path, lead: int) -> Optional[float]:
    """When to wake, or None when there is nothing to keep warm: no response
    yet, or a five-minute cache no sane rate can bridge."""
    history = read_history(transcript) if transcript.is_file() else None
    if history is None or history.ttl != TTL_1H:
        return None
    # The TTL runs from the request's start, which the response's timestamp
    # follows; `lead` absorbs the gap.
    last = epoch(history.last.timestamp)
    return None if last is None else last + history.ttl - lead


def watch(state: State, transcript: Path, lead: int) -> int:
    start = time.time()
    state.write({**state.read(), "pid": os.getpid(), "fired": False})
    try:
        period: Optional[float] = float(state.period_knob.read_text())
    except (OSError, ValueError):
        period = None
    seen, due = -1.0, None
    while time.time() - start < LIFETIME:
        if period is not None:
            due = start + period
        else:
            mtime = transcript.stat().st_mtime if transcript.is_file() else 0.0
            if mtime != seen:
                seen, due = mtime, deadline(transcript, lead)
        now = time.time()
        # Past the expiry itself the cache is already cold, and a wake would
        # pay the re-cache it exists to avoid: wait for the next response.
        if due is not None and due <= now < due + lead:
            data = state.read()
            state.write({**data, "wakes": int(data.get("wakes", 0)) + 1, "pid": None, "fired": True})
            return 0
        time.sleep(POLL if due is None or due <= now else max(1.0, min(POLL, due - now)))
    state.write({**state.read(), "pid": None})
    return 0


# --- The hook -----------------------------------------------------------------


def start_line(session: str, transcript: str) -> str:
    return (
        f"start the cache keepalive's watcher: one Bash call with `run_in_background: true`,"
        f" `timeout: {BASH_CAP * 1000}`, description `{TASK}`, command"
        f" `{HOOK} watch {session} {transcript}`."
    )


SUFFICIENT = (
    "the branch alone lets a fresh session continue: everything committed and pushed, the work"
    " at a loop boundary (a draft plan published awaiting `/go`, a paused plan, `/go` done"
    " awaiting `/finalize`, a relay summary written), and nothing said since that the repo"
    " does not hold"
)


def context(data: Dict[str, Any], wakes: int, session: str, transcript: str) -> Optional[str]:
    if running(data.get("pid")):
        return (
            f"A {MARK.lower()} watcher is running. If, as this turn ends, {SUFFICIENT},"
            " stop it with TaskStop (its id is in the Bash result that started it)."
        )
    spent = int(data.get("wakes", 0))
    if not data.get("fired"):
        return (
            f"As this turn's last action, {start_line(session, transcript)}"
            f" Skip it when, at that point, {SUFFICIENT}."
        )
    if spent >= wakes:
        return (
            f"{MARK}, last wake ({spent} of {wakes}): the session has idled for hours. Run `/relay`"
            " per `.claude/skills/relay/SKILL.md` § \"Without a successor\": commit the summary,"
            " start no session, and end the reply with the `/relay take <branch>` line."
            " Do not start the watcher again."
        )
    return (
        f"{MARK}, wake {spent} of {wakes}: this turn exists only to keep the prompt cache warm, so "
        + start_line(session, transcript)
        + " Then reply in the conversation's language with one line of at most seven words"
        f" saying so (e.g. «🕯 кеш продлён, {spent}/{wakes}»), and nothing else."
    )


def on_prompt(state: State, prompt: str, wakes: int, session: str, transcript: str) -> Optional[str]:
    data = state.read()
    if MARK not in prompt:
        data["wakes"] = 0
    out = context(data, wakes, session, transcript)
    data["fired"] = False
    state.write(data)
    return out


def setting(name: str, default: int) -> Optional[int]:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"keepalive: {name} must be a whole number; nothing armed.", file=sys.stderr)
        return None


def safe(session: str) -> bool:
    return bool(session) and "/" not in session and not session.startswith(".")


def main() -> int:
    if os.environ.get("CACHE_KEEPALIVE") == "off":
        return 0
    wakes = setting("CACHE_KEEPALIVE_WAKES", DEFAULT_WAKES)
    lead = setting("CACHE_KEEPALIVE_LEAD", DEFAULT_LEAD)
    if wakes is None or lead is None:
        return 0
    home = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ROOT) / "tmp" / "keepalive"
    if sys.argv[1:2] == ["watch"] and len(sys.argv) == 4:
        session, transcript = sys.argv[2], sys.argv[3]
        if not safe(session):
            return 0
        return watch(State(home, session), Path(transcript), lead)
    event = json.load(sys.stdin)
    session = event.get("session_id") or ""
    if event.get("hook_event_name") != "UserPromptSubmit" or not safe(session):
        return 0
    state = State(home, session)
    out = on_prompt(state, event.get("prompt") or "", wakes, session, event.get("transcript_path") or "")
    if out is not None:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": out}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
