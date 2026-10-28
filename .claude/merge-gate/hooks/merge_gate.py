#!/usr/bin/env python3
"""`UserPromptSubmit` hook: on a bare `/merge`, squash-merge the branch's PR
when every mechanical condition of `/merge`'s gate holds, and stop the prompt
with the merge's line. `.claude/merge-gate/CLAUDE.md` carries the contract.

Stdout is the interface: nothing lets the prompt through to the agent, a
`block` decision stops it, and `additionalContext` tells the model about a
merge it never saw. Stdlib only — Python 3.9+.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# `lib` is one namespace package across both directories, and `lib.github` is
# `scripts/lib/`'s: nothing here may import a `.claude/costs/lib/` module that
# imports that directory's own `lib.github`.
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]
sys.path.append(str(ROOT / ".claude" / "costs"))

import record
from gh_export.api import api_get, api_paginated, fetch_thread_resolution, request
from gh_export.awaiting import awaiting_rows
from gh_export.previous import PreviousExport, previous_export
from lib.filing import PREFIX
from lib.github import AllRoutesFailed, detect_origin_repo, gh_token
from lib.restart import epoch, read_history

COMMAND = "/merge"
# Read by the cold-cache guard, which passes a bare `/merge` to this hook
# unless the event carries it.
DECLINED = "merge_gate_declined"
COLD_CACHE = Path(".claude") / "cold-cache" / "hooks" / "cold_cache.py"
TEST_ON_GH = ".claude/skills/test-on-gh/SKILL.md"
# GitHub's compare lists at most this many files, so a full page may hide more.
COMPARE_FILES_CAP = 300
PASSING = ("success", "neutral", "skipped")


@dataclass(frozen=True)
class Merged:
    pr: int
    base: str
    sha: str

    def line(self) -> str:
        return f"✅ Merged #{self.pr} into {self.base} at {self.sha[:7]}"


@dataclass
class GitHub:
    """The gate's every read of GitHub and its one write, which is where the
    tests stand in for the network."""

    repo: str
    token: str

    def get(self, path: str) -> Any:
        return api_get(f"repos/{self.repo}/{path}", self.token)

    def pages(self, path: str) -> List[Any]:
        return api_paginated(f"repos/{self.repo}/{path}", self.token)

    def file(self, path: str, ref: str) -> Optional[str]:
        url = f"https://api.github.com/repos/{self.repo}/contents/{path}?ref={ref}"
        try:
            body, _ = request(url, self.token, "application/vnd.github.raw")
        except AllRoutesFailed as exc:
            if any(f.status.startswith("404") for f in exc.failures):
                return None
            raise
        return body.decode("utf-8")

    def resolution(self, number: int) -> Dict[int, bool]:
        return fetch_thread_resolution(self.repo, number, self.token)

    def previous(self, number: int, pr: Dict[str, Any]) -> Optional[PreviousExport]:
        return previous_export(Path("docs") / "pr" / str(number) / "pr.md", pr, self.repo, self.token)

    def merge(self, number: int, squash: record.Squash, head: str, body_file: Path) -> bool:
        """`--match-head-commit` refuses a head that moved since the checks."""
        body_file.parent.mkdir(parents=True, exist_ok=True)
        body_file.write_text(squash.body, encoding="utf-8")
        command = ["gh", "pr", "merge", str(number), "-R", self.repo, "--squash", "--subject", squash.subject]
        command += ["--body-file", str(body_file), "--match-head-commit", head]
        done = subprocess.run(command, capture_output=True, text=True, check=False)
        if done.returncode != 0:
            print(f"merge-gate: GitHub refused the merge: {done.stderr.strip()}", file=sys.stderr)
        return done.returncode == 0


def still_a_stub(github: GitHub, head: str) -> bool:
    """`/test-on-gh`'s frontmatter on the PR head still says STUB."""
    text = github.file(TEST_ON_GH, head)
    if text is None or not text.startswith("---\n"):
        return False
    return "STUB" in text.split("\n---", 2)[0]


def ledger_rows_only(github: GitHub, attested: str, head: str) -> bool:
    compare = github.get(f"compare/{attested}...{head}")
    files = compare.get("files") or []
    return (
        compare["status"] in ("ahead", "identical")
        and len(files) < COMPARE_FILES_CAP
        and all(f["filename"].startswith(f"{PREFIX}/") for f in files)
    )


def checks_pass(github: GitHub, head: str, ci_runs: bool) -> bool:
    """No check runs or statuses at all pass only where the attestation says
    nothing runs on a PR."""
    runs: List[Dict[str, Any]] = []
    while True:
        page = github.get(f"commits/{head}/check-runs?per_page=100&page={len(runs) // 100 + 1}")
        runs.extend(page["check_runs"])
        if not page["check_runs"] or len(runs) >= page["total_count"]:
            break
    statuses = github.get(f"commits/{head}/status")["statuses"]
    if not runs and not statuses:
        return not ci_runs
    return all(r["status"] == "completed" and r["conclusion"] in PASSING for r in runs) and all(
        s["state"] == "success" for s in statuses
    )


