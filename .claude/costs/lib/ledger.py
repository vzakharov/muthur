"""The `cost-ledger` branch: the rows' source of truth, an orphan branch on
`origin` holding them at the same paths a working tree does.

Every write is a commit built in a throwaway index on the ledger's tip and
pushed without force, so two sessions racing for the tip cannot lose each
other's row: the push that loses re-reads the tip and builds again. Rows never
collide, one file being one session.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, TypeVar

from lib.rows import ROOT, SESSIONS, SessionCost, parse_session_cost
from lib.shape import ShapeError

BRANCH = "cost-ledger"
REMOTE_REF = f"refs/remotes/origin/{BRANCH}"
PREFIX = SESSIONS.relative_to(ROOT).as_posix()
# Where `backfill` fetches every PR's head, apart from anything a person reads.
PR_REFS = "refs/costs-pr"
TRIES = 3

T = TypeVar("T")


class LedgerError(RuntimeError):
    """A ledger read or write git refused, in git's words."""


def run(*args: str, input: Optional[bytes] = None, env: Optional[Mapping[str, str]] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        input=input,
        capture_output=True,
        env=None if env is None else {**os.environ, **env},
        check=False,
    )


def stderr(done: subprocess.CompletedProcess) -> str:
    return done.stderr.decode(errors="replace").strip()


