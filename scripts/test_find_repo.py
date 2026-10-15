#!/usr/bin/env python3
"""Tests for `scripts/find-repo.py`, run against a fixture session root of
clones with local bare remotes.

Each clone's `origin` is a `https://github.com/acme/<name>.git` URL redirected
to its bare repo through `url.<file>.insteadOf` in `GIT_CONFIG_*`, so URL
matching and `git ls-remote` both see what a cloud session's clones show. A fake
`gh` on `PATH` answers `#N` lookups.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "find-repo.py"
MUTHUR = SCRIPT.parent.parent

# Answers `gh api repos/<owner>/<repo>/issues/<n> --silent` from $FAKE_GH_FOUND,
# a space-separated list of `<owner>/<repo>/<n>` that exist.
FAKE_GH = """#!/bin/sh
path=$(echo "$2" | sed 's|^repos/||; s|/issues/|/|')
case " $FAKE_GH_FOUND " in
*" $path "*) exit 0 ;;
esac
if [ -n "$FAKE_GH_BROKEN" ]; then echo "connection refused" >&2; exit 1; fi
echo "gh: Not Found (HTTP 404)" >&2
exit 1
"""


class Fixture:
    def __init__(self, base: Path, names: list[str]) -> None:
        self.root = base / "session"
        self.root.mkdir()
        bin_dir = base / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(FAKE_GH)
        (bin_dir / "gh").chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "CLAUDE_CODE_REMOTE": "true",
            "CLAUDE_PROJECT_DIR": str(self.root),
            "FAKE_GH_FOUND": "",
        }
        self.env["GIT_CONFIG_COUNT"] = str(len(names))
        for i, name in enumerate(names):
            bare = base / f"{name}.git"
            self.env[f"GIT_CONFIG_KEY_{i}"] = f"url.file://{bare}.insteadOf"
            self.env[f"GIT_CONFIG_VALUE_{i}"] = f"https://github.com/acme/{name}.git"
        for name in names:
            bare = base / f"{name}.git"
            self.git(base, "init", "-q", "--bare", "-b", "main", str(bare))
            clone = self.root / name
            self.git(base, "clone", "-q", f"https://github.com/acme/{name}.git", str(clone))
            self.git(clone, "commit", "-q", "--allow-empty", "-m", "base")
            self.git(clone, "push", "-q", "origin", "main")

    def git(self, cwd: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=cwd, env=self.env, check=True, capture_output=True)

    def push_branch(self, name: str, branch: str) -> None:
        self.git(self.root / name, "push", "-q", "origin", f"main:refs/heads/{branch}")

    def run(self, target: str, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), target],
            env={**self.env, **env},
            capture_output=True,
            text=True,
        )


class FindRepoTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(Path(self._tmp.name), ["alpha", "beta"])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def assertFound(self, result: subprocess.CompletedProcess, name: str) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.fx.root / name))

    def test_branch_in_one_repo(self) -> None:
        self.fx.push_branch("beta", "claude/feature-x1y2")
        self.assertFound(self.fx.run("claude/feature-x1y2"), "beta")

    def test_branch_in_both_repos_is_ambiguous(self) -> None:
        self.fx.push_branch("alpha", "claude/auto-z0ln0c")
        self.fx.push_branch("beta", "claude/auto-z0ln0c")
        result = self.fx.run("claude/auto-z0ln0c")
        self.assertEqual(result.returncode, 2)
        self.assertIn("several attached repositories: alpha, beta", result.stderr)

    def test_branch_prefix_does_not_match(self) -> None:
        self.fx.push_branch("alpha", "claude/feature-x1y2")
        self.assertEqual(self.fx.run("feature-x1y2").returncode, 1)

    def test_branch_nowhere(self) -> None:
        result = self.fx.run("claude/missing")
        self.assertEqual(result.returncode, 1)
        self.assertIn("none of the attached repositories: alpha, beta", result.stderr)

    def test_pr_url_with_a_fragment(self) -> None:
        url = "https://github.com/acme/alpha/pull/12#pullrequestreview-99"
        self.assertFound(self.fx.run(url), "alpha")

    def test_issue_url_is_case_insensitive(self) -> None:
        self.assertFound(self.fx.run("https://github.com/Acme/Beta/issues/3"), "beta")

    def test_url_of_an_unattached_repo(self) -> None:
        self.assertEqual(self.fx.run("https://github.com/acme/gamma/pull/1").returncode, 1)

    def test_number_in_one_repo(self) -> None:
        self.assertFound(self.fx.run("#7", FAKE_GH_FOUND="acme/beta/7"), "beta")

    def test_number_in_both_repos_is_ambiguous(self) -> None:
        result = self.fx.run("#7", FAKE_GH_FOUND="acme/alpha/7 acme/beta/7")
        self.assertEqual(result.returncode, 2)

    def test_a_failed_lookup_is_not_a_miss(self) -> None:
        result = self.fx.run("#7", FAKE_GH_BROKEN="1")
        self.assertEqual(result.returncode, 3)
        self.assertIn("connection refused", result.stderr)

    def test_single_repo_session_prints_its_own_repo(self) -> None:
        env = {k: v for k, v in self.fx.env.items() if k != "CLAUDE_CODE_REMOTE"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "anything"], env=env, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(MUTHUR))


if __name__ == "__main__":
    unittest.main()
