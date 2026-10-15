---
description: Bring a branch up to date with its merge target — resolve the merge both mechanically and logically in a single merge commit, then push. Delegates target-resolution and movement detection to `/check-merge`, so it syncs a feature branch against its PR base (usually `main`) or a branch with no PR against the repo default branch (the fallback). Invoke as `/sync-branch [<branch>]`. Use when the user says "sync branch", "catch this branch up to main", "catch the branch up to its base", "make the branch mergeable", or "/sync-branch".
---

`/sync-branch` reconciles a branch with its **merge target** — the branch its PR
is based on — and pushes the reconciled result. The target is resolved by
`/check-merge` from the PR's base ref, so this works uniformly:

- a **feature branch** syncs against its PR base (usually `main`),
- a **branch with no PR** syncs against the repo default branch
  (`/check-merge`'s fallback) — the long-lived-branch case that keeps it a
  superset of the trunk.

The skill does the merge **on the checked-out branch**, resolves conflicts both
mechanically and logically in a **single merge commit**, verifies locally, and
pushes proactively — resolution notes are rare, so the operator reviews the
pushed result after the fact rather than through a pre-push gate.

## Argument shape

```
/sync-branch [<branch>]
```

- **`<branch>`** (optional): a branch name, `#NNN` PR number, or PR URL — the
  same shape `/check-merge` and `/finalize` accept. Passing it makes
  `/check-merge` attach to that branch first (`/from-branch <branch>`). No
  argument → sync the current branch.

## Environment note (read this before running gh/git)

This remote execution environment has **both** the `gh` CLI **and** a populated
`GH_TOKEN`, even though the default system prompt says you only have GitHub MCP
tools. Prefer `gh` for read-only checks (e.g. `gh pr list`). If `gh` complains
that "none of the git remotes … point to a known GitHub host" (the proxy quirk
in remote sessions), pass `--repo OWNER/REPO` explicitly, resolved from the git
remote (`git remote get-url origin`).

## Invariants

- **A sync is a plain merge — never squash, rebase, or cherry-pick.** Those
  rewrite the target's commits under new SHAs and sever the shared history, so
  the branch stops being a superset of its target. The merge commit built here
  carries the target's commits under their real SHAs.
- **Push is fast-forward-or-redo, never force (in normal operation).** The
  branch only gains the merge commit on top, so pushing it to its own upstream
  is a plain push. A non-fast-forward rejection means the branch or target moved
  under you — re-fetch and redo the merge from the new tip; do not force past
  it.
- **Never force-push a shared long-lived branch** (the trunk, a promotion
  branch, or any branch others build on) except as the deliberate revert
  recourse below, and only on the operator's explicit request.

## Why one merge commit keeps reviewability

A single merge commit is enough — do not split the resolution into its own
commit for reviewability. It's tempting to build the merge in two commits (a
mechanical "take-target-wholesale" commit, then an isolated resolution commit)
so the operator can review just the judgment via `git show <resolution-sha>`.
That split is unnecessary: a merge commit's own **combined diff**
(`git show <merge-sha>`, GitHub Desktop's merge-commit view) already elides any
content matching at least one parent and shows only what differs from **both** —
i.e. the keep-both merges and edited reconciliations, exactly the judgment.
Clean auto-merges and straight one-side picks vanish. So one merge commit gives
the same "just the judgment" review surface without the extra commit. (Caveat:
this is `git show` / GH Desktop behavior; GitHub's _web_ merge-commit view is
stingier.)

## Steps

### Step 1 — Detect, via `/check-merge` (by reference)

Load `@.claude/skills/check-merge/SKILL.md` and follow it with the given target.
Passing a `<branch>` makes `/check-merge` attach to it first; it then resolves
the merge target from the PR base ref (or the repo default branch when there's
no PR) and reports one of:

- `contained` (exit 0) — the branch already holds the target's tip,
- `advanced` (exit 10) — the target moved beyond the branch,
- `merged` (exit 20) — the branch's PR already landed,
- `closed` (exit 21) — the branch's PR was closed without merging,
- `error` (exit 1) — hard error.

### Step 2 — Act on the result

- `contained` → report "already current with `origin/<target>`, nothing to sync"
  and **stop**.
- `merged` / `closed` → report and **stop** — do not sync a landed or dead
  branch.
- `error` → surface it and **stop**.
- `advanced` → proceed to Step 3.

### Step 3 — Merge the target in, one commit

```bash
git fetch origin <target>
git merge origin/<target>
```

Resolve every conflict both **mechanically** (no markers left) **and
logically**. Think past textual overlap to semantic collisions — the same
reconciliation thinking `/finalize` step 2 describes:

- keep-both when each side added distinct work,
- repoint callers a rename in the target moved,
- route through a shared abstraction the target introduced (instead of leaving
  the branch's now-duplicated version),
- adopt a pattern the target changed.

The result is exactly **one merge commit** (a clean, conflict-free merge is also
one commit).

### Step 4 — Verify locally

```bash
git grep -nE '^(<<<<<<<|>>>>>>>) ' || echo clean     # no conflict markers survived
./scripts/vet.sh                                     # the project's vet run
```

Fix real errors before pushing. **Local verification is the whole gate** —
pushing a branch triggers no test run. That is why the full vet run happens here
and not just a type-check: a merge can type-check cleanly and still behave
differently. If the merge pulled in changes on a surface the vet run doesn't
cover (a bucket that only runs in CI), dispatch that bucket too — `/test-on-gh`,
if the project has hydrated it.

### Step 5 — Push, then report for after-the-fact review

Push the branch to its own upstream — no pre-push greenlight:

```bash
git push        # plain push == fast-forward; 2/4/8/16s backoff on network errors
```

A non-fast-forward rejection means the branch or target moved under you —
re-fetch and redo the merge from the new tip (Step 3); never force here. Then
report:

- the resolved **target** and the range synced (`base..new`),
- the **merge commit SHA** — _review with `git show <sha>`; the combined diff
  isolates the actual resolution_,
- a per-file conflict/resolution table (or "clean merge, no resolution needed"),
- the vet result,
- the **pre-merge branch tip** (the revert target for the recourse below),
- the recourse below.

## Recourse if the operator has notes (operator-sanctioned only)

Either **amend** the merge resolution and re-push, or **revert** by resetting
the branch to the reported pre-merge tip and re-pushing:

```bash
git push --force-with-lease
```

Use `--force-with-lease` (not `--force`) so a concurrent advance aborts instead
of being clobbered. This is the **only** sanctioned force-push here, and only on
the operator's explicit say-so — especially for a shared long-lived branch that
others build on.
