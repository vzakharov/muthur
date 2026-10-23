#!/usr/bin/env python3
"""Tests for `scripts/format.py`, each against a throwaway git repository
carrying copies of it and of the prettier setup the shipped Markdown entry uses.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`. The Markdown cases need `npx`, which fetches the
pinned prettier once; the generic ones run a stand-in formatter.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

COPIED = (
    ".claude/format.json",
    ".prettierrc.json",
    ".prettierignore",
    "scripts/prettier.sh",
    "scripts/staged.sh",
    "scripts/format.py",
)

LONG = " ".join(["word"] * 40)
UNWRAPPED = f"# Title\n\n{LONG}\n"

# A formatter that upper-cases its files, and a check that fails on any
# lower-case letter in them.
UPPER = "#!/bin/sh\nfor f; do tr a-z A-Z <\"$f\" >\"$f.tmp\" && mv \"$f.tmp\" \"$f\"; done\n"
IS_UPPER = "#!/bin/sh\nstatus=0\nfor f; do grep -q '[a-z]' \"$f\" && echo \"$f\" && status=1; done\nexit $status\n"
SHOUT = {
    "name": "shout",
    "files": ["src/*.txt"],
    "format": ["bin/upper.sh"],
    "check": ["bin/is-upper.sh"],
}


class Format(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        for path in COPIED:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / path, self.root / path)
        for name, text in (("upper.sh", UPPER), ("is-upper.sh", IS_UPPER)):
            self.write(f"bin/{name}", text).chmod(0o755)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, path: str, text: str = UNWRAPPED) -> Path:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def track(self, path: str, text: str = UNWRAPPED) -> Path:
        target = self.write(path, text)
        subprocess.run(["git", "add", path], cwd=self.root, check=True)
        return target

    def configure(self, entries: object) -> None:
        self.write(".claude/format.json", json.dumps(entries))

    def hook(
        self, path: Path | str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        payload = {"tool_name": "Edit", "tool_input": {"file_path": str(path)}}
        return subprocess.run(
            ["python3", "scripts/format.py", "hook"],
            cwd=self.root,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.root), **(env or {})},
        )

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "scripts/format.py", "check"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def assert_wrapped(self, path: Path) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertGreater(len(lines), 3)
        self.assertTrue(all(len(line) <= 80 for line in lines))

    # The shipped Markdown entry.

    def test_hook_wraps_an_edited_markdown_file(self) -> None:
        target = self.write("notes.md")
        self.assertEqual(self.hook(target).returncode, 0)
        self.assert_wrapped(target)

    def test_hook_wraps_a_staged_copy(self) -> None:
        target = self.write(".claude/staged/CLAUDE.md.staged")
        self.assertEqual(self.hook(target).returncode, 0)
        self.assert_wrapped(target)

    def test_hook_leaves_github_bound_files_alone(self) -> None:
        for path in ("docs/pr/1/body.md", "docs/issue/2/issue.md", "tmp/reply.md"):
            target = self.write(path)
            self.assertEqual(self.hook(target).returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), UNWRAPPED)

    def test_hook_leaves_fenced_text_alone(self) -> None:
        fenced = f"```markdown\n{LONG}\n```\n"
        target = self.write("notes.md", fenced)
        self.assertEqual(self.hook(target).returncode, 0)
        self.assertEqual(target.read_text(encoding="utf-8"), fenced)

    def test_hook_reports_a_prettier_failure(self) -> None:
        target = self.write("notes.md")
        fake = self.write("fake-bin/npx", "#!/bin/sh\necho 'registry unreachable' >&2\nexit 1\n")
        fake.chmod(0o755)
        result = self.hook(target, {"PATH": f"{fake.parent}:{os.environ['PATH']}"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("markdown wrap could not format", result.stderr)
        self.assertIn("registry unreachable", result.stderr)

    def test_check_fails_on_unwrapped_tracked_markdown(self) -> None:
        self.track("notes.md")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("notes.md", result.stdout + result.stderr)

    def test_check_passes_on_wrapped_and_exempt_markdown(self) -> None:
        target = self.track("notes.md")
        self.hook(target)
        self.track("docs/pr/1/body.md")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_check_reads_a_staged_file_through_its_copy(self) -> None:
        self.track("CLAUDE.md")
        copy = self.track(".claude/staged/CLAUDE.md.staged")
        self.assertNotEqual(self.check().returncode, 0)
        self.hook(copy)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    # The mechanism, through a stand-in formatter.

    def test_hook_formats_a_file_an_entry_covers(self) -> None:
        self.configure([SHOUT])
        target = self.write("src/deep/a.txt", "quiet\n")
        result = self.hook(target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "QUIET\n")

    def test_hook_leaves_uncovered_ignored_and_outside_files_alone(self) -> None:
        self.configure([SHOUT])
        self.write(".gitignore", "src/vendor/\n")
        uncovered = self.write("lib/a.txt", "quiet\n")
        ignored = self.write("src/vendor/a.txt", "quiet\n")
        with tempfile.TemporaryDirectory() as outside:
            elsewhere = Path(outside) / "src" / "a.txt"
            elsewhere.parent.mkdir()
            elsewhere.write_text("quiet\n", encoding="utf-8")
            for target in (uncovered, ignored, elsewhere):
                self.assertEqual(self.hook(target).returncode, 0)
                self.assertEqual(target.read_text(encoding="utf-8"), "quiet\n")

    def test_hook_runs_every_matching_entry_in_order(self) -> None:
        mark = self.write("bin/mark.sh", "#!/bin/sh\nfor f; do echo marked >>\"$f\"; done\n")
        mark.chmod(0o755)
        self.configure([SHOUT, {**SHOUT, "name": "mark", "format": ["bin/mark.sh"]}])
        target = self.write("src/a.txt", "quiet\n")
        self.assertEqual(self.hook(target).returncode, 0)
        self.assertEqual(target.read_text(encoding="utf-8"), "QUIET\nmarked\n")

    def test_check_runs_each_entry_over_its_tracked_files(self) -> None:
        self.configure([SHOUT])
        target = self.track("src/a.txt", "quiet\n")
        self.write("src/untracked.txt", "quiet\n")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("shout", result.stderr)
        self.assertIn("src/a.txt", result.stderr)
        self.assertNotIn("untracked", result.stderr)
        self.hook(target)
        self.assertEqual(self.check().returncode, 0)

    def test_no_list_formats_and_checks_nothing(self) -> None:
        (self.root / ".claude/format.json").unlink()
        target = self.track("notes.md")
        self.assertEqual(self.hook(target).returncode, 0)
        self.assertEqual(target.read_text(encoding="utf-8"), UNWRAPPED)
        self.assertEqual(self.check().returncode, 0)

    def test_a_malformed_list_fails_both_modes(self) -> None:
        target = self.write("src/a.txt", "quiet\n")
        for entries in ("{", {"name": "x"}, [{**SHOUT, "check": []}], [{**SHOUT, "extra": 1}]):
            self.write(".claude/format.json", entries if isinstance(entries, str) else json.dumps(entries))
            hooked = self.hook(target)
            self.assertEqual(hooked.returncode, 2, entries)
            self.assertIn("format.json", hooked.stderr)
            self.assertEqual(self.check().returncode, 1, entries)


if __name__ == "__main__":
    unittest.main()
