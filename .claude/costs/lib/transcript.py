"""The billed responses in a session's transcripts, read one record at a time.
`.claude/costs/CLAUDE.md` § "Reading a transcript" carries the file's shape."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from lib.orientation import ToolCall, calls_in
from lib.shape import mistyped, read_count, read_object, read_string, required
from lib.tally import Tally

# Claude Code's placeholder for a turn no model served — a cancellation, an
# interrupted request. It is not a model, so the unpriced-pair error would be
# reporting the wrong thing; a warning covers one ever arriving with tokens.
SYNTHETIC_MODEL = "<synthetic>"


@dataclass(frozen=True)
class Response:
    message_id: str
    model: str
    speed: Optional[str]
    session_id: Optional[str]
    git_branch: Optional[str]
    cwd: Optional[str]
    timestamp: Optional[str]
    is_sidechain: bool
    stop_reason: Optional[str]
    request_id: Optional[str]
    calls: Tuple[ToolCall, ...]
    tokens: Tally


def is_response_record(record: Any) -> bool:
    # Prompts, attachments and tool results share the file and carry no usage,
    # so only a record that looks like a billed response is held to the shape.
    if not isinstance(record, dict):
        return False
    message = record.get("message")
    return isinstance(message, dict) and "usage" in message


def merged(earlier: Response, later: Response) -> Response:
    """One API response is written as one record per content block, each carrying
    the whole response's usage: the usage counts once, the calls are every
    record's, and the turn ended if any record says it did."""
    ended = "end_turn" in (earlier.stop_reason, later.stop_reason)
    return replace(
        earlier,
        calls=earlier.calls + later.calls,
        stop_reason="end_turn" if ended else later.stop_reason or earlier.stop_reason,
    )


def parse_response(record: Dict[str, Any], where: str, warnings: List[str]) -> Response:
    message = required(read_object, record, "message", where)
    message_id = required(read_string, message, "id", where)
    usage = required(read_object, message, "usage", where)
    at = f"{where} usage"

    written = read_count(usage, "cache_creation_input_tokens", at) or 0
    split = read_object(usage, "cache_creation", at) or {}
    split_5m = read_count(split, "ephemeral_5m_input_tokens", at) or 0
    split_1h = read_count(split, "ephemeral_1h_input_tokens", at) or 0
    # A split that does not account for the whole write leaves the rest at the
    # API's own default TTL, and says so rather than rounding it away.
    trust_split = split_5m + split_1h == written
    if not trust_split and written > 0:
        warnings.append(
            f"{message_id}: cache_creation split ({split_5m} + {split_1h}) does not"
            f" account for {written} written tokens; billed at the 5-minute rate"
        )
    details = read_object(usage, "output_tokens_details", at) or {}
    sidechain = record.get("isSidechain")
    if sidechain is not None and not isinstance(sidechain, bool):
        raise mistyped(where, "isSidechain", sidechain, "a boolean")

    return Response(
        message_id=message_id,
        model=required(read_string, message, "model", where),
        speed=read_string(usage, "speed", at),
        session_id=read_string(record, "sessionId", where),
        git_branch=read_string(record, "gitBranch", where),
        cwd=read_string(record, "cwd", where),
        timestamp=read_string(record, "timestamp", where),
        is_sidechain=sidechain is True,
        stop_reason=read_string(message, "stop_reason", where),
        request_id=read_string(record, "requestId", where),
        calls=calls_in(message, where),
        tokens=Tally(
            input_tokens=required(read_count, usage, "input_tokens", at),
            cache_write_5m_tokens=split_5m if trust_split else written,
            cache_write_1h_tokens=split_1h if trust_split else 0,
            cache_read_tokens=read_count(usage, "cache_read_input_tokens", at) or 0,
            output_tokens=required(read_count, usage, "output_tokens", at),
            thinking_tokens=read_count(details, "thinking_tokens", at) or 0,
        ),
    )


@dataclass(frozen=True)
class TranscriptSources:
    """A session's transcripts: the main file, and one per subagent it spawned.

    A subagent's responses are billed to the session that spawned it and are
    written to a **separate file**, so a reading that opens only the main
    transcript prices the session short by however much it delegated — silently,
    since the shortfall looks exactly like a session that delegated nothing.
    """

    main: str
    subagents: Sequence[str] = ()


def subagents_of(main: Path) -> List[str]:
    """A subagent's responses are billed to this session and written to their own
    file under `<transcript>/subagents/`, so the directory is read rather than
    assumed empty. A session that spawned none has no directory at all."""
    directory = main.parent / main.stem / "subagents"
    if not directory.is_dir():
        return []
    return [path.read_text(encoding="utf-8") for path in sorted(directory.glob("*.jsonl"))]
