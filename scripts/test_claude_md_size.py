#!/usr/bin/env python3
"""Tests for `scripts/check-claude-md-size.sh`, each against a throwaway git
repository carrying a copy of it, with `origin/main` pointed at its base commit.

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

CHECK = Path(__file__).resolve().parent / "check-claude-md-size.sh"


def constant(name: str) -> int:
    return int(re.search(rf"^{name}=(\d+)$", CHECK.read_text(), re.M).group(1))


CEILING = constant("CEILING_CHARS")
TARGET = constant("TARGET_CHARS")
STAGED_COPY = ".claude/staged/CLAUDE.md.staged"


class CheckClaudeMdSize(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir()
        shutil.copy2(CHECK, self.root / "scripts" / CHECK.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, capture_output=True, text=True
        ).stdout.strip()

    def write(self, path: str, chars: int, char: str = "a") -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(char * chars, encoding="utf-8")

    def remove(self, path: str) -> None:
        (self.root / path).unlink()

    def commit(self, message: str = "commit") -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)

    def base(self, chars: int) -> None:
        """Commit a CLAUDE.md of `chars` and point `origin/main` at it."""
        self.write("CLAUDE.md", chars)
        self.commit("base")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["sh", f"scripts/{CHECK.name}"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def assertPasses(self) -> subprocess.CompletedProcess[str]:
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def assertFails(self) -> subprocess.CompletedProcess[str]:
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout)
        return result

    def test_growth_up_to_the_ceiling_passes(self) -> None:
        self.base(TARGET - 100)
        self.write("CLAUDE.md", CEILING)
        self.commit()
        self.assertPasses()

    def test_a_file_over_the_ceiling_fails_and_names_the_target(self) -> None:
        self.base(TARGET)
        self.write("CLAUDE.md", CEILING + 1)
        self.commit()
        result = self.assertFails()
        self.assertIn(f"lands at {TARGET} or under", result.stderr)
        self.assertIn("subagent", result.stderr)

    def test_an_uncommitted_file_over_the_ceiling_fails(self) -> None:
        self.base(TARGET)
        self.write("CLAUDE.md", CEILING + 1)
        self.assertIn("the worktree", self.assertFails().stderr)

    def test_trimming_back_under_the_ceiling_alone_still_fails(self) -> None:
        self.base(TARGET)
        self.write("CLAUDE.md", CEILING + 1)
        self.commit("grow")
        crossed = self.git("rev-parse", "--short", "HEAD")
        self.write("CLAUDE.md", CEILING - 1)
        self.commit("trim a little")
        result = self.assertFails()
        self.assertIn(crossed, result.stderr)
        self.assertIn(f"cut {CEILING - 1 - TARGET} more", result.stderr)

    def test_trimming_to_the_target_passes(self) -> None:
        self.base(TARGET)
        self.write("CLAUDE.md", CEILING + 1)
        self.commit("grow")
        self.write("CLAUDE.md", TARGET)
        self.commit("trim")
        self.assertIn("back under", self.assertPasses().stdout)

    def test_a_crossing_on_the_base_is_not_this_branchs(self) -> None:
        self.base(TARGET)
        self.write("CLAUDE.md", CEILING + 1)
        self.commit("someone else's crossing")
        self.write("CLAUDE.md", CEILING - 1)
        self.commit("someone else's partial trim")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.commit("this branch")
        self.assertPasses()

    def test_a_base_already_over_counts_as_crossed(self) -> None:
        self.base(CEILING + 1)
        self.commit("this branch, not touching CLAUDE.md")
        self.assertFails()

    def test_a_staged_copy_over_the_ceiling_fails_though_the_real_file_fits(
        self,
    ) -> None:
        self.base(TARGET)
        self.write(STAGED_COPY, CEILING + 1)
        self.commit("stage and grow")
        self.assertIn(STAGED_COPY, self.assertFails().stderr)

    def test_a_staged_trim_passes_though_the_real_file_is_over(self) -> None:
        self.base(CEILING + 1)
        self.write(STAGED_COPY, CEILING + 1)
        self.commit("stage")
        self.write(STAGED_COPY, TARGET)
        self.commit("trim the copy")
        self.assertIn(STAGED_COPY, self.assertPasses().stdout)

    def test_the_swap_commit_measures_the_real_file_again(self) -> None:
        self.base(TARGET)
        self.write(STAGED_COPY, TARGET + 10)
        self.commit("stage and edit")
        self.remove(STAGED_COPY)
        self.write("CLAUDE.md", TARGET + 10)
        self.commit("swap")
        self.assertIn("CLAUDE.md is", self.assertPasses().stdout)

    def test_multibyte_characters_count_once(self) -> None:
        self.base(TARGET)
        self.write("CLAUDE.md", CEILING, char="я")
        self.commit()
        self.assertPasses()

    def test_with_no_base_only_the_ceiling_is_checked(self) -> None:
        self.write("CLAUDE.md", CEILING)
        self.commit()
        self.assertIn("ceiling only", self.assertPasses().stdout)
        self.write("CLAUDE.md", CEILING + 1)
        self.assertFails()

    def test_no_claude_md_passes(self) -> None:
        self.assertIn("skipped", self.assertPasses().stdout)


if __name__ == "__main__":
    unittest.main()
