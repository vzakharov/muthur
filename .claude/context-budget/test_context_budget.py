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

    def auto_relay(self, handle: str, setting: str) -> None:
        path = self.root / ".claude" / "context-budget" / "auto-relay" / handle
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

    def test_the_warning_gives_the_work_the_room_up_to_the_pause_line(self) -> None:
        # The half-of-the-session gauge matches that room only at the default
        # lines, which is all it claims: "roughly".
        warning, _ = self.notices()
        self.assertIn("under ~100k more tokens", warning)
        self.assertIn("less than half", warning)
        self.assertIn("steer to a pause within that same ~100k", warning)

    def test_the_room_follows_the_lines(self) -> None:
        self.session.append(assistant(60_000))
        notice = self.session.notice(
            {"CONTEXT_BUDGET_WARN": "50000", "CONTEXT_BUDGET_PAUSE": "80000"}
        )
        assert notice is not None
        self.assertIn("under ~30k more tokens", notice)

    def test_the_pause_leaves_room_only_for_a_last_step(self) -> None:
        _, pause = self.notices()
        self.assertIn("Pause now, without asking, wherever the work stands", pause)
        self.assertIn("under ~20k more tokens", pause)
        self.assertNotIn("100k", pause)

    def test_the_warning_judges_an_elephants_open_bite(self) -> None:
        warning, _ = self.notices()
        self.assertIn("the open bite", warning)

    def test_both_notices_offer_relay_as_the_way_on(self) -> None:
        warning, pause = self.notices()
        self.assertIn("offering `/relay`", warning)
        self.assertIn("offering `/relay`", pause)


class WhetherThePauseRelaysOnItsOwn(BudgetTestCase):
    OPT_IN = "has not said whether to relay on their own"

    def test_an_operator_never_asked_is_offered_it_with_the_relay(self) -> None:
        self.session.signed_in_as("Someone")
        warning, pause = self.notices()
        self.assertIn(self.OPT_IN, warning)
        self.assertIn("@someone", pause)
        self.assertIn("offering `/relay`", pause)

    def test_on_makes_either_pause_relay_without_asking(self) -> None:
        self.session.signed_in_as("Someone")
        self.session.auto_relay("someone", "on\n")
        for notice in self.notices():
            self.assertIn("without asking and with no argument, run `/relay`", notice)
            self.assertIn("auto-relay/someone", notice)
            self.assertNotIn("offering `/relay`", notice)
            self.assertNotIn(self.OPT_IN, notice)

    def test_off_keeps_the_offer_and_asks_nothing(self) -> None:
        self.session.signed_in_as("someone")
        self.session.auto_relay("someone", "off")
        warning, pause = self.notices()
        self.assertIn("offering `/relay`", pause)
        self.assertNotIn(self.OPT_IN, warning)
        self.assertNotIn(self.OPT_IN, pause)

    def test_a_setting_that_is_neither_reads_as_never_asked(self) -> None:
        self.session.signed_in_as("someone")
        self.session.auto_relay("someone", "yes please")
        _, pause = self.notices()
        self.assertIn(self.OPT_IN, pause)
        self.assertNotIn("with no argument, run", pause)

    def test_a_bot_token_has_no_operator_to_ask(self) -> None:
        self.session.signed_in_as("claude[bot]", kind="Bot")
        self.session.auto_relay("claude[bot]", "on")
        _, pause = self.notices()
        self.assertIn("offering `/relay`", pause)
        self.assertNotIn(self.OPT_IN, pause)

    def test_an_unanswering_gh_has_no_operator_to_ask(self) -> None:
        _, pause = self.notices()
        self.assertIn("offering `/relay`", pause)
        self.assertNotIn(self.OPT_IN, pause)


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
