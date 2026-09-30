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

    def write(self, path: str, chars: int, char: str = "a", head: str = "") -> None:
        """Write `chars` characters to `path`: `head`, padded out with `char`."""
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        text = head + char * (chars - len(head))
        (self.root / path).write_text(text, encoding="utf-8")

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
        self.assertIn(f"(CLAUDE.md {TARGET + 10})", self.assertPasses().stdout)

    def test_an_import_counts_toward_the_total(self) -> None:
        self.base(100)
        self.write("CLAUDE.md", TARGET, head="See @docs/moved.md for more.\n")
        self.write("docs/moved.md", CEILING - TARGET + 1)
        self.commit("move text into an import")
        self.assertIn("docs/moved.md", self.assertFails().stderr)

    def test_imports_are_followed_transitively_from_each_files_directory(
        self,
    ) -> None:
        self.base(100)
        self.write("CLAUDE.md", 100, head="@docs/a.md\n")
        self.write("docs/a.md", 100, head="@sub/b.md\n")
        self.write("docs/sub/b.md", CEILING)
        self.commit()
        self.assertIn("docs/sub/b.md", self.assertFails().stderr)

    def test_a_cited_path_is_not_an_import(self) -> None:
        self.base(100)
        self.write(
            "CLAUDE.md",
            TARGET,
            head="Cited as `@docs/big.md`, or mailed to me@docs/big.md\n"
            "```\n@docs/big.md\n```\n",
        )
        self.write("docs/big.md", CEILING)
        self.commit()
        self.assertNotIn("docs/big.md", self.assertPasses().stdout)

    def test_an_imports_staged_copy_is_what_counts(self) -> None:
        self.base(100)
        self.write("CLAUDE.md", 100, head="@docs/a.md\n")
        self.write("docs/a.md", 100)
        self.write(".claude/staged/docs/a.md.staged", CEILING)
        self.commit("stage and grow the import")
        self.assertIn(".claude/staged/docs/a.md.staged", self.assertFails().stderr)

    def test_imports_past_the_hop_limit_are_not_followed(self) -> None:
        hops = constant("MAX_IMPORT_HOPS")
        self.base(100)
        self.write("CLAUDE.md", 100, head="@f1.md\n")
        for n in range(1, hops + 1):
            self.write(f"f{n}.md", 100, head=f"@f{n + 1}.md\n")
        self.write(f"f{hops + 1}.md", CEILING)
        self.commit()
        stdout = self.assertPasses().stdout
        self.assertIn(f"f{hops}.md", stdout)
        self.assertNotIn(f"f{hops + 1}.md", stdout)

    def test_an_import_cycle_is_counted_once(self) -> None:
        self.base(100)
        self.write("CLAUDE.md", 100, head="@a.md\n")
        self.write("a.md", 100, head="@CLAUDE.md\n")
        self.commit()
        self.assertIn("are 200/", self.assertPasses().stdout)

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
