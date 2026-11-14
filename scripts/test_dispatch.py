#!/usr/bin/env python3
"""Tests for `.claude/hooks/dispatch.sh`, run against a temp repository.

The fixture is a repository carrying the dispatcher and a probe hook, plus a
worktree of it whose probe identifies itself differently, so each case reads
off which checkout's hook ran and with which `CLAUDE_PROJECT_DIR`.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

DISPATCHER = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "dispatch.sh"
HOOK = ".claude/hooks/probe.sh"

# Prints its checkout's label, the project dir it was given, its args and its
# stdin, then exits with PROBE_EXIT.
PROBE = """#!/bin/sh
printf '%s|%s|%s|' "{label}" "$CLAUDE_PROJECT_DIR" "$*"
cat
exit "${{PROBE_EXIT:-0}}"
"""


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def write_probe(checkout: Path, label: str) -> None:
    path = checkout / HOOK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PROBE.format(label=label))
    path.chmod(0o755)


class DispatchTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name).resolve()
        self.main = root / "main"
        self.main.mkdir()
        git(self.main, "init", "-q", "-b", "main")
        hooks = self.main / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        shutil.copy2(DISPATCHER, hooks / "dispatch.sh")
        write_probe(self.main, "main")
        git(self.main, "add", ".")
        git(self.main, "commit", "-q", "-m", "init")
        self.worktree = self.main / ".claude" / "worktrees" / "feature"
        git(self.main, "worktree", "add", "-q", "-b", "feature", str(self.worktree))
        write_probe(self.worktree, "worktree")
        self.outside = root / "plain"
        self.outside.mkdir()
        self.other = root / "other"
        self.other.mkdir()
        git(self.other, "init", "-q")
        write_probe(self.other, "other")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def dispatch(
        self,
        cwd: Path | None,
        *args: str,
        project_dir: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        payload = json.dumps({"cwd": str(cwd)} if cwd else {"session_id": "s"})
        environ = dict(os.environ)
        environ.pop("CLAUDE_PROJECT_DIR", None)
        environ.pop("PROBE_EXIT", None)
        environ.update(env or {})
        if project_dir is not None:
            environ["CLAUDE_PROJECT_DIR"] = str(project_dir)
        return subprocess.run(
            [str(self.main / ".claude" / "hooks" / "dispatch.sh"), HOOK, *args],
            input=payload,
            env=environ,
            capture_output=True,
            text=True,
        )

    def ran(self, result: subprocess.CompletedProcess) -> tuple[str, str]:
        label, project_dir, _args, _stdin = result.stdout.split("|", 3)
        return label, project_dir

    def test_worktree_cwd_runs_the_worktrees_hook(self) -> None:
        result = self.dispatch(self.worktree, project_dir=self.main)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.ran(result), ("worktree", str(self.worktree)))

    def test_worktree_subdirectory_cwd_runs_the_worktrees_hook(self) -> None:
        result = self.dispatch(self.worktree / ".claude" / "hooks", project_dir=self.main)
        self.assertEqual(self.ran(result), ("worktree", str(self.worktree)))

    def test_same_checkout_runs_from_the_anchor(self) -> None:
        result = self.dispatch(self.main / ".claude", project_dir=self.main)
        self.assertEqual(self.ran(result), ("main", str(self.main)))

    def test_non_git_cwd_runs_from_the_anchor(self) -> None:
        result = self.dispatch(self.outside, project_dir=self.main)
        self.assertEqual(self.ran(result), ("main", str(self.main)))

    def test_other_repository_cwd_runs_from_the_anchor(self) -> None:
        result = self.dispatch(self.other, project_dir=self.main)
        self.assertEqual(self.ran(result), ("main", str(self.main)))

    def test_worktree_without_the_hook_runs_from_the_anchor(self) -> None:
        (self.worktree / HOOK).unlink()
        result = self.dispatch(self.worktree, project_dir=self.main)
        self.assertEqual(self.ran(result), ("main", str(self.main)))

    def test_payload_without_cwd_runs_from_the_anchor(self) -> None:
        result = self.dispatch(None, project_dir=self.main)
        self.assertEqual(self.ran(result), ("main", str(self.main)))

    def test_unset_project_dir_anchors_on_the_dispatchers_repository(self) -> None:
        result = self.dispatch(self.outside)
        self.assertEqual(self.ran(result), ("main", str(self.main)))

    def test_args_stdin_and_exit_code_pass_through(self) -> None:
        result = self.dispatch(
            self.worktree, "stop", "--x", project_dir=self.main, env={"PROBE_EXIT": "3"}
        )
        self.assertEqual(result.returncode, 3)
        _label, _dir, args, stdin = result.stdout.split("|", 3)
        self.assertEqual(args, "stop --x")
        self.assertEqual(json.loads(stdin), {"cwd": str(self.worktree)})


if __name__ == "__main__":
    unittest.main()
