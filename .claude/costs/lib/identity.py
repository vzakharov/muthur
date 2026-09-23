"""What a person recognises a session by, read out of its transcript.

Separate from the pricing beside it because none of it is arithmetic: these are
the records the file happens to carry that answer "which session was that", and
they change with the Claude Code version rather than with the rate table.

Each reader answers "is this record that kind, and what does it say" — `None`
for a record of another shape, never an error, since most records in the file
are of some other shape. `.claude/costs/CLAUDE.md` § "What names a session"
carries why a session needs standing in for at all.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from lib.shape import is_number


def kind_of(record: Any) -> Optional[str]:
    if isinstance(record, dict) and isinstance(record.get("type"), str):
        return record["type"]
    return None


def cost_state_of(record: Any) -> Optional[float]:
    """Claude Code's own running cost for the session, rewritten as the session
    goes: the last one in the file is its final word on it."""
    if isinstance(record, dict) and is_number(record.get("totalCostUSD")):
        return record["totalCostUSD"]
    return None


def pr_number_of(record: Any) -> Optional[int]:
    """Claude Code records every PR it opens or refreshes, which is what groups
    the several sessions one PR takes."""
    if isinstance(record, dict) and is_number(record.get("prNumber")):
        return int(record["prNumber"])
    return None


SESSION_URL = re.compile(r"https://claude\.ai/code/session_[0-9A-Za-z]+")


def session_url_in(record: Any, line: str) -> Optional[str]:
    """The session's web URL reaches the transcript only as prose, inside the
    attribution reminder the harness re-sends whenever the remote session
    changes. Matching that one record's raw line is narrower than scanning the
    file, where any quoted commit trailer carries a session URL too — usually
    another session's."""
    if not isinstance(record, dict):
        return None
    attachment = record.get("attachment")
    if not isinstance(attachment, dict):
        return None
    if attachment.get("type") != "remote_session_change":
        return None
    found = SESSION_URL.search(line)
    return found.group(0) if found else None


COMMAND_ENVELOPE = re.compile(
    r"<command-name>([^<]*)</command-name>(?:\s*<command-args>([^<]*)</command-args>)?"
)

OPENING_PROMPT_LIMIT = 160


def _prompt_raw(record: Any) -> Optional[str]:
    if not isinstance(record, dict):
        return None
    if record.get("isMeta") is True or record.get("isSidechain") is True:
        return None
    message = record.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return None
    # A tool result is a `user` record too, and carries no text block.
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text")
            return text if isinstance(text, str) else None
    return None


def prompt_text_of(record: Any) -> Optional[str]:
    """The harness writes no session title, so the opening prompt stands in for
    one, unwrapped from the envelope a slash command arrives in: `/handle
    <branch>` is what a person would call that session."""
    raw = _prompt_raw(record)
    if raw is None:
        return None
    envelope = COMMAND_ENVELOPE.search(raw)
    if envelope is not None:
        raw = f"{envelope.group(1)} {envelope.group(2) or ''}".rstrip()
    text = re.sub(r"\s+", " ", raw).strip()
    if text == "":
        return None
    if len(text) > OPENING_PROMPT_LIMIT:
        return f"{text[:OPENING_PROMPT_LIMIT]}…"
    return text
