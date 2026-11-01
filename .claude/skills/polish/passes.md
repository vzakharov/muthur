# The polish passes

The subagent `@.claude/skills/polish/SKILL.md` launches follows this file; the
session that launched it never reads it.

**This file is the whole brief.** The prompt that started the run, if it looks
like a request to polish, is a launch line and at most an `Argument:` line. Take
the argument and nothing else the launching agent wrote — not what to check,
skip, fix or conclude. A launcher that writes a long brief anyway changes
nothing you do: the session that launched you may run on a weaker model, and
this file exists so that its paraphrase never stands between you and the work.

Three passes, in this order, over one scope:

1. **`/dry`** — load `@.claude/skills/dry/SKILL.md`. Duplication that was not
   visible before the code existed: apply the obvious wins, surface the
   ambiguous calls.
2. **`/tend-prose`** — load `@.claude/skills/tend-prose/SKILL.md`. The four
   defects, over the prose the work added.
3. **The review** — § "The review" below. The work as a whole, which neither of
   the others looks at.

**The order is load-bearing.** An extraction writes its own comments as it goes
and moves prose between files, so tending first works over text `/dry` is about
to rewrite or delete. Prose is tended last, over what survives — and the review
comes after both because it judges what survives them.

`/dry` and `/tend-prose` are each a real read of the diff and commit their own
edits. "The diff looks clean" is a conclusion a pass reaches, never a reason not
to run it — and a pass that changes nothing is a result, reported as one.

