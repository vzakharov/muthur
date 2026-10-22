#!/usr/bin/env python3
"""Append the agent's last reply, verbatim, to a relay summary.

Usage:
  python3 scripts/relay-last-reply.py <summary.md> [--transcript PATH]

`/relay` runs this on the summary it has just written
(`@.claude/skills/relay/SKILL.md` § "Step 2"). The reply is copied rather than
retold because it usually explains most of what the session accumulated, and
because the operator of the successor quotes from it.

The reply is the text of the last turn before the one running this script: a
turn is every record sharing a user record's `promptId`, which a tool result
carries as well as the prompt that opened the turn. All of a turn's text blocks
are kept, in order, so a report written before a hook forced one more tool call
survives that call. A turn holding no text — interrupted before it wrote any —
is passed over for the one before it.

The transcript defaults to `~/.claude/projects/*/$CLAUDE_CODE_SESSION_ID.jsonl`,
the session id being unique across project directories.

Exit status is non-zero when the transcript cannot be found or read, or holds no
earlier turn with text, and then nothing is written. The record shape belongs to
the client and is not documented, so a change to it surfaces as that last error.

Stdlib only — no third-party deps. Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, NoReturn, Optional

HEADING = "## Last reply"
LEAD = (
    "The agent's final reply before the relay, verbatim, appended by\n"
    "`scripts/relay-last-reply.py`."
)


def _die(message: str) -> NoReturn:
    print(f"relay-last-reply: {message}", file=sys.stderr)
    raise SystemExit(1)


def find_transcript() -> Path:
    session = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session:
        _die("no CLAUDE_CODE_SESSION_ID; name the transcript with --transcript")
    found = sorted((Path.home() / ".claude" / "projects").glob(f"*/{session}.jsonl"))
    if len(found) != 1:
        _die(f"expected one transcript for session {session}, found {len(found)}")
    return found[0]


def turn_texts(transcript: Path) -> List[List[str]]:
    """Each turn's text blocks, turns in the order they opened."""
    turns: Dict[str, List[str]] = {}
    current: Optional[str] = None
    with transcript.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # The transcript is appended to while this reads it, so the last
                # line can be half-written; it belongs to the running turn.
                continue
            if not isinstance(record, dict) or record.get("isSidechain"):
                continue
            if record.get("type") == "user":
                prompt = record.get("promptId")
                if isinstance(prompt, str) and prompt:
                    current = prompt
                    turns.setdefault(prompt, [])
            elif record.get("type") == "assistant" and current is not None:
                content = (record.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                turns[current].extend(
                    block["text"].strip()
                    for block in content
                    if isinstance(block, dict)
                    and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                    and block["text"].strip()
                )
    return list(turns.values())


def last_reply(transcript: Path) -> Optional[str]:
    """The text of the latest turn before the running one that wrote any."""
    for texts in reversed(turn_texts(transcript)[:-1]):
        if texts:
            return "\n\n".join(texts)
    return None


def fenced(text: str) -> str:
    """`text` in a code fence longer than any backtick run inside it, which is
    also the fence prettier settles on, so the vet run leaves it alone."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}text\n{text}\n{fence}\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append the agent's last reply, verbatim, to a relay summary."
    )
    parser.add_argument("summary", type=Path, help="the relay-<N>.md just written")
    parser.add_argument(
        "--transcript",
        type=Path,
        help="the session .jsonl (default: found from CLAUDE_CODE_SESSION_ID)",
    )
    args = parser.parse_args()

    summary: Path = args.summary
    if not summary.is_file():
        _die(f"summary not found: {summary}")
    transcript: Path = args.transcript or find_transcript()
    if not transcript.is_file():
        _die(f"transcript not found: {transcript}")

    try:
        reply = last_reply(transcript)
    except OSError as exc:
        _die(f"cannot read {transcript}: {exc}")
    if reply is None:
        _die(f"no turn before this one wrote any text in {transcript}")

    body = summary.read_text(encoding="utf-8")
    separator = "\n" if body.endswith("\n") else "\n\n"
    try:
        with summary.open("a", encoding="utf-8") as fh:
            fh.write(f"{separator}{HEADING}\n\n{LEAD}\n\n{fenced(reply)}")
    except OSError as exc:
        _die(f"cannot write {summary}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
