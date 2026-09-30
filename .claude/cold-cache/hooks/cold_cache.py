#!/usr/bin/env python3
"""`SessionStart` + `UserPromptSubmit` hook: stop the first prompt after the
prompt cache has expired and price the ways on. `.claude/cold-cache/CLAUDE.md`
carries why it reads what it reads.

Stdout is the interface: nothing lets the prompt through, a `block` decision
stops it, and `additionalContext` tells the model what a bare `!` resends. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# The ledger's lib is reached by path, as its own scripts reach it.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude" / "costs"))

from lib.pricing import parse_prices
from lib.restart import FINISH, History, Saving, context_of, epoch, read_history, saving_over, session_of, verdict

PRICES = ROOT / ".claude" / "costs" / "prices.json"
RESEND = "!"
DEFAULT_MIN_USD = 0.30

# The commands a cold cache lets through: the ways on that shed context, and the
# built-ins that make no model request over this session's context, aliases
# included, per https://code.claude.com/docs/en/commands. Skills, workflows and
# the built-ins that prompt the model are stopped like any other prompt. A
# command that never reaches `UserPromptSubmit` passes all the same, so the list
# can be exhaustive without knowing which ones arrive.
PASSES = frozenset(
    """
    compact clear reset new relay
    add-dir advisor agents android app artifacts auto-mode-setup autocompact
    bashes branch bug cd checkpoint chrome color config context continue copy
    cost design-login desktop diff effort exit export fast feedback focus
    heapdump help hooks ide import install-github-app install-slack-app ios
    keybindings list-agents login logout mcp memory mobile model output-style
    passes permissions allowed-tools plugin powerup privacy-settings quit radio
    rate-limit-options rc release-notes reload-plugins reload-skills
    remote-control remote-env rename resume rewind sandbox scroll-speed settings
    setup-bedrock setup-vertex share skill-doctor skills stats status stickers
    stop tasks teleport terminal-setup theme tp tui undo upgrade usage
    usage-credits voice web-setup workflows
    """.split()
)


def passes(prompt: str) -> bool:
    words = prompt.strip().split()
    return bool(words) and words[0].startswith("/") and words[0][1:] in PASSES


# --- The two events -----------------------------------------------------------


@dataclass(frozen=True)
class State:
    """`tmp/cold-cache/` under the project: the resume's reading, and the block
    last raised — the response it was raised against and the prompt it stopped."""

    dir: Path
    session: str

    @property
    def flag(self) -> Path:
        return self.dir / f"{self.session}.json"

    @property
    def blocked(self) -> Path:
        return self.dir / f"{self.session}.blocked"


def on_session_start(event: Dict[str, Any], state: State) -> None:
    if event.get("source") in ("resume", "fork") and event.get("prompt_cache_likely_expired") is True:
        state.dir.mkdir(parents=True, exist_ok=True)
        fields = ("seconds_since_last_response", "context_tokens", "estimated_cache_write_usd")
        state.flag.write_text(json.dumps({**{k: event.get(k) for k in fields}, "written_at": time.time()}))
    else:
        state.flag.unlink(missing_ok=True)


def read_flag(state: State, last_at: Optional[float]) -> Optional[Dict[str, Any]]:
    """The resume's own reading, while no response has landed since it."""
    if not state.flag.exists():
        return None
    data = json.loads(state.flag.read_text())
    if last_at is not None and last_at > data["written_at"]:
        state.flag.unlink()
        return None
    return data


def span(seconds: float) -> str:
    return f"{seconds / 3600:.1f} h" if seconds >= 5400 else f"{seconds / 60:.0f} min"


def kilo(tokens: float) -> str:
    return f"{tokens / 1000:.0f}k"


def relay_line(saving: Saving) -> str:
    return (
        f"/relay: ~${saving.relay:.2f} up front, more than carrying on, since its summary turn"
        f" re-caches the context too, and then {verdict(saving)} over the next {kilo(FINISH)}"
        " tokens of work."
    )


