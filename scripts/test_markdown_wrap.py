#!/usr/bin/env python3
"""Tests for `.claude/hooks/format-md.sh` and `scripts/check-markdown-wrap.sh`,
each against a throwaway git repository carrying copies of them and of the
prettier setup they share.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`. Needs `npx`, which fetches the pinned prettier once.
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
    ".prettierrc.json",
    ".prettierignore",
    "scripts/prettier.sh",
    "scripts/staged.sh",
    "scripts/check-markdown-wrap.sh",
    ".claude/hooks/format-md.sh",
    ".claude/hooks/lib.sh",
)

LONG = " ".join(["word"] * 40)
UNWRAPPED = f"# Title\n\n{LONG}\n"


class MarkdownWrap(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        for path in COPIED:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / path, self.root / path)
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

    def hook(
        self, path: Path | str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        payload = {"tool_name": "Edit", "tool_input": {"file_path": str(path)}}
        return subprocess.run(
            ["bash", ".claude/hooks/format-md.sh"],
            cwd=self.root,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.root), **(env or {})},
        )

    def check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "scripts/check-markdown-wrap.sh"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def assert_wrapped(self, path: Path) -> None:
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertGreater(len(lines), 3)
        self.assertTrue(all(len(line) <= 80 for line in lines))

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

    def test_hook_leaves_a_file_outside_the_project_alone(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "draft.md"
            target.write_text(UNWRAPPED, encoding="utf-8")
            self.assertEqual(self.hook(target).returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), UNWRAPPED)

    def test_hook_ignores_other_files(self) -> None:
        target = self.write("script.sh", LONG + "\n")
        self.assertEqual(self.hook(target).returncode, 0)
        self.assertEqual(target.read_text(encoding="utf-8"), LONG + "\n")

    def test_hook_reports_a_prettier_failure(self) -> None:
        target = self.write("notes.md")
        fake = self.write("bin/npx", "#!/bin/sh\necho 'registry unreachable' >&2\nexit 1\n")
        fake.chmod(0o755)
        result = self.hook(target, {"PATH": f"{fake.parent}:{os.environ['PATH']}"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("prettier could not wrap", result.stderr)
        self.assertIn("registry unreachable", result.stderr)

    def test_hook_leaves_fenced_text_alone(self) -> None:
        fenced = f"```markdown\n{LONG}\n```\n"
        target = self.write("notes.md", fenced)
        self.assertEqual(self.hook(target).returncode, 0)
        self.assertEqual(target.read_text(encoding="utf-8"), fenced)

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


if __name__ == "__main__":
    unittest.main()
