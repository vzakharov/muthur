> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# `report.py --github`: one cost report across every repo you can see

## Goal

`python3 .claude/costs/report.py --github` finds every repository the `gh`
user owns, collaborates on or reaches as an organization member, keeps the
ones whose default branch carries `.claude/costs/sessions/`, and sums their
ledgers in one report: every existing table as today, plus a `repo` table.
`--repo <owner/name>` (repeatable) narrows it to named repos; `--month` and
`--json` work alongside.

It needs no clone of anything, so it runs the same on a laptop, in a cloud
session (whose `gh` carries the operator's token) or in a scheduled routine.
The ledger's own docs name the gap it closes: "the transcript directory is
keyed by working directory, so these totals are this repo's"
(`.claude/costs/CLAUDE.md` § "What the totals do not cover").

**Measured on the operator's token** (spike in the session scratchpad, not
committed): the listing pass covers 357 repos in 37 s at 40 per page —
100 per page answered HTTP 502 — and found 7 with a ledger, two of them
under other organizations (`Playgramai/playgramapp`, `metkain/metka`).

## What qualifies a repo: the ledger, not the muthur watermark

A repo is read when `HEAD:.claude/costs/sessions` is a tree. The watermark
(`.claude/skills/update-muthur/watermark.json`) does not decide anything:
the ledger is opt-in for adopters, so a watermark without a ledger has
nothing to count, and a ledger without a watermark still has rows. The
watermark is read only for one line — "muthur, no ledger: a, b" — naming
adopters that opted out, so a missing repo has a visible reason. Today all 7
ledger repos carry the watermark too.

## Where the rows are read from: each repo's default branch on GitHub

`HEAD:` in a GraphQL object expression is the default branch, so every repo
contributes its trunk ledger — what "the work done" means here, since rows
reach the trunk by merge. Nothing local is read, so there is no checkout to
be off `main` or out of sync, and no warning for either.

What is warned about, above the tables:

- **a session id in two repos** — a fork carries its source's rows; counted
  once, both repos named;
- **a row whose blob GitHub truncates or will not return as text** — raised,
  not skipped: a silently missing row understates every total downstream.

What the report cannot see, stated in `.claude/costs/CLAUDE.md` rather than
warned about per run: repos under an organization that enforces SAML SSO
until the token is authorized for it, and any work not yet on a trunk.

## Steps

1. **Split parsing from writing in `lib/rows.py`.** Extract
   `reshape(text, where) -> (SessionCost, changes)` out of `read_row`, which
   becomes `reshape` + `write_atomic` when `changes` is non-empty. GitHub rows
   go through `reshape` only. A remote row in a retired shape, or one on a
   newer ledger than this repo's (dropped keys), is counted per repo on stderr
   — "N rows in an older or newer shape" — since this repo's parser is the one
   in force.
2. **`lib/github.py` (new)** — stdlib only, one injected transport:
   - `Transport = Callable[[str, Dict[str, Any]], Dict[str, Any]]`, defaulting
     to `gh api graphql` through `subprocess`; a non-zero exit or a GraphQL
     `errors` array raises with the message. `gh` handles auth and the
     session's proxy, which is why it is the default over raw HTTP;
   - `discover(transport, only=None) -> List[Candidate]`: paginates
     `viewer.repositories(affiliations, ownerAffiliations: [OWNER,
     COLLABORATOR, ORGANIZATION_MEMBER])` 40 at a time, retrying a 5xx page
     up to three times with backoff, and reads per node the month names under
     `HEAD:.claude/costs/sessions` and whether the watermark exists. `only`
     (from `--repo`) queries those repos directly instead of listing;
   - `ledger_texts(transport, candidates, months) -> Dict[repo, Dict[path, text]]`:
     one aliased query per batch of repos, each alias an
     `object(expression: "HEAD:.claude/costs/sessions/<month>")` tree with its
     entries' blob `text` and `isTruncated`; months outside `--month` are never
     requested.
3. **`lib/totals.py`** — `totals_of` takes an optional
   `repo_of: Mapping[str, str]` (session id → `owner/name`). When given, it
   fills a new `by_repo` and labels branches `<owner/name>:<branch>`, since the
   same branch name recurs across repos. Absent, nothing changes: the
   single-repo report is byte-identical.
4. **`report.py`** — `--github` and `--repo`. The warnings and the "muthur, no
   ledger" line print first; the `repo` table prints before `month`. `--json`
   gains a `repos` array: name, months, rows, warnings. The repo-reading lives
   in `lib/github.py` so `report.py` stays under ~450 lines.
5. **`test_github.py`** — a fake transport answering from recorded response
   shapes, which is the mock at the network boundary. Cases:
   - discovery keeps ledger repos, lists watermark-only ones, drops the rest,
     and follows pagination;
   - a 502 page is retried, a GraphQL `errors` array raises;
   - `--month` requests only that month's trees;
   - the same session id in two repos is counted once and named;
   - a truncated blob raises;
   - a retired-shape row is reshaped and reported, nothing written;
   - branch labels are repo-prefixed only under `repo_of`.
   `scripts/vet.sh` already runs every `.claude/costs/test_*.py`.
6. **Docs.** `.claude/costs/CLAUDE.md`: § "The report" gains a short paragraph
   — what `--github` reads, why the ledger and not the watermark qualifies a
   repo, the SSO blind spot; the "Other repositories" bullet in § "What the
   totals do not cover" narrows to that blind spot. The `report.py` usage
   docstring names both flags; the catalog row in
   `.claude/skills/update-muthur/catalog.md` names the flag and adds `gh` as a
   requirement of it alone.

## Not in this PR

- **A scheduled routine** that runs `--github --json` weekly and publishes the
  result as a private artifact page: the cross-repo view with no machine
  involved. It needs nothing from the report beyond this PR's `--json`.

Ruled out:

- **Local sibling clones** (`--siblings`, reading each clone's fetched
  `origin/<default>`): it sees only what happens to be cloned next to this
  repo, needs a machine, and reads the same trunks GitHub serves directly.
- **A central ledger repository** that each repo's `Stop` hook or an Action
  pushes rows into: it changes the write path in every adopting repo and needs
  a cross-repo credential, to obtain what is already on each trunk.

## DRY notes

- **Shared, reused as-is:** `totals_of`, `Bucket`, `table`, `parse_session_cost`,
  `parse_rates`/`parse_prices` — the cross-repo report is the same rollup over
  more rows, so no second report path exists.
- **Extracted:** `reshape` out of `read_row`, because the remote path needs the
  parse-and-reshape without the write; leaving it inline would mean a copy of
  the retired-shape logic that drifts the next time a shape retires.
- **Deliberately not shared:** `scripts/lib/github.py`, which resolves a token
  and talks REST. `.claude/costs/` is adopted on its own (catalog: opt-in), so
  it cannot import from `scripts/`; `lib/github.py` here is one GraphQL call
  through `gh` and the two queries built on it.
- **`repo_of` as a parameter rather than a `repo` field on `SessionCost`:** a
  row's repo is where it was read from, not something the row records, and
  writing it into the row shape would make every existing row a retired shape.
