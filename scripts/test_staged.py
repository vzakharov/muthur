#!/usr/bin/env python3
"""Tests for `scripts/staged.sh`, each against a throwaway git repository
carrying a copy of the script.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "staged.sh"
DIR = "docs/staged"


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        (root / "scripts").mkdir()
        shutil.copy2(SCRIPT, root / "scripts" / "staged.sh")
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, capture_output=True, text=True
        ).stdout

    def write(self, path: str, text: str) -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text)

    def read(self, path: str) -> str:
        return (self.root / path).read_text()

    def exists(self, path: str) -> bool:
        return (self.root / path).exists()

    def commit(self, message: str = "commit") -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def staged(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "scripts/staged.sh", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
        )


ORIGINAL = "one\ntwo\nthree\nfour\nfive\n"
SKILL = ".claude/skills/go/SKILL.md"


class StagedTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(Path(self.tmp.name))
        self.repo.write("CLAUDE.md", ORIGINAL)
        self.repo.write(SKILL, "skill\n")
        self.repo.commit("base")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def stage(self, *paths: str) -> None:
        result = self.repo.staged("stage", *paths)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.repo.commit("stage")


class Stage(StagedTestCase):
    def test_the_copy_is_byte_identical_at_the_mirrored_path(self) -> None:
        self.stage("CLAUDE.md", SKILL)
        self.assertEqual(self.repo.read(f"{DIR}/CLAUDE.md"), ORIGINAL)
        self.assertEqual(self.repo.read(f"{DIR}/{SKILL}"), "skill\n")

    def test_staging_twice_is_refused(self) -> None:
        self.stage("CLAUDE.md")
        result = self.repo.staged("stage", "CLAUDE.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already staged", result.stderr)

    def test_an_untracked_file_is_refused(self) -> None:
        self.repo.write("new.md", "new\n")
        result = self.repo.staged("stage", "new.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not tracked", result.stderr)
        self.assertFalse(self.repo.exists(f"{DIR}/new.md"))

    def test_a_missing_file_is_refused(self) -> None:
        result = self.repo.staged("stage", "nope.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no such file", result.stderr)


class Swap(StagedTestCase):
    def test_an_edited_copy_replaces_the_unmoved_real_file(self) -> None:
        self.stage("CLAUDE.md", SKILL)
        self.repo.write(f"{DIR}/CLAUDE.md", "edited\n")
        self.repo.commit("edit")
        result = self.repo.staged("swap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.repo.read("CLAUDE.md"), "edited\n")
        self.assertEqual(self.repo.read(SKILL), "skill\n")
        self.assertFalse(self.repo.exists(DIR))
        self.assertEqual(self.repo.git("diff", "--name-only"), "")
        self.assertEqual(
            sorted(self.repo.git("diff", "--cached", "--name-only").split()),
            sorted(["CLAUDE.md", f"{DIR}/CLAUDE.md", f"{DIR}/{SKILL}"]),
        )

    def test_a_copy_edited_in_its_staging_commit_still_swaps_cleanly(self) -> None:
        self.repo.staged("stage", "CLAUDE.md")
        self.repo.write(f"{DIR}/CLAUDE.md", "edited\n")
        self.repo.commit("stage and edit")
        result = self.repo.staged("swap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.repo.read("CLAUDE.md"), "edited\n")

    def test_an_uncommitted_copy_swaps_against_head(self) -> None:
        self.repo.staged("stage", "CLAUDE.md")
        self.repo.write(f"{DIR}/CLAUDE.md", "edited\n")
        result = self.repo.staged("swap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.repo.read("CLAUDE.md"), "edited\n")

    def test_an_edit_the_real_file_got_since_staging_survives(self) -> None:
        self.stage("CLAUDE.md")
        self.repo.write(f"{DIR}/CLAUDE.md", ORIGINAL.replace("one", "ONE"))
        self.repo.write("CLAUDE.md", ORIGINAL.replace("five", "FIVE"))
        self.repo.commit("both sides")
        result = self.repo.staged("swap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.repo.read("CLAUDE.md"), ORIGINAL.replace("one", "ONE").replace("five", "FIVE")
        )

    def test_overlapping_edits_leave_markers_and_fail(self) -> None:
        self.stage("CLAUDE.md")
        self.repo.write(f"{DIR}/CLAUDE.md", ORIGINAL.replace("three", "staged"))
        self.repo.write("CLAUDE.md", ORIGINAL.replace("three", "real"))
        self.repo.commit("conflict")
        result = self.repo.staged("swap")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflicts left in CLAUDE.md", result.stderr)
        text = self.repo.read("CLAUDE.md")
        self.assertIn("<<<<<<< CLAUDE.md (staged)", text)
        self.assertIn("real", text)
        self.assertFalse(self.repo.exists(f"{DIR}/CLAUDE.md"))

    def test_a_restage_after_an_early_swap_merges_against_the_new_copy(self) -> None:
        self.stage("CLAUDE.md")
        self.repo.write(f"{DIR}/CLAUDE.md", "first\n")
        self.repo.commit("edit")
        self.repo.staged("swap")
        self.repo.commit("early swap")
        self.stage("CLAUDE.md")
        self.repo.write(f"{DIR}/CLAUDE.md", "second\n")
        self.repo.commit("edit again")
        result = self.repo.staged("swap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.repo.read("CLAUDE.md"), "second\n")

    def test_nothing_staged_is_a_no_op(self) -> None:
        result = self.repo.staged("swap")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.repo.read("CLAUDE.md"), ORIGINAL)


class Check(StagedTestCase):
    def test_nothing_staged_passes_silently(self) -> None:
        result = self.repo.staged("check")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_a_staged_copy_passes(self) -> None:
        self.stage("CLAUDE.md")
        result = self.repo.staged("check")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_fails_while_anything_is_staged(self) -> None:
        self.stage("CLAUDE.md")
        result = self.repo.staged("check", "--empty")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("still staged", result.stderr)

    def test_a_copy_of_nothing_fails(self) -> None:
        self.repo.write(f"{DIR}/.claude/rules/gone.md", "stray\n")
        result = self.repo.staged("check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stands for .claude/rules/gone.md, which is not a tracked file", result.stderr)

    def test_a_moved_target_is_a_note_not_a_failure(self) -> None:
        self.stage("CLAUDE.md")
        self.repo.write("CLAUDE.md", "moved\n")
        result = self.repo.staged("check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("changed since it was staged", result.stderr)


class Resolve(StagedTestCase):
    def test_a_staged_path_resolves_to_its_copy(self) -> None:
        self.stage("CLAUDE.md")
        result = self.repo.staged("resolve", "CLAUDE.md")
        self.assertEqual(result.stdout, f"{DIR}/CLAUDE.md\n")

    def test_an_unnormalized_spelling_of_a_staged_path_resolves(self) -> None:
        self.stage("CLAUDE.md")
        result = self.repo.staged("resolve", ".claude/skills/../../CLAUDE.md")
        self.assertEqual(result.stdout, f"{DIR}/CLAUDE.md\n")

    def test_an_unstaged_path_resolves_to_itself(self) -> None:
        self.stage("CLAUDE.md")
        result = self.repo.staged("resolve", SKILL)
        self.assertEqual(result.stdout, f"{SKILL}\n")


class List(StagedTestCase):
    def test_each_staged_file_is_listed_with_its_copy(self) -> None:
        self.stage("CLAUDE.md", SKILL)
        result = self.repo.staged("list")
        self.assertEqual(
            result.stdout, f"{SKILL}\t{DIR}/{SKILL}\nCLAUDE.md\t{DIR}/CLAUDE.md\n"
        )

    def test_nothing_staged_lists_nothing(self) -> None:
        result = self.repo.staged("list")
        self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
