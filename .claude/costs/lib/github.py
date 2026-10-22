"""The ledger of every repository the `gh` user can see, read off each one's
`cost-ledger` branch and default branch through GitHub's GraphQL API, with no
clone of anything. The default branch's side counts a repository whose rows are
still in its tree.

A repository qualifies by carrying a ledger, not muthur's watermark: the
ledger is opt-in for adopters, so a watermark alone has nothing to count. The
watermark is read only to name the adopters that opted out, so a repository
missing from the report has a visible reason.

Every call goes through one `Transport`, which is where the tests stand in
for the network.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Collection, Dict, List, Mapping, Optional, Sequence, Tuple

from lib.ledger_branch import BRANCH, RATES_PATH, union
from lib.rows import SessionCost, reshape
from lib.shape import ShapeError, read_object, read_string, required

LEDGER = ".claude/costs/sessions"
# A row may name a role only its own repository rates, so the report reads that
# repository's table, off the ledger beside the rows.
ADDED_ROLES = f"refs/heads/{BRANCH}:{RATES_PATH}"
WATERMARK = ".claude/skills/update-muthur/watermark.json"
# A page of 100 answered HTTP 502 on a token reaching 357 repositories; 40 did not.
PAGE = 40
# Month trees per query, each arriving as its rows' text, a few kB a row.
BATCH = 5
RETRIES = 3
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
MONTH = re.compile(r"\d{4}-\d{2}")
AFFILIATIONS = "[OWNER, COLLABORATOR, ORGANIZATION_MEMBER]"
# Where a repository's rows can be, keyed by the alias each is queried under.
SIDES = {"ledger": f"refs/heads/{BRANCH}", "tree": "HEAD"}

# `(query, variables)` to the response, `data` and `errors` as GitHub sent them.
Transport = Callable[[str, Mapping[str, Any]], Dict[str, Any]]
Sleep = Callable[[float], None]
Progress = Callable[[str], None]


class GitHubError(RuntimeError):
    """A query GitHub refused or failed, in GitHub's words."""


class ServerError(GitHubError):
    """A 5xx, which a retry can clear."""


def gh_transport(query: str, variables: Mapping[str, Any]) -> Dict[str, Any]:
    """Through `gh` rather than raw HTTP: it carries the operator's auth, and a
    cloud session's proxy along with it."""
    body = json.dumps({"query": query, "variables": dict(variables)})
    try:
        done = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=body,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise GitHubError("reading other repositories needs `gh`, which is not installed") from error
    if done.returncode != 0:
        message = done.stderr.strip() or done.stdout.strip()
        raise (ServerError if re.search(r"HTTP 5\d\d", message) else GitHubError)(message)
    response = json.loads(done.stdout)
    if not isinstance(response, dict):
        raise ShapeError("GraphQL response: not an object")
    return response


def _quiet(_: str) -> None:
    pass


def _count(n: int, noun: str, plural: Optional[str] = None) -> str:
    return f"{n} {noun if n == 1 else plural or noun + 's'}"


