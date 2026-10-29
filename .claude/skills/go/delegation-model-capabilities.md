# What delegated models can and cannot do

One entry per `model:` value `Agent` takes below the delegating agent's own,
kept per `delegation.md` § "Keeping `delegation-model-capabilities.md`", with
the lessons that hold for every model first. An entry records the model as a
delegate and as the session's own driver, the latter from the verdicts of
`review-gate.md`'s reviewer.

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
  back clean with nothing to repair. As the session's driver, a new loop
  procedure across several skills came out structurally sound and faithful to
  the operator's ask.
- **Misses:** as the driver of procedure prose, the cross-check of a clause
  against what it depends on: a rule contradicting another in the same file, a
  check placed behind the condition it was meant to decide, a step needing a
  fact the acting session does not have. Its own polish pass did not catch
  these.
- **Brief:** naming the style reference and the run-until-green command was
  enough; ask for "anything that surprised you" — it reports useful edges.
- **Cost, by eye:** that suite, a few hundred lines, cost about twice as much
  delegated as written in-session; the rework ran to about 137k subagent tokens.

## haiku

- **Handles:** — (untried)
- **Misses:** —
- **Brief:** —
