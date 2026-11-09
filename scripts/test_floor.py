#!/usr/bin/env python3
"""Drives `scripts/floor.py` in a throwaway repository with a bare `origin`. What
it protects is that the floor is the newest branch commit whose subject opens
with one of the given types exactly, never a commit the base carries, and that
the scope it starts leaves out what a base merge brought in while keeping the
branch's own work on either side of it.

Run by path (`python3 scripts/test_floor.py`), as `scripts/check-muthur.sh` does.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Dict, List

SCRIPT = Path(__file__).resolve().parent / "floor.py"


def load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("floor", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


floor = load()


class FloorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.origin = Path(tmp.name) / "origin.git"
        self.root = Path(tmp.name) / "work"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.git("init", "-q", "-b", "main")
        self.git("remote", "add", "origin", str(self.origin))
        self.commit({"src.py": "1"}, "chore: base")
        self.commit({}, "polish: the base's own")
        self.git("push", "-q", "origin", "main")
        self.git("fetch", "-q", "origin")
        self.git("checkout", "-q", "-b", "feature")

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 and args[0] != "merge":
            self.fail(f"git {args}: {result.stderr}")
        return result.stdout

    def commit(self, files: Dict[str, str], message: str) -> str:
        for name, content in files.items():
            (self.root / name).write_text(content)
            self.git("add", name)
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def land_on_main(self, files: Dict[str, str]) -> None:
        self.git("checkout", "-q", "main")
        self.commit(files, "feat: landed on main")
        self.git("push", "-q", "origin", "main")
        self.git("fetch", "-q", "origin")
        self.git("checkout", "-q", "feature")

    def changed(self, start: str) -> List[str]:
        return self.git("diff", "--name-only", start, "HEAD").split()

    def cli(self, *args: str) -> List[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--base", "main", *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.splitlines()


class FindFloor(FloorTestCase):
    def test_none_on_a_fresh_branch_even_with_a_marked_base_commit(self) -> None:
        self.commit({"src.py": "2"}, "feat: work")
        self.assertIsNone(floor.find_floor(self.root, "origin/main", ["polish:"]))

    def test_the_newest_exact_match(self) -> None:
        older = self.commit({}, "polish: first")
        self.assertEqual(floor.find_floor(self.root, "origin/main", ["polish:"]), (older, "polish: first"))
        newer = self.commit({}, "review: second")
        self.commit({}, "polish(prose only): focused")
        self.commit({}, "fix: polish: in the middle")
        self.assertEqual(floor.find_floor(self.root, "origin/main", ["polish:"])[0], older)
        found = floor.find_floor(self.root, "origin/main", ["polish:", "review:"])
        self.assertEqual(found, (newer, "review: second"))


class ScopeStart(FloorTestCase):
    def test_no_floor_starts_at_the_merge_base(self) -> None:
        self.commit({"a.py": "a"}, "feat: work")
        self.assertEqual(self.changed(floor.scope_start(self.root, "origin/main", None)), ["a.py"])

    def test_a_floor_hides_what_came_before_it(self) -> None:
        self.commit({"a.py": "a"}, "feat: work")
        mark = self.commit({}, "polish: tidy")
        self.commit({"b.py": "b"}, "feat: more")
        self.assertEqual(self.changed(floor.scope_start(self.root, "origin/main", mark)), ["b.py"])

    def test_a_base_merge_after_the_floor_stays_below_the_line(self) -> None:
        mark = self.commit({"a.py": "a"}, "polish: tidy")
        self.land_on_main({"other.py": "landed"})
        self.git("merge", "-q", "--no-edit", "origin/main")
        self.commit({"b.py": "b"}, "feat: more")
        self.assertEqual(self.changed(floor.scope_start(self.root, "origin/main", mark)), ["b.py"])

    def test_an_unreadable_floor_is_an_error(self) -> None:
        with self.assertRaises(floor.GitError):
            floor.scope_start(self.root, "origin/main", "0" * 40)


class Cli(FloorTestCase):
    def test_prints_the_floor_and_where_the_scope_starts(self) -> None:
        self.commit({"a.py": "a"}, "feat: work")
        mark = self.commit({}, "polish: tidy")
        self.commit({"b.py": "b"}, "feat: more")
        found, start = self.cli("polish:")
        self.assertEqual(found, f"floor {mark} polish: tidy")
        self.assertEqual(self.changed(start.removeprefix("from ")), ["b.py"])

    def test_full_and_no_floor_start_at_the_base(self) -> None:
        self.commit({"a.py": "a"}, "feat: work")
        self.assertEqual(self.cli("review:")[0], "floor none")
        self.commit({}, "polish: tidy")
        start = self.cli("--full", "polish:")[1]
        self.assertEqual(self.changed(start.removeprefix("from ")), ["a.py"])

    def test_a_base_the_remote_lacks_fails(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--base", "nope", "polish:"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("floor:", result.stderr)


if __name__ == "__main__":
    unittest.main()
