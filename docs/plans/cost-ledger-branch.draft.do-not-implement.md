> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Cost ledger on its own branch

## Goal

Count every session that spent money, whether or not its branch reaches main:
abandoned branches, the turn that merges, turns after finalize, and sessions run
on main itself. Keep a session's cost visible in its PR's diff while the work is
in flight, and keep main free of rows that land after finalize.

The design was settled in the parked session
(`docs/remove-before-merging/relay-1.md` § "Decisions"); this plan maps it onto
the code and closes what that session left open.

## Shape

- **`cost-ledger`**, an orphan branch, is the source of truth. It holds rows at
  the same path as today, `.claude/costs/sessions/<YYYY-MM>/<session-id>.json`,
  so every reader's path logic stays the same. The name is one constant; an
  adopter that already has a `cost-ledger` branch renames it at adoption.
- **Dual write.** The `Stop` hook always commits the row to `cost-ledger`, and
  also commits a display copy to the feature branch until that branch is
  finalized.
- **Finalized** means the PR's `<!-- finalize-attestation -->` comment names a
  SHA, and no commit after that SHA touches anything outside
  `.claude/costs/sessions/`. The hook asks GitHub once; on "yes" it caches the
  SHA in `tmp/costs/finalized/<branch>`, and later turns check only the local
  log against it. A work commit after the SHA makes the cache stale, so the hook
  writes to the branch again and asks GitHub again.
- **Readers union** `cost-ledger` with the default branch's tree, per session
  id, the later `lastResponseAt` winning. No migration copy: main's existing
  rows stay where they are and keep counting.
- **`/finalize` sweeps the display copies** that the branch added, and restores
  the rows it changed to the base's version, in the same commit as the
  `docs/remove-before-merging/` sweep.

## Steps

1. **Spike the push.** From `tmp/`, build an orphan commit holding one row and
   push it to `refs/heads/cost-ledger`. The session's git proxy has refused a
   branch delete before (relay-1 § State), and a refusal to create a branch
   outside `claude/*` would sink the design. If the push is refused, stop and
   report. Whether this first commit stays or is rebuilt by the backfill
   (question 3) is decided there.
2. **`lib/ledger.py`**: the branch-name constant, plus reading rows from a git
   ref with one `git ls-tree -r` and one `git cat-file --batch` over the blobs,
   returning `(path, text)` pairs. It has one CLI, `ledger.py stop-plan`, which
   the hook calls. That CLI prints the ledger ref, and whether to write the
   display copy, as `key=value` lines.
3. **`lib/finalized.py`**: one GraphQL query through `lib/github.py`'s `Client`
   for the PR whose head is the branch, plus its comments. From the attestation
   comment it takes the SHA from the marker. `/finalize` step 7 changes its
   marker to `<!-- finalize-attestation <full-sha> -->`, because a short SHA in
   prose is not a contract a parser can lean on. An older marker with no SHA
   counts as not finalized. A revoked marker
   (`<!-- finalize-attestation revoked -->`, question 2) counts as not
   finalized. The function also reads and writes the marker cache and runs the
   local `git log <sha>..HEAD -- . ':!.claude/costs/sessions'` invalidation. A
   SHA that is not an ancestor of HEAD (a rebase) counts as stale too.
4. **`hooks/stop-session-cost.sh`**:
   - Generalize `commit_row` into "commit this blob at this path on top of this
     parent, push it to this ref", and call it twice: once for `cost-ledger`,
     once for the feature branch.
   - The ledger write fetches `cost-ledger` and builds on its tip. A non-fast-
     forward push re-fetches and rebuilds, up to three tries; rows never
     collide, so a rebuild cannot lose another session's row. With no
     `cost-ledger` yet, it builds the orphan root.
   - The ledger write touches no ref but `refs/remotes/origin/cost-ledger` and
     no file in the tree, so it runs before `wait_out_harness_check`. Only the
     branch write still has to wait the check out.
   - On `main`/`master` the hook writes the ledger only, where today it exits.
     This closes the "trunk itself" gap.
   - A ledger push that fails after its retries blocks the stop once with the
     error, exactly as an unpriced turn does: the ledger is the accounting, and
     a quiet failure on the session's last turn loses it. The next turn's row
     covers the missed one.
5. **`session_cost.py` `previous()`**: read the row from both the tree and the
   ledger ref, and take the later one. After the sweep the tree copy is gone,
   and the estimate and unwritten-tail warning have to survive it.
