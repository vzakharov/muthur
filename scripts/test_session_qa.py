#!/usr/bin/env python3
"""Tests for which transcript records `session-qa.py` prints, and that the
envelope pattern it reads typed commands with is the cost ledger's own.

The transcripts are built from the record shapes the client writes: a prompt that
starts a turn is a `user` record with `origin.kind == "human"`, one sent mid-turn
a `queued_command` attachment, a subagent's hand-back the same attachment from a
`peer`.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional

SCRIPT = Path(__file__).resolve().parent / "session-qa.py"
COSTS = Path(__file__).resolve().parents[1] / ".claude" / "costs"
MODEL = "claude-sonnet-5-5"


def prompt(text: object, stamp: str = "2026-10-01T10:00:00.000Z", **extra: object) -> dict:
    return {
        "type": "user",
        "timestamp": stamp,
        "origin": {"kind": "human"},
        "message": {"role": "user", "content": text},
        **extra,
    }


def mid_turn(text: str, stamp: str = "2026-10-01T10:05:00.000Z", origin: str = "human") -> dict:
    return {
        "type": "attachment",
        "timestamp": stamp,
        "attachment": {"type": "queued_command", "prompt": text, "origin": {"kind": origin}},
    }


def said(*blocks: dict, stamp: str = "2026-10-01T10:00:30.000Z", model: str = MODEL, **extra: object) -> list:
    """One response, as the client writes it: a record per block."""
    return [
        {"type": "assistant", "timestamp": stamp, "message": {"model": model, "content": [block]}, **extra}
        for block in blocks
    ]


def text(value: str) -> dict:
    return {"type": "text", "text": value}


def tool_use(name: str, **tool_input: object) -> dict:
    return {"type": "tool_use", "id": "t", "name": name, "input": tool_input}


TOOL_RESULT = {
    "type": "user",
    "timestamp": "2026-10-01T10:00:40.000Z",
    "message": {"role": "user", "content": [{"type": "tool_result", "content": "SECRET-OUTPUT"}]},
}
SKILL_BODY = {
    "type": "user",
    "isMeta": True,
    "timestamp": "2026-10-01T10:00:20.000Z",
    "message": {"role": "user", "content": [{"type": "text", "text": "SKILL-BODY"}]},
}
WAKE = {
    "type": "user",
    "timestamp": "2026-10-01T10:30:00.000Z",
    "origin": {"kind": "task-notification"},
    "message": {"role": "user", "content": "<task-notification>Cache keepalive WAKE</task-notification>"},
}


class QaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.transcript = self.dir / "session.jsonl"

    def write(self, *records: object, tail: str = "") -> None:
        lines = [json.dumps(r) + "\n" for item in records for r in (item if isinstance(item, list) else [item])]
        self.transcript.write_text("".join(lines) + tail)

    def run_script(self, *args: str, cwd: Optional[Path] = None, env: Optional[dict] = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            check=False,
        )

    def output(self, *args: str, cwd: Optional[Path] = None) -> str:
        result = self.run_script("--transcript", str(self.transcript), *args, cwd=cwd)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def headings(self, out: str) -> List[str]:
        return [line.split(" ", 2)[1] for line in out.splitlines() if line.startswith("## ")]


class WhatIsPrinted(QaTestCase):
    def test_questions_and_answers_in_order_with_their_timestamps(self) -> None:
        self.write(
            prompt("first question"),
            said(text("first answer")),
            mid_turn("sent while it worked"),
            prompt("second question", stamp="2026-10-01T11:00:00.000Z"),
        )
        self.assertEqual(
            self.output(),
            "## Q 2026-10-01T10:00:00.000Z\n\nfirst question\n\n"
            "## A 2026-10-01T10:00:30.000Z\n\nfirst answer\n\n"
            "## Q 2026-10-01T10:05:00.000Z\n\nsent while it worked\n\n"
            "## Q 2026-10-01T11:00:00.000Z\n\nsecond question\n\n",
        )

    def test_what_is_not_a_question_or_an_answer_stays_out(self) -> None:
        self.write(
            prompt("the question"),
            SKILL_BODY,
            said({"type": "thinking", "thinking": "THOUGHT"}, text("the answer"), tool_use("Bash", command="ls")),
            TOOL_RESULT,
            WAKE,
            mid_turn("a subagent's report", origin="peer"),
            said(text("A SUBAGENT SAYS"), isSidechain=True),
            prompt("a subagent's prompt", isSidechain=True),
            said(text("No response requested."), model="<synthetic>"),
        )
        out = self.output()
        self.assertEqual(self.headings(out), ["Q", "A"])
        for left_out in ("SKILL-BODY", "THOUGHT", "SECRET-OUTPUT", "WAKE", "subagent", "SUBAGENT", "No response", "ls"):
            self.assertNotIn(left_out, out)

    def test_a_typed_command_is_unwrapped_from_its_envelope(self) -> None:
        envelope = (
            "<command-message>go</command-message>\n<command-name>/go</command-name>\n"
            "<command-args>claude/x-1</command-args>"
        )
        bare = "<command-message>polish</command-message>\n<command-name>/polish</command-name>"
        self.write(prompt(envelope), prompt(bare))
        self.assertEqual(
            [line for line in self.output().splitlines() if line.startswith("/")],
            ["/go claude/x-1", "/polish"],
        )

    def test_a_message_with_an_image_prints_its_text(self) -> None:
        blocks = [text("the cover"), {"type": "image", "source": {"type": "base64", "data": "AAAA"}}]
        self.write(prompt(blocks), prompt([{"type": "image", "source": {"type": "base64", "data": "AAAA"}}]))
        out = self.output()
        self.assertIn("the cover", out)
        self.assertIn("(no text)", out)

    def test_an_answer_keeps_its_text_blocks_apart_with_tool_lines_between(self) -> None:
        self.write(
            prompt("q"),
            said(text("Checking."), tool_use("Bash", command="git  log\n--oneline"), text("Done.")),
        )
        self.assertNotIn("Bash", self.output())
        out = self.output("--tools")
        self.assertEqual(self.headings(out), ["Q", "A", "A"])
        self.assertLess(out.index("Checking."), out.index("- Bash: git log --oneline"))
        self.assertLess(out.index("- Bash: git log --oneline"), out.index("Done."))

    def test_a_tool_line_names_the_tool_alone_when_it_has_nothing_to_show(self) -> None:
        self.write(said(tool_use("ExitPlanMode"), tool_use("Read", file_path="/a/b.py")))
        self.assertEqual(self.output("--tools").split(), ["-", "ExitPlanMode", "-", "Read:", "/a/b.py"])

    def test_a_half_written_last_line_is_passed_over(self) -> None:
        self.write(prompt("q"), said(text("a")), tail='{"type": "assistant", "message": {"mod')
        self.assertEqual(self.headings(self.output()), ["Q", "A"])


class Since(QaTestCase):
    def repo_with_commit_at(self, when: str) -> Path:
        repo = self.dir / "repo"
        repo.mkdir()
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
            "GIT_AUTHOR_DATE": when,
            "GIT_COMMITTER_DATE": when,
        }
        for command in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "floor"]):
            subprocess.run(["git", *command], cwd=repo, env=env, check=True, capture_output=True)
        return repo

    def test_starts_at_the_commits_committer_time(self) -> None:
        repo = self.repo_with_commit_at("2026-10-01T10:03:00+00:00")
        self.write(
            prompt("before"),
            said(text("answer before")),
            mid_turn("after"),
            said(text("answer after"), stamp="2026-10-01T10:06:00.000Z"),
        )
        out = self.output("--since", "HEAD", cwd=repo)
        self.assertEqual(self.headings(out), ["Q", "A"])
        self.assertNotIn("before", out)
        self.assertIn("answer after", out)

    def test_an_unknown_commit_fails_loudly(self) -> None:
        repo = self.repo_with_commit_at("2026-10-01T10:03:00+00:00")
        self.write(prompt("q"))
        result = self.run_script("--transcript", str(self.transcript), "--since", "nosuchcommit", cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("nosuchcommit", result.stderr)
        self.assertEqual(result.stdout, "")


class Failing(QaTestCase):
    def test_an_unknown_transcript(self) -> None:
        result = self.run_script("--transcript", str(self.dir / "missing.jsonl"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("transcript not found", result.stderr)

    def test_no_transcript_named_and_no_session(self) -> None:
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
        result = self.run_script(env=env)
        self.assertEqual(result.returncode, 1)
        self.assertIn("CLAUDE_CODE_SESSION_ID", result.stderr)

    def test_the_default_is_the_sessions_transcript_under_home(self) -> None:
        project = self.dir / ".claude" / "projects" / "p"
        project.mkdir(parents=True)
        self.transcript = project / "sess-1.jsonl"
        self.write(prompt("found by id"))
        env = {**os.environ, "HOME": str(self.dir), "CLAUDE_CODE_SESSION_ID": "sess-1"}
        result = self.run_script(env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("found by id", result.stdout)


class TheCostLedgersEnvelope(unittest.TestCase):
    @unittest.skipUnless((COSTS / "lib" / "identity.py").is_file(), "no cost ledger in this tree")
    def test_the_pattern_is_the_ledgers_own(self) -> None:
        # Its own process: the ledger's `lib` package and `scripts/lib` share a name.
        source = "from lib.identity import COMMAND_ENVELOPE; print(COMMAND_ENVELOPE.pattern)"
        ledger = subprocess.run(
            [sys.executable, "-c", source], cwd=COSTS, capture_output=True, text=True, check=True
        ).stdout.strip()
        source = "from lib.session_transcript import COMMAND_ENVELOPE; print(COMMAND_ENVELOPE.pattern)"
        ours = subprocess.run(
            [sys.executable, "-c", source],
            cwd=Path(__file__).resolve().parent,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(ours, ledger)


if __name__ == "__main__":
    unittest.main()
