"""The `cost-ledger` branch: the rows' source of truth, an orphan branch on
`origin` holding them where `lib/filing.py` places them.

Every write is a commit built in a throwaway index on the ledger's tip and
pushed without force, so two sessions racing for the tip cannot lose each
other's row: the push that loses re-reads the tip and builds again, taking the
next ordinal where the winner took the one it planned on.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Callable, Collection, Dict, List, Mapping, Optional, Sequence, Tuple

from lib.estimate_model import REPO_RATES, SHARED_RATES, Rates, parse_rates, with_added_roles
from lib.filing import PREFIX, Filing, is_row, refile, session_of
from lib.rows import ROOT, SESSIONS, SessionCost, parse_session_cost, tree_copies, union
from lib.shape import ShapeError

BRANCH = "cost-ledger"
REMOTE_REF = f"refs/remotes/origin/{BRANCH}"
# The repository's own estimate roles, beside the rows they rate and nowhere
# else: a copy per branch would leave rows only an unmerged branch could rate.
RATES_PATH = (SESSIONS.parent / REPO_RATES).relative_to(ROOT).as_posix()
RATES_ON_LEDGER = f"{BRANCH}:{RATES_PATH}"
# Where `backfill` fetches every PR's head, apart from anything a person reads.
PR_REFS = "refs/costs-pr"
TRIES = 3


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


def rates_text(rev: Optional[str]) -> Optional[str]:
    return text_at(rev, RATES_PATH) if rev else None


def shared_rates() -> Rates:
    return parse_rates((SESSIONS.parent / SHARED_RATES).read_text(encoding="utf-8"))


def ledger_rates(rev: Optional[str]) -> Rates:
    """This checkout's `rates.json` plus the roles the ledger's table at `rev`
    adds; the shared table alone where `rev` or its table is missing."""
    shared = shared_rates()
    text = rates_text(rev)
    return shared if text is None else with_added_roles(shared, text, RATES_ON_LEDGER)


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


def listing(rev: Optional[str]) -> List[str]:
    """The paths under `sessions/` at `rev`, names only."""
    if rev is None or resolve(rev) is None:
        return []
    return git("ls-tree", "-r", "--name-only", "--full-tree", rev, "--", PREFIX).splitlines()


def held_paths(rev: Optional[str], session_id: str) -> List[str]:
    return [path for path in listing(rev) if is_row(path) and session_of(path) == session_id]


def copies(session_id: str) -> List[Tuple[str, str]]:
    """`(where, text)` for each copy of the session's row: the tree's and the
    local copy of the ledger's."""
    found = [(str(path), path.read_text(encoding="utf-8")) for path in tree_copies(session_id)]
    held = [(path, text_at(REMOTE_REF, path)) for path in held_paths(REMOTE_REF, session_id)]
    return found + [(f"{BRANCH}:{path}", text) for path, text in held if text is not None]


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


def commit(parent: Optional[str], rows: Mapping[str, Optional[str]], message: str) -> str:
    """A commit of `rows`, path to text or to None for a file it removes, on
    `parent` (an orphan root where None), built in a throwaway index so whatever
    the agent has staged stays out of it. `commit-tree` runs no commit hooks,
    which suits a file no formatter should rewrite, and signs only when asked,
    so `-S` follows `commit.gpgsign`."""
    index = ROOT / "tmp" / f"ledger-index.{os.getpid()}"
    index.parent.mkdir(parents=True, exist_ok=True)
    env = {"GIT_INDEX_FILE": str(index)}
    try:
        git("read-tree", *([parent] if parent else ["--empty"]), env=env)
        for path, text in rows.items():
            if text is None:
                git("update-index", "--force-remove", path, env=env)
                continue
            blob = git("hash-object", "-w", "--stdin", "--path", path, input=text).strip()
            git("update-index", "--add", "--cacheinfo", f"100644,{blob},{path}", env=env)
        tree = git("write-tree", env=env).strip()
    finally:
        index.unlink(missing_ok=True)
    signed = run("config", "--type=bool", "commit.gpgsign").stdout.decode().strip() == "true"
    return git(
        "commit-tree", *(["-S"] if signed else []), *(["-p", parent] if parent else []), "-m", message, tree
    ).strip()


Plan = Callable[[Optional[str]], Tuple[Dict[str, Optional[str]], str]]


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


def filed(rev: Optional[str], incoming: Sequence[str] = ()) -> Filing:
    """`refile` over the ledger at `rev`, reading a row only where it has to."""

    def read(path: str) -> str:
        text = text_at(rev or "", path)
        if text is None:
            raise LedgerError(f"{rev}:{path} is listed and does not read")
        return text

    return refile(listing(rev), read, incoming)


