"""The fixture every suite that drives a cost hook, or the ledger over a real
repository, builds on.

Its name keeps the `test_*.py` glob in `scripts/vet.sh` from running it as a
suite. Importing it needs this directory on `sys.path`, which running a suite by
path provides.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from test_pricing import PRICE_TABLE, response

COSTS = Path(__file__).resolve().parent
LIB = COSTS.parent / "hooks" / "lib.sh"
STOP_HOOK = ".claude/costs/hooks/stop-session-cost.sh"
SESSIONS = ".claude/costs/sessions"
SESSION = "sess"
ROW = f"{SESSIONS}/2026-03/{SESSION}.json"


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
            ignore=shutil.ignore_patterns("sessions", "__pycache__", "test_*.py", "hook_clone.py"),
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

    def ledger_commit(self, parent: Optional[str], rows: Dict[str, Optional[str]], message: str = "rows") -> str:
        """A commit of `rows` on `parent` (an orphan root where None), built by
        the clone's own `lib.ledger_branch.commit` and not pushed."""
        built = subprocess.run(
            [
                "python3",
                "-c",
                "import json, sys\n"
                "from lib.ledger_branch import commit\n"
                "print(commit(sys.argv[1] or None, json.loads(sys.argv[2]), sys.argv[3]))",
                parent or "",
                json.dumps(rows),
                message,
            ],
            cwd=self.root / ".claude" / "costs",
            capture_output=True,
            text=True,
            check=True,
            env=self.env(),
        )
        return built.stdout.strip()

    def other_row(self, parent: str) -> str:
        """Another session's row committed on `parent`, and not pushed."""
        return self.ledger_commit(parent, {f"{SESSIONS}/2026-03/other.json": json.dumps({"sessionId": "other"})})

    def answer(self, *comments: str) -> None:
        """GitHub's answer to the attestation query: one PR carrying `comments`."""
        nodes = [{"body": body} for body in comments]
        pulls = {"nodes": [{"comments": {"nodes": nodes}}]}
        self.answer_file.write_text(json.dumps({"data": {"repository": {"pullRequests": pulls}}}))

    @property
    def cached(self) -> Path:
        """Where `lib/finalized.py` caches the branch's attestation."""
        return self.root / "tmp" / "costs" / "finalized" / "feature"

    def cache(self, sha: str) -> Path:
        """`sha` cached as the branch's attestation, the way a yes from GitHub
        leaves it."""
        self.cached.parent.mkdir(parents=True, exist_ok=True)
        self.cached.write_text(sha + "\n")
        return self.cached

    def stage_work(self) -> None:
        """Something else for a commit to take, staged by the agent."""
        (self.root / "work.txt").write_text("in flight\n")
        self.git("add", "work.txt")

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

    def hook(self, path: str, payload: Dict[str, object]) -> subprocess.CompletedProcess:
        """The hook at `path` run as the harness runs it, `payload` on stdin."""
        return subprocess.run(
            [str(self.root / path)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**self.env(), "CLAUDE_PROJECT_DIR": str(self.root)},
        )

    def stop(self, *, active: bool = False) -> subprocess.CompletedProcess:
        return self.hook(
            STOP_HOOK,
            {
                "hook_event_name": "Stop",
                "session_id": SESSION,
                "transcript_path": str(self.transcript),
                "cwd": str(self.root),
                "stop_hook_active": active,
            },
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
        [row] = (self.root / ".claude" / "costs" / "sessions").glob(f"*/{SESSION}.json")
        return row

    def status(self) -> str:
        return self.git("status", "--porcelain")

    def commits(self) -> int:
        return int(self.git("rev-list", "--count", "HEAD"))

    def files_in(self, rev: str) -> List[str]:
        return self.git("show", "--name-only", "--format=", rev).splitlines()
