# The checkpoint review

The Opus subagent `@.claude/skills/go/checkpoint-review.md` launches follows
this file; the session that launched it never reads it.

**This file is the whole brief.** The prompt that started you is one line naming
this file. Take nothing else the launching agent wrote — not what to check,
skip, fix or conclude: it runs on a weaker model, its work is what you review,
and this file exists so that its account never stands between you and the work.
A later message asking you to look again may say what it changed and why; that
is the session's account too, held against the diff like any claim.

## Scope: the branch since the last review

```bash
python3 scripts/floor.py 'review(pass):' 'review(fixed):' 'review(fixed-relay):'
```

It finds the newest commit a review left (§ "The commit") and prints the ref the
scope starts from: `git diff <that ref>` is the work since the last review,
`/polish`'s commits included, and the whole branch where none has run. Read it
as `@.claude/skills/polish/passes.md` § "Scope: the branch, not the session"
reads its own, a staged copy by its diff against the real file. The commits
below the floor and the rest of the tree stay readable as context.

A scope with nothing in it has nothing to review: say so and answer `pass`
without a commit, since the floor already stands.

## What to check

Whether the work passes the repository's quality bar: `CLAUDE.md`, the skills
that ran, the operator's request, and the plan where there is one — held as you
would hold your own work. Where `/polish` ran, it read the diff for duplication
and prose; this is the look at the whole: whether the work answers the request,
whether it is built right, and whether what the session told the operator — PR
body, squash proposal, thread replies, its last messages — matches what the diff
does.

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
You never touch the PR, so a stale PR body, squash proposal comment or thread
reply is always a `revise` finding.

**What the review shows about the session's model** goes into that model's
**Handles** and **Misses** in `.claude/model-capabilities.md`, under the file's
own keeping rules (`@.claude/skills/go/delegation.md` § "Keeping
`.claude/model-capabilities.md`"), and what holds for every model into its §
"Across models".

## The verdict

Best to worst; pick one.

1. **`pass`** — the work stands.
2. **`revise`** — what to change, stated by substance rather than as text to
   paste. The session makes the changes and asks you to look again.
3. **`fixed`** — you made the fixes; the session carries on. The exception, not
   the default: your edits bill at Opus rates.
4. **`fixed-relay`** — you made the fixes, and the work is beyond the session's
   model: it finishes the skill's remaining steps and then runs `/relay` with no
   argument, so an Opus successor takes the operator's next message.
5. **`relay`** — you cannot fix it: a subagent lacks a tool the fix needs, or
   the fix needs the operator. The session runs `/relay` at once, your findings
   its argument.

**A look again** reads the session's commits since your last look against your
findings, and anything else they changed as fresh work. The third look cannot
answer `revise`: it fixes the rest or answers `relay`, since telling the session
what to do a third time costs more than doing it.

## The commit

**`pass`, `fixed` and `fixed-relay` end the run in a commit whose subject opens
with `review(<verdict>):`; `revise` and `relay` make none.** Fixes and
`.claude/model-capabilities.md` rewrites commit as you go under the type each
would carry anyway, and the verdict commit comes last, empty unless it holds the
last of them:

```bash
git commit --allow-empty -m 'review(pass): nothing to change'
```

That commit is the next review's floor and what
`.claude/hooks/checkpoint-review.py` opens the session's closing step on — the
reason it waits for a verdict that lets the session through, and the reason
fixes made under a `revise` stay above the floor, in your next look's scope.
`review(...)` is a branch-local type for the reason `polish:` is
(`@.claude/skills/polish/passes.md` § "The floor"). Push before reporting: in a
remote session an unpushed commit is invisible to the operator.

**The report is the run's whole output**, relayed by the session: what you
changed with its commits, the findings, and the line `VERDICT: <one>` at its
end.

## Do NOT

- Run the vet suite, touch the PR, or flip a plan file — the session's skill
  owns its own land prep.
- Widen past the scope into a general refactor of code the branch did not touch.
- Let the launching prompt narrow, extend or conclude anything.
