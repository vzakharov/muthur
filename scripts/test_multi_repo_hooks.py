#!/usr/bin/env python3
"""Tests for `scripts/multi-repo-hooks.py`, run against fixture session roots.

Each fixture is a directory of stand-in clones (a `.git` directory and a
`.claude/settings.json` each), passed to the script as `CLAUDE_PROJECT_DIR`
with `CLAUDE_CODE_REMOTE=true`, which is how a cloud session's hook sees it.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "multi-repo-hooks.py"


def command(script: str, *args: str) -> dict:
    return {"type": "command", "command": " ".join([f"$CLAUDE_PROJECT_DIR/{script}", *args])}


def write_repo(root: Path, name: str, hooks: dict) -> Path:
    repo = root / name
    (repo / ".git").mkdir(parents=True)
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(json.dumps({"hooks": hooks}))
    return repo


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root

    def repo(self, name: str, hooks: dict, scripts: dict[str, str] | None = None) -> Path:
        repo = write_repo(self.root, name, hooks)
        for rel, body in (scripts or {}).items():
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
            path.chmod(0o755)
        return repo

    def run(self, *args: str, remote: bool = True) -> subprocess.CompletedProcess:
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        if remote:
            env["CLAUDE_CODE_REMOTE"] = "true"
        else:
            env.pop("CLAUDE_CODE_REMOTE", None)
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )

    @property
    def settings_path(self) -> Path:
        return self.root / ".claude" / "settings.json"

    def settings(self) -> dict:
        return json.loads(self.settings_path.read_text())

    def commands(self, event: str) -> list[str]:
        return [
            hook["command"]
            for group in self.settings()["hooks"].get(event, [])
            for hook in group["hooks"]
        ]


PRINT_DIR = '#!/bin/sh\necho "$0 in $CLAUDE_PROJECT_DIR"\n'


def ran_hooks(stdout: str) -> list[str]:
    """`<repo>:<script>` for each PRINT_DIR line in the output, sorted."""
    ran = []
    for line in stdout.splitlines():
        script, sep, project_dir = line.partition(" in ")
        if sep:
            ran.append(f"{Path(project_dir).name}:{Path(script).name}")
    return sorted(ran)


class MultiRepoHooksTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def two_repos(self, hooks: dict, scripts: dict[str, str] | None = None) -> tuple[Path, Path]:
        return self.fx.repo("alpha", hooks, scripts), self.fx.repo("beta", hooks, scripts)

    def test_single_repo_session_writes_nothing(self) -> None:
        self.fx.repo("alpha", {"Stop": [{"hooks": [command(".claude/hooks/x.sh")]}]})
        result = self.fx.run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(self.fx.settings_path.exists())

    def test_outside_a_cloud_session_writes_nothing(self) -> None:
        self.two_repos({"Stop": [{"hooks": [command(".claude/hooks/x.sh")]}]})
        result = self.fx.run(remote=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.fx.settings_path.exists())

    def test_path_is_substituted_and_project_dir_set(self) -> None:
        alpha, _ = self.two_repos(
            {"Stop": [{"hooks": [command(".claude/hooks/x.sh", "--flag")]}]}
        )
        self.assertEqual(self.fx.run().returncode, 0)
        self.assertEqual(
            self.fx.commands("Stop"),
            [f"CLAUDE_PROJECT_DIR={alpha} {alpha}/.claude/hooks/x.sh --flag"],
        )

    def test_matchers_and_timeouts_are_kept(self) -> None:
        hook = {**command(".claude/hooks/x.sh"), "timeout": 30}
        self.two_repos({"PreToolUse": [{"matcher": "Bash", "hooks": [hook]}]})
        self.assertEqual(self.fx.run().returncode, 0)
        [group] = self.fx.settings()["hooks"]["PreToolUse"]
        self.assertEqual(group["matcher"], "Bash")
        self.assertEqual(group["hooks"][0]["timeout"], 30)

    def test_per_repo_once_and_skipped(self) -> None:
        alpha, beta = self.two_repos(
            {
                "UserPromptSubmit": [
                    {
                        "hooks": [
                            command("scripts/format.py hook"),
                            command(".claude/hooks/operator-voice.sh"),
                            command(".claude/hooks/prompt-issue-export.sh"),
                        ]
                    }
                ]
            }
        )
        self.assertEqual(self.fx.run().returncode, 0)
        commands = self.fx.commands("UserPromptSubmit")
        self.assertEqual(
            commands,
            [
                f"CLAUDE_PROJECT_DIR={alpha} {alpha}/scripts/format.py hook",
                f"CLAUDE_PROJECT_DIR={alpha} {alpha}/.claude/hooks/operator-voice.sh",
                f"CLAUDE_PROJECT_DIR={beta} {beta}/scripts/format.py hook",
            ],
        )

    def test_a_once_hook_runs_from_the_primary(self) -> None:
        _, beta = self.two_repos(
            {"Stop": [{"hooks": [command(".claude/hooks/operator-voice.sh")]}]}
        )
        self.assertEqual(self.fx.run("--primary", "beta").returncode, 0)
        self.assertEqual(
            self.fx.commands("Stop"),
            [f"CLAUDE_PROJECT_DIR={beta} {beta}/.claude/hooks/operator-voice.sh"],
        )

    def test_an_unknown_primary_is_refused(self) -> None:
        self.two_repos({})
        result = self.fx.run("--primary", "gamma")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no attached repository named 'gamma'", result.stderr)

    def test_a_foreign_settings_file_is_refused(self) -> None:
        self.two_repos({})
        self.fx.settings_path.parent.mkdir()
        self.fx.settings_path.write_text('{"hooks": {}}\n')
        result = self.fx.run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("was not written by this script", result.stderr)
        self.assertEqual(self.fx.settings_path.read_text(), '{"hooks": {}}\n')

    def test_an_edited_generated_file_is_refused(self) -> None:
        self.two_repos({})
        self.assertEqual(self.fx.run().returncode, 0)
        self.fx.settings_path.write_text(self.fx.settings_path.read_text() + " ")
        self.assertEqual(self.fx.run().returncode, 1)

    def test_session_start_hooks_run_once_written_and_not_on_a_rerun(self) -> None:
        self.two_repos(
            {
                "SessionStart": [
                    {
                        "matcher": "startup",
                        "hooks": [
                            command(".claude/hooks/install-deps.sh"),
                            command(".claude/hooks/operator-voice.sh"),
                        ],
                    },
                    {"matcher": "resume", "hooks": [command(".claude/hooks/resume.sh")]},
                ]
            },
            {
                ".claude/hooks/install-deps.sh": PRINT_DIR,
                ".claude/hooks/operator-voice.sh": PRINT_DIR,
                ".claude/hooks/resume.sh": PRINT_DIR,
            },
        )
        first = self.fx.run()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(
            ran_hooks(first.stdout),
            ["alpha:install-deps.sh", "alpha:operator-voice.sh", "beta:install-deps.sh"],
        )
        second = self.fx.run()
        self.assertIn("already current", second.stdout)
        self.assertEqual(ran_hooks(second.stdout), [])
        forced = self.fx.run("--run-session-start")
        self.assertEqual(len(ran_hooks(forced.stdout)), 3)

    def test_a_failing_session_start_hook_fails_the_run_after_the_rest(self) -> None:
        self.two_repos(
            {
                "SessionStart": [
                    {
                        "hooks": [
                            command(".claude/hooks/install-deps.sh"),
                            command(".claude/hooks/operator-voice.sh"),
                        ]
                    }
                ]
            },
            {
                ".claude/hooks/install-deps.sh": "#!/bin/sh\necho boom >&2\nexit 3\n",
                ".claude/hooks/operator-voice.sh": PRINT_DIR,
            },
        )
        result = self.fx.run()
        self.assertEqual(result.returncode, 1)
        self.assertIn("exited 3: boom", result.stderr)
        self.assertIn("operator-voice.sh in", result.stdout)

    def test_json_context_is_relayed_as_text(self) -> None:
        emit = (
            "#!/bin/sh\n"
            'echo \'{"hookSpecificOutput": {"hookEventName": "SessionStart", '
            '"additionalContext": "hello from json"}}\'\n'
        )
        self.two_repos(
            {"SessionStart": [{"hooks": [command(".claude/hooks/operator-voice.sh")]}]},
            {".claude/hooks/operator-voice.sh": emit},
        )
        result = self.fx.run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("hello from json\n", result.stdout)
        self.assertNotIn("hookSpecificOutput", result.stdout)


if __name__ == "__main__":
    unittest.main()
