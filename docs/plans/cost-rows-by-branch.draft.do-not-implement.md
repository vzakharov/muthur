> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Cost rows filed by branch

## Goal

A session's row moves from `.claude/costs/sessions/<YYYY-MM>/<uuid>.json` to

```
.claude/costs/sessions/<full/branch/path>/<N>/<uuid>.json
```

where `<N>` is the session's ordinal on that branch, 1-based. A row with no
branch goes under `.no-branch/` the same way. Every existing row is re-filed: in
this repository's ledger, and in any adopter's, by code that knows nothing about
their rows in advance.

## Decisions (each a recommendation in force; see Questions)

- **The month folder goes.** The branch is the grouping, and the month is
  already in `firstResponseAt`, which is what `--month` filters on. Keeping it
  (`<YYYY-MM>/<branch>/<N>/`) would split a branch that spans a month boundary
  and restart its ordinals.
- **Branchless rows go under `.no-branch/`.** Git forbids a ref component that
  starts with a dot, so no real branch can collide with it. Leaving those rows
  in the month layout would keep two layouts alive for good.
- **`<N>` is plain, unpadded.** The width cannot be known in advance. The cost
  is that GitHub's file view sorts `10` before `2`.

## How the ordinal is assigned

- **The ledger decides it**, because only the ledger sees every session on a
  branch. A new session on branch `b` gets one more than the highest `<N>` in
  the ledger's `sessions/b/`. The highest, not the count, so the gap a moved row
  leaves is never reused.
- **Once assigned, it stays**, as long as the row's `branch` stays the same.
- **A row whose `branch` changes moves.** `pricing.py` already takes the last
  `gitBranch` it sees, so a session that renames its auto-branch (this one did)
  or attaches with `/from-branch` gets a new `<N>` on the new branch, and its
  old path is deleted in the same commit.
