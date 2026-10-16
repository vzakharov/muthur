#!/usr/bin/env python3
"""Tests for `scripts/muthur-sync.sh`, run with real git against local bare
repositories standing in for the source and for the adopter's origin.

The source's GitHub URL is redirected to its bare repo through
`url.<file>.insteadOf` in `GIT_CONFIG_*`, and a fake `gh` on `PATH` answers the
calls the script makes, so the script under test carries no test-only knob.

Run by path, as `scripts/check-muthur.sh` does — see the note there on why never
through `unittest discover`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
WATERMARK = ".claude/skills/update-muthur/watermark.json"
SOURCE_REPO = json.loads((SCRIPTS.parent / WATERMARK).read_text())["repo"]
DAY = 24 * 3600

FAKE_GH = """#!/bin/sh
case "$1 $2" in
"repo view") echo "$FAKE_GH_REPO" ;;
"api user") echo "$FAKE_GH_LOGIN" ;;
"pr view") [ -n "$FAKE_GH_PR" ] && echo "$FAKE_GH_PR" ;;
*) exit 1 ;;
esac
"""
PR_URL = "https://github.com/acme/app/pull/12"


def pr_json(state: str = "OPEN", idle: int = 0) -> str:
    updated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - idle))
    return json.dumps({"number": 12, "state": state, "updatedAt": updated, "url": PR_URL})


def days_ago(days: int) -> dict[str, str]:
    """The env that dates a commit `days` back, author and committer alike."""
    date = f"@{int(time.time()) - days * DAY} +0000"
    return {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}


def run(args: list[str], cwd: Path, env: dict[str, str]) -> str:
    return subprocess.run(
        args, cwd=cwd, env=env, check=True, capture_output=True, text=True
    ).stdout.strip()


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.source = root / "source.git"
        self.origin = root / "origin.git"
        self.source_work = root / "source-work"
        bin_dir = root / "bin"
        bin_dir.mkdir()
        (bin_dir / "gh").write_text(FAKE_GH)
        (bin_dir / "gh").chmod(0o755)
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": f"url.file://{self.source}.insteadOf",
            "GIT_CONFIG_VALUE_0": f"https://github.com/{SOURCE_REPO}.git",
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.com",
            "FAKE_GH_REPO": "acme/app",
            "FAKE_GH_LOGIN": "alice",
            "FAKE_GH_PR": pr_json(),
        }
        self.env.pop("CLAUDE_CODE_REMOTE_SESSION_ID", None)
        self.env.pop("GIT_AUTHOR_DATE", None)
        self.env.pop("GIT_COMMITTER_DATE", None)

        self.git(root, "init", "-q", "--bare", "-b", "main", str(self.source))
        self.git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(root, "clone", "-q", str(self.source), str(self.source_work))
        self.base = self.source_commit(
            "feat: base",
            {".claude/skills/go/SKILL.md": "go\n", "scripts/a.sh": "a\n"},
        )

    def git(self, cwd: Path, *args: str) -> str:
        return run(["git", *args], cwd, self.env)

    def source_commit(self, message: str, files: dict[str, str]) -> str:
        for path, text in files.items():
            target = self.source_work / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        self.git(self.source_work, "add", "-A")
        self.git(self.source_work, "commit", "-q", "-m", message)
        self.git(self.source_work, "push", "-q", "origin", "HEAD:refs/heads/main")
        return self.git(self.source_work, "rev-parse", "HEAD")

    def adopter(self, last_synced: str | None, name: str = "work") -> Path:
        """Seed origin's trunk with a watermark (none for `None`) and clone it."""
        seed = self.root / f"seed-{name}"
        self.git(self.root, "init", "-q", "-b", "main", str(seed))
        files = {".claude/skills/go/SKILL.md": "go, adapted\n"}
        if last_synced is not None:
            files[WATERMARK] = json.dumps(
                {
                    "repo": SOURCE_REPO,
                    "lastSyncedSha": last_synced,
                    "adopted": [".claude/", {"scripts/": "ported"}],
                    "declined": {},
                }
            )
        for path, text in files.items():
            target = seed / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        self.git(seed, "add", "-A")
        self.git(seed, "commit", "-q", "-m", "seed")
        self.git(seed, "push", "-q", "--force", str(self.origin), "main")
        work = self.root / name
        self.git(self.root, "clone", "-q", str(self.origin), str(work))
        (work / "scripts" / "lib").mkdir(parents=True)
        shutil.copy2(SCRIPTS / "muthur-sync.sh", work / "scripts" / "muthur-sync.sh")
        shutil.copy2(SCRIPTS / "lib" / "gh-repo.sh", work / "scripts" / "lib" / "gh-repo.sh")
        return work

    def sync(
        self, work: Path, *args: str, **env: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "scripts/muthur-sync.sh", *args],
            cwd=work,
            env={**self.env, **env},
            capture_output=True,
            text=True,
        )

    def lock_message(self, last_synced: str) -> str:
        ref = f"refs/heads/muthur-sync-lock-{last_synced[:12]}"
        return self.git(self.origin, "log", "-1", "--format=%B", ref)


class MuthurSyncTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.fx = Fixture(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def nudge(self, work: Path, **env: str) -> str:
        result = self.fx.sync(work, "nudge", **env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def claim(self, work: Path, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        return self.fx.sync(work, "claim", *args, **env)

    def lagging(self) -> Path:
        work = self.fx.adopter(self.fx.base)
        self.fx.source_commit("feat: sharpen go", {".claude/skills/go/SKILL.md": "go 2\n"})
        self.fx.source_commit("feat: add new.sh", {"scripts/new.sh": "new\n"})
        self.fx.source_commit(
            "chore: bookkeeping",
            {WATERMARK: "{}", ".claude/costs/sessions/x.json": "{}"},
        )
        return work


class SilentTest(MuthurSyncTestCase):
    def test_no_watermark_on_the_trunk(self) -> None:
        self.fx.source_commit("feat: more", {"scripts/b.sh": "b\n"})
        self.assertEqual(self.nudge(self.fx.adopter(None)), "")

    def test_placeholder_sha(self) -> None:
        self.assertEqual(self.nudge(self.fx.adopter("<the source's HEAD>")), "")

    def test_the_template_itself(self) -> None:
        work = self.lagging()
        self.assertEqual(self.nudge(work, FAKE_GH_REPO=SOURCE_REPO.upper()), "")

    def test_up_to_date(self) -> None:
        self.assertEqual(self.nudge(self.fx.adopter(self.fx.base)), "")

    def test_a_sync_landed_since_the_last_fetch(self) -> None:
        work = self.lagging()
        tip = self.fx.git(self.fx.source_work, "rev-parse", "HEAD")
        self.fx.adopter(tip, name="elsewhere")
        self.assertEqual(self.nudge(work), "")


class LagTest(MuthurSyncTestCase):
    def test_titles_files_and_adopted(self) -> None:
        out = self.nudge(self.lagging())
        self.assertIn("is 3 commit(s) past the last sync", out)
        self.assertIn("feat: sharpen go", out)
        self.assertIn("chore: bookkeeping", out)
        self.assertIn("  here      .claude/skills/go/SKILL.md", out)
        self.assertIn("  not here  scripts/new.sh", out)
        self.assertNotIn("watermark.json", out)
        self.assertNotIn(".claude/costs/sessions/", out)
        self.assertIn("  .claude/\n  scripts/\n", out)
        self.assertIn("Investigate nothing before the operator says yes", out)
        self.assertIn(
            f"`git ls-remote origin refs/heads/muthur-sync-lock-{self.fx.base[:12]}`", out
        )
        self.assertIn("The offer is a new session.", out)

    def test_single_branch_clone_of_another_branch(self) -> None:
        work = self.lagging()
        self.fx.git(work, "push", "-q", "origin", "HEAD:refs/heads/feature")
        narrow = self.fx.root / "narrow"
        self.fx.git(
            self.fx.root, "clone", "-q", "--single-branch", "-b", "feature",
            str(self.fx.origin), str(narrow),
        )
        shutil.copytree(work / "scripts", narrow / "scripts")
        self.assertIn("is 3 commit(s) past the last sync", self.nudge(narrow))

    def test_cap(self) -> None:
        work = self.fx.adopter(self.fx.base)
        for n in range(50):
            self.fx.source_commit(f"feat: step {n}", {f"scripts/s{n}.sh": "s\n"})
        out = self.nudge(work)
        self.assertIn("is 50 commit(s) past", out)
        self.assertIn("  … and 62 more", out)
        self.assertNotIn("scripts/s0.sh", out)

    def test_unreachable_source(self) -> None:
        work = self.lagging()
        out = self.nudge(work, GIT_CONFIG_KEY_0=f"url.file://{self.fx.root}/gone.git.insteadOf")
        self.assertEqual(len(out.splitlines()), 1, out)
        self.assertIn(f"could not run — could not reach {SOURCE_REPO}.", out)


class LockTest(MuthurSyncTestCase):
    def test_fresh_lock_is_silent(self) -> None:
        work = self.lagging()
        result = self.claim(work)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.nudge(work), "")

    def test_claim_names_the_holder(self) -> None:
        work = self.lagging()
        result = self.claim(work, CLAUDE_CODE_REMOTE_SESSION_ID="cse_01abc")
        self.assertEqual(result.returncode, 0, result.stderr)
        message = self.fx.lock_message(self.fx.base)
        self.assertIn("Claimed-By: @alice", message)
        self.assertIn("Session: https://claude.ai/code/session_01abc", message)

    def test_local_session(self) -> None:
        work = self.lagging()
        self.assertEqual(self.claim(work).returncode, 0)
        self.assertIn("Session: local", self.fx.lock_message(self.fx.base))

    def test_stale_lock_reports_the_holder(self) -> None:
        work = self.lagging()
        result = self.claim(work, CLAUDE_CODE_REMOTE_SESSION_ID="cse_x", **days_ago(2))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.nudge(work)
        self.assertIn("claimed over a day ago, and no PR has been attached", out)
        self.assertIn("PR: none attached", out)
        self.assertIn("Claimed-By: @alice, 2d ago", out)
        self.assertIn("Session: https://claude.ai/code/session_x", out)
        self.assertIn("claim --takeover", out)

    def test_second_claim_is_refused(self) -> None:
        work = self.lagging()
        self.assertEqual(self.claim(work).returncode, 0)
        result = self.claim(work, FAKE_GH_LOGIN="bob")
        self.assertEqual(result.returncode, 3)
        self.assertIn("Claimed-By: @alice", result.stderr)

    def test_concurrent_claims(self) -> None:
        first = self.lagging()
        second = self.fx.root / "second"
        self.fx.git(self.fx.root, "clone", "-q", str(self.fx.origin), str(second))
        shutil.copytree(first / "scripts", second / "scripts")
        procs = [
            subprocess.Popen(
                ["bash", "scripts/muthur-sync.sh", "claim"],
                cwd=work,
                env={**self.fx.env, "FAKE_GH_LOGIN": login},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for work, login in ((first, "alice"), (second, "bob"))
        ]
        codes = sorted(proc.wait() for proc in procs)
        for proc in procs:
            proc.communicate()
        self.assertEqual(codes, [0, 3])

    def test_takeover(self) -> None:
        work = self.lagging()
        self.assertEqual(self.claim(work).returncode, 0)
        result = self.claim(work, "--takeover", FAKE_GH_LOGIN="bob")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Claimed-By: @bob", self.fx.lock_message(self.fx.base))


class AttachTest(MuthurSyncTestCase):
    def attached(self, days: int = 2) -> Path:
        """A lock claimed `days` ago, attached to PR #12 from branch `sync`,
        with the work tree left on `sync`."""
        work = self.lagging()
        self.assertEqual(self.claim(work, **days_ago(days)).returncode, 0)
        self.fx.git(work, "checkout", "-q", "-b", "sync")
        result = self.fx.sync(work, "attach")
        self.assertEqual(result.returncode, 0, result.stderr)
        return work

    def nudge_elsewhere(self, work: Path, **env: str) -> str:
        self.fx.git(work, "checkout", "-q", "main")
        return self.nudge(work, **env)

    def test_records_branch_and_pr_beside_the_claim(self) -> None:
        work = self.attached()
        message = self.fx.lock_message(self.fx.base)
        self.assertIn("Claimed-By: @alice", message)
        self.assertIn("Branch: sync", message)
        self.assertIn("PR: 12", message)
        out = self.nudge_elsewhere(work, FAKE_GH_PR=pr_json("CLOSED"))
        self.assertIn("Claimed-By: @alice, 2d ago", out)

    def test_reattaching_replaces_the_trailers(self) -> None:
        work = self.attached()
        self.fx.git(work, "branch", "-q", "-m", "sync-renamed")
        self.assertEqual(self.fx.sync(work, "attach").returncode, 0)
        message = self.fx.lock_message(self.fx.base)
        self.assertIn("Branch: sync-renamed", message)
        self.assertEqual(message.count("Branch:"), 1)
        self.assertEqual(message.count("PR:"), 1)

    def test_refused_without_a_lock(self) -> None:
        result = self.fx.sync(self.lagging(), "attach")
        self.assertEqual(result.returncode, 1)
        self.assertIn("claim the sync before attaching", result.stderr)

    def test_refused_without_a_pr(self) -> None:
        work = self.lagging()
        self.assertEqual(self.claim(work).returncode, 0)
        result = self.fx.sync(work, "attach", FAKE_GH_PR="")
        self.assertEqual(result.returncode, 1)
        self.assertIn("has no PR", result.stderr)

    def test_silent_on_the_sync_branch(self) -> None:
        work = self.attached(days=30)
        self.assertEqual(self.nudge(work, FAKE_GH_PR=pr_json("CLOSED")), "")

    def test_an_open_pr_awaiting_review_is_alive(self) -> None:
        work = self.attached()
        self.assertEqual(self.nudge_elsewhere(work, FAKE_GH_PR=pr_json(idle=3 * DAY)), "")

    def test_an_idle_pr_is_reported(self) -> None:
        work = self.attached(days=10)
        out = self.nudge_elsewhere(work, FAKE_GH_PR=pr_json(idle=8 * DAY))
        self.assertIn("looks stuck: its PR has seen no activity in over a week.", out)
        self.assertIn(f"PR: #12 — open, last activity 8d ago, {PR_URL}", out)
        self.assertIn("Branch: sync", out)
        self.assertIn("claim --takeover", out)

    def test_a_closed_pr_is_reported(self) -> None:
        work = self.attached()
        out = self.nudge_elsewhere(work, FAKE_GH_PR=pr_json("CLOSED", idle=DAY))
        self.assertIn("looks stuck: its PR was closed without merging.", out)
        self.assertIn("PR: #12 — closed, last activity 24h ago", out)

    def test_claim_refusal_names_the_pr(self) -> None:
        work = self.attached()
        result = self.claim(work, FAKE_GH_LOGIN="bob")
        self.assertEqual(result.returncode, 3)
        self.assertIn("PR: #12", result.stderr)
        self.assertIn("Branch: sync", result.stderr)

    def test_takeover_drops_the_pr(self) -> None:
        work = self.attached()
        self.assertEqual(self.claim(work, "--takeover", FAKE_GH_LOGIN="bob").returncode, 0)
        message = self.fx.lock_message(self.fx.base)
        self.assertIn("Claimed-By: @bob", message)
        self.assertNotIn("PR:", message)


class CloneTest(MuthurSyncTestCase):
    def test_clone_then_refresh(self) -> None:
        work = self.lagging()
        self.assertEqual(self.fx.sync(work, "clone", "tmp/up").returncode, 0)
        tip = self.fx.source_commit("feat: later", {"scripts/c.sh": "c\n"})
        result = self.fx.sync(work, "clone", "tmp/up")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.fx.git(work / "tmp" / "up", "rev-parse", "HEAD"), tip)

    def test_refuses_a_foreign_clone(self) -> None:
        work = self.lagging()
        self.fx.git(work, "clone", "-q", str(self.fx.origin), "tmp/up")
        result = self.fx.sync(work, "clone", "tmp/up")
        self.assertEqual(result.returncode, 1)
        self.assertIn("something other than", result.stderr)


if __name__ == "__main__":
    unittest.main()
