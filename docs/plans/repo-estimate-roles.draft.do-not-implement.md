> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# A repository's estimate roles live on `cost-ledger`

## The failure

`report.py --all-my-repos` stops on one row of vzakharov/vovazakharov.com's
ledger that books a part as `artist`. That role was rated by a
`rates.repo.json` on a feature branch, and the report reads that file off the
**default** branch only. The Stop hook writes a row to `cost-ledger` from any
branch on every turn, so a row reaches the ledger that no reader can rate. One
such row is enough to stop the cross-repo report.

The cause is where the table lives, not the reader. The rows have one home that
every branch writes to. The table that rates them has a home per branch, and
only the default branch's copy is ever read. The fix gives the table the rows'
home.

## Where this lands

In this PR (#186), before it merges, so `main` never ships the default-branch
file. The branch is 20 commits behind `main`, and `main` has since rewritten
`lib/github.py` to read `cost-ledger`. So implementation starts with
`/sync-branch`: merge `main`, resolving `lib/github.py` toward `main`'s
ledger-side discovery and re-applying #186's `addedRoles` blob on that side
(below). The rework comes after that.

## The design

### Home

`.claude/costs/rates.repo.json` on `cost-ledger`: the same path, at the root of
the ledger's tree, beside `sessions/`. The ledger already mirrors tree paths, so
nothing new needs a name. Its shape stays this PR's,
`{"roles": {"<name>": {"multiplier", "grade", "work"}}}`.

**The default branch carries none.** A tree copy would be a second home, and two
homes are the failure this fixes.

### Writer: a command that writes the ledger directly

- `estimate.py role set <name> <multiplier> <grade> "<work>"` adds a role or
  re-rates one.
- `estimate.py role drop <name>` removes one.

Both go through `lib/ledger.append`: fetch the tip, commit in a throwaway index,
push without force, re-read the tip if the push loses. That is the mechanics the
Stop hook's row write already uses. The commit subject names the change, for
example `chore: estimate role artist ×1.2 at senior`. That line is how
`git log cost-ledger` reads as the table's history.

Consequences:

- **A role added on any branch is on the ledger before any row can book it**,
  whether or not that branch ever merges.
- **A multiplier edit is the same command.** It re-rates every row booked under
  the role, across history alike. That is the "retuning re-rates the whole
  history" property `CLAUDE.md` § "Human-hour estimates" already states for the
  shared table. No branch copy exists to drift, so nothing reaches the ledger
  late.
- **`role drop` refuses while a ledger row books the role and the shared table
  does not rate it.** That keeps "every role a ledger row names is rateable" true
  by construction. A role the shared table has since taken up can be dropped,
  because the rows stay rateable.
- **`estimate.py set` checks against the ledger's table.** It reads the local
  copy of the ledger (`refs/remotes/origin/cost-ledger`). Only on a role that
  copy does not rate does it fetch and check again, so the common path makes no
  network call. A row that names an unrated role therefore cannot be written.

### Readers

One loader serves all of them: `rates.json` from this checkout, plus the
ledger's `rates.repo.json` at a given revision, through `with_added_roles`.

- **`estimate.py set` / `show` / `rates`** and **`check_estimates.py`** read it
  at the local ledger ref, as above. `check_estimates.py` fetches once, since
  the vet run is where a stale table would mislead.
- **`hooks/estimate-notice.sh`** reads `estimate.py rates`. A fresh container
  has no local ledger ref until its first Stop, so where the ref is missing the
  hook runs `ledger.py fetch` once. Otherwise the session's first notice would
  leave out the repository's roles. On every later prompt it reads the local
  ref with no network call.
- **`report.py`, this repository**, already reads the ledger at the fetched tip
  on `main`. It reads the table at that same tip, so rows and rates come from
  one commit.
- **`report.py --all-my-repos` / `--repo`** read the file as an aliased
  `refs/heads/cost-ledger:.claude/costs/rates.repo.json` blob on the ledger
  side of the GraphQL discovery, instead of `HEAD:`. The `rates_of` mapping
  that already runs through `totals_of` stays as it is.

### Adding only, and a collision

`role set` keeps refusing a role `rates.json` already rates, for the reason
`with_added_roles`' docstring gives: re-rating a shared role through a
repository's table would re-rate every row booked under it.

Moving the file creates one new case: the **shared table later takes up a role a
ledger adds**, because an `/update-muthur` port brings in a `rates.json` that
rates `artist`. The role then has two multipliers.

**That repository's rows keep its own entry, and every reader warns.** The
rows were booked against the ledger's multiplier, so switching them to the
shared one would re-rate their history. Every other repository's rows take the
shared entry, as they would anyway. `with_added_roles` therefore stops raising
on such a role. It returns the role in a `shadowed` list, and the table keeps
the ledger's multiplier for that repository.

Each reader names the collision with the repository, the role and both
multipliers, and points at `estimate.py role drop <name>` for adopting the
shared rate:

- `report.py`, local and cross-repo, in its notes;
- `check_estimates.py`, on stderr, without failing the vet run;
- the estimate notice, in a sentence.

The report's figures stay whole either way. Each row is rated by a defined
rule, and the warning is there so the person reading knows two rates exist.

### Migration

- **`ledger.py backfill`** is already the "move this repository onto the ledger"
  command. It also carries a tree `rates.repo.json` onto the ledger when the
  ledger has none. Where both exist and differ, it stops and names the
  difference rather than picking one.
- **`check_estimates.py` fails while the tree carries a `rates.repo.json`.** The
  message names `ledger.py backfill` and then `git rm` of the file. Without this,
  a stale tree copy reads as the live table to anyone who opens it.
- vzakharov/life (`tutor`) and vzakharov/vovazakharov.com (`artist`, still only
  on a branch) each migrate in one step: run `backfill`, or `role set` for a role
  only a branch holds.
- The squash body carries `[attn adopters]` for whoever took this PR's branch
  early: one paragraph naming the two commands.

## Edits

Against this PR's current state, after the `main` merge:

- `.claude/costs/lib/estimate.py`: `load_rates(costs)`'s tree read gives way to
  `ledger_rates(rev)`. `with_added_roles` returns shadowed roles instead of
  raising on them. Add a `role_change` plan for `append`.
- `.claude/costs/lib/ledger.py`: `RATES_PATH` beside `PREFIX`, plus
  `rates_text(rev)`. `backfill` carries the tree file.
- `.claude/costs/estimate.py`: the `role set` / `role drop` subcommands, and
  `set` reading the ledger table with the fetch-on-miss.
- `.claude/costs/check_estimates.py`: fetch, then load from the ledger. Fail on
  a tree `rates.repo.json`, and warn on a shadowed role.
- `.claude/costs/report.py` and `lib/github.py`: this-repo reads at the fetched
  tip; cross-repo uses the ledger-side blob. Shadowed roles go into the notes.
- `.claude/costs/hooks/estimate-notice.sh`: fetch when the ref is missing. The
  added-role sentence names `role set` as the way to add one, and the notice
  adds a sentence for a shadowed role.
- `.claude/costs/CLAUDE.md`: this PR's § "Human-hour estimates" bullet and
  § "The report" sentence get rewritten to say the table lives on
  `cost-ledger`, who writes it, and what a collision does.
- `.claude/skills/update-muthur/catalog/g7-cost-ledger.md`: the entry, re-pointed.
- Tests:
  - `test_estimate.py`: the ledger-backed table, and the `role set` / `drop`
    refusals.
  - `test_estimate_notice.py`: the fresh-container fetch, and the shadowed
    sentence.
  - `test_github.py`: the ledger-side blob.
  - `test_check_estimates.py`: a tree file fails, and a shadowed role warns.
  - `test_totals.py`: a shadowed role is rated per repository.
  - A `backfill` carry case.

  They run over a local bare `origin`, as the existing ledger tests do, so
  nothing touches the network.

## DRY notes

- **Reused, not duplicated:** `with_added_roles` stays the one parser and
  validator of the table, for every reader and for `role set`.
  `lib/ledger.append`, `text_at`, `fetch` and `REMOTE_REF` are the only ledger
  I/O; `role set` / `drop` are a new `Plan` for `append`, not new push code.
  `_blob_text` serves the GraphQL blob unchanged.
- **One loader:** `load_rates(costs)` and `load_shared_rates` give way to
  `ledger_rates(rev)`, where `rev` is the local ref for the writers and the
  fetched tip for this-repo's report. The cross-repo side already has text in
  hand and calls `with_added_roles` directly. A wrapper over it would add a name
  without removing any logic.
- **One warning text:** the shadowed-role sentence is built once, in
  `lib/estimate.py`, and printed by the three readers. Only the notice wraps it
  in its own prose.
- **Not extracted:** the "fetch only on a miss" check exists only in
  `estimate.py set`; the notice fetches on a missing ref, not a missing role.
  These are two different triggers, and one helper with a flag would hide that.

## Out of scope, noticed

The error in the report lists `physician` among the shared roles. vzakharov/life
has edited its own `rates.json`, so a cross-repo report run from any other
checkout raises on a life row booked as `physician`, for the same reason this
plan fixes. Once this lands, `physician` belongs in life's ledger table via
`role set`, and that is life's change to make, not this one.
