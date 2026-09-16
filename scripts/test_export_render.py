#!/usr/bin/env python3
"""Tests for hunk trimming and the export's index-plus-bodies layout.

What they guard above all is that a trimmed hunk still carries the reviewer's
selection byte for byte.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import unittest

from gh_export.markdown import comments_parts
from gh_export.reviews import (
    CONTEXT_LINE_CHARS,
    review_parts,
    selection_of,
    thread_summary,
    trim_hunk,
)
from gh_export.index import Indexed, indexed_section

# Rows, in order: context(9/9), -old ten(10/-), +new ten(-/10),
# +new eleven(-/11), +new twelve(-/12), context after(11/13).
HUNK = (
    "@@ -9,4 +9,5 @@\n"
    " context nine\n"
    "-old ten\n"
    "+new ten\n"
    "+new eleven\n"
    "+new twelve\n"
    " context after"
)

COMMENT = {
    "id": 1,
    "path": "scripts/vet.sh",
    "line": 12,
    "start_line": 11,
    "side": "RIGHT",
    "diff_hunk": HUNK,
    "user": {"login": "vzakharov"},
    "created_at": "2026-09-14T21:16:32Z",
    "body": "why not just make the whole thing one function?",
}


def long_hunk(rows: int = 40) -> str:
    """A hunk long enough that the run-up window leaves something to elide."""
    body = "\n".join(f"+line {n}" for n in range(1, rows + 1))
    return f"@@ -1,1 +1,{rows} @@\n{body}"


class TrimHunk(unittest.TestCase):
    def test_the_selection_survives_byte_for_byte(self) -> None:
        """The property the whole change turns on: what the reviewer highlighted
        is quoted whole and unshortened."""
        trimmed = trim_hunk(HUNK, 11, 12)
        self.assertIn("+new eleven\n+new twelve", trimmed)

    def test_a_single_line_selection_is_the_commented_line_alone(self) -> None:
        trimmed = trim_hunk(long_hunk(), None, 40).split("\n")
        self.assertEqual(trimmed[-1], "+line 40")
        self.assertEqual(trimmed[-4:-1], ["+line 37", "+line 38", "+line 39"])

    def test_lines_before_the_run_up_are_elided_with_a_count(self) -> None:
        trimmed = trim_hunk(long_hunk(), 39, 40).split("\n")
        self.assertEqual(trimmed[0], "@@ -1,1 +1,40 @@")
        self.assertEqual(trimmed[1], "… 35 lines elided …")
        self.assertEqual(
            trimmed[2:],
            ["+line 36", "+line 37", "+line 38", "+line 39", "+line 40"],
        )

    def test_one_elided_line_is_singular(self) -> None:
        self.assertIn("… 1 line elided …", trim_hunk(long_hunk(5), 5, 5))

    def test_a_hunk_shorter_than_the_run_up_window_elides_nothing(self) -> None:
        trimmed = trim_hunk(long_hunk(3), 3, 3)
        self.assertNotIn("elided", trimmed)
        self.assertEqual(trimmed, "@@ -1,1 +1,3 @@\n+line 1\n+line 2\n+line 3")

    def test_lines_after_the_selection_are_elided_too(self) -> None:
        self.assertIn("… 3 lines elided …", trim_hunk(HUNK, 10, 10))

    def test_an_overlong_run_up_line_is_capped_but_the_selection_is_not(self) -> None:
        wide = "x" * (CONTEXT_LINE_CHARS + 50)
        hunk = f"@@ -1,1 +1,2 @@\n+{wide}\n+{wide}"
        trimmed = trim_hunk(hunk, 2, 2).split("\n")
        self.assertEqual(trimmed[1], "+" + "x" * (CONTEXT_LINE_CHARS - 1) + "…")
        self.assertEqual(trimmed[2], "+" + wide)

    def test_a_left_side_selection_reads_the_old_numbering(self) -> None:
        self.assertIn("-old ten", trim_hunk(HUNK, 10, 10, side="LEFT"))

    def test_an_unresolvable_line_falls_back_to_the_hunk_tail(self) -> None:
        """A mixed-side or malformed selection shows more than asked, never
        less."""
        self.assertTrue(trim_hunk(HUNK, None, 999).endswith(" context after"))

    def test_a_file_level_comment_has_no_hunk_to_trim(self) -> None:
        self.assertEqual(trim_hunk("", None, None), "")


class SelectionOf(unittest.TestCase):
    def test_a_live_comment_reads_the_line_fields(self) -> None:
        self.assertEqual(selection_of(COMMENT), (11, 12, "RIGHT"))

    def test_an_outdated_comment_reads_the_original_fields(self) -> None:
        outdated = {
            **COMMENT,
            "line": None,
            "start_line": None,
            "original_start_line": 4,
            "original_line": 6,
        }
        self.assertEqual(selection_of(outdated), (4, 6, "RIGHT"))

    def test_a_live_line_never_pairs_with_a_stale_start(self) -> None:
        stale = {**COMMENT, "original_start_line": 999, "original_line": 999}
        self.assertEqual(selection_of(stale), (11, 12, "RIGHT"))

    def test_a_file_level_comment_has_no_line_at_all(self) -> None:
        file_level = {"path": "README.md", "subject_type": "file"}
        self.assertEqual(selection_of(file_level), (None, None, "RIGHT"))


class ThreadIndex(unittest.TestCase):
    def test_a_row_carries_the_fields_the_tail_test_selects_on(self) -> None:
        self.assertEqual(
            thread_summary([COMMENT], "T01", {1: False}),
            "- **T01** `scripts/vet.sh`:12 — unresolved"
            " — last: @vzakharov (human) 2026-09-14T21:16:32Z"
            ' — "why not just make the whole thing one function?"',
        )

    def test_a_file_level_comment_indexes_without_a_line(self) -> None:
        file_level = {**COMMENT, "line": None, "path": "README.md"}
        self.assertIn("`README.md` — ", thread_summary([file_level], "T01", {1: True}))

    def test_the_tail_is_the_newest_post_not_the_root(self) -> None:
        reply = {
            **COMMENT,
            "id": 2,
            "created_at": "2026-09-14T22:00:00Z",
            "body": "done",
            "user": {"login": "claude"},
        }
        self.assertIn(
            'last: @claude (human) 2026-09-14T22:00:00Z — "done"',
            thread_summary([COMMENT, reply], "T01", {1: False}),
        )

    def test_a_row_renders_end_to_end_and_links_to_the_body(self) -> None:
        heading, items = review_parts([], [COMMENT], {}, {1: False})
        main = "\n".join(["# PR", heading, indexed_section(items)])
        self.assertIn(
            "- **T01** `scripts/vet.sh`:12 — unresolved"
            " — last: @vzakharov (human) 2026-09-14T21:16:32Z"
            ' — "why not just make the whole thing one function?"'
            " → [↓](#t01)",
            main,
        )
        self.assertIn('<a id="t01"></a>', main)
        self.assertIn("+new twelve", main)


class IndexedSection(unittest.TestCase):
    def test_every_body_follows_the_rows_in_order(self) -> None:
        items = [
            Indexed(anchor=f"x{n:02d}", summary=f"- **x{n:02d}**", body=f"body {n}")
            for n in (1, 2)
        ]
        self.assertEqual(
            indexed_section(items).split("\n"),
            ["- **x01** → [↓](#x01)", "- **x02** → [↓](#x02)", "", "body 1", "body 2"],
        )

    def test_a_conversation_comment_indexes_and_renders_in_one_file(self) -> None:
        _, items = comments_parts(
            [{**COMMENT, "html_url": "https://example.test/1"}], {}
        )
        section = indexed_section(items)
        self.assertIn(
            "- **C01** @vzakharov (human) — 2026-09-14T21:16:32Z", section
        )
        self.assertIn("→ [↓](#c01)", section)
        self.assertIn('<a id="c01"></a>', section)
        self.assertIn("why not just make the whole thing one function?", section)


if __name__ == "__main__":
    unittest.main()
