# The cost row rides the agent's own commits

## Why

`hooks/stop-session-cost.sh` commits and pushes the session's display copy
(`.claude/costs/sessions/<month>/<id>.json`) to the working branch on **every
turn** — one `chore:`-style commit per turn, so a branch's history is mostly
cost rows. That made sense before `cost-ledger` existed; now the ledger is the
source of truth and gets its own per-turn commit anyway. The display copy only
needs to keep the PR's diff showing what the work cost, and a copy refreshed at
each of the agent's own commits does that.

## What changes

### 1. A `PreToolUse` hook stages the row into the agent's commit

New `.claude/costs/hooks/stage-cost-row.sh`, registered under `PreToolUse` with
matcher `Bash` beside `file-tools-nudge.py`. When the command about to run is a
`git commit`, it prices the session into `tmp/`
(`session_cost.py --row-path --out`, ~0.1 s), moves the row into place and
`git add`s it — so whatever the command commits carries the row. It never blocks
the command: every failure exits 0, and the `Stop` hook still reports pricing
and ledger failures as now.

It stages nothing — the command runs as if the hook were absent — when:

- **the command is not a commit**: no `git [-c k=v | -C dir]… commit` followed
  by whitespace or end (so `commit-tree`, `log --grep commit` do not match);
- **the branch gets no copy**: `ledger.py display <branch>` (today's
  `stop-plan`, renamed — the `Stop` hook no longer asks it) says no — the trunk,
  or a finalized branch;
- **the commit cannot land in this repository**: the payload's `cwd` is in a
  different work tree (a `/go` delegate's worktree) and the command does not
  name this root by path (`cd <root>`, `-C <root>`, as every multi-repo
  session's call does);
- **a merge, cherry-pick, revert or rebase is in progress** (`MERGE_HEAD` and
  kin under `git rev-parse --git-path`): concluding it must commit exactly what
  git left, which `/sync-branch` relies on;
- **the command manages the rows itself** — it names `.claude/costs/sessions`.
  That is `/finalize`'s sweep (`git rm -r .claude/costs/sessions` then commit):
  a staged row would make `git rm` refuse ("changes staged in the index") or
  re-add the row the sweep deletes;
- **nothing else would be committed**: the index matches `HEAD` outside the row,
  and the command neither stages (`git add|rm|mv`) nor commits with `-a`,
  `--all` or `--amend`. Otherwise a commit that would have failed with "nothing
  to commit" succeeds as a row-only commit under the agent's message — exactly
  the clutter this removes.

### 2. The `Stop` hook stops touching the branch

`stop-session-cost.sh` keeps pricing the turn and appending the row to
`cost-ledger`. It drops the display commit: `commit_row`, the push, the
`stop-plan` call. What it keeps is the guarantee that the row never leaves the
tree unclean for the harness's git check:

- **A row that differs from `HEAD` at stop is put back to `HEAD`'s copy** (or
  removed, where `HEAD` has none), index and file alike. That is the hook having
  staged it for a commit that did not take it — a pathspec commit
  (`git commit -- a.py`), a commit that failed, a false-positive match — or a
  hand run of `session_cost.py`. Nothing is lost: the ledger holds this turn's
  row, and the next agent commit re-prices.
- It still waits out the harness's check before touching the tree, and still
  tells the agent, with one `exit 2` bailed on `stop_hook_active`, when the
  check read a stray row — the message now says the row was put back rather than
  committed.

### 3. Dead code and its tests

- `ledger.py commit-row` loses its last production caller and goes;
  `test_estimate_notice.py` builds its broken-rates commit with
  `lib.ledger_branch.commit` directly. `row_change`/`commit` stay — the ledger
  append uses them.
- `test_stop_hook.py`'s display-copy tests move to a new
  `test_stage_cost_row.py`; the `Clone` fixture moves to a shared module both
  import. New cases: the row rides a commit; trunk and finalized branches get
  none; a work commit after the attestation brings it back; each skip condition
  above; a stray staged row is put back at stop, leaving the tree clean and the
  agent's own staged work untouched.

### 4. Every place that states the old contract

- `.claude/costs/CLAUDE.md` § "Where rows live" (the display copy is refreshed
  at the agent's commits) and § "Running beside the harness's Stop check"
  (rewritten around the revert; the throwaway-index commit and push-before-move
  go).
- `.claude/skills/finalize/SKILL.md` steps 6–7: "the cost ledger's `Stop` hook"
  → the staging hook; the sweep's command naming the directory is what keeps the
  hook out of it.
- `.claude/skills/relay/after-handoff.md`: the predecessor's "cost ledger's own
  commits are the one exception" goes — it no longer commits at all.
- `.claude/skills/update-muthur/catalog/g7-cost-ledger.md`: no per-turn commit
  to the working branch; six hook entries, not five.
- `scripts/multi-repo-hooks.py`: the new hook in `PER_REPO`.
- `.claude/hooks/lib.sh` header: four hooks under `.claude/costs/hooks/`.
- `scripts/gh_export/awaiting.py` docstring: a branch's head is no longer
  "routinely a session-cost row", so the reason a timestamp cannot stand in for
  "seen" is restated without it.

## Edge cases, and what each costs

- **A session that never commits** (an answer, a review, a relay's predecessor)
  leaves no copy on the branch. The ledger counts it as before; the PR diff just
  does not show it. Accepted: that is the trade the change asks for.
- **The copy lags the work** by whatever ran after the last commit — up to and
  including `/finalize`, whose sweep carries the latest rows into the ledger
  (`backfill HEAD`) before deleting them, so the ledger loses nothing.
- **A commit chained before a push** (`git add -A && git commit … && git push`)
  is the common shape and works: the row is staged before the command starts.
- **Parallel tool calls**: a `git` command running beside the hook's `git add`
  can meet `index.lock`. The hook's own failure is silent; the other command
  fails as git always does under a held lock. Agents do not commit in parallel
  with other git calls, so this is noted, not engineered around.
- **A match inside a string** (`gh pr create --body "…git commit…"`) stages the
  row with nothing to commit it; the `Stop` revert cleans it up.
- **A finalized branch** never gets a row staged, so `finalized.holds`'s "rows
  only after the SHA" clause stays true; a work commit reopens it exactly as
  today.

## Rejected

A `PostToolUse` amend (fold the row into the commit after it is made) breaks on
`commit && push`, which then needs a force-push. A git `pre-commit` hook needs
`core.hooksPath` set per clone and git hands it a temporary index on a pathspec
commit. Keeping the per-turn commit but squashing at `/finalize` leaves the
clutter visible for the PR's whole life, which is the complaint.

## DRY notes

- **Pricing** reuses `session_cost.py --row-path --out` exactly as the `Stop`
  hook calls it; no second pricing path.
- **The copy-or-not decision** is the one `lib/finalized.py` + the trunk list in
  `ledger.py`, renamed from `stop-plan` to `display` and called by the new hook
  only.
- **Shell helpers** (`read_payload`, `field`, `project_root`, `say`,
  `need_command`) come from `.claude/hooks/lib.sh`; the `dirty` helper is small
  enough that the two hooks each keep a line of it rather than growing a
  costs-only shell lib.
- **The test fixture** (`Clone`: a repo with an origin, a fake `gh`, a
  transcript) moves out of `test_stop_hook.py` into a shared module rather than
  being copied into the new test file.