def git(*args: str, input: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> str:
    done = run(*args, input=None if input is None else input.encode(), env=env)
    if done.returncode != 0:
        raise LedgerError(f"git {args[0]}: {stderr(done)}")
    return done.stdout.decode()


def resolve(rev: str) -> Optional[str]:
    done = run("rev-parse", "-q", "--verify", f"{rev}^{{commit}}")
    return done.stdout.decode().strip() if done.returncode == 0 else None


def text_at(rev: str, path: str) -> Optional[str]:
    done = run("cat-file", "blob", f"{rev}:{path}")
    return done.stdout.decode() if done.returncode == 0 else None


def fetch() -> Optional[str]:
    """The ledger's tip on `origin`, fetched into `REMOTE_REF`; None where
    `origin` has no ledger yet."""
    listed = run("ls-remote", "--exit-code", "origin", f"refs/heads/{BRANCH}")
    if listed.returncode == 2:
        return None
    if listed.returncode != 0:
        raise LedgerError(f"reading {BRANCH} on origin: {stderr(listed)}")
    git("fetch", "-q", "origin", f"+refs/heads/{BRANCH}:{REMOTE_REF}")
    return resolve(REMOTE_REF)


def rows_at(rev: str) -> List[Tuple[str, str]]:
    """`(path, text)` for every row `rev` holds, in one `ls-tree` and one
    `cat-file --batch` however many there are."""
    if resolve(rev) is None:
        return []
    listed = []
    for line in git("ls-tree", "-r", "--full-tree", rev, "--", PREFIX).splitlines():
        meta, path = line.split("\t", 1)
        _, kind, blob = meta.split()
        if kind == "blob" and path.endswith(".json"):
            listed.append((blob, path))
    if not listed:
        return []
    done = run("cat-file", "--batch", input="".join(f"{blob}\n" for blob, _ in listed).encode())
    if done.returncode != 0:
        raise LedgerError(f"git cat-file: {stderr(done)}")
    out, at, rows = done.stdout, 0, []
    for _, path in listed:
        header_end = out.index(b"\n", at)
        size = int(out[at:header_end].split()[2])
        start = header_end + 1
        rows.append((path, out[start : start + size].decode()))
        at = start + size + 1
    return rows


def recency(row: SessionCost) -> Tuple[str, str]:
    """The later of two copies of a row is the one that saw more of the
    session, or, of two that saw the same, the one whose estimate was set later
    — which is how an estimate edited onto a finished session's row wins."""
    return row.last_response_at or "", row.estimate.at if row.estimate is not None else ""


def union(items: Iterable[T], row_of: Callable[[T], SessionCost]) -> List[T]:
    """One item per session id, the latest by `recency`; a tie keeps the first."""
    kept: Dict[str, Tuple[T, SessionCost]] = {}
    for item in items:
        row = row_of(item)
        held = kept.get(row.session_id)
        if held is None or recency(row) > recency(held[1]):
            kept[row.session_id] = (item, row)
    return [item for item, _ in kept.values()]


def path_of(session_id: str) -> Optional[str]:
    """Where the local copy of the ledger files the session's row, if it has
    one."""
    if resolve(REMOTE_REF) is None:
        return None
    listed = git("ls-tree", "-r", "--name-only", "--full-tree", REMOTE_REF, "--", PREFIX).splitlines()
    return next((path for path in listed if path.endswith(f"/{session_id}.json")), None)


def copies(session_id: str) -> List[Tuple[str, str]]:
    """`(where, text)` for each copy of the session's row: the tree's and the
    local copy of the ledger's."""
    found = [(str(path), path.read_text(encoding="utf-8")) for path in sorted(SESSIONS.glob(f"*/{session_id}.json"))]
    held = path_of(session_id)
    text = text_at(REMOTE_REF, held) if held is not None else None
    return found + ([(f"{BRANCH}:{held}", text)] if text is not None else [])


def latest_row(session_id: str) -> Optional[SessionCost]:
    """The later of the session's copies, by `recency`."""
    rows = union((parse_session_cost(text, where) for where, text in copies(session_id)), lambda row: row)
    return rows[0] if rows else None


def _cost(text: Optional[str], *keys: str) -> Optional[float]:
    value = json.loads(text) if text is not None else None
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def row_subject(before: Optional[str], after: str) -> str:
    """A turn's spend, measured from the row as last committed; a row the
    parent lacks is a session's first, and only that subject names what the
    session spent before it acted, which the first turn settles."""
    now = _cost(after, "total", "costUsd") or 0.0
    if before is not None:
        was = _cost(before, "total", "costUsd") or 0.0
        return f"chore: session cost +{now - was:.2f} USD, total {now:.2f} USD"
    oriented = _cost(after, "orientation", "spend", "costUsd")
    return f"chore: session cost (new) {now:.2f} USD" + (
        "" if oriented is None else f", incl. {oriented:.2f} USD orientation"
    )


def commit(parent: Optional[str], rows: Mapping[str, str], message: str) -> str:
    """A commit of `rows`, path to text, on `parent` (an orphan root where
    None), built in a throwaway index so whatever the agent has staged stays out
    of it. `commit-tree` runs no commit hooks, which suits a file no formatter
    should rewrite, and signs only when asked, so `-S` follows
    `commit.gpgsign`."""
    index = ROOT / "tmp" / f"ledger-index.{os.getpid()}"
    index.parent.mkdir(parents=True, exist_ok=True)
    env = {"GIT_INDEX_FILE": str(index)}
    try:
        git("read-tree", *([parent] if parent else ["--empty"]), env=env)
        for path, text in rows.items():
            blob = git("hash-object", "-w", "--stdin", "--path", path, input=text).strip()
            git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = git("write-tree", env=env).strip()
    finally:
        index.unlink(missing_ok=True)
    signed = run("config", "--type=bool", "commit.gpgsign").stdout.decode().strip() == "true"
    return git(
        "commit-tree", *(["-S"] if signed else []), *(["-p", parent] if parent else []), "-m", message, tree
    ).strip()


Plan = Callable[[Optional[str]], Tuple[Dict[str, str], str]]


def append(plan: Plan) -> Optional[str]:
    """Commit onto the ledger's tip what `plan` asks of that tip — the rows
    that differ from it and the message — and push it, re-reading the tip on a
    rejected push. None when the tip already holds every row."""
    error = ""
    for _ in range(TRIES):
        tip = fetch()
        rows, message = plan(tip)
        if not rows:
            return None
        built = commit(tip, rows, message)
        pushed = run("push", "-q", "origin", f"{built}:refs/heads/{BRANCH}")
        if pushed.returncode == 0:
            git("update-ref", REMOTE_REF, built)
            return built
        error = stderr(pushed)
    raise LedgerError(f"pushing to {BRANCH} failed {TRIES} times: {error}")


def row_change(parent: Optional[str], path: str, text: str) -> Tuple[Dict[str, str], str]:
    """What committing `text` at `path` onto `parent` changes — nothing where
    `parent` already holds it — and the commit's message."""
    before = text_at(parent, path) if parent else None
    return ({} if before == text else {path: text}), row_subject(before, text)


def append_row(path: str, text: str) -> Optional[str]:
    return append(lambda tip: row_change(tip, path, text))


def every_ref() -> List[str]:
    """Every branch on `origin` and every PR's head, fetched: between them they
    hold every row a session ever committed, merged or not."""
    git("fetch", "-q", "origin", "+refs/heads/*:refs/remotes/origin/*", f"+refs/pull/*/head:{PR_REFS}/*")
    listed = git("for-each-ref", "--format=%(refname)", "refs/remotes/origin", PR_REFS).split()
    return [ref for ref in listed if ref not in (REMOTE_REF, "refs/remotes/origin/HEAD")]


def _count(n: int) -> str:
    return f"{n} session row{'' if n == 1 else 's'}"


def backfill(refs: Sequence[str]) -> Tuple[int, Optional[str]]:
    """Carry into the ledger every row `refs` hold that it lacks or holds
    older: how many sessions the ledger holds after, and the commit, if one was
    needed. A second run commits nothing."""
    found = [(path, text) for ref in refs for path, text in rows_at(ref)]
    held_ids: List[str] = []

    def parsed(item: Tuple[str, str]) -> SessionCost:
        return parse_session_cost(item[1], item[0])

    def plan(tip: Optional[str]) -> Tuple[Dict[str, str], str]:
        held = dict(rows_at(tip)) if tip else {}
        winners = union([*held.items(), *found], parsed)
        held_ids[:] = [parsed(item).session_id for item in winners]
        carried = {path: text for path, text in winners if held.get(path) != text}
        return carried, f"chore: carry {_count(len(carried))} into the ledger"

    try:
        built = append(plan)
    except ShapeError as error:
        raise LedgerError(f"a row on one of the refs does not parse: {error}") from error
    return len(held_ids), built
