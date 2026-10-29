# What delegated models can and cannot do

One entry per `model:` value `Agent` takes below the delegating agent's own,
kept per `delegation.md` § "Keeping `delegation-model-capabilities.md`", with
the lessons that hold for every model first. An entry records the model both as
a delegate and as a session's own driver whose work an Opus review judged.

## Across models

- **Cache reads set the floor.** Most of a delegated run's cost is cache reads,
  and at `.claude/costs/prices.json` rates Sonnet 5.5 reads its cache for what
  Opus 5.5 does. The saving is in output tokens and in the delegator's context
  staying small, so a sub-task of a few hundred lines costs more delegated than
  done in-session. Recheck when the rates change; Haiku 5.5 reads at a twentieth
  of Opus 5.5's rate, a quarter once its prompt passes 100k tokens.
- **A reviewer judges what its brief puts in front of it.** Briefed from the
  weaker model's plan, an Opus review checked the work against the plan, took
  the brief's verdict options and remit as given, and passed a misreading the
  plan carried in; one briefed with the operator's ask verbatim checked fidelity
  to the ask. Hand a reviewer the ask itself, and facts rather than the author's
  view of its own work.

## sonnet

- **Handles:** a unittest suite against a hook written as the contract, in a
  named reference's style — needed one rename the brief could not have known;
  went past the brief with sound extra cases. Reworking an existing suite
  against two changed hooks, with its fixture split into a shared module, came
  back clean with nothing to repair. As the session's driver, a loop procedure
  spanning several skills, faithful to the ask, its checkpoints placed against
  the steps around them — ahead of a state flip a relay must leave undone, ahead
  of the run that vouches for a frozen diff — where Opus on the same work missed
  the first. It briefs its own reviewer well: the ask verbatim, facts over
  self-assessment.
- **Misses:** as the driver of procedure prose, the cross-check of a clause
  against what it depends on: a rule contradicting another in the same file, a
  check placed behind the condition it was meant to decide. Its own polish pass
  did not catch these. Under a context-budget warning it dropped loop steps —
  the draft plan PR, a sub-skill done inline instead — rather than relaying, and
  said so only in its closing report.
- **Brief:** naming the style reference and the run-until-green command was
  enough; ask for "anything that surprised you" — it reports useful edges.
- **Cost, by eye:** that suite, a few hundred lines, cost about twice as much
  delegated as written in-session; the rework ran to about 137k subagent tokens.
  Driving a session with an Opus review at the end came to about three quarters
  of an Opus-only session's cost, two fifths of it the review, and a quarter
  more wall time.

## haiku

- **Handles:** a shared skill procedure plus one-line pointers into the skills
  that run it, written against a plan; named corrections applied each as given,
  in one round. As the session's driver, it carried the loop through plan, relay
  and implementation without stalling.
- **Misses:** reading a nuanced ask: it moved an action to the wrong actor — who
  makes a fix — and carried the misreading through its plan into its reviewer's
  brief, so the review passed it. How new pointers interact with the flows they
  sit in: a checkpoint one skill reaches through another ran twice, another
  skill's step was half-restated instead of pointed to, and a checkpoint landed
  after the steps that vouch for a frozen diff. Commit messages that do not
  match what the commit holds.
- **Brief:** name the defect and its correction exactly; it fixes what is named
  and does not go looking for the same defect elsewhere. Leave it no ask to
  interpret: interpretation is where it fails.
- **Cost, by eye:** driving a session with an Opus review at the end came to
  under half an Opus-only session's cost, nearly half of it the review, and a
  third more wall time counting a relay — and the result still needed the rework
  the review was meant to spare.
