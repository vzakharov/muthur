#!/usr/bin/env python3
"""Drives the `Stop` hook as the harness does — a payload on stdin, over a clone
with a bare `origin` — and reads the repository it leaves behind. What it
protects is the tree the harness's own `Stop` check reads: the row committed and
pushed without leaving anything dirty or ahead, the agent's own work left where
it was, and a line to the agent only where the check had something to count.

Run by path (`python3 .claude/costs/test_stop_hook.py`), as `scripts/vet.sh`
does, which puts this directory on `sys.path` for `test_pricing`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import List

from test_filing import row as made_row
from test_pricing import PRICE_TABLE, response

COSTS = Path(__file__).resolve().parent
LIB = COSTS.parent / "hooks" / "lib.sh"
HOOK = ".claude/costs/hooks/stop-session-cost.sh"
SESSIONS = ".claude/costs/sessions"
SESSION = "sess"
ROW = f"{SESSIONS}/2026-03/a-branch/1/{SESSION}.json"
OTHER = f"{SESSIONS}/2026-03/other-branch/1/other.json"
EARLIER = "2026-03-01T00:00:00.000Z"

class Clone:
    """A branch pushed to a bare `origin`, carrying the ledger's code and nothing
    of its rows, with a `HOME` of its own so no global git config or launcher
    settings reach it."""

    def __init__(self, base: Path) -> None:
        self.origin = base / "origin.git"
        self.root = base / "repo"
        self.home = base / "home"
        self.transcript = base / "transcript.jsonl"
        self.home.mkdir()
        self.responses = 0

        # GitHub, as `lib/github.py` reaches it: a `gh` that answers with
        # whatever `answer` left for it, and fails where it left nothing.
        self.answer_file = self.home / "graphql.json"
        gh = self.home / "bin" / "gh"
        gh.parent.mkdir()
        gh.write_text(
            "#!/bin/sh\ncat >/dev/null\n"
            f"[ -f '{self.answer_file}' ] || {{ echo 'gh: offline' >&2; exit 1; }}\n"
            f"cat '{self.answer_file}'\n"
        )
        gh.chmod(0o755)

        subprocess.run(["git", "init", "-q", "--bare", str(self.origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        for key, value in {
            "user.name": "Test",
            "user.email": "test@example.com",
            "commit.gpgsign": "false",
        }.items():
            self.git("config", key, value)
        self.git("remote", "add", "origin", str(self.origin))

        costs = self.root / ".claude" / "costs"
        shutil.copytree(
            COSTS,
            costs,
            ignore=shutil.ignore_patterns("sessions", "__pycache__", "test_*.py"),
        )
        (costs / "prices.json").write_text(json.dumps(PRICE_TABLE))
        (self.root / ".claude" / "hooks").mkdir()
        shutil.copy(LIB, self.root / ".claude" / "hooks" / "lib.sh")
        (self.root / ".gitignore").write_text("tmp/\n__pycache__/\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "init")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-q", "-b", "feature")
        self.git("push", "-q", "-u", "origin", "feature")
        self.respond()

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            check=True,
            env=self.env(),
        ).stdout.strip()

    def env(self) -> dict:
        return {"PATH": f"{self.home / 'bin'}:/usr/bin:/bin", "HOME": str(self.home), "GIT_CONFIG_NOSYSTEM": "1"}

    def origin_git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.origin), *args], capture_output=True, text=True, check=True
        ).stdout.strip()

    def ledger_files(self) -> List[str]:
        return self.origin_git("ls-tree", "-r", "--name-only", "cost-ledger").splitlines()

    def seed_ledger(self) -> str:
        """`cost-ledger` on origin as an empty orphan root."""
        empty = self.git("hash-object", "-t", "tree", "-w", "/dev/null")
        root = self.git("commit-tree", empty, "-m", "root")
        self.git("push", "-q", "origin", f"{root}:refs/heads/cost-ledger")
        return root

    def other_row(self, parent: str, path: str = OTHER, text: str = made_row("other", "other-branch", EARLIER)) -> str:
        """Another session's row committed on `parent`, and not pushed."""
        staged = self.root.parent / "other.json"
        staged.write_text(text)
        return subprocess.run(
            ["python3", str(self.root / ".claude" / "costs" / "ledger.py"), "commit-row", parent, path, str(staged)],
            capture_output=True, text=True, check=True, env=self.env(),
        ).stdout.strip()

    def answer(self, *comments: str) -> None:
        """GitHub's answer to the attestation query: one PR carrying `comments`."""
        nodes = [{"body": body} for body in comments]
        pulls = {"nodes": [{"comments": {"nodes": nodes}}]}
        self.answer_file.write_text(json.dumps({"data": {"repository": {"pullRequests": pulls}}}))

    def cache(self, sha: str) -> Path:
        """`sha` cached as the branch's attestation, the way a yes from GitHub
        leaves it."""
        cached = self.root / "tmp" / "costs" / "finalized" / "feature"
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(sha + "\n")
        return cached

    def respond(self, **fields: str) -> None:
        """One more priced turn in the transcript, so the next row differs."""
        self.responses += 1
        with self.transcript.open("a") as f:
            record = response(id=f"msg_{self.responses}", output=1_000, stop="end_turn", **fields)
            f.write(record + "\n")

    def register_check(self) -> None:
        settings = {"hooks": {"Stop": [{"hooks": [{"command": "~/.claude/stop-hook-git-check.sh"}]}]}}
        (self.home / ".claude").mkdir(exist_ok=True)
        (self.home / ".claude" / "launcher-settings.json").write_text(json.dumps(settings))

    def stop(self, *, active: bool = False) -> subprocess.CompletedProcess:
        payload = {
            "hook_event_name": "Stop",
            "session_id": SESSION,
            "transcript_path": str(self.transcript),
            "cwd": str(self.root),
            "stop_hook_active": active,
        }
        return subprocess.run(
            [str(self.root / HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**self.env(), "CLAUDE_PROJECT_DIR": str(self.root)},
        )

    def cost(self, *args: str) -> None:
        """`session_cost.py` run by hand, the way an agent or a person runs it."""
        subprocess.run(
            ["python3", str(self.root / ".claude" / "costs" / "session_cost.py"),
             "--transcript", str(self.transcript), "--session-id", SESSION, *args],
            capture_output=True,
            check=True,
            env=self.env(),
        )

    def row(self) -> Path:
        [row] = (self.root / ".claude" / "costs" / "sessions").rglob(f"{SESSION}.json")
        return row

    def status(self) -> str:
        return self.git("status", "--porcelain")

    def commits(self) -> int:
        return int(self.git("rev-list", "--count", "HEAD"))

    def files_in(self, rev: str) -> List[str]:
        return self.git("show", "--name-only", "--format=", rev).splitlines()


class StopHookTest(unittest.TestCase):
    def setUp(self) -> None:
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.clone = Clone(Path(base.name))

    def assertLevelWithOrigin(self) -> None:
        self.assertEqual(self.clone.status(), "")
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), self.clone.git("rev-parse", "origin/feature"))
        remote = subprocess.run(
            ["git", "-C", str(self.clone.origin), "rev-parse", "feature"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(remote, self.clone.git("rev-parse", "HEAD"))

    def test_a_row_is_committed_and_pushed_leaving_the_tree_clean(self) -> None:
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertLevelWithOrigin()
        self.assertEqual(
            self.clone.git("log", "-1", "--format=%s"),
            "chore: session cost (new) 0.01 USD, incl. 0.00 USD orientation",
        )
        self.assertEqual(self.clone.files_in("HEAD"), [ROW])

    def test_a_new_session_s_subject_names_what_it_spent_before_acting(self) -> None:
        # A response that neither edits nor ends the turn, ahead of the one that
        # does, so the orientation has a spend of its own.
        before = response(id="msg_0", output=2_000, stop="tool_use", at="2026-03-04T05:06:06.000Z")
        self.clone.transcript.write_text(before + "\n" + self.clone.transcript.read_text())
        self.clone.stop()
        self.assertEqual(
            self.clone.git("log", "-1", "--format=%s"),
            "chore: session cost (new) 0.03 USD, incl. 0.02 USD orientation",
        )

    def test_a_continued_session_s_row_is_committed_as_the_turn_s_spend(self) -> None:
        self.clone.stop()
        self.clone.respond()
        self.clone.stop()
        self.assertEqual(
            self.clone.git("log", "-1", "--format=%s"),
            "chore: session cost +0.01 USD, total 0.02 USD",
        )

    def test_the_tree_is_clean_and_level_while_the_push_is_in_flight(self) -> None:
        # `origin` runs this before it takes the push, which is the stretch the
        # harness's check could land in. A repository hook runs with `origin`'s
        # own git environment set, which would point the clone's commands at it.
        seen = self.clone.root.parent / "seen"
        probe = self.clone.origin / "hooks" / "pre-receive"
        probe.write_text(
            "#!/bin/sh\n"
            "unset GIT_DIR GIT_QUARANTINE_PATH GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES\n"
            f"cd '{self.clone.root}' && {{ git status --porcelain; "
            f"git rev-list --count origin/feature..HEAD; }} > '{seen}'\n"
        )
        probe.chmod(0o755)
        self.assertEqual(self.clone.stop().returncode, 0)
        self.assertEqual(seen.read_text(), "0\n")

    def test_the_row_is_signed_where_commits_are(self) -> None:
        # A stand-in for gpg: git asks only for the status line and an armoured
        # block, so no key is needed to see whether it was asked at all.
        signer = self.clone.home / "sign"
        signer.write_text(
            "#!/bin/sh\ncat >/dev/null\necho '[GNUPG:] SIG_CREATED ' >&2\n"
            "printf -- '-----BEGIN PGP SIGNATURE-----\\n\\nstub\\n-----END PGP SIGNATURE-----\\n'\n"
        )
        signer.chmod(0o755)
        for setting, value in {"gpg.program": str(signer), "commit.gpgsign": "true"}.items():
            self.clone.git("config", setting, value)
        self.assertEqual(self.clone.stop().returncode, 0)
        self.assertIn("gpgsig", self.clone.git("cat-file", "commit", "HEAD"))

    def test_a_row_that_has_not_changed_is_not_committed_again(self) -> None:
        self.clone.stop()
        before = self.clone.commits()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(self.clone.commits(), before)
        self.assertLevelWithOrigin()

    def test_work_the_agent_has_staged_stays_staged_and_out_of_the_commit(self) -> None:
        (self.clone.root / "work.txt").write_text("in flight\n")
        self.clone.git("add", "work.txt")
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("committed and pushed", result.stderr)
        self.assertEqual(self.clone.git("diff", "--cached", "--name-only"), "work.txt")
        self.assertEqual(self.clone.files_in("HEAD"), [ROW])

    def test_a_row_left_dirty_is_named_to_the_agent_where_a_check_read_it(self) -> None:
        self.clone.register_check()
        self.clone.stop()
        self.clone.respond()
        self.clone.cost()
        self.assertNotEqual(self.clone.status(), "")
        result = self.clone.stop()
        self.assertEqual(result.returncode, 2)
        self.assertIn("was counting it", result.stderr)
        self.assertLevelWithOrigin()

    def test_a_row_left_dirty_is_committed_silently_where_no_check_ran(self) -> None:
        self.clone.stop()
        self.clone.respond()
        self.clone.cost()
        result = self.clone.stop()
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertLevelWithOrigin()

    def test_a_refired_stop_never_blocks(self) -> None:
        self.clone.register_check()
        self.clone.stop()
        self.clone.respond()
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
        self.assertEqual(self.clone.git("rev-list", "--count", "origin/feature..HEAD"), "1")


class LedgerWriteTest(unittest.TestCase):
    """Where the row goes: `cost-ledger` always, the branch until it is
    finalized."""

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
        self.assertEqual(self.clone.ledger_files(), [ROW, OTHER])
        self.assertEqual(self.clone.origin_git("rev-list", "--count", "cost-ledger"), "3")

    def test_a_new_session_on_a_branch_takes_the_next_number_on_both_sides(self) -> None:
        held = f"{SESSIONS}/2026-03/a-branch/1/other.json"
        tip = self.clone.other_row(self.clone.seed_ledger(), held, made_row("other", "a-branch", EARLIER))
        self.clone.git("push", "-q", "origin", f"{tip}:refs/heads/cost-ledger")
        self.stop()
        second = f"{SESSIONS}/2026-03/a-branch/2/{SESSION}.json"
        self.assertEqual(self.clone.ledger_files(), [held, second])
        self.assertEqual(self.clone.files_in("HEAD"), [second])

    def test_a_branch_change_moves_the_row_on_the_ledger_and_the_branch(self) -> None:
        self.stop()
        self.clone.respond(branch="renamed")
        self.stop()
        moved = f"{SESSIONS}/2026-03/renamed/1/{SESSION}.json"
        self.assertEqual(self.clone.ledger_files(), [moved])
        self.assertEqual(self.clone.git("ls-tree", "-r", "--name-only", "HEAD", "--", SESSIONS), moved)
        self.assertEqual(self.clone.status(), "")

    def test_a_stale_branch_s_month_only_rows_are_folded_in(self) -> None:
        root = self.clone.seed_ledger()
        stale = self.clone.other_row(root, f"{SESSIONS}/2026-03/other.json")
        mine = self.clone.other_row(stale, f"{SESSIONS}/2026-03/{SESSION}.json", made_row(SESSION, "a-branch", EARLIER))
        self.clone.git("push", "-q", "origin", f"{mine}:refs/heads/cost-ledger")
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [ROW, OTHER])
        self.assertTrue(self.clone.origin_git("log", "-1", "--format=%s", "cost-ledger").endswith("; re-file 1 session row"))

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
        self.assertEqual(self.clone.ledger_files(), [ROW, OTHER])

    def test_the_trunk_s_row_goes_to_the_ledger_alone(self) -> None:
        self.clone.git("checkout", "-q", "main")
        before = self.clone.git("rev-parse", "HEAD")
        self.stop()
        self.assertEqual(self.clone.ledger_files(), [ROW])
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.clone.origin_git("rev-parse", "main"), before)
        self.assertEqual(self.clone.status(), "")

    def test_an_unfinalized_branch_carries_a_copy(self) -> None:
        self.stop()
        self.assertEqual(self.clone.files_in("HEAD"), [ROW])
        self.assertEqual(self.clone.ledger_files(), [ROW])

    def test_a_branch_attested_on_github_carries_none_and_the_yes_is_cached(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        self.clone.answer(f"Attested.\n<!-- finalize-attestation {head} -->")
        self.stop()
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.clone.ledger_files(), [ROW])
        cached = self.clone.root / "tmp" / "costs" / "finalized" / "feature"
        self.assertEqual(cached.read_text().strip(), head)

    def test_a_revoked_attestation_is_none(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        self.clone.answer(f"<!-- finalize-attestation {head} -->", "<!-- finalize-attestation revoked -->")
        self.stop()
        self.assertEqual(self.clone.files_in("HEAD"), [ROW])

    def test_a_cached_attestation_needs_no_github(self) -> None:
        head = self.clone.git("rev-parse", "HEAD")
        self.clone.cache(head)
        self.stop()
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.clone.ledger_files(), [ROW])

    def test_rows_committed_after_the_attestation_leave_it_standing(self) -> None:
        attested = self.clone.git("rev-parse", "HEAD")
        self.stop()
        self.clone.cache(attested)
        self.clone.respond()
        after_row = self.clone.git("rev-parse", "HEAD")
        self.stop()
        self.assertEqual(self.clone.git("rev-parse", "HEAD"), after_row)

    def test_a_work_commit_after_the_attestation_brings_the_copy_back(self) -> None:
        cached = self.clone.cache(self.clone.git("rev-parse", "HEAD"))
        (self.clone.root / "work.txt").write_text("more\n")
        self.clone.git("add", "work.txt")
        self.clone.git("commit", "-q", "-m", "work")
        self.clone.git("push", "-q", "origin", "feature")
        self.stop()
        self.assertEqual(self.clone.files_in("HEAD"), [ROW])
        self.assertFalse(cached.exists())


if __name__ == "__main__":
    unittest.main()
