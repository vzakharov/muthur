#!/usr/bin/env python3
"""Drives the hook as the harness does — a payload on stdin, a transcript on
disk — and reads what it prints. What it protects is the once-per-climb rule and
which records count as the session's reading.

Run by path (`python3 .claude/context-budget/test_context_budget.py`), as
`scripts/vet.sh` does.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "hooks" / "post-tool-context-budget.sh"
WARN = 200_000
PAUSE = 300_000


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


def priced(message_id: str, context: int, *, tool: str | None = None) -> dict:
    # A response the price table covers, which the priced warn line reads.
    return {
        "type": "assistant",
        "isSidechain": False,
        "message": {
            "id": message_id,
            "model": "claude-opus-5-5",
            "stop_reason": "tool_use",
            "content": [{"type": "tool_use", "name": tool, "input": {}}] if tool else [],
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


class Session:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.transcript = root / "transcript.jsonl"
        self.transcript.write_text("")

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
            env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(self.root), **(env or {})},
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


class WhenTheNoticesFire(BudgetTestCase):
    def test_says_nothing_under_the_warn_line(self) -> None:
        self.session.append(assistant(WARN - 1), tool_result())
        self.assertIsNone(self.session.notice())

    def test_warns_once_on_crossing_the_warn_line(self) -> None:
        self.session.append(assistant(WARN + 5_000))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("~205k", notice)
        self.assertIn("warning line", notice)
        self.session.append(tool_result(), assistant(WARN + 9_000))
        self.assertIsNone(self.session.notice())

    def test_pauses_once_on_crossing_the_pause_line_after_the_warning(self) -> None:
        self.session.append(assistant(WARN + 1))
        self.session.notice()
        self.session.append(assistant(PAUSE))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("pause line", notice)
        self.session.append(assistant(PAUSE + 20_000))
        self.assertIsNone(self.session.notice())

    def test_a_jump_past_the_pause_line_skips_the_warning(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("pause line", notice)
        self.assertNotIn("warning line", notice)

    def test_dropping_under_the_warn_line_rearms_both(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        self.session.notice()
        self.session.append(assistant(40_000))
        self.assertIsNone(self.session.notice())
        self.session.append(assistant(WARN + 1))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("warning line", notice)

    def test_the_thresholds_follow_their_env_overrides(self) -> None:
        self.session.append(assistant(60_000))
        notice = self.session.notice(
            {"CONTEXT_BUDGET_WARN": "50000", "CONTEXT_BUDGET_PAUSE": "100000"}
        )
        assert notice is not None
        self.assertIn("50k warning line", notice)


class ThePricedWarnLine(BudgetTestCase):
    # Opening at 43k and editing at 90k prices the warm-up at ~$0.07, so a new
    # session pays for itself within 100 requests past ~90k + $0.07 / 100 reads.
    def setUp(self) -> None:
        super().setUp()
        self.session.append(priced("open", 43_000), priced("edit", 90_000, tool="Edit"))

    def test_warns_where_a_new_session_starts_paying_for_itself(self) -> None:
        self.session.append(priced("under", 91_000))
        self.assertIsNone(self.session.notice())
        self.session.append(priced("past", 150_000))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("warning line", notice)
        self.assertIn("a new session pays for itself after ~", notice)
        self.assertIn("/compact", notice)

    def test_a_smaller_request_budget_moves_the_line_out(self) -> None:
        self.session.append(priced("past", 150_000))
        self.assertIsNone(self.session.notice({"CONTEXT_BUDGET_REQUESTS": "5"}))

    def test_a_fixed_warn_line_set_by_hand_wins(self) -> None:
        self.session.append(priced("past", 150_000))
        self.assertIsNone(self.session.notice({"CONTEXT_BUDGET_WARN": "200000"}))

    def test_the_pause_line_stays_fixed(self) -> None:
        self.session.append(priced("past", PAUSE + 1))
        notice = self.session.notice()
        assert notice is not None
        self.assertIn("300k pause line", notice)


class WhichRecordsAreTheReading(BudgetTestCase):
    def test_reads_the_last_main_chain_response(self) -> None:
        self.session.append(assistant(PAUSE + 1), assistant(WARN - 1))
        self.assertIsNone(self.session.notice())

    def test_skips_a_sidechain_response(self) -> None:
        self.session.append(assistant(WARN - 1), assistant(PAUSE + 1, sidechain=True))
        self.assertIsNone(self.session.notice())

    def test_skips_a_synthetic_response(self) -> None:
        self.session.append(assistant(WARN + 1), assistant(0, model="<synthetic>"))
        self.assertIsNotNone(self.session.notice())

    def test_ignores_a_subagents_tool_call(self) -> None:
        self.session.append(assistant(PAUSE + 1))
        self.assertIsNone(self.session.notice(agent_id="agent-1"))
        self.assertIsNotNone(self.session.notice())


class WhenThereIsNothingToRead(BudgetTestCase):
    def test_a_missing_transcript_is_silent(self) -> None:
        self.session.transcript.unlink()
        result = self.session.tool_call()
        self.assertEqual(result.stdout, "")

    def test_a_transcript_with_no_response_yet_is_silent(self) -> None:
        self.session.append(tool_result())
        self.assertIsNone(self.session.notice())


if __name__ == "__main__":
    unittest.main()
