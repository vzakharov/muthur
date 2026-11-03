#!/usr/bin/env python3
"""Tests `.claude/hooks/finalize-bash-gate.py`: which entries into `/finalize`
it refuses on a machine whose bash is older than 4, how each refusal reaches the
agent, and that it stays out of every other call.

`/bin/bash` cannot be swapped for a test, so the version check runs against
stand-in shells, and the hook runs in-process with that check replaced.

Run by path (`python3 scripts/test_finalize_bash_gate.py`), as
`scripts/check-muthur.sh` does.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Optional
from unittest import mock

HOOKS = Path(__file__).resolve().parent.parent / ".claude" / "hooks"
HOOK = HOOKS / "finalize-bash-gate.py"

sys.path.insert(0, str(HOOKS))
spec = importlib.util.spec_from_file_location("finalize_bash_gate", HOOK)
assert spec is not None and spec.loader is not None
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class WhyRefused(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def shell(self, name: str, prints: str, status: int = 0) -> str:
        path = self.dir / name
        path.write_text(f"#!/bin/sh\nprintf '%s' '{prints}'\nexit {status}\n")
        path.chmod(0o755)
        return str(path)

    def test_every_shell_bash_4_or_newer_passes(self) -> None:
        shells = (self.shell("a", "5.2.21(1)-release"), self.shell("b", "4.0.0(1)-release"))
        self.assertIsNone(gate.why_refused(shells))

    def test_one_old_shell_is_named_with_its_version(self) -> None:
        old = self.shell("old", "3.2.57(1)-release")
        why = gate.why_refused((self.shell("new", "5.2"), old))
        self.assertEqual(why, f"`{old}` is bash 3.2.57(1)-release")

    def test_a_missing_shell(self) -> None:
        missing = str(self.dir / "nowhere")
        why = gate.why_refused((missing,))
        self.assertIsNotNone(why)
        self.assertIn("does not run", why or "")

    def test_a_shell_that_is_not_bash(self) -> None:
        for name, prints, status in (("empty", "", 0), ("words", "zsh", 0), ("fails", "5.2", 1)):
            with self.subTest(name=name):
                why = gate.why_refused((self.shell(name, prints, status),))
                self.assertIn("is not bash", why or "")

    def test_this_machine_has_bash_4(self) -> None:
        # The repo's own CI and cloud sessions run here; a refusal would stop
        # every /finalize, so the real shells are checked too.
        self.assertIsNone(gate.why_refused())


class TheHook(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.skill = self.root / ".claude" / "skills" / "finalize" / "SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("FINALIZE-BODY")
        env = mock.patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(self.root)})
        env.start()
        self.addCleanup(env.stop)

    def run_hook(self, payload: dict, why: Optional[str]) -> str:
        out = io.StringIO()
        with mock.patch.object(gate, "why_refused", return_value=why), mock.patch(
            "sys.stdin", io.StringIO(json.dumps(payload))
        ), redirect_stdout(out):
            self.assertEqual(gate.main([]), 0)
        return out.getvalue()

    def pre(self, tool: str, tool_input: object) -> dict:
        return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input}

    def skill_call(self, skill: str = "finalize") -> dict:
        return self.pre("Skill", {"skill": skill, "args": "and merge"})

    def typed(self, prompt: str) -> dict:
        return {"hook_event_name": "UserPromptSubmit", "prompt": prompt}

    def assert_denied(self, payload: dict) -> str:
        output = json.loads(self.run_hook(payload, "`/bin/bash` is bash 3.2"))["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("`/bin/bash` is bash 3.2", output["permissionDecisionReason"])
        return output["permissionDecisionReason"]

    def test_a_skill_call_is_denied_with_the_handoff(self) -> None:
        for skill in ("finalize", "/finalize"):
            with self.subTest(skill=skill):
                reason = self.assert_denied(self.skill_call(skill))
                self.assertIn('claude --cloud "/finalize', reason)
                self.assertIn("create_session", reason)
                self.assertIn("start_session", reason)
                self.assertIn("without asking", reason)

    def test_a_read_of_the_skill_body_is_denied(self) -> None:
        # How /merge and /from-branch reach /finalize.
        self.assert_denied(self.pre("Read", {"file_path": str(self.skill)}))

    def test_a_typed_command_gets_the_handoff_as_context(self) -> None:
        for prompt in ("/finalize", "/finalize and merge", "  /finalize no vet"):
            with self.subTest(prompt=prompt):
                output = json.loads(self.run_hook(self.typed(prompt), "old"))["hookSpecificOutput"]
                self.assertEqual(output["hookEventName"], "UserPromptSubmit")
                self.assertNotIn("permissionDecision", output)
                self.assertIn("set it aside", output["additionalContext"])

    def test_silent_where_bash_passes(self) -> None:
        for payload in (self.skill_call(), self.typed("/finalize")):
            with self.subTest(event=payload["hook_event_name"]):
                self.assertEqual(self.run_hook(payload, None), "")

    def test_silent_on_anything_else(self) -> None:
        other = self.root / ".claude" / "skills" / "go" / "SKILL.md"
        for payload in (
            self.skill_call("go"),
            self.skill_call("finalize-later"),
            self.pre("Read", {"file_path": str(other)}),
            self.pre("Read", {"file_path": str(self.skill.parent / "merge.md")}),
            self.pre("Bash", {"command": "/finalize"}),
            {**self.skill_call(), "hook_event_name": "PostToolUse"},
            self.typed("please /finalize"),
            self.typed("/finalizer"),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.run_hook(payload, "old"), "")


class AsAProcess(unittest.TestCase):
    def run_script(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(HOOK), *args], input=stdin, capture_output=True, text=True, check=False
        )

    def test_an_unreadable_payload_is_allowed_and_said_on_stderr(self) -> None:
        result = self.run_script(stdin="not json")
        self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertIn("unreadable payload", result.stderr)

    def test_check_passes_quietly_on_this_machine(self) -> None:
        result = self.run_script("check")
        self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_check_prints_the_handoff_where_bash_is_old(self) -> None:
        out = io.StringIO()
        with mock.patch.object(gate, "why_refused", return_value="old"), redirect_stdout(out):
            self.assertEqual(gate.main(["check"]), 1)
        self.assertIn('claude --cloud "/finalize', out.getvalue())

    def test_an_unknown_argument(self) -> None:
        result = self.run_script("nope")
        self.assertEqual(result.returncode, 2)
        self.assertIn("check", result.stderr)


if __name__ == "__main__":
    unittest.main()
