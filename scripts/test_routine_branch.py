#!/usr/bin/env python3
"""Tests for `scripts/routine-branch.sh`, each against a throwaway clone of a
throwaway origin, with `gh` replaced on PATH by a stub that answers from a
fixture.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
DEFAULT = "trunk"
SESSION = "claude/lucid-hamilton-MigdG"

# The stub serves the repo lookups and `pr list` from FAKE_GH's fixture,
# performs `pr checkout` as a fetch and switch to the PR's head, and fails any
# call whose arguments contain a string the fixture lists under "fail".
GH_STUB = f"""#!{sys.executable}
import json, os, subprocess, sys
args = sys.argv[1:]
if args[:1] == ["-R"]:
    args = args[2:]
fixture = json.load(open(os.environ["FAKE_GH"]))
if any(f in " ".join(args) for f in fixture.get("fail", [])):
    sys.exit("gh: stubbed failure")
if args[:2] == ["repo", "view"]:
    print(fixture["default"] if "defaultBranchRef" in args else "owner/repo")
elif args[:2] == ["pr", "list"]:
    print(json.dumps(fixture["prs"]))
elif args[:2] == ["pr", "checkout"]:
    head = fixture["heads"][args[2]]
    subprocess.run(["git", "fetch", "-q", "origin", head], check=True)
    subprocess.run(["git", "switch", "-q", head], check=True)
else:
    sys.exit("gh stub: unexpected call " + " ".join(sys.argv[1:]))
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def pr(number: int, *paths: str, draft: bool = True) -> dict:
    return {"number": number, "isDraft": draft, "files": [{"path": p} for p in paths]}


class RoutineBranchTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        origin, self.clone, bin_dir = tmp / "origin.git", tmp / "clone", tmp / "bin"
        git(tmp, "init", "-q", "--bare", f"--initial-branch={DEFAULT}", str(origin))
        git(tmp, "clone", "-q", str(origin), str(self.clone))
        git(self.clone, "config", "user.email", "test@example.com")
        git(self.clone, "config", "user.name", "Test")
        (self.clone / "scripts" / "lib").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "routine-branch.sh", self.clone / "scripts")
        shutil.copy2(SCRIPTS / "lib" / "gh-repo.sh", self.clone / "scripts" / "lib")
        git(self.clone, "add", "-A")
        git(self.clone, "commit", "-q", "-m", "base")
        git(self.clone, "push", "-q", "origin", DEFAULT)
        self.base = git(self.clone, "rev-parse", "HEAD")
        git(self.clone, "switch", "-q", "-c", SESSION)

        bin_dir.mkdir()
        (bin_dir / "gh").write_text(GH_STUB)
        (bin_dir / "gh").chmod(0o755)
        self.fixture_path = tmp / "fixture.json"
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH": str(self.fixture_path),
        }
        self.fixture(prs=[])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def fixture(self, **fields: object) -> None:
        self.fixture_path.write_text(
            json.dumps({"default": DEFAULT, "heads": {}, **fields})
        )

    def push_head(self, number: int, branch: str) -> None:
        git(self.clone, "push", "-q", "origin", f"{self.base}:refs/heads/{branch}")
        fixture = json.loads(self.fixture_path.read_text())
        fixture["heads"][str(number)] = branch
        self.fixture_path.write_text(json.dumps(fixture))

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "scripts/routine-branch.sh", *args],
            cwd=self.clone,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def branch(self) -> str:
        return git(self.clone, "branch", "--show-current")


class NoDraft(RoutineBranchTestCase):
    def test_a_branch_is_cut_from_the_default_branch_keeping_the_session_tail(self) -> None:
        result = self.run_script("basilisk", "cases/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.branch(), "claude/basilisk-MigdG")
        self.assertEqual(git(self.clone, "rev-parse", "HEAD"), self.base)
        self.assertIn(f"created claude/basilisk-MigdG from origin/{DEFAULT}", result.stdout)

    def test_the_new_branch_tracks_nothing(self) -> None:
        self.run_script("basilisk", "cases/")
        upstream = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
            cwd=self.clone,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(upstream.returncode, 0)

    def test_a_session_branch_without_a_tail_gets_six_fresh_characters(self) -> None:
        git(self.clone, "switch", "-q", DEFAULT)
        result = self.run_script("basilisk", "cases/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(self.branch(), r"^claude/basilisk-[a-z0-9]{6}$")

    def test_a_ready_pr_on_the_paths_is_not_taken(self) -> None:
        self.fixture(prs=[pr(7, "cases/one.md", draft=False)])
        self.run_script("basilisk", "cases/")
        self.assertEqual(self.branch(), "claude/basilisk-MigdG")

    def test_a_draft_on_other_paths_is_not_taken(self) -> None:
        self.fixture(prs=[pr(7, "src/app.ts")])
        self.run_script("basilisk", "cases/")
        self.assertEqual(self.branch(), "claude/basilisk-MigdG")


class Drafts(RoutineBranchTestCase):
    def test_the_one_draft_is_checked_out(self) -> None:
        self.fixture(prs=[pr(12, "cases/one.md")])
        self.push_head(12, "claude/basilisk-abc123")
        result = self.run_script("basilisk", "cases/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.branch(), "claude/basilisk-abc123")
        self.assertIn("on draft #12", result.stdout)
        self.assertNotIn("other drafts", result.stdout)

    def test_any_given_path_recognises_the_draft(self) -> None:
        self.fixture(prs=[pr(12, "src/app.ts", "CASES.md")])
        self.push_head(12, "claude/basilisk-abc123")
        result = self.run_script("basilisk", "cases/", "CASES.md")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.branch(), "claude/basilisk-abc123")

    def test_of_several_the_oldest_is_taken_and_the_rest_named(self) -> None:
        self.fixture(prs=[pr(30, "cases/c.md"), pr(12, "cases/a.md"), pr(21, "cases/b.md")])
        self.push_head(12, "claude/basilisk-abc123")
        result = self.run_script("basilisk", "cases/")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.branch(), "claude/basilisk-abc123")
        self.assertIn("other drafts, not taken: #21, #30", result.stdout)


class Failures(RoutineBranchTestCase):
    def test_a_failed_pr_lookup_fails_the_run_on_the_session_branch(self) -> None:
        self.fixture(prs=[], fail=["pr list"])
        result = self.run_script("basilisk", "cases/")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stubbed failure", result.stderr)
        self.assertEqual(self.branch(), SESSION)

    def test_a_failed_default_branch_lookup_fails_the_run(self) -> None:
        self.fixture(prs=[], fail=["defaultBranchRef"])
        result = self.run_script("basilisk", "cases/")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stubbed failure", result.stderr)
        self.assertEqual(self.branch(), SESSION)

    def test_a_missing_path_is_a_usage_error(self) -> None:
        result = self.run_script("basilisk")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(re.search(r"usage: .*<branch-prefix> <path>", result.stderr))


if __name__ == "__main__":
    unittest.main()
