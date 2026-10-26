#!/usr/bin/env python3
"""Tests for `scripts/check-divergence.sh`, each against a throwaway directory
carrying a copy of it.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

CHECK = Path(__file__).resolve().parent / "check-divergence.sh"
WATERMARK = ".claude/skills/update-muthur/watermark.json"
RECORD = ".claude/skills/update-muthur/divergence.md"
POSITION = {
    "repo": "vzakharov/muthur",
    "lastSyncedSha": "0" * 40,
    "lastSyncedAt": "2026-10-26",
    "lineage": [],
}


class CheckDivergence(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        shutil.copy2(CHECK, self.root / "scripts" / CHECK.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, path: str, text: str) -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text, encoding="utf-8")

    def watermark(self, **extra: object) -> None:
        self.write(WATERMARK, json.dumps({**POSITION, **extra}, ensure_ascii=False, indent=2))

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", f"scripts/{CHECK.name}"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_the_position_alone_passes(self) -> None:
        self.watermark()
        self.assertEqual(self.check().returncode, 0)

    def test_no_watermark_and_no_record_passes(self) -> None:
        self.assertEqual(self.check().returncode, 0)

    def test_adopted_fails_naming_the_record(self) -> None:
        self.watermark(adopted=[".claude/"])
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn(RECORD, result.stderr)

    def test_declined_fails(self) -> None:
        self.watermark(declined={"docs/": "not taken"})
        self.assertEqual(self.check().returncode, 1)

    def test_the_words_inside_a_value_pass(self) -> None:
        self.watermark(note='nothing here is "adopted": or "declined": as a key')
        self.assertEqual(self.check().returncode, 0)

    def test_a_record_at_the_cap_passes(self) -> None:
        self.watermark()
        self.write(RECORD, "line\n" * 450)
        self.assertEqual(self.check().returncode, 0)

    def test_a_record_past_the_cap_fails(self) -> None:
        self.watermark()
        self.write(RECORD, "line\n" * 451)
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("451 lines", result.stderr)

    def test_long_lines_count_as_wrapped(self) -> None:
        self.watermark()
        self.write(RECORD, ("x" * 161 + "\n") * 151)
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("453 lines", result.stderr)

    def test_width_is_counted_in_characters(self) -> None:
        self.watermark()
        self.write(RECORD, ("я" * 80 + "\n") * 450)
        self.assertEqual(self.check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
