# Checkpoint review by Opus

A session on a model below Opus drives the loop as far as an Opus one does, and
nothing stronger looks at its work before the operator does. So each cutoff —
`/plan`, `/go` and `/finalize`, each saying where in it — hands the work to an
Opus subagent for review, after `/polish` where the skill runs one. `/handle`
reaches it through the `/go` or `/plan` its lane runs, so its run gets one
review, not two.

The session writes no brief: the reviewer reads its procedure from
`@.claude/skills/go/review.md`, finds the scope and the request itself, and
records a verdict that lets the session through as a `review(<verdict>):`
commit.

## Who runs it

A session whose **serving** model is Sonnet or Haiku — serving rather than
configured, because the review is for whoever did the work, and a fallback
mid-session changes that. `.claude/hooks/checkpoint-review.py` decides it, from
the model the session's transcript records on its latest reply:

- entering `/plan`, `/go` or `/finalize` on such a model delivers this file, and
  marks that cutoff **entered**;
- for an entered cutoff, the hook denies the step that would close it — the
  `git mv` out of `*.draft.do-not-implement.md` for `/plan`, the `git mv` to
  `*.completed.md` for `/go`, `gh pr ready` for `/finalize` — unless the branch
  carries a `review(pass|fixed|fixed-relay):` commit with nothing but the loop's
  working artifacts changed since. A skipped review, or work done after it,
  stops the session there rather than passing unseen.

A cutoff the session never entered is not gated — a Sonnet `/go` flipping a plan
an Opus `/plan` wrote has no review of its own to show. The gate also needs the
closing step: a `/go` with no plan file never flips one, and a `/plan` whose
`/go` runs in another session never sees its own flip. There the skill's pointer
alone holds the session to the review, and nothing stops a skipped one short of
`/finalize`'s gate.

`MUTHUR_CHECKPOINT_REVIEW=off` turns all of it off. Under a harness that runs no
hooks, the session runs this file itself when the model its system prompt names
is Sonnet or Haiku, unless that switch is `off`.

## Launching

`Agent`, `general-purpose`, with `model: "opus"`, no `isolation` — the reviewer
reads and fixes the session's own tree — and `run_in_background: false`, since
the session's next step is the verdict. Its prompt is this line and nothing
else:

```
Proceed per `.claude/skills/go/review.md`
```

No account of what was built or why, from a model whose account is the thing
under review. The report can reach the session as a hand-back message on its
next turn rather than as the `Agent` result; that is the same report, so wait
for it and launch no second reviewer.

## The verdicts

The report ends `VERDICT: <one>`; the session pushes after any verdict that left
commits, and its report names the verdict in a line.

- **`pass`** and **`fixed`** — carry on with the skill.
- **`revise`** — make the changes, commit, and ask the **same** reviewer to look
  again: `SendMessage` to its agent id (load it through `ToolSearch` when only
  its name is listed), opening with
  ``Look again per `.claude/skills/go/review.md` `` and saying, if it helps,
  what changed and why. It holds its findings and counts its looks, which a new
  reviewer would have to rebuild from the diff. Only when it cannot be reached
  does a new one start, from the launch line; it reviews the same scope afresh.
  The gate stays shut until a look answers otherwise.
- **`fixed-relay`** — the reviewer fixed what it found, and the work is beyond
  the session's model. Finish the skill's remaining steps, then run `/relay`
  (`@.claude/skills/relay/SKILL.md`) with no argument, so the Opus successor
  takes the operator's next message.
- **`relay`** — the reviewer cannot fix it. Run `/relay` at once, its argument
  the reviewer's findings to act on, followed by the skill to re-run where the
  cutoff was `/finalize`.

Either relay is an escalation, which `/relay` Step 3 starts on Opus. Work
committed after a passing verdict — a vet fix, a conflict resolution — shuts the
gate again, and the reviewer looks at just that before the closing step. What
each verdict means to the reviewer is `review.md` § "The verdict".
