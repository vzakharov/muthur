#!/usr/bin/env python3
"""Drives the `Stop` hook as the harness does — a payload on stdin, over a clone
with a bare `origin` — and reads the repository it leaves behind. What it
protects is the tree the harness's own `Stop` check reads: the row written to the
ledger and never committed to the branch, a row left in the tree put back to
HEAD's copy, the agent's own work left where it was, and a line to the agent only
where the check had something to count.

Run by path (`python3 .claude/costs/test_stop_hook.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `hook_clone`.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hook_clone import ROW, SESSIONS, Clone


class StopHookTest(unittest.TestCase):
    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.clone = Clone(Path(base.name))

    def commit_row_to_branch(self) -> str:
        """The session's row committed and pushed on the branch, the way an
        agent's commit carries it, and its text."""
        self.clone.cost()
        self.clone.git("add", ROW)
        self.clone.git("commit", "-q", "-m", "work")
        self.clone.git("push", "-q", "origin", "feature")
        return (self.clone.root / ROW).read_text()

    def assertLevelWithOrigin(self) -> None:
        self.assertEqual(self.clone.status(), "")
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), self.clone.git("rev-parse", "origin/feature"))

    def test_a_turn_with_a_clean_tree_leaves_the_branch_untouched(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        tree = self.clone.git("rev-parse", "HEAD^{tree}")
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.clone.git("rev-parse", "HEAD^{tree}"), tree)
        self.assertEqual(self.clone.status(), "")
        self.assertFalse((self.clone.root / ROW).exists())
        self.assertLevelWithOrigin()
        self.assertEqual(self.clone.ledger_files(), [ROW])

    def test_a_staged_row_whose_head_has_a_copy_is_restored_to_it(self) -> None:
        held = self.commit_row_to_branch()
        self.clone.respond()
        self.clone.cost()
        self.clone.git("add", ROW)
        self.assertNotEqual((self.clone.root / ROW).read_text(), held)
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual((self.clone.root / ROW).read_text(), held)
        self.assertEqual(self.clone.git("diff", "--cached", "--name-only"), "")
        self.assertLevelWithOrigin()

    def test_an_unstaged_edit_of_a_row_head_has_is_restored_too(self) -> None:
        held = self.commit_row_to_branch()
        self.clone.respond()
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual((self.clone.root / ROW).read_text(), held)
        self.assertEqual(self.clone.status(), "")

    def test_a_row_head_lacks_is_removed_from_the_index_and_the_tree(self) -> None:
        self.clone.cost()
        self.clone.git("add", ROW)
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertFalse((self.clone.root / ROW).exists())
        self.assertEqual(self.clone.git("ls-files", "--", SESSIONS), "")
        self.assertEqual(self.clone.status(), "")

    def test_an_untracked_row_head_lacks_is_removed(self) -> None:
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertFalse((self.clone.root / ROW).exists())
        self.assertEqual(self.clone.status(), "")

    def test_work_the_agent_has_staged_stays_staged_beside_a_row_put_back(self) -> None:
        self.clone.stage_work()
        self.clone.cost()
        self.clone.git("add", ROW)
        head = self.clone.git("rev-parse", "HEAD")
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.clone.git("diff", "--cached", "--name-only"), "work.txt")
        self.assertEqual((self.clone.root / "work.txt").read_text(), "in flight\n")
        self.assertFalse((self.clone.root / ROW).exists())
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), head)

    def test_a_row_put_back_is_named_to_the_agent_where_a_check_is_registered_and_nothing_is_outstanding(self) -> None:
        self.clone.register_check()
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("was counting it", result.stderr)
        self.assertIn("nothing is outstanding", result.stderr)
        self.assertLevelWithOrigin()

    def test_a_row_put_back_is_not_named_where_no_check_is_registered(self) -> None:
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertLevelWithOrigin()

    def test_a_row_put_back_is_not_named_while_work_is_outstanding(self) -> None:
        self.clone.register_check()
        self.clone.stage_work()
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_a_row_put_back_is_not_named_while_commits_are_unpushed(self) -> None:
        self.clone.register_check()
        (self.clone.root / "work.txt").write_text("committed\n")
        self.clone.git("add", "work.txt")
        self.clone.git("commit", "-q", "-m", "work")
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_a_row_that_cannot_be_put_back_blocks_the_stop_naming_the_restore(self) -> None:
        self.clone.cost()
        self.clone.git("add", ROW)
        # A held index lock refuses every write to the index, and a read of the
        # status goes on without it.
        (self.clone.root / ".git" / "index.lock").write_text("")
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("could not be put back", result.stderr)
        self.assertTrue((self.clone.root / ROW).exists())

    def test_a_refired_stop_never_blocks_and_still_puts_the_row_back(self) -> None:
        self.clone.register_check()
        self.clone.cost()
        result = self.clone.stop(active=True)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertLevelWithOrigin()

    def test_a_turn_that_cannot_be_priced_is_blocked_once_naming_the_model(self) -> None:
        self.clone.respond(model="unheard-of")
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("pricing failed", result.stderr)
        self.assertIn("unheard-of/standard", result.stderr)
        self.assertEqual(self.clone.commits(), 1)
        self.assertEqual(self.clone.status(), "")

    def test_a_refired_stop_over_an_unpriced_turn_never_blocks(self) -> None:
        self.clone.respond(model="unheard-of")
        result = self.clone.stop(active=True)
        self.assertEqual(result.returncode, 0)

    def test_an_unreachable_origin_is_reported_as_the_ledger_missing_the_row(self) -> None:
        self.clone.git("remote", "set-url", "origin", str(self.clone.root.parent / "missing.git"))
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("did not take this turn's row", result.stderr)
        self.assertIn("missing.git", result.stderr)
        self.assertEqual(self.clone.status(), "")
        self.assertEqual(self.clone.commits(), 1)


