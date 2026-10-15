# Cost ledger on its own branch

## Goal

Count every session that spent money, whether or not its branch reaches main:
abandoned branches, the turn that merges, turns after finalize, and sessions run
on main itself. Keep a session's cost visible in its PR's diff while the work is
in flight, and take the rows off main altogether.

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
- **Main carries no rows.** This PR backfills every row main and every other ref
  holds into `cost-ledger`, then deletes `.claude/costs/sessions/` from the
  tree. Each adopter does the same in its port, so the change is
  `[attn adopters]`.
- **Readers union** `cost-ledger` with the default branch's tree, per session
  id, the later `lastResponseAt` winning. The tree side is how an adopter that
  has not migrated yet still counts, under its own report and under someone
  else's `--all-my-repos`.
- **`/finalize` moves the display copies into the ledger, then sweeps them**, in
  the same commit as the `docs/remove-before-merging/` sweep. The move comes
  first because a branch that merged this change in mid-flight carries rows from
  before the merge that the old hook never sent to the ledger.
- **`/finalize revoke`** withdraws the attestation explicitly: the comment is
  edited in place to a revoked marker, and the PR goes back to draft.

## Steps

1. **Spike the push.** From `tmp/`, build an orphan commit holding one row and
   push it to `refs/heads/cost-ledger`. The session's git proxy has refused a
   branch delete before (relay-1 § State), and a refusal to create a branch
   outside `claude/*` would sink the design. If the push is refused, stop and
   report. The spike's commit is thrown away: step 9's backfill builds the real
   root.
2. **`lib/ledger.py`** and its CLI, `.claude/costs/ledger.py`:
   - the branch-name constant;
   - reading rows from a git ref with one `git ls-tree -r` and one
     `git cat-file --batch` over the blobs, returning `(path, text)` pairs;
   - `stop-plan`, which the hook calls: it prints the ledger ref and whether to
     write the display copy, as `key=value` lines;
   - `backfill [<ref>...]`: reads every named ref (by default every
     `refs/remotes/origin/*` plus `refs/pull/*/head`, fetched into a private
     `refs/costs-pr/*` namespace), keeps per session id the row with the latest
     `lastResponseAt`, and commits whatever the ledger lacks or holds older, in
     one commit on the ledger tip, through the same push-and-retry as the hook.
     It is idempotent, so a second run commits nothing new.
3. **`lib/finalized.py`**: one GraphQL query through `lib/github.py`'s `Client`
   for the PR whose head is the branch, plus its comments. From the attestation
   comment it takes the SHA from the marker. `/finalize` step 7 changes its
   marker to `<!-- finalize-attestation <full-sha> -->`, because a short SHA in
   prose is not a contract a parser can lean on. An older marker with no SHA
   counts as not finalized. A revoked marker
   (`<!-- finalize-attestation revoked -->`) counts as not finalized. The
   function also reads and writes the marker cache and runs the local
   `git log <sha>..HEAD -- . ':!.claude/costs/sessions'` invalidation. A SHA
   that is not an ancestor of HEAD (a rebase) counts as stale too.
   - **A failed query counts as not finalized**: the hook writes the display
     copy, caches nothing, and asks again next turn. This is a silent fallback,
     approved by the operator for this call site («1a»), and the code comment on
     it says so. Its worst case is one stray row on main, which the next
     finalize of any branch does not touch and the report still counts.
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
7. **`/finalize`** (`.claude/skills/finalize/SKILL.md`):
   - The sweep paragraph in step 6 gains the rows:
     `python3 .claude/costs/ledger.py backfill HEAD`, then
     `git rm -r .claude/costs/sessions`.
   - Step 7's marker gains the SHA.
   - The step 7 rule "a head that moved only by `.claude/costs/sessions/`"
     stays, now as the property the hook's invalidation relies on.
   - **`revoke` mode**:
     - edit the attestation comment in place to
       `<!-- finalize-attestation revoked -->`, saying when and why;
     - put the PR back to draft with `gh pr ready --undo`;
     - delete `tmp/costs/finalized/<branch>`.

     The description names the mode, which makes it an always-loaded edit, so
     `SKILL.md` is staged first (`.claude/rules/staging.md`).

8. **`/check-merge`** reads the attestation by marker. It learns that a revoked
   one is no attestation.
