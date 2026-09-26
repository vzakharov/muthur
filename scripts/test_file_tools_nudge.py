#!/usr/bin/env python3
"""Drives `.claude/hooks/file-tools-nudge.py` as the harness does — a payload on
stdin — and reads what it prints. What it protects is which commands count as a
shell read, edit or write of a file, and the refuse-once-then-allow contract.

Run by path (`python3 scripts/test_file_tools_nudge.py`), as
`scripts/check-muthur.sh` does.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "file-tools-nudge.py"


class NudgeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def run_hook(self, stdin: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        result = subprocess.run(
            [str(HOOK)], input=stdin, capture_output=True, text=True, env=env, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def reason(self, command: str, session: str = "sess") -> Optional[str]:
        """The refusal's reason, or None when the command is allowed."""
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": session,
            "tool_name": "Bash",
            "tool_input": {"command": command},
        }
        stdout = self.run_hook(json.dumps(payload)).stdout
        if not stdout:
            return None
        emitted = json.loads(stdout)["hookSpecificOutput"]
        self.assertEqual(emitted["hookEventName"], "PreToolUse")
        self.assertEqual(emitted["permissionDecision"], "deny")
        return emitted["permissionDecisionReason"]


class WhatIsRefused(NudgeTestCase):
    def assert_refused(self, command: str, tool: str) -> None:
        reason = self.reason(command)
        self.assertIsNotNone(reason, command)
        assert reason is not None
        self.assertIn(tool, reason, command)

    def test_reads(self) -> None:
        for command in (
            "cat README.md",
            "cat -n src/app.py",
            "head -n 40 CLAUDE.md",
            "tail -20 log.txt",
            "sed -n '10,20p' notes.md",
            "cd sub && cat file.txt",
            "git status; less CHANGELOG.md",
            "cat < input.txt",
            "echo $(cat VERSION)",
            "timeout 5 head big.log",
        ):
            with self.subTest(command=command):
                self.assert_refused(command, "`Read`")

    def test_edits(self) -> None:
        for command in (
            "sed -i 's/foo/bar/' a.txt",
            "sed -i.bak -e 's/a/b/' a.txt",
            "sed --in-place 's/a/b/' a.txt",
            "sed -Ei 's/a+/b/' a.txt",
            "perl -pi -e 's/a/b/' a.txt",
            "awk -i inplace '{print}' a.txt",
            "grep -rl foo . | xargs sed -i 's/foo/bar/g'",
            "find . -name '*.md' -exec sed -i 's/a/b/' {} +",
            "sudo sed -i 's/a/b/' /etc/hosts",
        ):
            with self.subTest(command=command):
                self.assert_refused(command, "`Edit`")

    def test_writes(self) -> None:
        for command in (
            "cat > out.txt <<'EOF'\nit's got an apostrophe\nEOF",
            "cat <<EOF > out.txt\nbody\nEOF",
            "echo hello > greeting.txt",
            "printf '%s\\n' a >> list.txt",
            "echo data | tee copy.txt",
        ):
            with self.subTest(command=command):
                self.assert_refused(command, "`Write`")


class WhatIsLeftAlone(NudgeTestCase):
    def test_commands_not_touching_a_file_through_the_shell(self) -> None:
        for command in (
            "git log --oneline | head -5",
            "ls -la | tail -n 3",
            "echo hi",
            "echo oops >&2",
            "echo gone > /dev/null",
            "head -5 2>/dev/null",
            "git diff | sed 's/^/  /'",
            "cat <<'EOF' | python3 -\nprint('x')\nEOF",
            "git commit -m \"$(cat <<'EOF'\nsubject\n\nit's the body\nEOF\n)\"",
            "grep -rn pattern src/",
            "python3 script.py > out.json",
            "perl -ne 'print if /x/' a.txt",
            "cat /proc/cpuinfo",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))

    def test_an_untokenisable_command_is_allowed(self) -> None:
        self.assertIsNone(self.reason("cat 'unterminated"))

    def test_another_tool_is_ignored(self) -> None:
        payload = {"session_id": "sess", "tool_name": "Read", "tool_input": {"command": "cat a"}}
        self.assertEqual(self.run_hook(json.dumps(payload)).stdout, "")

    def test_a_bad_payload_is_allowed_and_said_on_stderr(self) -> None:
        result = self.run_hook("not json")
        self.assertEqual(result.stdout, "")
        self.assertIn("unreadable payload", result.stderr)


class RefusedOnceThenAllowed(NudgeTestCase):
    def test_the_identical_command_goes_through_on_retry(self) -> None:
        self.assertIsNotNone(self.reason("cat README.md"))
        self.assertIsNone(self.reason("cat README.md"))
        self.assertIsNone(self.reason("cat README.md"))

    def test_a_different_command_is_refused_afresh(self) -> None:
        self.reason("cat README.md")
        self.assertIsNotNone(self.reason("cat CLAUDE.md"))

    def test_sessions_are_kept_apart(self) -> None:
        self.reason("cat README.md", session="one")
        self.assertIsNotNone(self.reason("cat README.md", session="two"))

    def test_the_reason_says_how_to_go_through(self) -> None:
        reason = self.reason("cat README.md")
        assert reason is not None
        self.assertIn("run the identical command again", reason)
        self.assertIn("with `cat`", reason)

    def test_an_unrecordable_refusal_is_not_made(self) -> None:
        (self.root / "tmp").write_text("a file where the state directory goes")
        self.assertIsNone(self.reason("cat README.md"))


if __name__ == "__main__":
    unittest.main()