6. **Readers**:
   - `report.py` `this_repo`: fetch `cost-ledger`, then union its rows with the
     tree's. Rows read off the ledger ref are reshaped in memory and never
     written back. Rewriting a ref's row is a commit on another branch, the same
     reason `--all-my-repos` never writes back.
   - `lib/github.py`: `REPO_FIELDS` gains a second `object(expression:)` for
     `refs/heads/cost-ledger:.claude/costs/sessions`. `discover` accepts a
     repository whose ledger is on either side. `ledger_texts` reads both sides'
     months, and `remote_ledger` unions them per repository before the
     cross-repository dedup it already does.
   - `check_estimates.py`: the sessions a branch carries become the tree's
     changed rows, plus the ledger's rows whose `branch` is this one. After the
     sweep, the first set is empty.
7. **`/finalize`** (`.claude/skills/finalize/SKILL.md`): the sweep paragraph in
   step 6 gains the rows. `git rm` every row the branch added against the merge
   base, and `git checkout <base> --` every row it changed. Step 7's marker
   gains the SHA. The step 7 rule "a head that moved only by
   `.claude/costs/sessions/`" stays, now as the property the hook's invalidation
   relies on.
8. **Explicit unfinalize** (question 2).
9. **Backfill** (question 3).
10. **Tests**: `test_stop_hook.py` gains a bare `origin` with and without
    `cost-ledger`, a racing second writer, main, and the finalized cache with
    and without a later work commit. `test_github.py` covers the union, and a
    ledger on one side only. `finalized.py` is tested through a stub
    `Transport`. `vet.sh` already globs `test_*.py`.
11. **Prose**: rewrite `.claude/costs/CLAUDE.md`:
    - a new § "Where rows live": the two writes, finalized detection, and what
      each failure costs;
    - § "What the totals do not cover" loses abandoned branches, the merge turn
      and the trunk;
    - § "The report" gains the union.

    Also add a line to `update-muthur`'s § on `.claude/costs/` saying that a
    `report.py` older than this change undercounts a migrated repository under
    `--all-my-repos`, so the cross-repo report runs from an updated checkout.

## Open questions

1. **When the GitHub query fails** (no `gh`, offline, 5xx after retries), what
   does the hook do about the display copy? The ledger write is unaffected
   either way.
   - **a (recommended):** treat the branch as not finalized: write the display
     copy, cache nothing, so the next turn asks again. The worst case is a stray
     row in main. This is a silent fallback, which CLAUDE.md lets in only with
     your explicit approval for this call site, so it is not in force until you
     approve it.
   - b: block the stop once with the error. This is loud, and nags every turn of
     a session without `gh`.
   - c: treat the branch as finalized. Diff visibility is lost without a word.
2. **The explicit unfinalize surface.**
   - **a (recommended):** a skill, `/unfinalize`. It edits the attestation
     comment in place to a revoked one (`<!-- finalize-attestation revoked -->`,
     saying when and why), flips the PR back to draft, and deletes this
     container's marker. That makes it a PR state change that the cost hook
     follows, rather than a cost-ledger feature.
   - b: only `python3 .claude/costs/finalized.py revoke`, with no skill and no
     draft flip.
   - c: none. The implicit unfinalize, a work commit, is enough.
3. **A one-off backfill of history that lives off main.**
   - **a (recommended):** run the batched recipe once over every remote branch
     and `refs/pull/*/head`, and seed `cost-ledger` with the rows main lacks or
     holds an older copy of: about 23 sessions and ~$72 by relay-1's count. The
     script lives in `tmp/` and is not shipped.
   - b: no backfill. The ledger counts from this change on, and the old gap
     stays in the history.

## DRY notes

- **Shared:** the plumbing commit (read-tree into a throwaway index,
  update-index, write-tree, commit-tree, push). It becomes one function taking a
  parent and a target ref, and the ledger and branch writes both call it.
  Duplicating it would mean two copies of the signing and throwaway-index rules.
- **Reused:** `lib/github.py`'s `Client` and `Transport` carry the finalized
  query, retries and test stub included. `lib/rows.py`'s `reshape` reads ledger
  rows. `estimate.latest` picks between the tree row and the ledger row in
  `previous()`.
- **One union, two callers:** "rows by session id, later `lastResponseAt` wins"
  is a function in `lib/ledger.py`. `report.py` (local) and `remote_ledger`
  (GitHub) both call it. The cross-repository rule in `remote_ledger` (first
  repo by name wins) stays separate: it answers a different question, the same
  session counted in a fork.
- **Not extracted:** reading a ref locally (`git cat-file`) and reading it on
  GitHub (GraphQL). They share only the path constant, and an abstraction over
  both transports would be an interface with two unrelated implementations.
- **The branch name** lives once, in `lib/ledger.py`. The hook gets it from
  `ledger.py stop-plan` rather than declaring its own.
