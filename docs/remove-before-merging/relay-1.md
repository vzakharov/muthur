# Relay 1 — repo estimate roles onto `cost-ledger`

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator:** `/go claude/repo-estimate-roles-cwl9kz`
   - **Agent:** attached from the auto-branch
     `claude/repo-estimate-roles-r5flyo` (never pushed, nothing to delete) to
     this branch, PR https://github.com/vzakharov/muthur/pull/186 (draft, was
     `CONFLICTING`). Flipped the draft plan to in-progress quoting the go-ahead,
     ran the plan's first step (`/sync-branch`, main's version: raw merge
     commit, then a resolution commit), fixed one test the merge broke, vet
     green, pushed. Then built the code side of the rework and paused for the
     context budget — the operator has not replied since the `/go`.

## Intent

Implement `docs/plans/repo-estimate-roles.paused.md`: a repository's own
estimate roles (`rates.repo.json`) live on the `cost-ledger` branch beside the
rows, written by `estimate.py role set` / `role drop`, never on the default
branch; a role the shared `rates.json` later takes up stays at the repository's
multiplier for that repository's rows, and every reader warns.

## Decisions

- **Sync followed `main`'s `/sync-branch`** (conflicts committed raw, resolved
  in their own commit), not the branch's older single-commit version — `main` is
  the convention the branch lands into.
- **The resolution commit kept the branch's `addedRoles` blob at `HEAD:`**; its
  move to the ledger side is in the rework commit add3bc0, so the resolution's
  diff holds only conflict calls.
- **`ledger_rates(rev)` lives in `lib/ledger.py`, not `lib/estimate.py`**:
  `lib/ledger` imports `lib/rows`, which imports `lib/estimate`, so the loader
  that needs both git and the parser sits on the ledger side. `role_change` is a
  pure function in `lib/estimate.py`; `estimate.py`'s `change_role` wraps it in
  an `append` plan.
- **Dropping the last role deletes the file** (`commit` takes `None` for a path
  to remove) rather than allowing an empty `{"roles": {}}`, so `added_roles_of`
  keeps refusing an empty table.
- **`role set` on a role `rates.json` rates is refused** (`checked_new_role`);
  re-rating a shadowed role is therefore refused too — `role drop` adopts the
  shared rate.
- **Shadow notes go to stderr** in `report.py` (both modes) and
  `check_estimates.py`, following `rows_in`'s "stderr so `--json` stays
  parseable"; `estimate.py rates` carries them as a `notes` array for the hook.
- **The notice's fetch-on-missing-ref failure is to be said in the notice**, not
  swallowed (CLAUDE.md's silent-fallback rule); not built yet.

## Errors and dead ends

- The Markdown formatter hook rewrote `>>>>>>>` conflict markers into
  blockquotes on the first edit of a hunk; resolving both hunks of a file in one
  `Edit` avoids it.

## State

- Branch `claude/repo-estimate-roles-cwl9kz`, PR
  https://github.com/vzakharov/muthur/pull/186 (draft, base `main`), last pushed
  2668cb2. Merge state after the sync not re-checked on GitHub.
- Plan: `docs/plans/repo-estimate-roles.paused.md`; its `## Progress` section is
  the done/left record.
- Vet: green at 0f28bb7; after add3bc0, four test files fail by design
  (`test_check_estimates.py`, `test_estimate.py`, `test_estimate_notice.py`,
  `test_github.py`) — they still use the tree table.
- Estimate: this session 5.5 h senior developer ("The main merge across seven
  conflicted files plus the ledger-backed writer and readers: git-ledger
  push/fetch semantics and the shadowed-role rule need a senior who has shipped
  concurrent-write code"). Remainder handed on: 3.5 h senior developer (tests
  over bare-origin clones, the notice hook's fetch and shadow sentence) and 1.5
  h senior editor ("The cost-ledger docs and catalog entry must restate the
  table's new home and collision rule exactly, without leaving the old
  default-branch story behind").

## Pointers

- `docs/plans/repo-estimate-roles.paused.md` — the plan and its `## Progress`.
- `.claude/costs/lib/estimate.py`, `lib/ledger.py`, `estimate.py`,
  `check_estimates.py`, `report.py`, `lib/github.py` — the code already moved.
- `.claude/costs/test_stop_hook.py` `Clone` — the bare-origin fixture the tests
  build on.
- Predecessor transcript:
  https://claude.ai/code/session_01SRDCi3snv4pFJxPPeM6LDk

## Next step

Resume the paused plan with `/go`: the `## Progress` "Left" list — tests, the
estimate notice hook, `.claude/costs/CLAUDE.md` and the catalog entry — then
`/polish` and the `/pr` refresh.