def reason(idle: float, context: int, priced: Optional[Tuple[Saving, str]], claude_code_usd: Optional[float]) -> str:
    lines = [f"Prompt cache expired: {span(idle)} since the last response, {kilo(context)} tokens to re-cache."]
    if priced is not None:
        saving, source = priced
        lines.append(f"Carry on: ~${saving.carry_on:.2f} up front.")
        lines.append(relay_line(saving))
        lines.append(f"The successor's reorientation is priced from {source}.")
    elif claude_code_usd is not None:
        lines.append(f"Claude Code estimates re-caching at ${claude_code_usd:.2f}; this model has no row in the price table to price a relay.")
    else:
        lines.append("This model has no row in the price table, so the options are not priced.")
    lines.append(
        f"This message was not sent: send {RESEND} alone to carry on with it as written, send anything"
        " else to carry on with that instead, or run /relay."
    )
    return " ".join(lines)


def price(transcript: Path, history: History, context: int, project: Path) -> Optional[Tuple[Saving, str]]:
    prices = parse_prices(PRICES.read_text(encoding="utf-8"))
    s = session_of(transcript, history, context, prices, project)
    if s is None:
        return None
    return saving_over(s, FINISH, cold=True), s.reorientation.source


@dataclass(frozen=True)
class Verdict:
    """What the hook prints: a block's reason, or context for a prompt it passes."""

    block: Optional[str] = None
    context: Optional[str] = None


def resent(state: State) -> Verdict:
    """A bare `!` stands for the stopped prompt. A hook cannot rewrite the prompt
    it is given, so the model is told what `!` stands for."""
    if not state.blocked.exists():
        return Verdict()
    stopped = json.loads(state.blocked.read_text()).get("prompt")
    if not isinstance(stopped, str):
        return Verdict()
    return Verdict(
        context=(
            f"The operator's `{RESEND}` resends the prompt the cold-cache guard stopped. Act on"
            f" that prompt exactly as if they had sent it again, verbatim:\n\n{stopped}"
        )
    )


def on_prompt(event: Dict[str, Any], state: State, min_usd: float, project: Path) -> Verdict:
    prompt = event.get("prompt") or ""
    if prompt.strip() == RESEND:
        return resent(state)
    transcript = Path(event.get("transcript_path") or "")
    if passes(prompt) or not transcript.is_file():
        return Verdict()
    history = read_history(transcript)
    if history is None:
        return Verdict()
    last_at = epoch(history.last.timestamp)
    flag = read_flag(state, last_at)
    if state.blocked.exists() and json.loads(state.blocked.read_text()).get("after") == history.last.message_id:
        state.flag.unlink(missing_ok=True)
        return Verdict()

    now = time.time()
    if flag is not None:
        idle = flag["seconds_since_last_response"] + now - flag["written_at"]
        context = flag["context_tokens"]
    elif last_at is not None and now - last_at > history.ttl:
        idle, context = now - last_at, context_of(history.last)
    else:
        return Verdict()

    priced = price(transcript, history, context, project)
    claude_code_usd = flag.get("estimated_cache_write_usd") if flag else None
    cost = priced[0].carry_on if priced else claude_code_usd
    if cost is not None and cost < min_usd:
        return Verdict()

    state.dir.mkdir(parents=True, exist_ok=True)
    state.blocked.write_text(json.dumps({"after": history.last.message_id, "prompt": prompt}))
    return Verdict(block=reason(idle, context, priced, claude_code_usd))


def main() -> None:
    if os.environ.get("COLD_CACHE_GUARD") == "off":
        return
    try:
        min_usd = float(os.environ.get("COLD_CACHE_MIN_USD", DEFAULT_MIN_USD))
    except ValueError:
        print("cold-cache: COLD_CACHE_MIN_USD must be a number of dollars; no check made.", file=sys.stderr)
        return
    event = json.load(sys.stdin)
    session = event.get("session_id") or ""
    if not session or "/" in session or session.startswith("."):
        return
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ROOT)
    state = State(project / "tmp" / "cold-cache", session)
    kind = event.get("hook_event_name")
    if kind == "SessionStart":
        on_session_start(event, state)
    elif kind == "UserPromptSubmit":
        verdict = on_prompt(event, state, min_usd, project)
        if verdict.block is not None:
            print(json.dumps({"decision": "block", "reason": verdict.block}))
        elif verdict.context is not None:
            out = {"hookEventName": "UserPromptSubmit", "additionalContext": verdict.context}
            print(json.dumps({"hookSpecificOutput": out}))


if __name__ == "__main__":
    main()
