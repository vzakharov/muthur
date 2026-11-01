#!/usr/bin/env python3
"""Print a session's questions and answers: what the operator asked and what the
agent said back, from its transcript, in order.

Usage:
  python3 scripts/session-qa.py [--transcript PATH] [--since COMMIT] [--tools]

An operator message is `## Q <timestamp>` with its text verbatim, an assistant
text block is `## A <timestamp>`. Thinking, tool results, hook context, skill
bodies, keepalive wakes, subagents' records and their hand-backs are left out. A
typed slash command, which the client stores in an envelope, is printed as
`/<name> <args>`. `--tools` adds one line per tool call, between the texts it
fell among.

The whole transcript is printed by default, since the request usually opens it,
well before any commit that could cut it. `--since COMMIT` starts at that
commit's committer time, compared with each record's timestamp.

`polish/passes.md`'s review reads the transcript through this: the reviewer can
settle what the operator asked without taking a launching agent's account of it.
The transcript defaults to the running session's, found from
`$CLAUDE_CODE_SESSION_ID`; a subagent sees its parent's id.

Exit status is non-zero when the transcript or the commit cannot be read. The
record shape belongs to the client and is not documented, so a change to it
surfaces as an empty output on a transcript that is not.

Stdlib only — no third-party deps. Python 3.9+.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator, NoReturn, Optional

from lib.session_transcript import (
    COMMAND_ENVELOPE,
    TranscriptError,
    find_transcript,
    iter_records,
    operator_message,
    prompt_text,
)

SYNTHETIC_MODEL = "<synthetic>"
TOOL_SUMMARY_KEYS = ("command", "file_path", "path", "pattern", "skill", "description", "prompt")
TOOL_SUMMARY_CHARS = 140


def _die(message: str) -> NoReturn:
    print(f"session-qa: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_time(raw: object) -> Optional[datetime]:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def commit_time(commit: str) -> datetime:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cI", commit], capture_output=True, text=True, check=False
    )
    found = parse_time(result.stdout.strip())
    if result.returncode != 0 or found is None:
        _die(f"cannot read the time of commit {commit!r}: {result.stderr.strip() or 'no such commit'}")
    return found


def question_text(content: object) -> str:
    text = prompt_text(content).strip()
    envelope = COMMAND_ENVELOPE.search(text)
    if envelope is not None:
        name = envelope.group(1).strip().lstrip("/")
        text = f"/{name} {envelope.group(2) or ''}".rstrip()
    return text


def tool_line(block: dict) -> str:
    name = str(block.get("name") or "?")
    tool_input = block.get("input")
    detail = ""
    if isinstance(tool_input, dict):
        for key in TOOL_SUMMARY_KEYS:
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                detail = " ".join(value.split())[:TOOL_SUMMARY_CHARS]
                break
    return f"- {name}: {detail}" if detail else f"- {name}"


def entries(transcript: Path, since: Optional[datetime], tools: bool) -> Iterator[str]:
    for record in iter_records(transcript):
        if record.get("isSidechain"):
            continue
        stamp = record.get("timestamp")
        moment = parse_time(stamp)
        if since is not None and moment is not None and moment < since:
            continue
        asked = operator_message(record)
        if asked is not None:
            content, timestamp = asked
            yield f"## Q {timestamp}\n\n{question_text(content) or '(no text)'}\n"
        elif record.get("type") == "assistant":
            message = record.get("message")
            if not isinstance(message, dict) or message.get("model") == SYNTHETIC_MODEL:
                continue
            blocks = message.get("content")
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    if block["text"].strip():
                        yield f"## A {stamp or ''}\n\n{block['text'].strip()}\n"
                elif tools and block.get("type") == "tool_use":
                    yield tool_line(block) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a session's questions and answers from its transcript."
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        help="the session .jsonl (default: found from CLAUDE_CODE_SESSION_ID)",
    )
    parser.add_argument(
        "--since", metavar="COMMIT", help="start at this commit's committer time"
    )
    parser.add_argument("--tools", action="store_true", help="add one line per tool call")
    args = parser.parse_args()

    try:
        transcript: Path = args.transcript or find_transcript()
    except TranscriptError as exc:
        _die(str(exc))
    if not transcript.is_file():
        _die(f"transcript not found: {transcript}")
    since = commit_time(args.since) if args.since else None

    try:
        for entry in entries(transcript, since, args.tools):
            sys.stdout.write(entry + "\n")
    except OSError as exc:
        _die(f"cannot read {transcript}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
