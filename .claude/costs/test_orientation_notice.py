#!/usr/bin/env python3
"""Drives the orientation notice as the harness does — a payload on stdin — over
transcripts with and without the mark. What it protects is the notice going
quiet once the stretch is marked, and coming back after a compaction.

Run by path (`python3 .claude/costs/test_orientation_notice.py`), as
`scripts/vet.sh` does.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "costs" / "hooks" / "orientation-notice.sh"


def bash(command: str) -> Dict[str, Any]:
    content = [{"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": {"command": command}}]
    return {"type": "assistant", "message": {"role": "assistant", "content": content}}


MARK = bash("python3 .claude/costs/oriented.py")
BOUNDARY = {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-03-04T05:00:00.000Z"}
PROMPT = {"type": "user", "message": {"role": "user", "content": "do it"}}


class OrientationNoticeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base)
        self.transcript = self.base / "transcript.jsonl"

    def notice(self, records: Optional[List[Any]], source: Optional[str] = None) -> Optional[str]:
        """The context the hook adds, or `None` when it adds nothing."""
        if records is not None:
            self.transcript.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        payload = {
            "session_id": "sess",
            "transcript_path": str(self.transcript),
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart" if source else "UserPromptSubmit",
        }
        if source:
            payload["source"] = source
        done = subprocess.run(
            [str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(ROOT)},
            check=True,
        )
        if not done.stdout.strip():
            return None
        return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_asks_for_the_mark_until_the_stretch_has_one(self) -> None:
        notice = self.notice([PROMPT, bash("cat .claude/costs/oriented.py")])
        assert notice is not None
        self.assertIn("`python3 .claude/costs/oriented.py`, bare", notice)
        self.assertIsNone(self.notice([PROMPT, MARK, PROMPT]))

    def test_asks_again_after_a_compaction(self) -> None:
        self.assertIsNotNone(self.notice([PROMPT, MARK, BOUNDARY, PROMPT]))
        self.assertIsNone(self.notice([PROMPT, MARK, BOUNDARY, MARK]))

    def test_asks_on_the_compaction_itself_without_reading_the_transcript(self) -> None:
        self.assertIsNotNone(self.notice([PROMPT, MARK], source="compact"))

    def test_a_transcript_that_does_not_parse_is_said_rather_than_skipped(self) -> None:
        self.transcript.write_text("{not json\n", encoding="utf-8")
        notice = self.notice(None)
        assert notice is not None
        self.assertIn("could not be read", notice)
        self.assertIn("not JSON", notice)

    def test_a_session_with_no_transcript_yet_is_asked(self) -> None:
        self.assertIsNotNone(self.notice(None))


if __name__ == "__main__":
    unittest.main()
