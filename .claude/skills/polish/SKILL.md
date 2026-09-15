---
description: >-
  Run the standard quality passes over work just done — `/dry`, then
  `/tend-prose` — scoped to the branch's whole diff, committing what they
  change. These are the passes `/go` runs at its Step 3; this skill is how work
  that never went through `/go` gets them. Invoke as `/polish [focus guidance]`.
  Use when the operator says "polish this", "tidy this up", or "run the checks
  that come after `/go`".
---

Two passes, in this order, over one scope:

1. **`/dry`** — load `@.claude/skills/dry/SKILL.md`. Duplication that was not visible before the code existed: apply the obvious wins, surface the ambiguous calls.
2. **`/tend-prose`** — load `@.claude/skills/tend-prose/SKILL.md`. The four defects, over the prose the work added.

**The order is load-bearing.** An extraction writes its own comments as it goes and moves prose between files, so tending first works over text `/dry` is about to rewrite or delete. Prose is tended last, over what survives.

Each pass is a real read of the diff and commits its own edits. "The diff looks clean" is a conclusion a pass reaches, never a reason not to run it.

Any argument is focus guidance and rides through to both passes unchanged — including a lens name, which is `/tend-prose`'s to read.

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

That range plus anything uncommitted is the scope.

**Re-covering ground an earlier pass covered is the expected shape**, not waste — a branch reaching `/finalize` has usually been polished once at `/go`, and later commits are exactly where drift re-enters. What the second run must not do is manufacture a finding to justify itself: a pass that changes nothing is a result, and gets reported as one.

## Where it runs

- **`@.claude/skills/go/SKILL.md` Step 3** — after implementing, before the PR.
- **`@.claude/skills/finalize/SKILL.md`, ahead of its numbered steps** — the backstop for work that reached a PR without passing through `/go`. That skill owns why it goes first.
- **On the operator's ask**, at any point in a session — the entry the other two exist to make unnecessary and routinely don't. A task asked for and done directly ends with the passes unrun unless someone names them.
- **`@.claude/skills/update-muthur/SKILL.md` Step 8**, over a port.

## Do NOT

- Run the vet suite, push, touch the PR, or flip a plan file — every caller owns its own land prep, and `/go` flips its plan file once this returns.
- Widen past the scope above into a general refactor of code the branch did not touch. Both passes are about the change, not the codebase.
- Skip either pass. Two passes are the whole skill; running one is not running it.
