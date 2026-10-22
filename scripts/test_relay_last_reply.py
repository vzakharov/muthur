#!/usr/bin/env python3
"""Tests for which reply `relay-last-reply.py` appends to a relay summary.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

SCRIPT = Path(__file__).resolve().parent / "relay-last-reply.py"
KEEPALIVE = Path(__file__).resolve().parents[1] / ".claude" / "keepalive" / "hooks" / "keepalive.py"


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # A `@dataclass` looks its module up here while the module still executes.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prompt(turn: str, text: str = "a prompt") -> dict:
    return {
        "type": "user",
        "promptId": turn,
        "origin": {"kind": "human"},
        "message": {"role": "user", "content": text},
    }


def tool_result(turn: str) -> dict:
    return {
        "type": "user",
        "promptId": turn,
        "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]},
    }


def wake(turn: str) -> dict:
    """A keepalive wake: the watcher's completion notice, opening a turn."""
    return {
        "type": "user",
        "promptId": turn,
        "origin": {"kind": "task-notification"},
        "message": {
            "role": "user",
            "content": '<task-notification><summary>Background command "Cache keepalive watcher"'
            " completed (exit code 0)</summary></task-notification>",
        },
    }


def said(*blocks: dict, **extra: object) -> list[dict]:
    """One response, written as the client writes it: a record per block."""
    return [
        {"type": "assistant", "message": {"role": "assistant", "content": [block]}, **extra}
        for block in blocks
    ]


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def tool_use() -> dict:
    return {"type": "tool_use", "id": "t", "name": "Bash", "input": {}}


class LastReplyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.summary = self.dir / "relay-1.md"
        self.summary.write_text("# Relay\n\n## Next step\n\nWait.\n")

    def run_script(self, *records: object) -> subprocess.CompletedProcess[str]:
        transcript = self.dir / "session.jsonl"
        lines = []
        for record in records:
            for r in record if isinstance(record, list) else [record]:
                lines.append(json.dumps(r) + "\n")
        transcript.write_text("".join(lines))
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.summary), "--transcript", str(transcript)],
            capture_output=True,
            text=True,
        )

    def appended(self, *records: object) -> str:
        result = self.run_script(*records)
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.summary.read_text().split("## Last reply\n", 1)[1]

    def test_appends_the_previous_turns_text_and_not_the_running_ones(self) -> None:
        out = self.appended(
            prompt("p1"),
            said(text("an older reply")),
            prompt("p2"),
            said(text("Checking."), tool_use()),
            tool_result("p2"),
            said({"type": "thinking", "thinking": "hm"}, text("The **whole** report.")),
            prompt("p3", "/relay"),
            said(text("Writing the summary."), tool_use()),
        )
        self.assertIn("```text\nChecking.\n\nThe **whole** report.\n```\n", out)
        self.assertNotIn("older", out)
        self.assertNotIn("Writing the summary", out)

    def test_passes_over_a_turn_that_wrote_no_text(self) -> None:
        out = self.appended(
            prompt("p1"),
            said(text("the reply")),
            prompt("p2"),
            said(tool_use()),
            prompt("p3", "/relay"),
        )
        self.assertIn("the reply", out)

    def test_skips_a_subagents_records(self) -> None:
        out = self.appended(
            prompt("p1"),
            said(text("the reply")),
            said(text("a subagent's report"), isSidechain=True),
            prompt("p2", "/relay"),
        )
        self.assertNotIn("subagent", out)

    def test_passes_over_a_keepalive_wake_the_operator_answered_with_park(self) -> None:
        out = self.appended(
            prompt("p1"),
            said(text("the reply")),
            wake("p2"),
            said(tool_use()),
            tool_result("p2"),
            said(text("🕯 cache extended 1/1 · say 'park' to record it and stop extending")),
            prompt("p3", "park"),
        )
        self.assertIn("the reply", out)
        self.assertNotIn("cache extended", out)

    def test_a_wake_that_parks_on_its_own_is_the_running_turn(self) -> None:
        out = self.appended(
            prompt("p1"),
            said(text("an older reply")),
            prompt("p2"),
            said(text("the reply")),
            wake("p3"),
            said(text("Parking."), tool_use()),
        )
        self.assertIn("the reply", out)
        self.assertNotIn("older", out)

    def test_keeps_a_reply_to_an_operator_who_named_the_keepalive(self) -> None:
        out = self.appended(
            prompt("p1", "why did the Cache keepalive watcher fire?"),
            said(text("the reply")),
            prompt("p2", "/relay"),
        )
        self.assertIn("the reply", out)

    @unittest.skipUnless(KEEPALIVE.is_file(), "no cache keepalive in this tree")
    def test_the_wake_mark_is_the_keepalives_own(self) -> None:
        self.assertEqual(
            load("relay_last_reply", SCRIPT).KEEPALIVE_MARK,
            load("keepalive", KEEPALIVE).MARK,
        )

    def test_fences_a_reply_holding_a_fence_with_a_longer_one(self) -> None:
        out = self.appended(
            prompt("p1"),
            said(text("Send this:\n\n```\n/relay take x\n```")),
            prompt("p2", "/relay"),
        )
        self.assertIn("````text\nSend this:\n\n```\n/relay take x\n```\n````\n", out)

    def test_keeps_the_summary_and_leaves_a_blank_line_before_the_section(self) -> None:
        self.appended(prompt("p1"), said(text("r")), prompt("p2"))
        self.assertTrue(self.summary.read_text().startswith("# Relay\n\n## Next step\n\nWait.\n\n## Last reply\n"))

    def test_fails_and_writes_nothing_with_no_earlier_reply(self) -> None:
        result = self.run_script(prompt("p1", "/relay"), said(text("Writing.")))
        self.assertEqual(result.returncode, 1)
        self.assertIn("no turn before this one", result.stderr)
        self.assertEqual(self.summary.read_text(), "# Relay\n\n## Next step\n\nWait.\n")


if __name__ == "__main__":
    unittest.main()
