# Checkpoint review by Opus

A session on a model below Opus drives the loop as far as an Opus one does, and
nothing stronger looks at its work before the operator does. So each cutoff —
`/plan`, `/go` and `/finalize`, each saying where in it — hands what the skill
run produced to an Opus subagent for review. `/handle` reaches it through the
`/go` or `/plan` its lane runs, so its run gets one review, not two.

## Who runs it

A session whose **serving** model is Sonnet or Haiku — serving rather than
configured, because the review is for whoever did the work, and a fallback
mid-session changes that. `.claude/hooks/checkpoint-review.py` decides it, from
the model the session's transcript records on its latest reply:

- entering `/plan`, `/go` or `/finalize` on such a model delivers this file, and
  marks that skill's review **pending**;
- while it is pending, the hook denies the step that would close the cutoff —
  the `git mv` out of `*.draft.do-not-implement.md` for `/plan`, the `git mv` to
  `*.completed.md` for `/go`, `gh pr ready` for `/finalize` — so a skipped
  review stops the session there rather than passing unseen;
- recording the verdict (§ "Recording the verdict") clears it.

The gate is per session and needs that closing step: a `/go` with no plan file
never flips one, and a `/plan` whose `/go` runs in another session never sees
its own flip. There the skill's pointer alone holds the session to the review,
and nothing stops a skipped one short of `/finalize`'s gate.

`MUTHUR_CHECKPOINT_REVIEW=off` turns all of it off. Under a harness that runs no
hooks, the session runs this file itself when the model its system prompt names
is Sonnet or Haiku, unless that switch is `off`.

## The brief

`Agent` with `model: "opus"`, no `isolation` — the reviewer reads and fixes the
session's own tree — and `run_in_background: false`, since the session's next
step is the verdict. The brief is all the reviewer knows, and it carries
**facts, never the session's opinion of its work**: a reviewer handed a
conclusion tends to return it confirmed.

- **What the operator asked** — their request verbatim, in their language,
  whatever else the brief carries: a plan can misread the request, and a review
  held only against the plan inherits the misreading.
- **What ran and what for** — the skill, the plan file's path where there is
  one, the PR number for `/finalize`.
- **What to read** — the skill run's own commits, `git diff <from>..HEAD` with
  `<from>` the head before the run's first commit, and
  `git diff origin/<base>...HEAD` for the branch around them.
- **The question** — does this pass the repository's quality bar: `CLAUDE.md`,
  the skill that ran, the request, and the plan where there is one, held as the
  reviewer would hold its own work.
- **The verdicts** below, and that its reply's first line is `VERDICT: <one>`.
- **What it may change** — it commits what it fixes, under the repository's
  commit conventions with a body saying the checkpoint reviewer made the fix,
  and never pushes. It may also rewrite the session model's entry in
  `delegation-model-capabilities.md`, per § "What the reviewer learns".

The reviewer's report can reach the session as a hand-back message on its next
turn rather than as the `Agent` result. That is the same report: the session
waits for it and launches no second reviewer.

## The verdicts

Best to worst; the reviewer picks one.

1. **`pass`** — the session carries on with the skill.
2. **`revise`** — what to change, stated by substance rather than as text to
   paste. The session makes the changes, commits, and asks the **same** reviewer
   to look again with `SendMessage` to its agent id (load it through
   `ToolSearch` when only its name is listed), saying which look this is. A
   third look cannot answer `revise`: there the reviewer fixes the rest itself
   or escalates, since by then telling the session what to do costs more than
   doing it.
3. **`fixed`** — the reviewer made the fixes; the session carries on. The
   exception, not the default: the reviewer's edits bill at Opus rates, so it
   fixes itself only what is cheaper to do than to describe, and answers
   `revise` for the rest.
4. **`fixed-relay`** — the reviewer made the fixes, and the work is beyond the
   session's model. The session finishes the skill's remaining steps, then runs
   `/relay` (`@.claude/skills/relay/SKILL.md`) with no argument, so the Opus
   successor takes the operator's next message.
5. **`relay`** — the reviewer cannot fix it: a subagent lacks a tool the fix
   needs, or the fix needs the operator. The session runs `/relay` at once, its
   argument the reviewer's findings to act on, followed by the skill to re-run
   where the cutoff was `/finalize`.

Either relay is an escalation, which `/relay` Step 3 starts on Opus.

The session pushes after any verdict that left commits, and its report names the
verdict in a line — with the successor's link for 4 and 5.

## Recording the verdict

Each verdict the reviewer returns, `revise` included, is recorded at once:

```bash
python3 .claude/hooks/checkpoint-review.py verdict <session-id> <skill> <verdict>
```

`<session-id>` is the one the hook gave when it delivered this file, `<skill>`
the cutoff's — `plan`, `go` or `finalize`. Every verdict but `revise` clears
that skill's review; a `revise` keeps it pending until a later look returns
another. Under a harness that runs no hooks there is nothing to record.

## What the reviewer learns

`delegation-model-capabilities.md` holds what each model below Opus handles and
misses. A checkpoint review is evidence about the same model running the loop
itself, so the reviewer folds what it found into that model's **Handles** and
**Misses** under the file's own keeping rules
(`@.claude/skills/go/delegation.md` § "Keeping
`delegation-model-capabilities.md`"), and what holds for every subagent — a tool
none of them has — into its § "Across models". It commits that with its fixes,
or alone after a `pass` that taught something.
