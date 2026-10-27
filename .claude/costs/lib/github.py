"""The ledger of every repository the `gh` user can see, read off each one's
`cost-ledger` branch and default branch through GitHub's API, with no clone of
anything. The default branch's side counts a repository whose rows are still in
its tree. GraphQL finds the ledgers and reads the rows, but lists a tree one
level at a time, so the rows, at any depth under a month, are listed over REST.

A repository qualifies by carrying a ledger, not muthur's watermark: the
ledger is opt-in for adopters, so a watermark alone has nothing to count. The
watermark is read only to name the adopters that opted out, so a repository
missing from the report has a visible reason.

Every call goes through a `Transport` for GraphQL and a `Rest` for REST, which
is where the tests stand in for the network.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, TypeVar

from lib.filing import MONTH, is_row
from lib.filing import PREFIX as LEDGER
from lib.ledger_branch import BRANCH, RATES_PATH
from lib.rows import SessionCost, reshape, union
from lib.shape import ShapeError, read_object, read_string, required

# A row may name a role only its own repository rates, so the report reads that
# repository's table, off the ledger beside the rows.
ADDED_ROLES = f"refs/heads/{BRANCH}:{RATES_PATH}"
WATERMARK = ".claude/skills/update-muthur/watermark.json"
# A page of 100 answered HTTP 502 on a token reaching 357 repositories; 40 did not.
PAGE = 40
# Rows per query, each arriving as its text, a few kB a row.
BATCH = 50
RETRIES = 3
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
AFFILIATIONS = "[OWNER, COLLABORATOR, ORGANIZATION_MEMBER]"
# Where a repository's rows can be, keyed by the alias each is queried under.
SIDES = {"ledger": f"refs/heads/{BRANCH}", "tree": "HEAD"}

# `(query, variables)` to the response, `data` and `errors` as GitHub sent them.
Transport = Callable[[str, Mapping[str, Any]], Dict[str, Any]]
# A REST path, `repos/...`, to its JSON.
Rest = Callable[[str], Any]
Sleep = Callable[[float], None]
Progress = Callable[[str], None]

T = TypeVar("T")


class GitHubError(RuntimeError):
    """A query GitHub refused or failed, in GitHub's words."""


class ServerError(GitHubError):
    """A 5xx, which a retry can clear."""


def gh_api(*args: str, input: Optional[str] = None) -> Any:
    """Through `gh` rather than raw HTTP: it carries the operator's auth, and a
    cloud session's proxy along with it."""
    try:
        done = subprocess.run(["gh", "api", *args], input=input, capture_output=True, text=True, check=False)
    except FileNotFoundError as error:
        raise GitHubError("reading other repositories needs `gh`, which is not installed") from error
    if done.returncode != 0:
        message = done.stderr.strip() or done.stdout.strip()
        raise (ServerError if re.search(r"HTTP 5\d\d", message) else GitHubError)(message)
    return json.loads(done.stdout)


def gh_transport(query: str, variables: Mapping[str, Any]) -> Dict[str, Any]:
    response = gh_api("graphql", "--input", "-", input=json.dumps({"query": query, "variables": dict(variables)}))
    if not isinstance(response, dict):
        raise ShapeError("GraphQL response: not an object")
    return response