def attempt(github: GitHub, branch: str, scratch: Path) -> Optional[Merged]:
    """The merge, when `merge.md` § "Step 8 — the gate" holds by every fact
    GitHub has; None at the first that fails. Cheapest checks first."""
    owner = github.repo.split("/", 1)[0]
    pulls = github.get(f"pulls?state=open&head={quote(owner)}:{quote(branch, safe='')}")
    if len(pulls) != 1 or pulls[0]["draft"]:
        return None
    number = pulls[0]["number"]
    pr = github.get(f"pulls/{number}")
    head, base = pr["head"]["sha"], pr["base"]["ref"]
    comments = github.pages(f"issues/{number}/comments")
    bodies = [c.get("body") or "" for c in comments]

    attested = record.attestation(bodies)
    if attested is None or (attested.claims_stub and not still_a_stub(github, head)):
        return None
    if not ledger_rows_only(github, attested.sha, head):
        return None
    if github.get(f"compare/{quote(base, safe='/')}...{head}")["behind_by"] != 0:
        return None
    if pr["mergeable"] is not True or pr["mergeable_state"] != "clean":
        return None
    if not checks_pass(github, head, attested.ci_runs):
        return None
    reviews = github.pages(f"pulls/{number}/reviews")
    review_comments = github.pages(f"pulls/{number}/comments")
    resolved = github.resolution(number)
    previous = github.previous(number, pr)
    if awaiting_rows(comments, reviews, review_comments, resolved, False, previous):
        return None
    squash = record.squash(bodies, pr["title"], number)
    if squash is None or not github.merge(number, squash, head, scratch / f"{number}.body"):
        return None
    landed = github.get(f"pulls/{number}")
    return Merged(number, base, landed["merge_commit_sha"]) if landed["merged"] else None


@dataclass(frozen=True)
class Note:
    """`tmp/merge-gate/<session>.json`: a merge whose blocked prompt never
    reached the model, told to it until a response lands after it."""

    dir: Path
    session: str

    @property
    def path(self) -> Path:
        return self.dir / f"{self.session}.json"

    def write(self, merged: Merged) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        fields = {"pr": merged.pr, "base": merged.base, "sha": merged.sha, "written_at": time.time()}
        self.path.write_text(json.dumps(fields))

    def pending(self, transcript: Path) -> Optional[str]:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text())
        history = read_history(transcript) if transcript.is_file() else None
        answered = epoch(history.last.timestamp) if history else None
        if answered is not None and answered > data["written_at"]:
            self.path.unlink()
            return None
        merged = Merged(data["pr"], data["base"], data["sha"])
        return (
            f"Before this prompt, the merge gate squash-merged #{merged.pr} into {merged.base}"
            f" at {merged.sha[:7]}; the PR is no longer a place to do work."
        )


def cold_cache(event: Dict[str, Any], project: Path) -> str:
    """The guard's verdict on the prompt this hook declined, which it left to
    this hook rather than race it."""
    guard = project / COLD_CACHE
    if not guard.is_file():
        return ""
    payload = json.dumps({**event, DECLINED: True})
    done = subprocess.run([sys.executable, str(guard)], input=payload, capture_output=True, text=True, check=False)
    sys.stderr.write(done.stderr)
    return done.stdout.strip()


def git_branch(project: Path) -> str:
    done = subprocess.run(["git", "branch", "--show-current"], cwd=project, capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else ""


def connect(project: Path) -> Optional[GitHub]:
    repo = detect_origin_repo(project)
    return GitHub(repo, gh_token()) if repo else None


def on_prompt(
    event: Dict[str, Any], project: Path, note: Note, connector: Callable[[Path], Optional[GitHub]] = connect
) -> Optional[Dict[str, Any]]:
    """What the hook prints, or None to let the prompt through untouched."""
    if (event.get("prompt") or "").strip() == COMMAND:
        merged = None
        try:
            github = connector(project)
            branch = git_branch(project)
            if github is not None and branch:
                merged = attempt(github, branch, project / "tmp" / "merge-gate")
        except (Exception, SystemExit):
            # A decline, not a swallowed error: the agent's `/merge` re-checks
            # everything this checked and meets the same failure, which it reports.
            traceback.print_exc()
        if merged is not None:
            note.write(merged)
            out = {"hookEventName": "UserPromptSubmit", "suppressOriginalPrompt": True}
            return {"decision": "block", "reason": merged.line(), "hookSpecificOutput": out}
        guard = cold_cache(event, project)
        if guard:
            return json.loads(guard)
    told = note.pending(Path(event.get("transcript_path") or ""))
    if told is None:
        return None
    return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": told}}


def main() -> None:
    event = json.load(sys.stdin)
    session = event.get("session_id") or ""
    if event.get("hook_event_name") != "UserPromptSubmit" or not session or "/" in session or session.startswith("."):
        return
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or ROOT)
    # The previous export is read relative to the working directory.
    os.chdir(project)
    out = on_prompt(event, project, Note(project / "tmp" / "merge-gate", session))
    if out is not None:
        print(json.dumps(out))


if __name__ == "__main__":
    main()
