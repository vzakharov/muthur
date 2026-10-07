> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# `report.py --siblings`: one report over every local clone's ledger

## Goal

`python3 .claude/costs/report.py --siblings` sums the cost ledgers of every git
repository next to this one — the parent directory of this repo's root — so one
run shows the work across all of an operator's repos. Every existing table
prints as today, plus a `repo` table, and `--month` and `--json` work alongside.

The ledger's own docs already name the gap: "the transcript directory is keyed
by working directory, so these totals are this repo's" (`.claude/costs/CLAUDE.md`
§ "What the totals do not cover").

## Where the rows are read from: each sibling's `origin/<default>`, not its working tree

The ask was to read each sibling's checkout and warn when it is off `main` or
out of sync. This plan reads each sibling's **`origin/<default-branch>` ref**
after a `git fetch`, through git's object store (`git ls-tree` + `git cat-file
--batch`), and never looks at the working tree.

**Why:** the warnings the ask wanted exist to flag a checkout that would give
the wrong numbers. Reading the ref removes that failure instead of reporting
it — a sibling sitting on a feature branch, behind `main`, or with a dirty tree
still contributes exactly its trunk ledger, which is what "the work done" means
here (rows reach the trunk by merge). The cost is the same: the reader needs
text-based parsing anyway, because a sibling's rows must never be written to
(below).

What is still warned about, once per repo, above the tables:

- **the fetch failed** (offline, auth, no `origin`) — rows are read from the ref
  as of the last successful fetch, and the warning says how old that is
  (`FETCH_HEAD`'s mtime, or "never fetched");
- **no default branch resolvable** — `refs/remotes/origin/HEAD` missing and
  neither `origin/main` nor `origin/master` present; the repo is skipped;
- **two directories are the same repo** (same `origin` URL) — read once, the
  duplicate named;
- **a session id appears in two repos** — counted once, both repos named.

Repos with no `.claude/costs/sessions/` on that ref are listed in one line
("no ledger: a, b"), not warned about one by one: most siblings may simply not
have adopted the ledger.

`--no-fetch` skips the network and reads whatever refs are there, with the
age line for each.

## Steps

1. **Split parsing from writing in `lib/rows.py`.** Extract
   `reshape(text, where) -> (SessionCost, changes)` out of `read_row`, which
   becomes `reshape` + `write_atomic` when `changes` is non-empty. A sibling's
   rows go through `reshape` only: the report never writes into another
   repository. A sibling row in a retired shape is reported on stderr as a
   count per repo ("N rows in a retired shape; a report there rewrites them").
   A sibling on a *newer* ledger than this one shows up the same way, as
   dropped keys — this repo's parser is the one in force.
2. **`lib/siblings.py` (new)** — discovery and reading, stdlib + `git` only:
   - `discover(parent) -> List[Path]`: immediate children that are git work
     trees (`git rev-parse --show-toplevel` equals the child), this repo included;
   - `default_ref(repo) -> Optional[str]`: `origin/HEAD`'s target, else
     `origin/main`, else `origin/master`;
   - `fetch(repo, branch) -> Optional[str]`: `git fetch --quiet origin <branch>`,
     returning the error text on failure; run for all repos in a thread pool so
     ten siblings do not cost ten round trips in series;
   - `ledger_texts(repo, ref) -> Dict[str, str]`: path → JSON text for every
     `.claude/costs/sessions/*/*.json` on the ref;
   - one `RepoLedger` dataclass per repo: name (directory name), path, ref,
     origin URL, texts, warnings.
3. **`lib/totals.py`** — `totals_of` takes an optional `repo_of: Mapping[str, str]`
   (session id → repo name). When given, it fills a new `by_repo` and labels
   branches `<repo>:<branch>`, since `main` or a `/spinoff`-seeded branch name
   can recur across repos. Absent, nothing changes: the single-repo report is
   byte-identical.
4. **`report.py`** — `--siblings` and `--no-fetch`. The month filter applies to
   the row paths' `<YYYY-MM>` segment, as it does to directories today. Status
   lines print first (stdout, before the tables, so they are not lost above a
   long report); the `repo` table prints before `month`. `--json` gains a
   `repos` array: name, ref, rows, fetch error, warnings. `report.py` stays
   under ~450 lines; the status printing goes in `lib/siblings.py` if it
   would not.
5. **`test_siblings.py`** — real git, in a temp directory: a bare `origin` plus
   clones, so nothing is mocked below the `git` boundary. Cases:
   - rows on `origin/main` counted while the clone sits on a feature branch with
     extra and uncommitted rows, which are not;
   - `--no-fetch` reads the stale ref; a fetch against a removed `origin`
     warns and still reads the last-fetched ref;
   - a sibling with no ledger lands in the "no ledger" line;
   - the same session id in two repos is counted once and named;
   - a sibling row in a retired shape is reshaped in memory and its file is
     untouched;
   - branch labels are repo-prefixed only under `repo_of`.
   `scripts/vet.sh` already runs every `.claude/costs/test_*.py`, so the file
   is picked up without a vet change.
6. **Docs.** `.claude/costs/CLAUDE.md`: § "The report" gains a short paragraph
   (what `--siblings` reads and why the ref rather than the tree; that it never
   writes into a sibling); the "Other repositories" bullet in § "What the totals
   do not cover" narrows to what `--siblings` still misses — repos not cloned
   next to this one, and anything not yet merged to their trunk. The
   `report.py` usage docstring and the catalog row in
   `.claude/skills/update-muthur/catalog.md` name the flag.

## Not in this PR: reading without a local clone

Proposed as a follow-up issue rather than built here, since the ask was the
local run:

- **GitHub GraphQL, no clones at all.** One query per batch of repos —
  `repository(owner, name) { object(expression: "HEAD:.claude/costs/sessions/2026-10") { ... on Tree { entries { name object { ... on Blob { text } } } } } }`
  with an alias per repo and month — returns every row's text from each default
  branch in a single request. Repos come from `--github <owner>` (the owner's
  repos, kept where the path exists) or an explicit list. It runs anywhere a
  `gh` token does — a cloud session, a routine — and plugs into the same
  `RepoLedger` shape Step 2 introduces, so it is a new source, not a new report.
- **A scheduled routine on top of it**, publishing the report as a private
  artifact page refreshed weekly: the "statistics across my repos" view with no
  machine involved.

Ruled out: **a central ledger repository** that each repo's `Stop` hook or a
GitHub Action pushes rows into. It changes the write path in every adopting
repo and needs a cross-repo credential, to obtain what the read-side options
above get from the rows already on each trunk.

## DRY notes

- **Shared, reused as-is:** `totals_of`, `Bucket`, `table`, `parse_session_cost`,
  `parse_rates`/`parse_prices` — the siblings report is the same rollup over
  more rows, so no second report path exists.
- **Extracted:** `reshape` out of `read_row`, because the sibling path needs the
  parse-and-reshape without the write; leaving it inline would mean a copy of
  the retired-shape logic that drifts the next time a shape retires.
- **Deliberately not shared:** `scripts/lib/github.py` and the bash helpers in
  `scripts/lib/`. `.claude/costs/` is adopted on its own (catalog: opt-in), so
  it cannot import from `scripts/`; the few `git` calls `lib/siblings.py` makes
  are a thin `subprocess.run` wrapper local to it.
- **`repo_of` as a parameter rather than a `repo` field on `SessionCost`:** a
  row's repo is where it was read from, not something the row records, and
  writing it into the row shape would make every existing row a retired shape.
