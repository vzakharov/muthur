#!/usr/bin/env python3
"""Tests for `scripts/check-markdown-tables.sh`, each against a throwaway git
repository carrying a copy of it.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

CHECK = Path(__file__).resolve().parent / "check-markdown-tables.sh"

TABLE = "| A | B |\n| --- | :-: |\n| 1 | 2 |\n"


class CheckMarkdownTables(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        shutil.copy2(CHECK, self.root / "scripts" / CHECK.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def track(self, path: str, text: str) -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text, encoding="utf-8")
        subprocess.run(["git", "add", path], cwd=self.root, check=True)

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", f"scripts/{CHECK.name}"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_table_outside_a_fence_fails_naming_its_line(self) -> None:
        self.track(".claude/rules/notes.md", "# Notes\n\n" + TABLE)
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn(".claude/rules/notes.md:4", result.stderr)

    def test_a_one_column_table_fails(self) -> None:
        self.track(".claude/a.md", "| A |\n|---|\n| 1 |\n")
        self.assertEqual(self.check().returncode, 1)

    def test_table_inside_a_fence_passes(self) -> None:
        self.track(".claude/a.md", "```markdown\n" + TABLE + "```\n")
        self.track("CLAUDE.md", "~~~\n" + TABLE + "~~~\n")
        self.assertEqual(self.check().returncode, 0)

    def test_a_shorter_run_inside_a_fence_does_not_close_it(self) -> None:
        self.track(".claude/a.md", "````\n```\n" + TABLE + "````\n")
        self.assertEqual(self.check().returncode, 0)

    def test_table_after_a_closed_fence_fails(self) -> None:
        self.track(".claude/a.md", "```\ncode\n```\n\n" + TABLE)
        self.assertEqual(self.check().returncode, 1)

    def test_a_dash_rule_and_a_list_pass(self) -> None:
        self.track(".claude/a.md", "Text\n\n---\n\n- **A** — 1\n- **B** — 2\n")
        self.assertEqual(self.check().returncode, 0)

    def test_a_nested_claude_md_is_checked(self) -> None:
        self.track("src/db/CLAUDE.md", TABLE)
        self.assertEqual(self.check().returncode, 1)

    def test_markdown_read_rendered_is_skipped(self) -> None:
        for path in ("README.md", "docs/guide.md", "docs/issue/1/issue.md"):
            self.track(path, TABLE)
        self.assertEqual(self.check().returncode, 0)

    def test_an_untracked_file_is_not_read(self) -> None:
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "scratch.md").write_text(TABLE, encoding="utf-8")
        self.assertEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
