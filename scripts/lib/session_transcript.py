"""Reading a Claude Code session transcript, for the scripts that do.

The record shape belongs to the client and is not documented, so what the
scripts need of it is kept here: where the transcript of the running session
lives, how a record reads as an operator's message, and how to walk the file
while the client is still appending to it. A change to the shape is fixed here
once, not in each script.

Imported as `from lib.session_transcript import …`; see `lib/github.py` for why
that resolves from any working directory. The name is not `transcript`, which
`.claude/costs/lib/` already uses: a process that loads both trees' `lib`
(a test loading a script and the keepalive hook) would resolve one to the other.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable, Iterator, Optional, Tuple

# `COMMAND_ENVELOPE` in `.claude/costs/lib/identity.py` is the same pattern; the
# costs tree is its own shipping group, so this copy is the one `scripts/`
# carries, and `test_session_qa.py` holds the two equal.
COMMAND_ENVELOPE = re.compile(
    r"<command-name>([^<]*)</command-name>(?:\s*<command-args>([^<]*)</command-args>)?"
)


class TranscriptError(Exception):
    """The transcript cannot be located; each script turns this into its failure."""


def find_transcript() -> Path:
    """The running session's transcript, by `$CLAUDE_CODE_SESSION_ID`, which is
    unique across project directories."""
    session = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session:
        raise TranscriptError("no CLAUDE_CODE_SESSION_ID; name the transcript with --transcript")
    found = sorted((Path.home() / ".claude" / "projects").glob(f"*/{session}.jsonl"))
    if len(found) != 1:
        raise TranscriptError(f"expected one transcript for session {session}, found {len(found)}")
    return found[0]


def prompt_text(content: object) -> str:
    """The text of a message's content, a plain string or a list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict) and isinstance(block.get("text"), str)
        )
    return ""


def iter_records(
    transcript: Path, skipped: Optional[Callable[[int, str], None]] = None
) -> Iterator[dict]:
    """Every JSON object in the transcript, in order. The client appends while
    this reads, so a half-written last line is passed over, reported to
    `skipped(line_number, why)` when given; the next read catches it."""
    with transcript.open(encoding="utf-8", errors="replace") as fh:
        for number, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                if skipped is not None:
                    skipped(number, "unparseable")
                continue
            if isinstance(record, dict):
                yield record


def _human(origin: object) -> bool:
    return isinstance(origin, dict) and origin.get("kind") == "human"


def operator_message(record: dict) -> Optional[Tuple[object, str]]:
    """An operator's message as its content and timestamp, or None.

    A prompt that starts a turn is a `user` record; one sent mid-turn is folded
    into the running turn as a `queued_command` attachment. Both carry
    `origin.kind == "human"`, which is what tells them from a tool result, a
    skill body, a hook's context and a subagent's hand-back (the same
    attachment with `origin.kind == "peer"`). The content is a string, or a list
    of blocks when the message carries an image.
    """
    if record.get("type") == "user":
        if not _human(record.get("origin")):
            return None
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        timestamp = record.get("timestamp")
    elif record.get("type") == "attachment":
        attachment = record.get("attachment")
        if not isinstance(attachment, dict) or attachment.get("type") != "queued_command":
            return None
        if not _human(attachment.get("origin")):
            return None
        content = attachment.get("prompt")
        timestamp = attachment.get("timestamp") or record.get("timestamp")
    else:
        return None
    if content is None:
        return None
    return content, str(timestamp or "")
