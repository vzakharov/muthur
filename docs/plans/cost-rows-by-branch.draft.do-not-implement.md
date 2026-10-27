> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Cost rows filed by branch

## Goal

A session's row moves from `.claude/costs/sessions/<YYYY-MM>/<uuid>.json` to

```
.claude/costs/sessions/<YYYY-MM>/<full/branch/path>/<N>/<uuid>.json
```

- **`<YYYY-MM>` is the month of the branch's first session**, so every session
  on a branch sits in one directory, whichever month it ran in.
- **`<N>` is the session's 1-based ordinal on that branch**, a plain integer.
  GitHub's file view then sorts `10` before `2`, which is accepted.
- **A row with no branch goes under `<YYYY-MM>/.no-branch/<N>/`**, `<YYYY-MM>`
  being that session's own month and `<N>` its ordinal within that month's
  branchless rows. Git forbids a ref component that starts with a dot, so no
  real branch can collide with `.no-branch`.

Every existing row is re-filed: in this repository's ledger, and in any
adopter's, by code that knows nothing about their rows in advance.

Rejected: dropping the month level (`sessions/<branch>/<N>/`) — the month at the
top keeps the ledger browsable by period. Leaving branchless rows in the month
layout — that would keep two layouts alive for good. Zero-padding `<N>` — the
width cannot be known in advance.

## How the month and the ordinal are assigned

- **The ledger decides both**, because only the ledger sees every session on a
  branch.
- **A branch's month is fixed once it has a directory.** A new session on branch
  `b` goes under the month that already holds `b` in the ledger. Only a branch
  the ledger has never filed takes a month, from the earliest `firstResponseAt`
  among its rows: the session's own month when it is the first, and the earliest
  of them in a backfill. A row found later that started earlier does not move
  the branch.
- **The ordinal is one more than the highest `<N>` in the branch's directory.**
  The highest, not the count, so the gap a moved row leaves is never reused.
  Once assigned, it stays for as long as the row's `branch` does.
- **A row whose `branch` changes moves.** `pricing.py` already takes the last
  `gitBranch` it sees. So a session that renames its auto-branch or attaches
  with `/from-branch` goes to the new branch's directory with a new `<N>`, and
  its old path is deleted in the same commit. This is the only way a row moves
  once it is filed.
- **A race heals itself.** When two sessions claim the same `<N>` at once, the
  push that loses re-plans on the new tip (`append`'s existing retry) and takes
  the next number. A row filed against a stale local ref after a failed fetch
  can still collide. The next good write then sees two rows in one `<N>`, or one
  branch under two months, and moves the later-started row to its proper place.
- **Backfill orders by `firstResponseAt`**, falling back to `lastResponseAt` and
  then the session id, so the result is deterministic and a second run changes
  nothing.

## The re-filing pass, which is also the migration

One function, `refile(listing, read)`. Given a ledger tip, it returns the
`{path: text | None}` changes that bring every row to its proper place:

1. Group the paths by session id. More than one copy → keep the winner by
   `recency` and delete the rest.
2. A path already of the form `<month>/<branch>/<N>/<id>.json` stays when its
   branch appears under no other month and no other session shares its `<N>`.
   The branch and the month are read off the path, so nothing has to be read to
   know that.
3. Every other row is read for its `branch` and `firstResponseAt` and filed by
   the rules above.

**The steady-state check reads names only, never row text.** An old-layout path
(a `.json` directly under a month), a duplicate id, two ids in one `<N>` and one
branch under two months all show in the listing. No other session's row changes
branch without its own session re-filing it. Only misplaced rows are read.
Measured on this ledger's 202 rows: 3 ms to list, 9 ms to read every row. The
re-filing rides the push `append` already makes.

`append` runs it on every ledger write, so the migration needs nobody to
remember to run it. In an adopter, the first `Stop` after `/update-muthur`
brings this code in re-files the whole ledger in one commit, and every write
after that is a no-op over a name listing. This runs on every write, not once,
because **stale branches keep writing the old layout**: a branch that has not
merged the new code runs the old `session_cost.py`, which files under the month.
Its row then exists twice, and the next new-code write merges the two.
`ledger.py backfill` and `/finalize`'s carry go through the same `append`.

## Changes, file by file

- **`lib/filing.py`** (new): `parse_path(path)` (month, branch, ordinal, id, or
  the old layout), `next_place(listing, branch, started)`, `refile(...)`, and
  the predicate "is a row path" (any `*.json` under `sessions/`, at any depth).
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
- **`report.py`, `lib/restart.py`**: read the tree's rows at any depth. A month
  directory no longer bounds when its rows started, because a branch's later
  sessions sit under its first month. So `--month` and friends stop pruning by
  directory and filter with `span.holds(row)`, as they already do for ledger
  rows.
- **`estimate.py` `edit`**: goes through `append_row(text)`, and rewrites the
  tree copy at the filed path.
- **`lib/github.py`**: GraphQL lists one tree level at a time, and the rows now
  sit at varying depth under each month. Discovery keeps its GraphQL probe for
  the month directories on each side. The rows are listed with REST
  `git/trees/<rev>:.claude/costs/sessions?recursive=1` through `gh api`, then
  read as blobs in GraphQL batches as now. A `truncated` listing raises, like a
  truncated row. The month narrowing goes, for the reason under `report.py`.
  Both layouts read the same way, which is what an adopter who has not updated
  still needs.
- **`check_estimates.py`**: a move reads as `D` plus `A` under `--no-renames`.
  The `A` is checked as a new row, which is right, since the session is the
  branch's either way.
- **Tests**: a new `test_filing.py` covering:
  - canonical paths;
  - a branch's month fixed by its first row;
  - a later session landing in an earlier month;
  - the ordinal after a gap;
  - a branch change moving the row;
  - two rows in one `<N>`, and one branch under two months;
  - a duplicate copy across layouts;
  - `.no-branch` per month;
  - an idempotent second pass.

  Updates to `test_stop_hook.py`, `test_totals.py`, `test_github.py` and
  `test_estimate.py` for the new paths.

- **Prose**: `.claude/costs/CLAUDE.md` (the layout line, § "Where rows live",
  and a short § on filing: month, ordinals, moves, the self-healing pass), the
  G7 catalog entry, and `docs/adopting/costs.md` where it names the layout.
  `scripts/check-repo-identity.sh` and `scripts/muthur-sync.sh` already match
  `sessions/*` at any depth.

## What it costs

- **An older `report.py --all-my-repos` undercounts a repository that has
  migrated.** Its GraphQL reader takes only the files directly under a month.
  This is the same cost the ledger branch's own arrival had, and it is paid
  until that checkout updates.
- **The trunk lives in its first month forever**: every session on `main` goes
  under the month of `main`'s first one, with `<N>` in the hundreds. The same
  holds for any long-lived branch. A branch name reused after deletion joins the
  old directory and continues its numbering. Totals are unaffected either way,
  since they come from the rows.
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
  over GitHub's API, not git, and shares only `parse_path` and the "is a row
  path" predicate, which it imports from `filing.py`. An abstraction over local
  git and remote REST would cost more than the two call sites it joins.
- **Folded together:** `rows.row_path`, `ledger_branch.copies`'s glob,
  `report.rows_in` and `restart.ledger_orientations` each glob `*/<id>.json` or
  `*/*.json`. All four become one `tree_rows()` / `tree_copies(id)` pair in
  `lib/rows.py`.
