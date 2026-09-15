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

**The order is load-bearing.** An extraction writes its own comments and docstrings as it goes, and moves prose from one file into another; tending first would work over text `/dry` is about to rewrite, move or delete. Prose is tended last, over what survives.

Each pass is a real read of the diff and commits its own edits. "The diff looks clean" is a conclusion a pass reaches, never a reason not to run it.

Any argument is focus guidance and rides through to both passes unchanged — including a lens name, which is `/tend-prose`'s to read.

## Scope: the branch, not the session

Both passes carry their own scope ladders and both bottom out at unpushed work (`git diff HEAD`, then `@{u}..HEAD`). That is right when they are invoked seconds after implementing, and wrong everywhere else this skill is called from: at `/finalize`, or on a branch another session wrote, the work is already pushed and the ladder falls through to "nothing to review".

So the scope is resolved **here**, once, and handed to both passes:

```bash
gh pr view --json baseRefName --jq .baseRefName   # the base, when there is a PR and gh reaches it
git diff origin/<base>...HEAD                     # the branch's net change
```

`<base>` is the repo's default branch wherever that lookup has no answer — no PR yet, no `gh`, no GitHub at all. Nothing here needs the PR except the name of the branch this work merges into.

That range plus anything uncommitted is the scope. In the ordinary `/go` case it is the same work the session wrote; everywhere else it is the range that ladder cannot reach on its own.

**Re-covering ground an earlier pass covered is the expected shape**, not waste — a branch reaching `/finalize` has usually been polished once at `/go`, and later commits are exactly where drift re-enters. What the second run must not do is manufacture a finding to justify itself: a pass that changes nothing is a result, and gets reported as one.

## Where it runs

- **`@.claude/skills/go/SKILL.md` Step 3** — after implementing, before the PR.
- **`@.claude/skills/finalize/SKILL.md`, before anything else it does.** Land prep is the funnel every branch reaches however its work got written, so it is where a branch that never passed through `/go` still gets the passes — and the last point at which changing the diff is cheap, since vetting, the base merge and the attestation are all statements about a diff that has stopped moving.
- **On the operator's ask**, at any point in a session. This is the entry the other two exist to make unnecessary and routinely don't: a task done directly, without `/go` in front of it, ends with the passes unrun unless someone names them.
- **`@.claude/skills/update-muthur/SKILL.md` Step 8**, over a port.

## Do NOT

- Run the vet suite, push, touch the PR, or flip a plan file — every caller owns its own land prep, and `/go` flips its plan file once this returns.
- Widen past the scope above into a general refactor of code the branch did not touch. Both passes are about the change, not the codebase.
- Skip either pass. Two passes are the whole skill; running one is not running it.