def _with_refiled(subject: str, filing: Filing, own: Collection[str]) -> str:
    moved = {session_of(path) for path in filing.changes if is_row(path)} - set(own)
    return subject if not moved else f"{subject}; re-file {_count(len(moved))}"


def append_row(text: str) -> str:
    """File the row on the ledger's tip, with whatever else there is not at
    its place, and push it; the path the row is filed at."""
    session = parse_session_cost(text, "row").session_id
    placed: List[str] = []

    def plan(tip: Optional[str]) -> Tuple[Dict[str, Optional[str]], str]:
        filing = filed(tip, [text])
        placed[:] = [filing.placed[session]]
        held = sorted(held_paths(tip, session), key=lambda path: path != placed[0])
        before = text_at(tip, held[0]) if tip and held else None
        return filing.changes, _with_refiled(row_subject(before, text), filing, {session})

    append(plan)
    return placed[0]


def path_for(text: str) -> str:
    """Where the local copy of the ledger, as last fetched, would file the row."""
    return filed(REMOTE_REF, [text]).placed[parse_session_cost(text, "row").session_id]


def every_ref() -> List[str]:
    """Every branch on `origin` and every PR's head, fetched: between them they
    hold every row a session ever committed, merged or not."""
    git("fetch", "-q", "origin", "+refs/heads/*:refs/remotes/origin/*", f"+refs/pull/*/head:{PR_REFS}/*")
    listed = git("for-each-ref", "--format=%(refname)", "refs/remotes/origin", PR_REFS).split()
    return [ref for ref in listed if ref not in (REMOTE_REF, "refs/remotes/origin/HEAD")]


def _count(n: int) -> str:
    return f"{n} session row{'' if n == 1 else 's'}"


def _roles(text: str) -> Optional[object]:
    try:
        return json.loads(text).get("roles")
    except (ValueError, AttributeError):
        return None


def _rates_carry(tree: Optional[str], held: Optional[str]) -> Optional[str]:
    """The tree's `rates.repo.json` where the ledger has none; nothing where the
    two agree. Where they differ, neither is picked: which multiplier a role's
    rows were booked against is the operator's to say."""
    if tree is None:
        return None
    if held is None:
        return tree
    tree_roles, held_roles = _roles(tree), _roles(held)
    if tree_roles is not None and tree_roles == held_roles:
        return None
    if isinstance(tree_roles, dict) and isinstance(held_roles, dict):
        differ = sorted(n for n in {*tree_roles, *held_roles} if tree_roles.get(n) != held_roles.get(n))
        what = f"they differ on {', '.join(f'`{n}`' for n in differ)}"
    else:
        what = "one of them does not parse"
    raise LedgerError(
        f"{RATES_PATH} is in the tree and on {BRANCH}, and {what}; settle {BRANCH}'s with"
        " `estimate.py role set` / `role drop`, then `git rm` the tree's"
    )


def backfill(refs: Sequence[str]) -> Tuple[int, Optional[str]]:
    """Carry into the ledger every row `refs` hold that it lacks or holds
    older, and the tree's `rates.repo.json` where the ledger has none: how many
    sessions the ledger holds after, and the commit, if one was needed. A second
    run commits nothing."""
    found = [(path, text) for ref in refs for path, text in rows_at(ref)]
    tree_rates = ROOT / RATES_PATH
    tree_text = tree_rates.read_text(encoding="utf-8") if tree_rates.is_file() else None
    held_ids: List[str] = []

    def parsed(item: Tuple[str, str]) -> SessionCost:
        return parse_session_cost(item[1], item[0])

    def plan(tip: Optional[str]) -> Tuple[Dict[str, Optional[str]], str]:
        held = dict(rows_at(tip)) if tip else {}
        # The held copy comes first, so a tie keeps it.
        winners = union([*held.items(), *found], parsed)
        held_ids[:] = [parsed(item).session_id for item in winners]
        carried = [(path, text) for path, text in winners if held.get(path) != text]
        filing = refile(list(held), held.__getitem__, [text for _, text in carried])
        changes = filing.changes
        message = f"chore: carry {_count(len(carried))}"
        rates = _rates_carry(tree_text, rates_text(tip))
        if rates is not None:
            changes[RATES_PATH] = rates
            message += " and the estimate roles"
        return changes, _with_refiled(f"{message} into the ledger", filing, {parsed(item).session_id for item in carried})

    try:
        built = append(plan)
    except ShapeError as error:
        raise LedgerError(f"a row on one of the refs does not parse: {error}") from error
    return len(held_ids), built
