#!/usr/bin/env python3
"""Runs `scripts/working-dir.sh` in a scratch repository and reads what it
prints. What it protects is that each branch gets a folder of its own, that the
`claude/` prefix is the only part dropped, and that `MUTHUR_ELEPHANT_BITE_PRS=off`
keeps the shared folder.

Run by path (`python3 scripts/test_working_dir.py`), as
`scripts/check-muthur.sh` does.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Optional

SCRIPT = Path(__file__).resolve().parent / "working-dir.sh"
SWITCH = "MUTHUR_ELEPHANT_BITE_PRS"
ROOT = "docs/remove-before-merging"


class WorkingDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.git("init", "-q", "-b", "claude/elephant")
        self.git("commit", "-q", "--allow-empty", "-m", "root")

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

    def run_script(
        self, *args: str, switch: Optional[str] = None
    ) -> subprocess.CompletedProcess[str]:
        env = {k: v for k, v in os.environ.items() if k != SWITCH}
        if switch is not None:
            env[SWITCH] = switch
        return subprocess.run(
            [str(SCRIPT), *args],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def path(self, *args: str, switch: Optional[str] = None) -> str:
        result = self.run_script(*args, switch=switch)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_names_the_current_branch_less_its_claude_prefix(self) -> None:
        self.assertEqual(self.path(), f"{ROOT}/elephant")

    def test_a_bite_gets_a_folder_apart_from_its_elephant(self) -> None:
        self.git("checkout", "-q", "-b", "claude/elephant-bite-02")
        self.assertEqual(self.path(), f"{ROOT}/elephant-bite-02")

    def test_keeps_a_branch_with_no_claude_prefix_whole(self) -> None:
        self.assertEqual(self.path("masd/sites-by-domain"), f"{ROOT}/masd/sites-by-domain")

    def test_strips_only_a_leading_claude_prefix(self) -> None:
        self.assertEqual(self.path("feature/claude/x"), f"{ROOT}/feature/claude/x")

    def test_off_keeps_the_shared_folder(self) -> None:
        self.assertEqual(self.path(switch="off"), ROOT)
        self.assertEqual(self.path("claude/other", switch="off"), ROOT)

    def test_any_other_value_leaves_it_on(self) -> None:
        self.assertEqual(self.path(switch="on"), f"{ROOT}/elephant")

    def test_a_detached_head_with_no_branch_named_fails(self) -> None:
        self.git("checkout", "-q", "--detach")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("detached HEAD", result.stderr)
        self.assertEqual(self.path("claude/elephant"), f"{ROOT}/elephant")


if __name__ == "__main__":
    unittest.main()