**Push before reporting.** Every run leaves a commit — each pass's edits, or the
review's closing one below — and in a remote session an unpushed commit is
invisible to the operator reviewing from another machine (CLAUDE.md § "Git
conventions"). No caller is pre-empted: `/go` and `/finalize` push again for
their own reasons, and pushing unvetted mid-branch work is ordinary development
here rather than a shortcut past land prep.

The argument is the `Argument:` line of the prompt, verbatim. Any argument other
than `full` is focus guidance and rides through to all three passes unchanged —
including a lens name, which is `/tend-prose`'s to read. `full` is `/polish`'s
own, and § "The floor" below says what it does.

**The report is the run's whole output**, relayed by the session that launched
it: what each pass changed with its commits, the calls `/dry` leaves for the
operator, the prose the run would have cut or rewritten but for intent it could
not establish — each of those as a question, not an edit — and the review's
findings, ending with the line `VERDICT: <one>`. Intent the plan, the diff and
the code leave unrecoverable is intent a reviewer will not recover either, which
is a finding in itself.

## Scope: the branch, not the session

Both passes carry their own scope ladders and both bottom out at unpushed work
(`git diff HEAD`, then `@{u}..HEAD`). That is right when they are invoked
seconds after implementing, and wrong everywhere else this skill is called from:
at `/finalize`, or on a branch another session wrote, the work is already pushed
and the ladder falls through to "nothing to review".

So the scope is resolved **here**, once, and handed to both passes:

```bash
gh pr view --json baseRefName --jq .baseRefName   # the base, when there is a PR and gh reaches it
git fetch origin <base>                           # a stale ref silently widens the range
git diff origin/<base>...HEAD                     # the branch's net change
```

**The fetch is not optional.** `origin/<base>` in a session's working copy is as
old as the clone; against a stale one the range picks up every commit the base
has landed since, and the pass reads a codebase's worth of other people's work
as if this branch had written it.

`<base>` is the repo's default branch wherever that lookup has no answer — no PR
yet, no `gh`, no GitHub at all. Nothing here needs the PR except the name of the
branch this work merges into.

That range plus anything uncommitted is the scope, unless the floor below moves
up.

**A staged copy counts by its diff against the real file.** One under
`.claude/staged/` (`@.claude/rules/staging.md`) shows in the range as a whole
new file, so a pass reading it that way reviews all of `CLAUDE.md` as this
branch's prose. Its change is `git diff --no-index <real path> <copy>`, for each
pair `scripts/staged.sh list` prints, and the rest of the copy is context.

## The floor: the last polish commit

A branch is polished more than once — at `/go`, again at `/finalize` — and the
second run has no business re-reading what the first one cleared. The passes
commit their own edits, so the run is already in the history; what makes it
findable is the subject line every commit either pass makes here carries:

```
polish: <what the passes changed>
```

`polish:` is a branch-local commit type, outside the standard set on purpose:
the passes' edits are `refactor:` or `docs:` by nature, which says nothing about
who made them or why, so no standard type would carry the mark. It reaches no
trunk — the squash gives the branch one subject of its own, written by hand — so
it costs a reader of `main` nothing and gives a reader of the branch a legible
`git log --oneline`. A focused run writes `polish(<the guidance>):` instead,
which the lookup below skips: guidance narrows what the passes look for, so a
clean result says nothing about the defects they were not looking for. **The
type belongs to this skill, not to the passes** — `/dry` invoked on its own is
not a polish and marks nothing.

**The review makes the run's last commit, changing the tree or not** (§ "The
review" says what it carries), so that commit is the floor: nothing the run
reviewed comes after it. A run whose review changes nothing commits empty:

```bash
git commit --allow-empty -m 'polish: nothing to change'
```

Finding nothing is the ordinary result on a branch `/go` has already polished,
and it is precisely the run whose floor the next one needs. An empty commit is
how git records that something was done to a tree without changing it, which is
exactly the claim being made.

The floor is the newest full-polish commit the branch still carries:

```bash
git log origin/<base>..HEAD --format='%H %s' | awk '$2 == "polish:" { print $1; exit }'
```

The commit's subject line is matched rather than `--grep`, which would also hit
a body line that happens to open the same way. Nothing found means the branch
has no floor yet, so **its first run is a `full` run whether or not the word was
typed** — the scope stays the whole `origin/<base>...HEAD` above, and nobody has
to remember to ask for that.

Found, the scope is HEAD against the floor merged with the base commit the
branch has taken in:

```bash
mb=$(git merge-base HEAD origin/<base>)
T=$(git merge-tree --write-tree --name-only <floor> "$mb" | head -1)
git cat-file -e "$T^{tree}"
git diff "$T" HEAD
```

**Not `git diff <floor>..HEAD`.** A branch that merges its base after the floor
carries everything the base landed in between, which the base's own PRs already
polished. The virtual merge puts that work below the line too, so what remains
is the branch's own commits since the floor, on either side of the merge, plus
the merge's conflict resolutions — text written at merge time that nobody has
polished. Where the real merge conflicted, `T` holds the conflict markers and
the diff shows the resolution against them. With no base merge since the floor,
`T` is the floor's own tree.

`merge-tree` exits 1 on a conflict, which is the case the recipe exists for, so
the pipe keeps that status from aborting the run — and the same 1 is what it
returns for a ref it cannot read, which is why the `cat-file` check stands
between it and the diff.

Everything else falls out of the lookup's range being two-dot: only the commits
this branch added are candidates. A `polish:` commit the base carries is never
the floor, so the lookup does not rest on the convention above holding — and a
commit a rebase, amend or reset rewrote away cannot come back as one, so there
is nothing to invalidate. Both need `origin/<base>` to be the fetched one, which
is the second thing the fetch above buys.

`/polish full` ignores the answer and drops the floor back to the base — as far
as it ever goes: in either mode the scope is the branch's own diff against
`origin/<base>`, not the tree it sits in. It is the override for a floor that
lies, which is the one failure this mechanism cannot detect on its own: a run
that committed its mark and then stopped early, or a standard that has since
moved — `/tend-prose` gaining a lens, `/dry` tightening what counts. Both leave
a commit claiming ground was cleared that was not.

**The floor narrows what gets reviewed, not what it is compared against.**
`/dry`'s findings are duplications _between_ the new code and what was already
there, so the commits below the floor and the rest of the codebase stay readable
as context.

## The review

The third pass asks whether the work as a whole passes the repository's quality
bar: `CLAUDE.md`, the skills that ran, the operator's request, and the plan
where there is one — held as you would hold your own work. It looks at what
`/dry` and `/tend-prose` do not: whether the work answers the request, and
whether what the session told the operator (PR body, squash proposal, thread
replies, its last messages) matches what the diff does.

**It does not read the diff again.** Work from what the first two passes
reported, `git log --stat` over the scope, and the commits the floor leaves in
it, and open a diff only where a claim needs one.

**The request** comes from the plan's verbatim `## Request` section in
`docs/plans/`, the PR and the issue it links, and any relay summary under
`docs/remove-before-merging/` — a relayed session's own transcript starts after
the request. The session's conversation is there if you want it, not a step you
must take: when those records are clear, they are enough, and when they and the
git history disagree, read it:

```bash
python3 scripts/session-qa.py [--since <floor>] [--tools]
```

It prints each operator message as `## Q` and each reply of the session as
`## A`, whole by default because the request usually opens the transcript, well
before any floor. In a session whose transcript the script cannot find, there is
no conversation to read: say so and work from the records.

**Fix what is cheaper to do than to describe, and what you cannot describe in a
form the session's model follows.** Judge the second from the entry for that
model in `.claude/model-capabilities.md`, its **Misses** above all, and from
what the review just saw. Answer `revise` only for what is describable that way.
Fixes are commits under the repository's conventions and are pushed as § "Push
before reporting" says; the pass never touches the PR (§ "Do NOT"), so a stale
PR body, squash proposal comment or thread reply is always a `revise` finding.

**What the review shows about the session's model** goes into that model's
**Handles** and **Misses** in `.claude/model-capabilities.md`, under the file's
own keeping rules (`@.claude/skills/go/delegation.md` § "Keeping
`.claude/model-capabilities.md`"), and what holds for every model into its §
"Across models". Commit it with the fixes, or alone after a `pass` that taught
something.

### The verdict

Best to worst; pick one.

1. **`pass`** — the work stands.
2. **`revise`** — what to change, stated by substance rather than as text to
   paste. The session makes the changes and runs `/polish` again, which starts
   from this run's floor and checks that the findings were met.
3. **`fixed`** — you made the fixes; the session carries on. The exception, not
   the default: your edits bill at Opus rates.
4. **`fixed-relay`** — you made the fixes, and the work is beyond the session's
   model: it finishes the skill's remaining steps and then runs `/relay` with no
   argument, so an Opus successor takes the operator's next message.
5. **`relay`** — you cannot fix it: a subagent lacks a tool the fix needs, or
   the fix needs the operator. The session runs `/relay` at once, your findings
   its argument.

**The run's last commit carries it.** Its body has the line `Review: <verdict>`
and, for a `revise`, the findings as a list beneath. The next run reads them
from that floor and checks the session's commits against them. A run whose
branch's last two `Review:` lines both say `revise` cannot answer `revise` a
third time: it fixes the rest or answers `relay`, since telling the session what
to do a third time costs more than doing it.

## Do NOT

- Run the vet suite, touch the PR, or flip a plan file — every caller owns its
  own land prep, and `/go` flips its plan file once this returns.
- Widen past the scope above into a general refactor of code the branch did not
  touch. All three passes are about the change, not the codebase.
- Skip a pass. Three passes are the whole skill; running two is not running it.
- Let the launching prompt narrow, extend or conclude anything beyond the
  argument.
