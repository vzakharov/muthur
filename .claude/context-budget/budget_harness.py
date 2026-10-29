"""What the context budget tests share: a session on disk, the hook run as the
harness runs it, and the records a transcript is made of. Imported by
`test_context_budget*.py`, which `scripts/vet.sh` runs by path, putting this
directory on `sys.path`.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "hooks" / "post-tool-context-budget.sh"
WARN = 300_000
PAUSE = 400_000


def assistant(context: int, *, sidechain: bool = False, model: str = "claude-x") -> dict:
    # The reading sums all three input fields, so the context is split across them.
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {
            "model": model,
            "usage": {
                "input_tokens": 2,
                "cache_read_input_tokens": context - 1_002,
                "cache_creation_input_tokens": 1_000,
                "output_tokens": 500,
            },
        },
    }


def priced(message_id: str, context: int, at: int, *, edits: str | None = None) -> dict:
    # A response the price table covers, which the priced lines read; `at` is
    # its second in the session, which orders it for the orientation measure.
    return {
        "type": "assistant",
        "isSidechain": False,
        "cwd": "/repo",
        "timestamp": f"2026-09-30T10:{at // 60:02d}:{at % 60:02d}Z",
        "message": {
            "id": message_id,
            "model": "claude-opus-5-5",
            "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": edits}}] if edits else [],
            "usage": {
                "input_tokens": 0,
                "cache_read_input_tokens": context - 2_000,
                "cache_creation_input_tokens": 2_000,
                "output_tokens": 500,
            },
        },
    }


def tool_result() -> dict:
    return {"type": "user", "isSidechain": False, "message": {"content": "ok"}}


# Stands in for `gh api user`: the hook's one network call, so every run gets a
# `gh` that answers from the environment rather than from GitHub.
GH_STUB = """#!/bin/sh
[ -n "$STUB_GH_USER" ] || exit 1
printf '%s\\n' "$STUB_GH_USER"
"""


class Session:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.transcript = root / "transcript.jsonl"
        self.transcript.write_text("")
        self.bin = root / "bin"
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text(GH_STUB)
        gh.chmod(0o755)
        # No identity: `gh` fails, as it does with no token or no network.
        self.identity: dict[str, str] | None = None

    def signed_in_as(self, login: str, kind: str = "User") -> None:
        self.identity = {"login": login, "type": kind}

    def manual_relay(self, handle: str, setting: str) -> None:
        path = self.root / ".claude" / "context-budget" / "manual-relay" / handle
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(setting)

    def append(self, *records: dict) -> None:
        with self.transcript.open("a") as f:
            for record in records:
                f.write(json.dumps(record, separators=(",", ":")) + "\n")

    def tool_call(
        self, env: dict[str, str] | None = None, **payload: str
    ) -> subprocess.CompletedProcess[str]:
        body = {
            "hook_event_name": "PostToolUse",
            "session_id": "sess",
            "transcript_path": str(self.transcript),
            "cwd": str(self.root),
            **payload,
        }
        return subprocess.run(
            [str(HOOK)],
            input=json.dumps(body),
            capture_output=True,
            text=True,
            check=True,
            env={
                "PATH": f"{self.bin}:/usr/bin:/bin",
                "CLAUDE_PROJECT_DIR": str(self.root),
                "STUB_GH_USER": json.dumps(self.identity) if self.identity else "",
                **(env or {}),
            },
        )

    def notice(self, env: dict[str, str] | None = None, **payload: str) -> str | None:
        out = self.tool_call(env, **payload).stdout
        if not out.strip():
            return None
        emitted = json.loads(out)["hookSpecificOutput"]
        # `hookSpecificOutput` is honoured only under the event that ran the hook.
        assert emitted["hookEventName"] == "PostToolUse", emitted
        return emitted["additionalContext"]


class BudgetTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.session = Session(Path(tmp.name))

    def notices(self) -> tuple[str, str]:
        """The warning, then the pause, from one climb past both lines."""
        self.session.append(assistant(WARN + 1))
        warning = self.session.notice()
        self.session.append(assistant(PAUSE + 1))
        pause = self.session.notice()
        assert warning is not None and pause is not None
        return warning, pause
