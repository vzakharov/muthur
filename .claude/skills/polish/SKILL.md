---
description: >-
  Run the standard quality passes over work just done — `/dry`, then
  `/tend-prose` — scoped to what the branch has changed since it was last
  polished, committing what they change. These are the passes `/go` runs at its
  Step 3; this skill is how work that never went through `/go` gets them. Invoke
  as `/polish [focus guidance]`, or `/polish full` to re-read the branch's whole
  diff against its base rather than only what it changed since the last polish
  commit.
  Use when the operator says "polish this", "tidy this up", or "run the checks
  that come after `/go`".
---

Two passes, in this order, over one scope:

1. **`/dry`** — load `@.claude/skills/dry/SKILL.md`. Duplication that was not visible before the code existed: apply the obvious wins, surface the ambiguous calls.
2. **`/tend-prose`** — load `@.claude/skills/tend-prose/SKILL.md`. The four defects, over the prose the work added.

**The order is load-bearing.** An extraction writes its own comments as it goes and moves prose between files, so tending first works over text `/dry` is about to rewrite or delete. Prose is tended last, over what survives.

Each pass is a real read of the diff and commits its own edits. "The diff looks clean" is a conclusion a pass reaches, never a reason not to run it — and a pass that changes nothing is a result, reported as one.

**Push before reporting.** Every run leaves a commit — each pass's edits, or the empty mark below — and in a remote session an unpushed commit is invisible to the operator reviewing from another machine (CLAUDE.md § "Git conventions"). No caller is pre-empted: `/go` and `/finalize` push again for their own reasons, and pushing unvetted mid-branch work is ordinary development here rather than a shortcut past land prep.

Any argument other than `full` is focus guidance and rides through to both passes unchanged — including a lens name, which is `/tend-prose`'s to read. `full` is this skill's own, and § "The floor" below says what it does.

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

That range plus anything uncommitted is the scope, unless the floor below moves up.

**A staged copy counts by its diff against the real file.** One under `docs/remove-before-merging/` (`@.claude/rules/staging.md`) shows in the range as a whole new file, so a pass reading it that way reviews all of `CLAUDE.md` as this branch's prose. Its change is `git diff --no-index <real path> <copy>`, for each pair `scripts/staged.sh list` prints, and the rest of the copy is context.

## The floor: the last polish commit

A branch is polished more than once — at `/go`, again at `/finalize` — and the second run has no business re-reading what the first one cleared. The passes commit their own edits, so the run is already in the history; what makes it findable is the subject line every commit either pass makes here carries:

```
polish: <what the passes changed>
```

`polish:` is a branch-local commit type, outside the standard set on purpose: the passes' edits are `refactor:` or `docs:` by nature, which says nothing about who made them or why, so no standard type would carry the mark. It reaches no trunk — the squash gives the branch one subject of its own, written by hand — so it costs a reader of `main` nothing and gives a reader of the branch a legible `git log --oneline`. A focused run writes `polish(<the guidance>):` instead, which the lookup below skips: guidance narrows what the passes look for, so a clean result says nothing about the defects they were not looking for. **The type belongs to this skill, not to the passes** — `/dry` invoked on its own is not a polish and marks nothing.

**A run that changes nothing commits anyway, empty:**

```bash
git commit --allow-empty -m 'polish: nothing to change'
```

Finding nothing is the ordinary result on a branch `/go` has already polished, and it is precisely the run whose floor the next one needs. An empty commit is how git records that something was done to a tree without changing it, which is exactly the claim being made.

The floor is the newest full-polish commit the branch still carries:

```bash
git log origin/<base>..HEAD --format='%H %s' | awk '$2 == "polish:" { print $1; exit }'
```

The commit's subject line is matched rather than `--grep`, which would also hit a body line that happens to open the same way. Found → `git diff <that sha>..HEAD`. Nothing found means the branch has no floor yet, so **its first run is a `full` run whether or not the word was typed** — the scope stays the whole `origin/<base>...HEAD` above, and nobody has to remember to ask for that.

Everything else falls out of the range being two-dot: only the commits this branch added are candidates. A `polish:` commit the base carries is never the floor, so the lookup does not rest on the convention above holding — and a commit a rebase, amend or reset rewrote away cannot come back as one, so there is nothing to invalidate. Both need `origin/<base>` to be the fetched one, which is the second thing the fetch above buys.

`/polish full` ignores the answer and drops the floor back to the base — as far as it ever goes: in either mode the scope is the branch's own diff against `origin/<base>`, not the tree it sits in. It is the override for a floor that lies, which is the one failure this mechanism cannot detect on its own: a run that committed its mark and then stopped early, or a standard that has since moved — `/tend-prose` gaining a lens, `/dry` tightening what counts. Both leave a commit claiming ground was cleared that was not.

**The floor narrows what gets reviewed, not what it is compared against.** `/dry`'s findings are duplications *between* the new code and what was already there, so the commits below the floor and the rest of the codebase stay readable as context.

## Where it runs

- **`@.claude/skills/go/SKILL.md` Step 3** — after implementing, before the PR.
- **`@.claude/skills/finalize/SKILL.md`, ahead of its numbered steps** — the backstop for work that reached a PR without passing through `/go`. That skill owns why it goes first.
- **On the operator's ask**, at any point in a session — the entry the other two exist to make unnecessary and routinely don't. A task asked for and done directly ends with the passes unrun unless someone names them.
- **`@.claude/skills/update-muthur/SKILL.md` Step 8**, over a port.

## Do NOT

- Run the vet suite, touch the PR, or flip a plan file — every caller owns its own land prep, and `/go` flips its plan file once this returns.
- Widen past the scope above into a general refactor of code the branch did not touch. Both passes are about the change, not the codebase.
- Skip either pass. Two passes are the whole skill; running one is not running it.