- **A race heals itself.** Two sessions that claim the same `<N>` at once: the
  push that loses re-plans on the new tip (`append`'s existing retry) and takes
  the next number. If the ledger fetch failed and a row was filed against a
  stale local ref, the next good write sees two rows in one `<N>` and moves the
  one that started later.
- **Backfill orders by `firstResponseAt`**, falling back to `lastResponseAt` and
  then the session id, so the result is deterministic and a second run changes
  nothing.

## The re-filing pass, which is also the migration

One function, `refile(listing, read)`. Given a ledger tip, it returns the
`{path: text | None}` changes that bring every row to its proper place:

1. Group the paths by session id. More than one copy → keep the winner by
   `recency` and delete the rest.
2. A path that is already `<dir of its branch>/<N>/<id>.json`, with no other
   session in that `<N>`, stays. Nothing has to be read to know that, because
   the branch can be read off the path. A row is read only when its path is in
   the old layout or does not match.
3. Every other row gets the next free `<N>` on its branch, in the order above.

`append` runs it on every ledger write, so the migration needs nobody to
remember to run it. In an adopter, the first `Stop` after `/update-muthur`
brings this code in re-files the whole ledger in one commit, and every write
after that is a no-op over a name listing. This runs on every write, not once,
because **stale branches keep writing the old layout**: a branch that has not
merged the new code runs the old `session_cost.py`, which files under the month.
Its row then exists twice, and the next new-code write merges the two.
`ledger.py backfill` and `/finalize`'s carry go through the same `append`.

## Changes, file by file

- **`lib/filing.py`** (new): `row_dir(branch)`, `canonical(path, row)`,
  `next_ordinal(listing, branch)`, `refile(...)`, and the predicate "is a row
  path" (any `*.json` under `sessions/`, at any depth).
- **`lib/ledger_branch.py`**: `append` adds `refile`'s changes to the plan's
  own. `append_row(text)` files the row and returns the path it used, so it no
  longer takes a path. `path_of` and `copies` look at any depth.
- **`lib/rows.py`**: `row_path` → every tree copy of a session at any depth
  (`rglob`).
- **`session_cost.py`**: `month_of` goes. `--row-path` prints the path the row
  would be filed at against the local ledger ref, and a hand run writes there
  and removes the session's other tree copies.
- **`ledger.py`**: `append-row <file>` prints the path the ledger filed it at,
  and `commit-row <parent> <path> <file>` also deletes the session's other
  copies in `<parent>`'s tree. A new `path-for <file>` covers a failed fetch,
  filing against the local ref.
- **`hooks/stop-session-cost.sh`**: the display copy's path comes from
  `append-row`, or from `path-for` when the fetch failed, instead of from
  `session_cost.py`. Old-layout display copies of _other_ sessions stay on the
  branch until `/finalize` carries and deletes them, as today.
- **`report.py`, `lib/restart.py`**: read the tree's rows at any depth. The
  month directories no longer prune the read: `span.holds(row)` filters, as it
  already does for ledger rows.
- **`estimate.py` `edit`**: goes through `append_row(text)`, and rewrites the
  tree copy at the filed path.
- **`lib/github.py`**: GraphQL cannot list a tree recursively, so discovery
  keeps its GraphQL probe (does `sessions/` exist on each side), and the rows
  are listed with REST `git/trees/<rev>?recursive=1` through `gh api`, then read
  as blobs in GraphQL batches as now. A `truncated` listing raises, like a
  truncated row. The `MONTH` regex and `Candidate.months` go. Both layouts read
  the same way, which is what an adopter who has not updated still needs.
- **`check_estimates.py`**: a move reads as `D` plus `A` under `--no-renames`.
  The `A` is checked as a new row, which is right, since the session is the
  branch's either way.
- **Tests**: a new `test_filing.py` (canonical paths, ordinal after a gap, a
  branch change moves the row, two rows in one `<N>`, a duplicate copy across
  layouts, an idempotent second pass, `.no-branch`), plus updates to
  `test_stop_hook.py`, `test_totals.py`, `test_github.py` and `test_estimate.py`
  for the new paths.
- **Prose**: `.claude/costs/CLAUDE.md` (the layout line, § "Where rows live",
  and a short § on filing: ordinals, moves, the self-healing pass), the G7
  catalog entry, and `docs/adopting/costs.md` where it names the layout.
  `scripts/check-repo-identity.sh` and `scripts/muthur-sync.sh` already match
  `sessions/*` at any depth.

## What it costs

- **An older `report.py --all-my-repos` undercounts a repository that has
  migrated.** Its GraphQL reader only knows month directories. This is the same
  cost the ledger branch's own arrival had, and it is paid until that checkout
  updates.
- **The first new-code `Stop` in a repository re-files every row in one
  commit**: about 200 rows here. After that, a write spends one extra name
  listing of the tip, which `append` already fetches.
- **A case-insensitive checkout** (macOS) folds `Foo` and `foo` into one
  directory. Their ordinals then share a sequence. Nothing is lost.

## DRY notes

- **Shared:** where a row goes (`lib/filing.py`) has one home, used by the
  ledger write, the hook's display copy, a hand run of `session_cost.py`, the
  estimate edit and backfill. Today the month rule lives only in
  `session_cost.py`, and every other writer takes the path it printed, so the
  hook passes a path the ledger then decides instead.
- **Reused:** `union`/`recency` settle duplicate copies, and `append`'s
  re-plan-on-rejected-push loop settles the ordinal race, with no new retry
  logic.
- **Kept apart:** the remote listing in `github.py` stays its own code. It reads
  over GitHub's API, not git, and shares only the "is a row path" predicate,
  which it imports from `filing.py`. An abstraction over local git and remote
  REST would cost more than the two call sites it joins.
- **Folded together:** `rows.row_path`, `ledger_branch.copies`'s glob,
  `report.rows_in` and `restart.ledger_orientations` each glob `*/<id>.json` or
  `*/*.json`. All four become one `tree_rows()` / `tree_copies(id)` pair in
  `lib/rows.py`.

## Questions

1. Month folder: **a) drop it (recommended)**; b) keep it above the branch.
2. Rows with no branch: **a) `.no-branch/<N>/` (recommended)**; b) leave them in
   the month layout.
3. `<N>`: **a) plain integers (recommended)**; b) zero-padded to 3 digits.
