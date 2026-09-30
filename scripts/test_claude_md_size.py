#!/usr/bin/env python3
"""Tests for `scripts/check-claude-md-size.sh`, each against a throwaway tree
carrying copies of it and of `scripts/staged.sh`.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
CHECK = SCRIPTS / "check-claude-md-size.sh"
MAX_CHARS = int(re.search(r"^MAX_CHARS=(\d+)$", CHECK.read_text(), re.M).group(1))
STAGED_COPY = ".claude/staged/CLAUDE.md.staged"


class CheckClaudeMdSize(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        for name in ("check-claude-md-size.sh", "staged.sh"):
            shutil.copy2(SCRIPTS / name, self.root / "scripts" / name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, path: str, chars: int, char: str = "a") -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(char * chars, encoding="utf-8")

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", "scripts/check-claude-md-size.sh"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_a_file_at_the_cap_passes(self) -> None:
        self.write("CLAUDE.md", MAX_CHARS)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_file_over_the_cap_fails_and_says_by_how_much(self) -> None:
        self.write("CLAUDE.md", MAX_CHARS + 7)
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("over the", result.stderr)
        self.assertIn("by 7", result.stderr)

    def test_multibyte_characters_count_once(self) -> None:
        self.write("CLAUDE.md", MAX_CHARS, char="я")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_staged_copy_over_the_cap_fails_though_the_real_file_fits(self) -> None:
        self.write("CLAUDE.md", 10)
        self.write(STAGED_COPY, MAX_CHARS + 1)
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn(STAGED_COPY, result.stderr)

    def test_a_staged_trim_passes_though_the_real_file_is_over(self) -> None:
        self.write("CLAUDE.md", MAX_CHARS + 1)
        self.write(STAGED_COPY, 10)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(STAGED_COPY, result.stdout)

    def test_no_claude_md_passes(self) -> None:
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("skipped", result.stdout)


if __name__ == "__main__":
    unittest.main()
