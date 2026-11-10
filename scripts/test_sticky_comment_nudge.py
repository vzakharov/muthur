#!/usr/bin/env python3
"""Drives `.claude/hooks/sticky-comment-nudge.py` as the harness does — a
payload on stdin — and reads what it prints. What it protects is which writes
count as a hand-built write of a sticky PR comment, the refuse-once-then-allow
contract, and the hook's markers staying those of `scripts/pr-comment.sh`.

`gh` is a stub first on `PATH`, answering the fetch of an edited comment from a
file and logging every call, so the fetch is tested at its boundary.

Run by path (`python3 scripts/test_sticky_comment_nudge.py`), as
`scripts/check-muthur.sh` does.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / ".claude" / "hooks" / "sticky-comment-nudge.py"
SCRIPT = REPO / "scripts" / "pr-comment.sh"
SQUASH = "Proposed squash title/body:\n\n```\nfix: a thing (#248)\n```\n"
ATTESTATION = "<!-- finalize-attestation sha=abc -->\nAttested.\n"
STUB = """#!/bin/sh
printf '%s\\n' "$*" >> "$STUB_DIR/calls"
[ -f "$STUB_DIR/fail" ] && exit 1
cat "$STUB_DIR/reply" 2>/dev/null
exit 0
"""


class NudgeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "repo"
        self.stub = Path(tmp.name) / "stub"
        self.root.mkdir()
        self.stub.mkdir()
        gh = self.stub / "gh"
        gh.write_text(STUB)
        gh.chmod(0o755)
        self.write("squash.md", SQUASH)
        self.write("attestation.md", ATTESTATION)
        self.write("plain.md", "Thanks, fixed in abc123.\n")

    def write(self, name: str, text: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def github_answers(self, body: str) -> None:
        (self.stub / "reply").write_text(body)

    def github_fails(self) -> None:
        (self.stub / "fail").write_text("")

    def fetches(self) -> list[str]:
        calls = self.stub / "calls"
        return calls.read_text().splitlines() if calls.is_file() else []

    def run_hook(self, payload: dict) -> Optional[str]:
        """The refusal's reason, or None when the call is allowed."""
        env = {
            **os.environ,
            "CLAUDE_PROJECT_DIR": str(self.root),
            "PATH": f"{self.stub}{os.pathsep}{os.environ['PATH']}",
            "STUB_DIR": str(self.stub),
        }
        result = subprocess.run(
            [str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout:
            return None
        emitted = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(emitted["hookEventName"], "PreToolUse")
        self.assertEqual(emitted["permissionDecision"], "deny")
        return emitted["permissionDecisionReason"]

    def reason(self, command: str, session: str = "sess") -> Optional[str]:
        return self.run_hook(
            {
                "session_id": session,
                "cwd": str(self.root),
                "tool_name": "Bash",
                "tool_input": {"command": command},
            }
        )

    def mcp(self, tool: str, **given: object) -> Optional[str]:
        return self.run_hook(
            {
                "session_id": "sess",
                "cwd": str(self.root),
                "tool_name": f"mcp__github__{tool}",
                "tool_input": given,
            }
        )

    def assert_refused(self, reason: Optional[str], line: str) -> None:
        self.assertIsNotNone(reason)
        assert reason is not None
        self.assertIn(line, reason)


class TheIncident(NudgeTestCase):
    def command(self) -> str:
        return (
            f"cd {self.root} && id=$(gh api repos/o/r/issues/248/comments "
            "--jq '.[] | select(.body | startswith(\"Proposed squash\")) | .id' | tail -1) "
            "&& gh api -X PATCH repos/o/r/issues/comments/$id -F body=@squash.md"
        )

    def test_refused_naming_the_script_line(self) -> None:
        self.assert_refused(self.reason(self.command()), "scripts/pr-comment.sh squash 248 squash.md")

    def test_the_identical_retry_goes_through(self) -> None:
        self.assertIsNotNone(self.reason(self.command()))
        self.assertIsNone(self.reason(self.command()))

    def test_sessions_are_kept_apart(self) -> None:
        self.reason(self.command(), session="one")
        self.assertIsNotNone(self.reason(self.command(), session="two"))

    def test_an_unreadable_id_is_not_fetched(self) -> None:
        self.reason(self.command())
        self.assertEqual(self.fetches(), [])

    def test_a_cd_moves_where_the_body_file_is_read(self) -> None:
        self.write("sub/squash-message.md", SQUASH)
        command = "cd sub && gh api repos/o/r/issues/7/comments -F body=@squash-message.md"
        self.assert_refused(
            self.reason(command), "scripts/pr-comment.sh squash 7 sub/squash-message.md"
        )


class BodiesThatLeadWithAMarker(NudgeTestCase):
    def test_gh_pr_comment_with_an_attestation_file(self) -> None:
        self.assert_refused(
            self.reason("gh pr comment 248 --body-file attestation.md"),
            "scripts/pr-comment.sh attestation 248 attestation.md",
        )

    def test_gh_issue_comment_too(self) -> None:
        self.assert_refused(self.reason("gh issue comment 9 -F squash.md"), "squash 9 squash.md")

    def test_an_inline_body_is_sent_to_a_file_first(self) -> None:
        reason = self.reason(
            "gh api repos/{owner}/{repo}/issues/248/comments -f body='Proposed squash: x'"
        )
        self.assert_refused(reason, "scripts/pr-comment.sh squash 248 <file>")
        assert reason is not None
        self.assertIn("write it to one first", reason)

    def test_option_spellings(self) -> None:
        for command in (
            "gh api --method=POST repos/o/r/issues/3/comments --field body=@squash.md",
            "gh api -XPATCH repos/o/r/issues/comments/$id -Fbody=@squash.md",
            "timeout 30 gh api repos/o/r/issues/3/comments -F body=@squash.md",
            "gh pr comment --body-file=attestation.md",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(self.reason(command))

    def test_a_number_the_command_lacks_is_left_to_fill_in(self) -> None:
        reason = self.reason("gh api -X PATCH repos/o/r/issues/comments/$id -F body=@squash.md")
        self.assert_refused(reason, "scripts/pr-comment.sh squash <n> squash.md")
        assert reason is not None
        self.assertIn("`<n>` is the PR's number", reason)


class EditsOfAStickyComment(NudgeTestCase):
    PATCH = "gh api -X PATCH repos/o/r/issues/comments/123 -F body=@plain.md"

    def test_a_markerless_patch_of_the_squash_proposal(self) -> None:
        self.github_answers(SQUASH)
        reason = self.reason(self.PATCH)
        self.assert_refused(reason, "scripts/pr-comment.sh squash <n> <file>")
        assert reason is not None
        self.assertIn("does not lead with `Proposed squash`", reason)
        self.assertEqual(self.fetches(), ["api repos/o/r/issues/comments/123 --jq .body"])

    def test_a_markerless_patch_of_an_ordinary_comment(self) -> None:
        self.github_answers("Thanks!\n")
        self.assertIsNone(self.reason(self.PATCH))

    def test_edit_last_over_the_attestation(self) -> None:
        self.github_answers(ATTESTATION)
        self.assert_refused(
            self.reason("gh pr comment 248 --edit-last --body-file plain.md"),
            "scripts/pr-comment.sh attestation 248 <file>",
        )
        self.assertEqual(len(self.fetches()), 1)
        self.assertTrue(self.fetches()[0].startswith("pr view 248 --json comments"))

    def test_a_failed_fetch_lets_it_through(self) -> None:
        self.github_fails()
        self.assertIsNone(self.reason(self.PATCH))


class WhatIsLeftAlone(NudgeTestCase):
    def test_writes_of_no_sticky_comment(self) -> None:
        for command in (
            "gh api repos/o/r/issues/3/comments -F body=@plain.md",
            "gh pr comment 3 --body 'LGTM'",
            "gh api repos/o/r/issues/3/comments -F body=@$f",
            "gh api repos/o/r/issues/3/comments -F body=@missing.md",
            "gh pr comment 3 --body-file -",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))

    def test_reads_and_deletes(self) -> None:
        for command in (
            "gh api repos/o/r/issues/248/comments --jq '.[].body'",
            "gh api repos/o/r/issues/248/comments -X GET -f per_page=100",
            "gh api -X DELETE repos/o/r/issues/comments/123",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))
        self.assertEqual(self.fetches(), [])

    def test_a_raw_field_sends_the_at_sign_as_written(self) -> None:
        self.assertIsNone(self.reason("gh api repos/o/r/issues/3/comments -f body=@squash.md"))

    def test_a_review_reply_is_not_fetched(self) -> None:
        command = "gh api repos/o/r/pulls/3/comments/55/replies -f body='Proposed squash'"
        self.assertIsNone(self.reason(command))
        self.assertEqual(self.fetches(), [])

    def test_the_script_itself(self) -> None:
        for command in (
            "scripts/pr-comment.sh squash 248 squash.md",
            "scripts/pr-comment.sh attestation --update-only 248 attestation.md",
        ):
            with self.subTest(command=command):
                self.assertIsNone(self.reason(command))

    def test_an_untokenisable_command_is_allowed(self) -> None:
        self.assertIsNone(self.reason("gh pr comment 3 --body 'unterminated"))

    def test_a_bad_payload_is_allowed(self) -> None:
        self.assertIsNone(self.run_hook({"tool_name": "Bash"}))

    def test_an_unrecordable_refusal_is_not_made(self) -> None:
        (self.root / "tmp").write_text("a file where the state directory goes")
        self.assertIsNone(self.reason("gh pr comment 3 --body-file squash.md"))


class TheMcpTools(NudgeTestCase):
    def test_adding_a_marked_body(self) -> None:
        reason = self.mcp("add_issue_comment", owner="o", repo="r", issue_number=248, body=SQUASH)
        self.assert_refused(reason, "scripts/pr-comment.sh squash 248 <file>")

    def test_updating_with_a_marked_body(self) -> None:
        self.github_answers("Thanks!\n")
        self.assertIsNotNone(
            self.mcp("update_issue_comment", owner="o", repo="r", comment_id=5, body=ATTESTATION)
        )

    def test_updating_the_squash_proposal_without_its_marker(self) -> None:
        self.github_answers(SQUASH)
        self.assertIsNotNone(
            self.mcp("update_issue_comment", owner="o", repo="r", comment_id=5, body="x")
        )
        self.assertEqual(self.fetches(), ["api repos/o/r/issues/comments/5 --jq .body"])

    def test_ordinary_comments_and_reactions(self) -> None:
        self.github_answers("Thanks!\n")
        self.assertIsNone(self.mcp("add_issue_comment", owner="o", repo="r", issue_number=3, body="x"))
        self.assertIsNone(
            self.mcp("add_issue_comment", owner="o", repo="r", issue_number=3, reaction="+1")
        )
        self.assertIsNone(
            self.mcp("update_issue_comment", owner="o", repo="r", comment_id=5, body="x")
        )


class TheMarkers(unittest.TestCase):
    def test_they_are_the_scripts(self) -> None:
        arms = re.findall(r'^\s*([a-z-]+)\) MARKER="([^"]+)" ;;$', SCRIPT.read_text(), re.M)
        self.assertTrue(arms, f"no marker arms found in {SCRIPT}")
        spec = importlib.util.spec_from_file_location("sticky_comment_nudge", HOOK)
        assert spec is not None and spec.loader is not None
        hook = importlib.util.module_from_spec(spec)
        # A `@dataclass` looks its module up here while the module still executes.
        sys.modules[spec.name] = hook
        sys.path.insert(0, str(HOOK.parent))
        spec.loader.exec_module(hook)
        self.assertEqual(hook.MARKERS, dict(arms))
        self.assertEqual(set(hook.WHAT), set(hook.MARKERS))


if __name__ == "__main__":
    unittest.main()
