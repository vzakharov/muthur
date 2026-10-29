#!/usr/bin/env python3
"""What `oriented.py` run bare tells the operator, against transcripts built
from `test_pricing.py`'s records and rate table, where each `step` costs $10.

Run by path (`python3 .claude/costs/test_oriented.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `lib`.
"""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from typing import Sequence

from oriented import figures, transcript_of
from test_pricing import EDIT, MARK, PRICES, ROOT, boundary, response, step, t


def written(lines: Sequence[str], subagents: Sequence[str] = ()) -> str:
    with tempfile.TemporaryDirectory() as directory:
        transcript = Path(directory) / "sess.jsonl"
        transcript.write_text("\n".join(lines), encoding="utf-8")
        if subagents:
            folder = Path(directory) / "sess" / "subagents"
            folder.mkdir(parents=True)
            (folder / "agent-a.jsonl").write_text("\n".join(subagents), encoding="utf-8")
        return figures(transcript, PRICES)


class WhatTheMarkReports(unittest.TestCase):
    def test_the_context_now_and_what_orientation_cost(self) -> None:
        line = written([step(1), step(2), step(3, MARK, input=5, read=120_000, write_1h=2_000)])
        self.assertEqual(line, "context 122,005 tokens; orientation $20.00.")

    def test_takes_the_context_from_the_session_s_own_response_not_a_subagent_s(self) -> None:
        line = written(
            [step(1, read=50_000), step(3, MARK, read=60_000)],
            [response(id="msg_sub", sidechain=True, at=t(2), cwd=ROOT, read=900_000, output=1_000_000)],
        )
        self.assertTrue(line.startswith("context 60,000 tokens; "), line)

    def test_names_re_orientation_after_a_compaction(self) -> None:
        line = written([step(1), step(2, EDIT), boundary(3), step(4), step(5, MARK)])
        self.assertTrue(line.endswith("; re-orientation since the last compaction $10.00."), line)

    def test_gives_the_session_total_where_an_action_ended_orientation_first(self) -> None:
        line = written([step(1), step(2, EDIT), step(3, MARK)])
        self.assertTrue(line.endswith("; $30.00 spent, orientation having ended earlier at $10.00 by Edit."), line)

    def test_gives_the_session_total_on_a_repeat_mark(self) -> None:
        line = written([step(1), step(2, MARK), step(3), step(4, MARK)])
        self.assertTrue(line.endswith("; $40.00 spent, orientation having ended earlier at $10.00 by a mark."), line)


class WhereTheTranscriptIs(unittest.TestCase):
    def test_finds_the_session_s_file_under_any_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            projects = Path(directory)
            self.assertIsNone(transcript_of("abc", projects))
            older = projects / "-old-cwd" / "abc.jsonl"
            newer = projects / "-home-user-repo" / "abc.jsonl"
            for path in (older, newer):
                path.parent.mkdir()
                path.write_text("", encoding="utf-8")
            past = time.time() - 60
            os.utime(older, (past, past))
            self.assertEqual(transcript_of("abc", projects), newer)


if __name__ == "__main__":
    unittest.main()
