"""What the merge gate reads off the PR's conversation comments: the attestation
and the squash record. Each mirrors a prose home — the attestation template in
`.claude/skills/finalize/attest.md`, the read-back in
`.claude/skills/finalize/merge.md` § "Merging" — and `test_merge_gate.py` reads
the template, so the patterns here cannot drift from it unnoticed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

from lib.attestation import MARKER

HEADING = "### Attestation"
VET = "- `./scripts/vet.sh` — "
CI = "- CI on this PR — "
BUCKETS = "- CI-only buckets — "
NOTHING_RUNS = "**nothing runs on a PR in this repo**"
STUB = "**/test-on-gh is an unhydrated stub**"

# Each line's values the template allows; anything else — a red line, a
# recorded two-shot stop — is a run the gate does not merge on.
ALLOWED = {
    VET: re.compile(r"\*\*green\*\*(?: \(.*\))?"),
    CI: re.compile(r"\*\*green \(.+\)\*\*|" + re.escape(NOTHING_RUNS)),
    BUCKETS: re.compile(
        r"\*\*dispatched and passed \(.+\)\*\*"
        r"|\*\*not dispatched: the diff doesn't reach them\*\*|" + re.escape(STUB)
    ),
}

SQUASH_HEADERS = ("Proposed squash body:", "Proposed squash title/body:")
FENCE = re.compile(r"^```[^\n]*\n(.*?)\n```$", re.MULTILINE | re.DOTALL)
# `.claude/skills/squash-message/SKILL.md` § "Format rules": a bare
# conventional-commit type, no scope, at most `TITLE_MAX` characters.
TITLE = re.compile(r"(?:feat|fix|refactor|docs|chore|style|test|ci|perf): \S.*")
TITLE_MAX = 72
BYLINE = "Co-authored-by:"


@dataclass(frozen=True)
class Attestation:
    sha: str
    # False where its CI line says nothing runs on a PR.
    ci_runs: bool
    # Its CI-only line says `/test-on-gh` is a stub, which the tree must confirm.
    claims_stub: bool


@dataclass(frozen=True)
class Squash:
    subject: str
    body: str


def _lines(body: str) -> str:
    """A comment edited in GitHub's web UI comes back with CRLF line ends."""
    return body.replace("\r\n", "\n")


def attestation(bodies: Sequence[str]) -> Optional[Attestation]:
    """The comments' last marker, when it names a SHA and its comment is a full
    attestation whose every line holds a value the template allows. A
    `none required` heading is a `no vet` run, whose precondition only the
    agent can check."""
    last = None
    for body in map(_lines, bodies):
        for found in MARKER.finditer(body):
            last = (found.group(1), body)
    if last is None or last[0] in (None, "revoked"):
        return None
    sha, body = last
    lines = [line.rstrip() for line in body.split("\n")]
    if HEADING not in lines:
        return None
    values = {}
    for prefix, allowed in ALLOWED.items():
        found = [line[len(prefix) :] for line in lines if line.startswith(prefix)]
        if len(found) != 1 or not allowed.fullmatch(found[0]):
            return None
        values[prefix] = found[0]
    return Attestation(sha, values[CI] != NOTHING_RUNS, values[BUCKETS] == STUB)


def squash(bodies: Sequence[str], title: str, number: int) -> Optional[Squash]:
    """The last proposal's body — its last fenced block, ending on the byline —
    under the PR's title, which a title block, where there is one, must equal."""
    proposals = [body for body in map(_lines, bodies) if body.lstrip().startswith(SQUASH_HEADERS)]
    if not proposals:
        return None
    blocks = FENCE.findall(proposals[-1])
    if not blocks:
        return None
    body = blocks[-1].rstrip()
    if not body or not body.split("\n")[-1].startswith(BYLINE):
        return None
    if len(title) > TITLE_MAX or not TITLE.fullmatch(title):
        return None
    subject = f"{title} (#{number})"
    if len(blocks) > 1 and blocks[0].strip() != subject:
        return None
    return Squash(subject, body + "\n")
