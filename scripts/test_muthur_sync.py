#!/usr/bin/env python3
"""Tests for `scripts/muthur-sync.sh`, run with real git against local bare
repositories standing in for the source and for the adopter's origin.

The source's GitHub URL is redirected to its bare repo through
`url.<file>.insteadOf` in `GIT_CONFIG_*`, and a fake `gh` on `PATH` answers the
two calls the script makes, so the script under test carries no test-only knob.

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
*) exit 1 ;;
esac
"""


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
        }
        self.env.pop("CLAUDE_CODE_REMOTE_SESSION_ID", None)
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

    def lock_ref(self, last_synced: str) -> str:
        return f"refs/heads/muthur-sync-lock-{last_synced[:12]}"

    def lock_message(self, last_synced: str) -> str:
        return self.git(self.origin, "log", "-1", "--format=%B", self.lock_ref(last_synced))


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

    def lock_sha(self) -> str:
        ref = self.fx.lock_ref(self.fx.base)
        return self.fx.git(self.fx.origin, "for-each-ref", "--format=%(objectname)", ref)

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
        self.assertNotIn("ride-along is unavailable", out)

    def test_cap(self) -> None:
        work = self.fx.adopter(self.fx.base)
        for n in range(50):
            self.fx.source_commit(f"feat: step {n}", {f"scripts/s{n}.sh": "s\n"})
        out = self.nudge(work)
        self.assertIn("is 50 commit(s) past", out)
        self.assertIn("  … and 62 more", out)
        self.assertNotIn("scripts/s0.sh", out)

    def test_branch_watermark_behind_the_trunk(self) -> None:
        work = self.lagging()
        (work / WATERMARK).write_text(json.dumps({"lastSyncedSha": "0" * 40}))
        self.assertIn("ride-along is unavailable on", self.nudge(work))

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
        old = f"@{int(time.time()) - 2 * DAY} +0000"
        result = self.claim(work, GIT_COMMITTER_DATE=old, CLAUDE_CODE_REMOTE_SESSION_ID="cse_x")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = self.nudge(work)
        self.assertIn("claimed over a day ago", out)
        self.assertIn("Claimed-By: @alice", out)
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

    def test_reclaim_by_the_holder(self) -> None:
        work = self.lagging()
        session = {"CLAUDE_CODE_REMOTE_SESSION_ID": "cse_a"}
        self.assertEqual(self.claim(work, **session).returncode, 0)
        before = self.lock_sha()
        result = self.claim(work, **session)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already holds", result.stdout)
        self.assertEqual(self.lock_sha(), before)

    def test_another_session_of_the_same_operator_is_refused(self) -> None:
        work = self.lagging()
        self.assertEqual(self.claim(work, CLAUDE_CODE_REMOTE_SESSION_ID="cse_a").returncode, 0)
        self.assertEqual(self.claim(work, CLAUDE_CODE_REMOTE_SESSION_ID="cse_b").returncode, 3)


class ReleaseTest(MuthurSyncTestCase):
    def release(self, work: Path, **env: str) -> subprocess.CompletedProcess[str]:
        return self.fx.sync(work, "release", **env)

    def test_release_frees_the_lock(self) -> None:
        work = self.lagging()
        self.assertEqual(self.claim(work).returncode, 0)
        result = self.release(work)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.lock_sha(), "")
        self.assertIn("is 3 commit(s) past", self.nudge(work))

    def test_someone_elses_lock_is_kept(self) -> None:
        work = self.lagging()
        self.assertEqual(self.claim(work).returncode, 0)
        result = self.release(work, FAKE_GH_LOGIN="bob")
        self.assertEqual(result.returncode, 3)
        self.assertIn("Claimed-By: @alice", result.stderr)
        self.assertNotEqual(self.lock_sha(), "")

    def test_nothing_to_release(self) -> None:
        result = self.release(self.lagging())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("nothing to release", result.stdout)


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
