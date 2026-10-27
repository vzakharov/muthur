#!/usr/bin/env python3
"""Drives the `PreToolUse` hook that stages the session's cost row, as the
harness does — a payload on stdin, over a clone with a bare `origin` — and reads
the index it leaves behind. What it protects is the branch's display copy riding
the agent's own commit, and the hook staying out of every commit that is not
that: it never blocks, and stages nothing where another process owns the index,
the branch takes no copy, or the commit would take nothing else.

Run by path (`python3 .claude/costs/test_stage_cost_row.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `hook_clone`.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List, Optional

from hook_clone import EARLIER, RENAMED, ROW, SESSION, SESSIONS, Clone
from test_filing import row as made_row

HOOK = ".claude/costs/hooks/stage-cost-row.sh"


class StageCostRowTest(unittest.TestCase):
    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.base = Path(base.name)
        self.clone = Clone(self.base)
        self.top = self.clone.git("rev-parse", "--show-toplevel")

    def stage(self, command: str, *, cwd: Optional[Path] = None, **payload: str) -> None:
        """The hook run for `command` as the harness would, asserting that it
        let the command through quietly."""
        result = self.clone.hook(
            HOOK,
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": str(cwd or self.clone.root),
                "transcript_path": str(self.clone.transcript),
                "session_id": SESSION,
                **payload,
            },
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""), command)

    def run_command(self, command: str) -> None:
        subprocess.run(["bash", "-c", command], cwd=self.clone.root, env=self.clone.env(), check=True, capture_output=True)

    def staged(self) -> List[str]:
        return self.clone.git("diff", "--cached", "--name-only").splitlines()

    def other_work_tree(self) -> Path:
        """A second work tree of the clone, the way a delegate's sits beside it."""
        elsewhere = self.base / "elsewhere"
        self.clone.git("worktree", "add", "-q", "-b", "other", str(elsewhere))
        return elsewhere

    def test_the_row_is_staged_for_an_add_and_a_commit_and_lands_in_the_commit(self) -> None:
        (self.clone.root / "work.txt").write_text("in flight\n")
        command = "git add -A && git commit -q -m x"
        self.stage(command)
        self.assertEqual(self.staged(), [ROW])
        self.assertEqual(json.loads(self.clone.git("show", f":{ROW}"))["sessionId"], SESSION)
        self.run_command(command)
        self.assertEqual(sorted(self.clone.files_in("HEAD")), sorted([ROW, "work.txt"]))
        self.assertEqual(self.clone.status(), "")

    def test_a_commit_that_stages_what_it_takes_stages_the_row(self) -> None:
        (self.clone.root / ".gitignore").write_text("tmp/\n__pycache__/\nmore/\n")
        for command in (
            "git commit -am x",
            "git commit -a -m x",
            "git commit --all -m x",
            "git commit --amend --no-edit",
            "git commit -qam x",
        ):
            with self.subTest(command):
                self.stage(command)
                self.assertEqual(self.staged(), [ROW])
                self.clone.git("rm", "-q", "--cached", ROW)

    def test_the_row_is_staged_beside_work_the_agent_staged(self) -> None:
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(sorted(self.staged()), sorted([ROW, "work.txt"]))

    def test_a_commit_with_options_before_the_subcommand_stages_the_row(self) -> None:
        self.clone.stage_work()
        for command in (
            "git -c user.name=a commit -m x",
            "git -C . commit -m x",
            "git -c commit.gpgsign=false -C . commit -m x",
            "cd . && git commit -m x",
            "(git commit -m x)",
            "echo hi; git commit -m x",
        ):
            with self.subTest(command):
                self.stage(command)
                self.assertEqual(sorted(self.staged()), sorted([ROW, "work.txt"]))
                self.clone.git("rm", "-q", "--cached", ROW)

    def test_staging_twice_leaves_one_row(self) -> None:
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.stage("git commit -m x")
        self.assertEqual(sorted(self.staged()), sorted([ROW, "work.txt"]))

    def test_the_row_is_staged_where_the_fetched_ledger_files_it(self) -> None:
        held = f"{SESSIONS}/2026-03/a-branch/1/other.json"
        tip = self.clone.other_row(self.clone.seed_ledger(), held, made_row("other", "a-branch", EARLIER))
        self.clone.git("push", "-q", "origin", f"{tip}:refs/heads/cost-ledger")
        self.clone.git("fetch", "-q", "origin", "+refs/heads/cost-ledger:refs/remotes/origin/cost-ledger")
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(sorted(self.staged()), sorted([f"{SESSIONS}/2026-03/a-branch/2/{SESSION}.json", "work.txt"]))

    def test_a_row_the_ledger_moves_leaves_its_old_copy_in_the_same_commit(self) -> None:
        self.clone.stage_work()
        command = "git commit -q -m x"
        self.stage(command)
        self.run_command(command)
        self.clone.respond(branch="renamed")
        (self.clone.root / "more.txt").write_text("more\n")
        self.clone.git("add", "more.txt")
        self.stage(command)
        staged = self.clone.git("diff", "--cached", "--no-renames", "--name-only").splitlines()
        self.assertEqual(sorted(staged), sorted([ROW, RENAMED, "more.txt"]))
        self.run_command(command)
        self.assertEqual(self.clone.git("ls-tree", "-r", "--name-only", "HEAD", "--", SESSIONS), RENAMED)
        self.assertEqual(self.clone.status(), "")

    def test_a_bare_commit_over_a_clean_index_stages_nothing(self) -> None:
        self.stage("git commit -m x")
        self.assertEqual(self.staged(), [])
        self.assertFalse((self.clone.root / ROW).exists())
        self.assertEqual(self.clone.status(), "")

    def test_a_commit_that_runs_an_add_over_a_clean_tree_stages_the_row(self) -> None:
        for command in ("git add -A && git commit -m x", "git rm -q .gitignore; git commit -m x", "git mv .gitignore g && git commit -m x"):
            with self.subTest(command):
                self.stage(command)
                self.assertEqual(self.staged(), [ROW])
                self.clone.git("rm", "-q", "--cached", ROW)

    def test_a_command_that_only_mentions_commit_stages_nothing(self) -> None:
        self.clone.stage_work()
        for command in (
            "git log --grep commit",
            "git commit-tree HEAD^{tree} -m x",
            "git status && echo commit",
            "git show HEAD",
            "echo git-commit",
        ):
            with self.subTest(command):
                self.stage(command)
                self.assertEqual(self.staged(), ["work.txt"])

    def test_a_command_naming_the_rows_directory_stages_nothing(self) -> None:
        self.clone.stage_work()
        for command in (
            "git rm -r -q --cached .claude/costs/sessions && git commit -m x",
            "git add .claude/costs/sessions/2026-03/sess.json && git commit -m x",
        ):
            with self.subTest(command):
                self.stage(command)
                self.assertEqual(self.staged(), ["work.txt"])

    def test_a_commit_concluding_a_merge_or_a_rebase_stages_nothing(self) -> None:
        self.clone.stage_work()
        head = self.clone.git("rev-parse", "HEAD")
        git_dir = self.clone.root / ".git"
        for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"):
            with self.subTest(marker):
                (git_dir / marker).write_text(head + "\n")
                self.stage("git commit -m x")
                self.assertEqual(self.staged(), ["work.txt"])
                (git_dir / marker).unlink()
        for directory in ("rebase-merge", "rebase-apply"):
            with self.subTest(directory):
                (git_dir / directory).mkdir()
                self.stage("git commit -m x")
                self.assertEqual(self.staged(), ["work.txt"])
                (git_dir / directory).rmdir()
        self.stage("git commit -m x")
        self.assertEqual(sorted(self.staged()), sorted([ROW, "work.txt"]))

    def test_a_commit_on_the_trunk_stages_nothing(self) -> None:
        self.clone.git("checkout", "-q", "main")
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(self.staged(), ["work.txt"])

    def test_a_detached_head_stages_nothing(self) -> None:
        self.clone.git("checkout", "-q", "--detach")
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(self.staged(), ["work.txt"])

    def test_a_branch_attested_on_github_stages_nothing_and_the_yes_is_cached(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        self.clone.answer(f"Attested.\n<!-- finalize-attestation {head} -->")
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(self.staged(), ["work.txt"])
        self.assertEqual(self.clone.cached.read_text().strip(), head)

    def test_a_cached_attestation_needs_no_github(self) -> None:
        self.clone.cache(self.clone.git("rev-parse", "HEAD"))
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(self.staged(), ["work.txt"])

    def test_a_revoked_attestation_stages_the_row(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        self.clone.answer(f"<!-- finalize-attestation {head} -->", "<!-- finalize-attestation revoked -->")
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(sorted(self.staged()), sorted([ROW, "work.txt"]))

    def test_a_work_commit_after_the_attestation_brings_the_row_back(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        self.clone.answer(f"<!-- finalize-attestation {head} -->")
        self.clone.stage_work()
        self.stage("git commit -m work")
        self.assertEqual(self.staged(), ["work.txt"])
        self.run_command("git commit -q -m work")

        (self.clone.root / "more.txt").write_text("more\n")
        self.clone.git("add", "more.txt")
        self.stage("git commit -m more")
        self.assertEqual(sorted(self.staged()), sorted([ROW, "more.txt"]))
        self.assertFalse(self.clone.cached.exists())

    def test_a_cache_the_branch_has_outgrown_brings_the_row_back(self) -> None:
        self.clone.cache(self.clone.git("rev-parse", "HEAD"))
        self.clone.stage_work()
        self.run_command("git commit -q -m work")
        (self.clone.root / "more.txt").write_text("more\n")
        self.clone.git("add", "more.txt")
        self.stage("git commit -m more")
        self.assertEqual(sorted(self.staged()), sorted([ROW, "more.txt"]))

    def test_a_commit_in_another_work_tree_leaves_this_index_alone(self) -> None:
        elsewhere = self.other_work_tree()
        self.clone.stage_work()
        for command in ("git commit -m x", f"cd {elsewhere} && git commit -m x", "cd ../elsewhere && git commit -m x"):
            with self.subTest(command):
                self.stage(command, cwd=elsewhere)
                self.assertEqual(self.staged(), ["work.txt"])

    def test_a_commit_in_another_work_tree_that_names_this_one_stages_the_row(self) -> None:
        elsewhere = self.other_work_tree()
        self.clone.stage_work()
        for command in (
            f"cd {self.top} && git commit -m x",
            f'cd "{self.top}" && git commit -m x',
            f"cd '{self.top}/' && git commit -m x",
            f"git -C {self.top} commit -m x",
        ):
            with self.subTest(command):
                self.stage(command, cwd=elsewhere)
                self.assertEqual(sorted(self.staged()), sorted([ROW, "work.txt"]))
                self.clone.git("rm", "-q", "--cached", ROW)

    def test_a_command_naming_a_path_inside_this_work_tree_is_not_naming_it(self) -> None:
        self.clone.stage_work()
        self.stage(f"cd {self.top}/.claude && git commit -m x", cwd=self.other_work_tree())
        self.assertEqual(self.staged(), ["work.txt"])

    def test_a_session_that_cannot_be_priced_stages_nothing(self) -> None:
        self.clone.stage_work()
        self.clone.respond(model="unheard-of")
        self.stage("git commit -m x")
        self.assertEqual(self.staged(), ["work.txt"])
        self.assertEqual(self.clone.git("ls-files", "--others", "--exclude-standard"), "")

    def test_a_payload_without_a_transcript_stages_nothing(self) -> None:
        self.clone.stage_work()
        self.stage("git commit -m x", transcript_path="")
        self.stage("git commit -m x", transcript_path=str(self.base / "missing.jsonl"))
        self.assertEqual(self.staged(), ["work.txt"])

    def test_a_payload_without_a_command_stages_nothing(self) -> None:
        self.clone.stage_work()
        self.stage("", tool_input={})
        self.assertEqual(self.staged(), ["work.txt"])

    def test_the_hook_leaves_no_priced_copy_behind(self) -> None:
        self.clone.stage_work()
        self.stage("git commit -m x")
        self.assertEqual(sorted((self.clone.root / "tmp").glob("cost-row.*")), [])


if __name__ == "__main__":
    unittest.main()
