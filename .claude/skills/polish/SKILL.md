---
description: >-
  Run the standard quality passes over work just done — `/dry`, then
  `/tend-prose` — scoped to what the branch has changed since it was last
  polished, committing what they change. These are the passes `/go` runs at its
  Step 3; this skill is how work that never went through `/go` gets them. Invoke
  as `/polish [focus guidance]`, or `/polish full` to re-read the whole branch.
  Use when the operator says "polish this", "tidy this up", or "run the checks
  that come after `/go`".
---

Two passes, in this order, over one scope:

1. **`/dry`** — load `@.claude/skills/dry/SKILL.md`. Duplication that was not visible before the code existed: apply the obvious wins, surface the ambiguous calls.
2. **`/tend-prose`** — load `@.claude/skills/tend-prose/SKILL.md`. The four defects, over the prose the work added.

**The order is load-bearing.** An extraction writes its own comments as it goes and moves prose between files, so tending first works over text `/dry` is about to rewrite or delete. Prose is tended last, over what survives.

Each pass is a real read of the diff and commits its own edits. "The diff looks clean" is a conclusion a pass reaches, never a reason not to run it — and a pass that changes nothing is a result, reported as one.

Any argument other than `full` is focus guidance and rides through to both passes unchanged — including a lens name, which is `/tend-prose`'s to read. `full` is this skill's own, and § "The watermark" below says what it does.

## Scope: the branch, not the session

Both passes carry their own scope ladders and both bottom out at unpushed work (`git diff HEAD`, then `@{u}..HEAD`). That is right when they are invoked seconds after implementing, and wrong everywhere else this skill is called from: at `/finalize`, or on a branch another session wrote, the work is already pushed and the ladder falls through to "nothing to review".

So the scope is resolved **here**, once, and handed to both passes:

```bash
gh pr view --json baseRefName --jq .baseRefName   # the base, when there is a PR and gh reaches it
git fetch origin <base>                           # a stale ref silently widens the range
git diff origin/<base>...HEAD                     # the branch's net change
```

**The fetch is not optional.** `origin/<base>` in a session's working copy is as old as the clone; against a stale one the range picks up every commit the base has landed since, and the pass reads a codebase's worth of other people's work as if this branch had written it.

`<base>` is the repo's default branch wherever that lookup has no answer — no PR yet, no `gh`, no GitHub at all. Nothing here needs the PR except the name of the branch this work merges into.

That range plus anything uncommitted is the scope, unless the watermark below moves its floor up.

## The watermark

A branch is polished more than once — at `/go`, again at `/finalize` — and the second run has no business re-reading what the first one cleared. So a full run records where it got to, in `docs/remove-before-merging/polished.md`:

```markdown
# Polished

| Head | When | Range read |
| --- | --- | --- |
| `a1b2c3d` | 2026-09-15 | `origin/main...HEAD` |
| `e4f5a6b` | 2026-09-16 | `a1b2c3d..HEAD` |
```

**The last row is the watermark.** The rows above it are the branch's polish history, and the directory's sweep at `/finalize` throws the lot away before anything lands. So the scope resolved above gets one rung narrower: `git diff <watermark>..HEAD` where a row names a commit, the full `origin/<base>...HEAD` where none does.

Write the row **after** both passes have committed, recording `git rev-parse --short HEAD` as it stands then, and commit it on its own (`docs: record /polish watermark`). That commit lands inside the next run's range and is not work — skip it, and any later commit that touches nothing else.

Three things put the floor back at the base:

- **No file, or no row in it** — the first full run on this branch.
- **A watermark `HEAD` does not descend from** (`git merge-base --is-ancestor <sha> HEAD`) — the branch was rebased, amended or reset, so the row names a commit that no longer describes this history.
- **`/polish full`** — the operator asking for the whole branch again, which is the override for a watermark that is merely *wrong*: written by a run that cut itself short, or by one whose judgment they don't share.

**A focused run writes no row.** Guidance narrows what the passes look for, so a clean result says nothing about the defects they weren't looking for, and a row claiming otherwise would bury those for the rest of the branch's life.

**The watermark narrows the subject, not the comparison.** `/dry`'s findings are duplications *between* the new code and what was already there, so the commits below the watermark and the rest of the codebase stay readable as context. It is what gets reviewed that starts at the watermark, not what it gets compared against.

## Where it runs

- **`@.claude/skills/go/SKILL.md` Step 3** — after implementing, before the PR.
- **`@.claude/skills/finalize/SKILL.md`, ahead of its numbered steps** — the backstop for work that reached a PR without passing through `/go`. That skill owns why it goes first.
- **On the operator's ask**, at any point in a session — the entry the other two exist to make unnecessary and routinely don't. A task asked for and done directly ends with the passes unrun unless someone names them.
- **`@.claude/skills/update-muthur/SKILL.md` Step 8**, over a port.

## Do NOT

- Run the vet suite, push, touch the PR, or flip a plan file — every caller owns its own land prep, and `/go` flips its plan file once this returns.
- Widen past the scope above into a general refactor of code the branch did not touch. Both passes are about the change, not the codebase.
- Skip either pass. Two passes are the whole skill; running one is not running it.