def gh_rest(path: str) -> Any:
    return gh_api(path)


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
    rest: Rest = gh_rest

    def retrying(self, attempt: Callable[[], T]) -> T:
        tries = 0
        while True:
            try:
                return attempt()
            except ServerError as error:
                tries += 1
                if tries > RETRIES:
                    raise
                self.progress(f"{error}; retrying in {2**tries}s")
                self.sleep(2**tries)

    def get(self, path: str) -> Any:
        return self.retrying(lambda: self.rest(path))

    def call(self, query: str, variables: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """A GraphQL error raises rather than leaving a repository out, since a
        missing one understates every total it belongs to."""
        response = self.retrying(lambda: self.transport(query, variables or {}))
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
        f"  {alias}: object(expression: {literal(f'{rev}:{LEDGER}')}) {{ ... on Tree {{ oid entries {{ name type }} }} }}\n"
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
class Side:
    # The oid of the side's `sessions/` tree, which the rows are listed from.
    tree: str
    months: List[str]


@dataclass
class Candidate:
    repo: str
    # Each side that has a ledger, by its rev.
    sides: Dict[str, Side]
    # The text of its `rates.repo.json`, where it carries one.
    added_roles: Optional[str] = None

    @property
    def months(self) -> List[str]:
        return sorted({month for side in self.sides.values() for month in side.months})


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


def _read_node(node: Any) -> Tuple[str, Dict[str, Side], bool, Optional[str]]:
    if not isinstance(node, dict):
        raise ShapeError("repository node: not an object")
    repo = required(read_string, node, "nameWithOwner", "repository node")
    added = node.get("addedRoles")
    added_roles = None if added is None else _blob_text(added, f"{repo}:{ADDED_ROLES}")
    sides: Dict[str, Side] = {}
    for alias, rev in SIDES.items():
        entries = _entries(node.get(alias), f"{repo} {rev}")
        if entries is not None:
            months = sorted(
                entry["name"]
                for entry in entries
                if entry.get("type") == "tree" and MONTH.fullmatch(str(entry.get("name")))
            )
            sides[rev] = Side(required(read_string, node[alias], "oid", f"{repo} {rev}"), months)
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


def row_blobs(client: Client, repo: str, rev: str, side: Side) -> List[Tuple[str, str]]:
    """`(where, blob oid)` for each row the side holds, at any depth. A listing
    GitHub truncates raises rather than leaving rows out."""
    where = f"{repo}:{rev}:{LEDGER}"
    listed = client.get(f"repos/{repo}/git/trees/{side.tree}?recursive=1")
    if not isinstance(listed, dict):
        raise ShapeError(f"{where}: the tree listing is not an object")
    if listed.get("truncated"):
        raise ShapeError(f"{where}: GitHub truncated the tree listing")
    entries = listed.get("tree")
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ShapeError(f"{where}: `tree` is not a list of objects")
    found = []
    for entry in entries:
        path = required(read_string, entry, "path", f"{where} entry")
        if entry.get("type") == "blob" and is_row(f"{LEDGER}/{path}"):
            found.append((f"{where}/{path}", required(read_string, entry, "sha", f"{where}/{path}")))
    return found


def _blob_query(blobs: Sequence[Tuple[str, str]]) -> str:
    aliased = " ".join(
        f"b{i}: {repository(repo)} {{ object(oid: {literal(oid)}) {{ ... on Blob {{ isTruncated isBinary text }} }} }}"
        for i, (repo, oid) in enumerate(blobs)
    )
    return f"query {{ {aliased} }}"


def ledger_texts(client: Client, candidates: Sequence[Candidate]) -> List[Tuple[str, str, str]]:
    """`(repo, where, text)` for each row on each side of the candidates, each
    side listed in one call and the rows read in batches, a blob both sides
    share read once. A row GitHub truncates raises rather than going missing."""
    listed: List[Tuple[str, str, str]] = []
    for c in candidates:
        for rev, side in c.sides.items():
            client.progress(f"listing {c.repo}'s rows on {rev}")
            listed.extend((c.repo, where, oid) for where, oid in row_blobs(client, c.repo, rev, side))
    named: Dict[Tuple[str, str], str] = {}
    for repo, where, oid in listed:
        named.setdefault((repo, oid), where)
    blobs = sorted(named)
    texts: Dict[Tuple[str, str], str] = {}
    for start in range(0, len(blobs), BATCH):
        batch = blobs[start : start + BATCH]
        client.progress(f"reading {_count(len(candidates), 'ledger')}: {start} of {_count(len(blobs), 'row')}")
        data = client.call(_blob_query(batch))
        for i, blob in enumerate(batch):
            where = named[blob]
            found = required(read_object, data, f"b{i}", where)
            texts[blob] = _blob_text(required(read_object, found, "object", where), where)
    return [(repo, where, texts[(repo, oid)]) for repo, where, oid in listed]


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


def remote_ledger(client: Client, only: Optional[Sequence[str]] = None) -> RemoteLedger:
    """Rows are reshaped in memory and never written back: this repository's
    parser is the one in force, but the rows are another branch's to change.
    Within a repository the two sides' copies of a row are one session, the
    later copy winning. A session id in two repositories — a fork carries its
    source's rows — is counted in the first, by name."""
    found = discover(client, only)
    client.progress(f"{_count(len(found.ledgers), 'ledger')} among {_count(found.seen, 'repository', 'repositories')}")
    repos = {c.repo: RepoLedger(c.repo, c.months) for c in found.ledgers}
    by_repo: Dict[str, List[Tuple[SessionCost, bool]]] = {}
    for repo, where, text in ledger_texts(client, found.ledgers):
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