@dataclass
class Client:
    transport: Transport = gh_transport
    sleep: Sleep = time.sleep
    # Told what the run is doing at each step: a listing of hundreds of
    # repositories takes tens of seconds, and a silent one reads as a hang.
    progress: Progress = _quiet

    def call(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """A GraphQL error raises rather than leaving a repository out, since a
        missing one understates every total it belongs to."""
        attempt = 0
        while True:
            try:
                response = self.transport(query, variables or {})
                break
            except ServerError as error:
                attempt += 1
                if attempt > RETRIES:
                    raise
                self.progress(f"{error}; retrying in {2**attempt}s")
                self.sleep(2**attempt)
        errors = response.get("errors")
        if errors:
            raise GitHubError("; ".join(str(error.get("message", error)) for error in errors))
        return required(read_object, response, "data", "GraphQL response")


def literal(value: str) -> str:
    """A GraphQL string literal: JSON's escaping is GraphQL's for these."""
    return json.dumps(value)


def repository(repo: str) -> str:
    owner, name = repo.split("/", 1)
    return f"repository(owner: {literal(owner)}, name: {literal(name)})"


REPO_FIELDS = (
    "\n  nameWithOwner\n"
    + "".join(
        f"  {alias}: object(expression: {literal(f'{rev}:{LEDGER}')}) {{ ... on Tree {{ entries {{ name type }} }} }}\n"
        for alias, rev in SIDES.items()
    )
    + f"  watermark: object(expression: {literal('HEAD:' + WATERMARK)}) {{ __typename }}\n"
    + f"  addedRoles: object(expression: {literal(ADDED_ROLES)})"
    " { ... on Blob { isTruncated isBinary text } }\n"
)

LISTING = f"""
query($cursor: String) {{
  viewer {{
    repositories(
      first: {PAGE}, after: $cursor,
      affiliations: {AFFILIATIONS}, ownerAffiliations: {AFFILIATIONS}
    ) {{
      pageInfo {{ hasNextPage endCursor }}
      nodes {{ {REPO_FIELDS} }}
    }}
  }}
}}
"""


@dataclass
class Candidate:
    repo: str
    # The months each side that has a ledger holds, by the side's rev.
    sides: Dict[str, List[str]]
    # The text of its `rates.repo.json`, where it carries one.
    added_roles: Optional[str] = None

    @property
    def months(self) -> List[str]:
        return sorted({month for months in self.sides.values() for month in months})


@dataclass
class Discovery:
    ledgers: List[Candidate]
    # muthur's watermark and no ledger: adopters that opted out of it.
    without_ledger: List[str]
    seen: int


def _entries(tree: Any, where: str) -> Optional[List[Dict[str, Any]]]:
    """A tree's entries; None where the path is missing or not a tree."""
    if tree is None:
        return None
    if not isinstance(tree, dict):
        raise ShapeError(f"{where}: not an object")
    entries = tree.get("entries")
    if entries is None:
        return None
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ShapeError(f"{where}: `entries` is not a list of objects")
    return entries


def _blob_text(blob: Any, where: str) -> str:
    if not isinstance(blob, dict):
        raise ShapeError(f"{where}: not an object")
    if blob.get("isTruncated") or blob.get("isBinary"):
        raise ShapeError(f"{where}: GitHub did not return the file whole as text")
    return required(read_string, blob, "text", where)


def _read_node(node: Any) -> Tuple[str, Dict[str, List[str]], bool, Optional[str]]:
    if not isinstance(node, dict):
        raise ShapeError("repository node: not an object")
    repo = required(read_string, node, "nameWithOwner", "repository node")
    added = node.get("addedRoles")
    added_roles = None if added is None else _blob_text(added, f"{repo}:{ADDED_ROLES}")
    sides: Dict[str, List[str]] = {}
    for alias, rev in SIDES.items():
        entries = _entries(node.get(alias), f"{repo} {rev}")
        if entries is not None:
            sides[rev] = sorted(
                entry["name"]
                for entry in entries
                if entry.get("type") == "tree" and MONTH.fullmatch(str(entry.get("name")))
            )
    return repo, sides, node.get("watermark") is not None, added_roles


def _nodes(client: Client, only: Optional[Sequence[str]]) -> List[Any]:
    if only:
        client.progress(f"reading {_count(len(only), 'named repository', 'named repositories')}")
        aliased = " ".join(f"r{i}: {repository(repo)} {{ {REPO_FIELDS} }}" for i, repo in enumerate(only))
        data = client.call(f"query {{ {aliased} }}")
        return [data.get(f"r{i}") for i in range(len(only))]
    nodes: List[Any] = []
    cursor: Optional[str] = None
    while True:
        client.progress(f"listing your repositories: {len(nodes)} so far")
        data = client.call(LISTING, {"cursor": cursor})
        page = required(read_object, required(read_object, data, "viewer", "listing"), "repositories", "listing")
        nodes.extend(page.get("nodes") or [])
        info = required(read_object, page, "pageInfo", "listing")
        if not info.get("hasNextPage"):
            return nodes
        cursor = required(read_string, info, "endCursor", "listing pageInfo")


def discover(client: Client, only: Optional[Sequence[str]] = None) -> Discovery:
    """Every repository the viewer owns, collaborates on or reaches through an
    organization — or, given `only`, those alone, where one without a ledger
    raises: it was named, so leaving it out quietly would answer a question
    nobody asked."""
    ledgers: List[Candidate] = []
    without_ledger: List[str] = []
    nodes = _nodes(client, only)
    for repo, sides, watermarked, added_roles in sorted(map(_read_node, nodes), key=lambda read: read[0]):
        if sides:
            ledgers.append(Candidate(repo, sides, added_roles))
        elif only:
            raise GitHubError(f"{repo}: no {LEDGER} on its {BRANCH} branch or its default branch")
        elif watermarked:
            without_ledger.append(repo)
    return Discovery(ledgers, without_ledger, len(nodes))


def _month_query(trees: Sequence[Tuple[str, str, str]]) -> str:
    aliased = " ".join(
        f"p{i}: {repository(repo)} {{ object(expression: {literal(f'{rev}:{LEDGER}/{month}')}) {{"
        " ... on Tree { entries { name type object { ... on Blob { isTruncated isBinary text } } } } } }"
        for i, (repo, rev, month) in enumerate(trees)
    )
    return f"query {{ {aliased} }}"


def _row_text(entry: Dict[str, Any], where: str) -> str:
    return _blob_text(required(read_object, entry, "object", where), where)


def ledger_texts(client: Client, candidates: Sequence[Candidate]) -> List[Tuple[str, str, str]]:
    """`(repo, where, text)` for each row of the candidates' months, on each
    side, read in batches of month trees. A row GitHub truncates raises rather
    than going missing."""
    trees = [(c.repo, rev, m) for c in candidates for rev, months in c.sides.items() for m in months]
    texts: List[Tuple[str, str, str]] = []
    for start in range(0, len(trees), BATCH):
        batch = trees[start : start + BATCH]
        client.progress(
            f"reading {_count(len(candidates), 'ledger')}: {start} of {_count(len(trees), 'month')},"
            f" {_count(len(texts), 'row')} so far"
        )
        data = client.call(_month_query(batch))
        for i, (repo, rev, name) in enumerate(batch):
            where = f"{repo}:{rev}:{LEDGER}/{name}"
            found = required(read_object, data, f"p{i}", where)
            entries = _entries(found.get("object"), where)
            if entries is None:
                raise ShapeError(f"{where}: no longer a tree")
            for entry in entries:
                file = str(entry.get("name"))
                if entry.get("type") == "blob" and file.endswith(".json"):
                    texts.append((repo, f"{where}/{file}", _row_text(entry, f"{where}/{file}")))
    return texts


@dataclass
class RepoLedger:
    name: str
    months: List[str]
    warnings: List[str] = field(default_factory=list)


@dataclass
class RemoteLedger:
    rows: List[SessionCost]
    # Session id to the repository its row was counted from.
    repo_of: Dict[str, str]
    repos: List[RepoLedger]
    without_ledger: List[str]
    seen: int
    # Repository to the text of its `rates.repo.json`, for those that carry one.
    added_roles: Dict[str, str] = field(default_factory=dict)


def remote_ledger(
    client: Client,
    only: Optional[Sequence[str]] = None,
    months: Optional[Collection[str]] = None,
) -> RemoteLedger:
    """Rows are reshaped in memory and never written back: this repository's
    parser is the one in force, but the rows are another branch's to change.
    Within a repository the two sides' copies of a row are one session, the
    later copy winning. A session id in two repositories — a fork carries its
    source's rows — is counted in the first, by name."""
    found = discover(client, only)
    client.progress(f"{_count(len(found.ledgers), 'ledger')} among {_count(found.seen, 'repository', 'repositories')}")
    wanted = [
        Candidate(c.repo, {rev: [m for m in ms if months is None or m in months] for rev, ms in c.sides.items()})
        for c in found.ledgers
    ]
    repos = {c.repo: RepoLedger(c.repo, c.months) for c in wanted}
    by_repo: Dict[str, List[Tuple[SessionCost, bool]]] = {}
    for repo, where, text in ledger_texts(client, wanted):
        row, changes = reshape(text, where)
        by_repo.setdefault(repo, []).append((row, bool(changes)))
    rows: List[SessionCost] = []
    repo_of: Dict[str, str] = {}
    reshaped: Dict[str, int] = {}
    for repo, row, changed in (
        (repo, row, changed) for repo, read in by_repo.items() for row, changed in union(read, lambda item: item[0])
    ):
        if changed:
            reshaped[repo] = reshaped.get(repo, 0) + 1
        first = repo_of.get(row.session_id)
        if first is not None:
            repos[repo].warnings.append(f"session {row.session_id} is also in {first}, counted there")
            continue
        repo_of[row.session_id] = repo
        rows.append(row)
    for repo, n in reshaped.items():
        repos[repo].warnings.append(f"{_count(n, 'row')} in an older or newer shape than this ledger's")
    return RemoteLedger(
        rows=rows,
        repo_of=repo_of,
        repos=[ledger for ledger in repos.values() if ledger.months],
        without_ledger=found.without_ledger,
        seen=found.seen,
        added_roles={c.repo: c.added_roles for c in found.ledgers if c.added_roles is not None},
    )