class LedgerWriteTest(unittest.TestCase):
    """Where the row goes: `cost-ledger` on every branch and the trunk, and the
    working branch never."""

    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.clone = Clone(Path(base.name))

    def stop(self) -> None:
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))

    def test_the_first_row_roots_the_ledger(self) -> None:
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [ROW])
        self.assertEqual(self.clone.origin_git("rev-list", "--count", "cost-ledger"), "1")

    def test_a_row_lands_on_the_ledger_s_tip_beside_the_rows_it_holds(self) -> None:
        root = self.clone.seed_ledger()
        self.clone.git("push", "-q", "origin", f"{self.clone.other_row(root)}:refs/heads/cost-ledger")
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [f"{SESSIONS}/2026-03/other.json", ROW])
        self.assertEqual(self.clone.origin_git("rev-list", "--count", "cost-ledger"), "3")

    def test_a_continued_session_s_row_replaces_its_copy_on_the_ledger(self) -> None:
        self.stop()
        self.clone.respond()
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [ROW])
        self.assertEqual(self.clone.origin_git("rev-list", "--count", "cost-ledger"), "2")
        self.assertEqual(
            self.clone.origin_git("log", "-1", "--format=%s", "cost-ledger"),
            "chore: session cost +0.01 USD, total 0.02 USD",
        )

    def test_a_turn_that_changes_nothing_adds_no_ledger_commit(self) -> None:
        self.stop()
        self.stop()
        self.assertEqual(self.clone.origin_git("rev-list", "--count", "cost-ledger"), "1")

    def test_a_writer_that_takes_the_tip_first_loses_no_row(self) -> None:
        # The other session's push lands while this one's is being received, so
        # this one is refused as no longer a fast-forward and has to rebuild.
        other = self.clone.other_row(self.clone.seed_ledger())
        raced = self.clone.root.parent / "raced"
        probe = self.clone.origin / "hooks" / "pre-receive"
        probe.write_text(
            "#!/bin/sh\n"
            "unset GIT_DIR GIT_QUARANTINE_PATH GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES\n"
            "while read old new ref; do\n"
            f"  [ \"$ref\" = refs/heads/cost-ledger ] && [ ! -e '{raced}' ] || continue\n"
            f"  touch '{raced}'\n"
            f"  git -C '{self.clone.root}' push -q origin '{other}:refs/heads/cost-ledger'\n"
            "done\n"
        )
        probe.chmod(0o755)
        self.stop()
        self.assertTrue(raced.exists())
        self.assertEqual(self.clone.ledger_files(), [f"{SESSIONS}/2026-03/other.json", ROW])

    def test_the_trunk_s_row_goes_to_the_ledger_alone(self) -> None:
        self.clone.git("checkout", "-q", "main")
        before = self.clone.git("rev-parse", "HEAD")
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [ROW])
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.clone.origin_git("rev-parse", "main"), before)
        self.assertEqual(self.clone.status(), "")

    def test_a_branch_s_row_goes_to_the_ledger_and_not_to_the_branch(self) -> None:
        before = self.clone.git("rev-parse", "HEAD")
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [ROW])
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.clone.origin_git("rev-parse", "feature"), before)

    def test_a_finalized_branch_s_row_goes_to_the_ledger_too(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        self.clone.cache(head)
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [ROW])
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), head)


if __name__ == "__main__":
    unittest.main()
