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
EDIT = "sed -i 's/a/b/' README.md"


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

    def reason(
        self, command: str, session: str = "sess", cwd: Optional[Path] = None
    ) -> Optional[str]:
        """The refusal's reason, or None when the command is allowed."""
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": session,
            "cwd": str(cwd or self.root),
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

    def test_edits(self) -> None:
        for command in (
            "sed -i 's/foo/bar/' a.txt",
            "sed -i.bak -e 's/a/b/' a.txt",
            "sed --in-place 's/a/b/' a.txt",
            "sed -Ei 's/a+/b/' a.txt",
            "sed -e 's/a/b/' -i a.txt",
            "cd sub && sed -i 's/a/b/' a.txt",
            "timeout 5 sed -i 's/a/b/' a.txt",
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

    def test_reads_of_project_files(self) -> None:
        for command in (
            "cat README.md",
            "head -n 40 CLAUDE.md",
            "tail -20 log.txt",
            "head -n 5 a.md b.md",
            "sed -n '10,20p' notes.md",
            "sed 's/i/x/' notes.md",
            "sed -n -e '1p' notes.md",
            "cat < input.txt",
            "cd sub && cat a.md",
            "timeout 5 head a.md",
            "less docs/guide.md",
            "nl -ba script.py",
            "cat .claude/hooks/../rules/staging.md",
        ):
            with self.subTest(command=command):
                self.assert_refused(command, "`Read`")

    def test_an_absolute_path_inside_the_project(self) -> None:
        self.assert_refused(f"cat {self.root}/CLAUDE.md", "`Read`")

    def test_a_relative_path_resolves_against_the_cwd(self) -> None:
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        self.assertIsNone(self.reason("cat notes.md", cwd=Path(outside.name)))


class WhatIsLeftAlone(NudgeTestCase):
    def test_reads_that_feed_another_command(self) -> None:
        for command in (
            "cat data.json | jq .name",
            "head -100 log.txt | grep ERROR",
            "echo $(cat VERSION)",
            "v=$(head -1 VERSION) && echo $v",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))

    def test_reads_of_files_outside_the_project(self) -> None:
        for command in (
            "cat /etc/hosts",
            "head -20 ~/.bashrc",
            "cat ../elsewhere.md",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))

    def test_commands_reading_no_named_file(self) -> None:
        for command in (
            "sed 's/i/x/'",
            "head -n 5",
            "perl -e 'print' -i",
            "find . -name '*.md' | xargs cat",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))

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
        self.assertIsNone(self.reason("sed -i 'unterminated"))

    def test_another_tool_is_ignored(self) -> None:
        payload = {"session_id": "sess", "tool_name": "Read", "tool_input": {"command": "cat a"}}
        self.assertEqual(self.run_hook(json.dumps(payload)).stdout, "")

    def test_a_bad_payload_is_allowed_and_said_on_stderr(self) -> None:
        result = self.run_hook("not json")
        self.assertEqual(result.stdout, "")
        self.assertIn("unreadable payload", result.stderr)


class TheBatchPrefix(NudgeTestCase):
    def test_everything_after_it_goes_through_the_first_time(self) -> None:
        for command in (
            "BATCH_EDIT=1 sed -i 's/a/b/' a.txt",
            "LC_ALL=C BATCH_EDIT=1 sed -i 's/a/b/' a.txt",
            "BATCH_EDIT=1 find . -name '*.md' -exec sed -i 's/a/b/' {} +",
            "cd sub && BATCH_EDIT=1 sed -i 's/a/b/' a.txt && echo x > b.txt",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))

    def test_what_comes_before_it_is_still_checked(self) -> None:
        self.assertIsNotNone(self.reason("echo x > b.txt && BATCH_EDIT=1 sed -i 's/a/b/' a.txt"))

    def test_only_as_an_assignment_in_front_of_a_command(self) -> None:
        for command in (
            "echo BATCH_EDIT=1 > notes.txt",
            "BATCH_EDIT=0 sed -i 's/a/b/' a.txt",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(self.reason(command))


class RefusedOnceThenAllowed(NudgeTestCase):
    def test_the_identical_command_goes_through_on_retry(self) -> None:
        self.assertIsNotNone(self.reason(EDIT))
        self.assertIsNone(self.reason(EDIT))
        self.assertIsNone(self.reason(EDIT))

    def test_a_different_command_is_refused_afresh(self) -> None:
        self.reason(EDIT)
        self.assertIsNotNone(self.reason("sed -i 's/a/b/' CLAUDE.md"))

    def test_sessions_are_kept_apart(self) -> None:
        self.reason(EDIT, session="one")
        self.assertIsNotNone(self.reason(EDIT, session="two"))

    def test_the_reason_says_how_to_go_through(self) -> None:
        reason = self.reason(EDIT)
        assert reason is not None
        self.assertIn("run the identical command again", reason)
        self.assertIn("with `sed -i`", reason)
        self.assertIn("`BATCH_EDIT=1`", reason)

    def test_a_read_is_told_what_the_shell_misses(self) -> None:
        reason = self.reason("head -n 40 CLAUDE.md")
        assert reason is not None
        self.assertIn("with `head`", reason)
        self.assertIn("path-scoped rule", reason)

    def test_an_unrecordable_refusal_is_not_made(self) -> None:
        (self.root / "tmp").write_text("a file where the state directory goes")
        self.assertIsNone(self.reason(EDIT))


if __name__ == "__main__":
    unittest.main()
