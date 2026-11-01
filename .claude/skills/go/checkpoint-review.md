# Checkpoint review by Opus

A session on a model below Opus drives the loop as far as an Opus one does, and
nothing stronger looks at its work before the operator does. So each cutoff —
`/plan`, `/go` and `/finalize`, each saying where in it — runs `/polish`
(`@.claude/skills/polish/SKILL.md`), whose third pass is an Opus review of the
whole. `/handle` reaches it through the `/go` or `/plan` its lane runs, so its
run gets one review, not two.

The session writes no brief and records nothing: `/polish` launches the reviewer
with one line, the reviewer reads its procedure from
`@.claude/skills/polish/passes.md`, and the verdict is the `Review:` line of the
polish commit.

## Who runs it

A session whose **serving** model is Sonnet or Haiku — serving rather than
configured, because the review is for whoever did the work, and a fallback
mid-session changes that. `.claude/hooks/checkpoint-review.py` decides it, from
the model the session's transcript records on its latest reply:

- entering `/plan`, `/go` or `/finalize` on such a model delivers this file, and
  marks that cutoff **entered**;
- for an entered cutoff, the hook denies the step that would close it — the
  `git mv` out of `*.draft.do-not-implement.md` for `/plan`, the `git mv` to
  `*.completed.md` for `/go`, `gh pr ready` for `/finalize` — unless the
  branch's newest `polish:` commit carries a `Review:` line other than `revise`
  and nothing but the loop's working artifacts changed since. A skipped review,
  or work done after it, stops the session there rather than passing unseen.

A cutoff the session never entered is not gated — a Sonnet `/go` flipping a plan
an Opus `/plan` wrote has no review of its own to show. The gate also needs the
closing step: a `/go` with no plan file never flips one, and a `/plan` whose
`/go` runs in another session never sees its own flip. There the skill's pointer
alone holds the session to the review, and nothing stops a skipped one short of
`/finalize`'s gate.

`MUTHUR_CHECKPOINT_REVIEW=off` turns all of it off. Under a harness that runs no
hooks, the session runs `/polish` at each cutoff itself when the model its
system prompt names is Sonnet or Haiku, unless that switch is `off`.

## The verdicts

The report ends `VERDICT: <one>`; the session pushes after any verdict that left
commits, and its report names the verdict in a line.

- **`pass`** and **`fixed`** — carry on with the skill.
- **`revise`** — the findings are in the polish commit's body. Make the changes,
  commit, and run `/polish` again: it starts from that floor and checks them.
  The gate stays shut until a run answers otherwise.
- **`fixed-relay`** — the reviewer fixed what it found, and the work is beyond
  the session's model. Finish the skill's remaining steps, then run `/relay`
  (`@.claude/skills/relay/SKILL.md`) with no argument, so the Opus successor
  takes the operator's next message.
- **`relay`** — the reviewer cannot fix it. Run `/relay` at once, its argument
  the reviewer's findings to act on, followed by the skill to re-run where the
  cutoff was `/finalize`.

Either relay is an escalation, which `/relay` Step 3 starts on Opus. What each
verdict means to the reviewer is `passes.md` § "The verdict".
