# What delegated models can and cannot do

One entry per `model:` value `Agent` takes below the delegating agent's own,
kept per `delegation.md` § "Keeping `delegation-model-capabilities.md`", with
the lessons that hold for every model first.

## Across models

- **Cache reads set the floor.** Most of a delegated run's cost is cache reads,
  and at `.claude/costs/prices.json` rates Sonnet 5.5 reads its cache for what
  Opus 5.5 does. The saving is in output tokens and in the delegator's context
  staying small, so a sub-task of a few hundred lines costs more delegated than
  done in-session. Recheck when the rates change; Haiku 5.5 reads at a twentieth
  of Opus 5.5's rate, a quarter once its prompt passes 100k tokens.

## sonnet

- **Handles:** a unittest suite against a hook written as the contract, in a
  named reference's style — needed one rename the brief could not have known;
  went past the brief with sound extra cases. Reworking an existing suite
  against two changed hooks, with its fixture split into a shared module, came
  back clean with nothing to repair. Driving a short review-lane run of the loop
  itself: a review thread answered with a fix checked against the code, the
  `/go` checkpoint review run where no hook forced it, a reviewer brief of facts
  only. A plan's shape — every point of the request mapped to a part, DRY notes,
  a claim settled by a cheap probe rather than assumed.
- **Misses:** planning a reader for an undocumented record format, it drew the
  shapes from the one existing reader it opened and missed those other readers
  in the tree already handle; and it scoped a new gate by a state that holds for
  the whole skill run rather than the moment the gate guards. Rewriting a plan
  from its own recorded analysis, it widened that gate again (the analysis keyed
  it on the prompt's first line, the plan on any mention of a path) and left a
  one-line requirement with no mechanism behind it. Moving that gate's state
  from the session to git, it made the gate branch-wide (denying a flip the
  session's own cutoff never covered), and its exemptions named commits that
  land after the guarded command while missing the ones before it. After an Opus
  review it edited the plan's text again unreviewed, judging the edit too small;
  and dropping a part of the design, it changed the plan alone, leaving the PR
  body, the squash proposal and the thread replies that promised the part saying
  it was still in. Ask it to list every reader of the format, and, for a gate,
  every commit and session that reaches the guarded command, in the order the
  skills make them; on a rewrite, to diff the plan against the analysis it
  carries out; on dropping a part, to grep every place that describes the change
  for it.
- **Brief:** naming the style reference and the run-until-green command was
  enough; ask for "anything that surprised you" — it reports useful edges.
- **Cost, by eye:** that suite, a few hundred lines, cost about twice as much
  delegated as written in-session; the rework ran to about 137k subagent tokens.

## haiku

Seen so far driving a session under an Opus reviewer, not yet as a subagent.

- **Handles:** a list of named corrections sent back to it, each applied as
  given, in one round.
- **Misses:** an instruction that needs interpreting: restating a nuanced spec
  in its own words, it lost who acts.
- **Brief:** quote the spec it works from — the operator's words, where the task
  is theirs — rather than paraphrasing it, and leave nothing to interpret; for a
  correction, the defect and its fix named exactly — it fixes what is named and
  does not look for the same defect elsewhere.