9. **Migrate this repo**:
   - run `ledger.py backfill` over every ref and check that the ledger holds
     every session id main holds;
   - `git rm -r .claude/costs/sessions`.

   `/finalize` on this PR reruns the backfill (step 7), which catches rows that
   other PRs merged into main in the meantime.

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

    `update-muthur`'s § on `.claude/costs/` loses the "source's own ledger"
    carve-out for `sessions/`, which no longer exists on main to sync. The
    squash body carries the `Adopters:` paragraph: run
    `python3 .claude/costs/ledger.py backfill`, check its count, and
    `git rm -r .claude/costs/sessions` in the port's PR. Their operator says yes
    first, because the backfill pushes a new branch to their origin. A
    `report.py` older than this change undercounts a migrated repository under
    `--all-my-repos`, so the cross-repo report runs from an updated checkout.

## Progress

Done (through 4281ba5):

- **Step 1.** The push works: `cost-ledger` exists on origin, rooted at ec2bfe9,
  an orphan commit with an empty tree. It stays as the ledger's root rather than
  being thrown away; the backfill builds on it.
- **Step 2.** `lib/ledger.py` and the `ledger.py` CLI (`backfill`, `fetch`,
  `stop-plan`, `commit-row`, `append-row`). The commit plumbing and the
  row-commit subject moved from the hook into `lib/ledger.py`, so the branch
  write calls `ledger.py commit-row` too: one copy of the signing and
  throwaway-index rules. `union` picks by `recency` = (`lastResponseAt`,
  `estimate.at`), so an estimate edited onto a finished row wins a tie. Also
  `latest_row(session_id)`, tree plus local ledger copy, for steps 5–6.
  `backfill` has not been run yet.
- **Step 3.** `lib/finalized.py`. The marker regex already reads
  `<!-- finalize-attestation <sha>|revoked -->`.
- **Step 4.** The hook: `ledger fetch` (a failed fetch skips the ledger write,
  since the row would be priced without the ledger's estimate), price,
  `append-row`, `stop-plan`, and only then the harness-check wait and the
  display copy. On the trunk it writes the ledger alone. A ledger error blocks
  the stop once with git's whole message. The 13 existing hook tests pass, one
  renamed: an unreachable origin is now reported as the ledger missing the row.

Left:

- **Steps 5–11** as written above. Two additions found on the way:
  - `estimate.py --session` for a session whose row is only on the ledger:
    commit the edited row to the ledger with `ledger.append` (`recency` already
    makes the edit win). `check_estimates.running_is_estimated` and
    `session_cost.previous` should both use `ledger.latest_row`.
  - The hook tests reach GitHub: `stop-plan` on the test's `feature` branch
    parses the bare origin's path as a repo and runs `gh`, which fails and falls
    back to display. Step 10 needs a seam there (a test transport, or no query
    when origin is not on GitHub) and tests for the finalized cache.

## Decided

- **The query fails → not finalized** (operator: «1a»), as step 3 states.
- **Explicit unfinalize is `/finalize revoke`** (operator: «2
  `/finalize revoke`»), not a separate skill and not a bare script. The
  cache-only `finalized.py revoke` and doing without one were both ruled out.
- **Backfill everything, and ship it** (operator: «3а. И это должен будет
  сделать каждый адоптер, так как после этого пиара на main-е больше не будет
  костов»). The backfill takes main's rows too, so main can drop `sessions/`,
  and it is a shipped command rather than a `tmp/` script, because every adopter
  runs it once and `/finalize` runs it on every branch.

## DRY notes

- **Shared:** the plumbing commit (read-tree into a throwaway index,
  update-index, write-tree, commit-tree, push). It becomes one function taking a
  parent and a target ref, and the ledger and branch writes both call it.
  Duplicating it would mean two copies of the signing and throwaway-index rules.
- **Reused:** `lib/github.py`'s `Client` and `Transport` carry the finalized
  query, retries and test stub included. `lib/rows.py`'s `reshape` reads ledger
  rows. `estimate.latest` picks between the tree row and the ledger row in
  `previous()`.
- **One union, three callers:** "rows by session id, later `lastResponseAt`
  wins" is a function in `lib/ledger.py`. `report.py` (local), `remote_ledger`
  (GitHub) and `backfill` all call it.
- **One ledger write, two callers:** the hook's push-and-retry onto the ledger
  tip and `backfill`'s commit are the same plumbing with one row or many, so
  `backfill` shells out to the hook's function or the function moves into
  `ledger.py` and the hook calls that. The implementation picks whichever keeps
  the signing and throwaway-index rules in one place. The cross-repository rule
  in `remote_ledger` (first repo by name wins) stays separate: it answers a
  different question, the same session counted in a fork.
- **Not extracted:** reading a ref locally (`git cat-file`) and reading it on
  GitHub (GraphQL). They share only the path constant, and an abstraction over
  both transports would be an interface with two unrelated implementations.
- **The branch name** lives once, in `lib/ledger.py`. The hook gets it from
  `ledger.py stop-plan` rather than declaring its own.
