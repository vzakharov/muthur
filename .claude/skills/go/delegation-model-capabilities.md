# What delegated models can and cannot do

One entry per `model:` value `Agent` takes below the delegating agent's own,
kept per `delegation.md` § "Keeping `delegation-model-capabilities.md`".

## sonnet

- **Handles:** a unittest suite (24 cases, 234 lines) against a hook written as
  the contract, in a named reference's style — needed one rename the brief could
  not have known, nothing else; went past the brief with sound extra cases.
- **Misses:** —
- **Brief:** naming the style reference and the run-until-green command was
  enough; ask for "anything that surprised you" — it reports useful edges.
- **Cost, by eye:** the suite above, ~$0.45 (16 turns, context to ~80k) against
  ~$0.25 to write it in a ~175k-context Opus session. Not worth it at that size:
  its cache reads cost what Opus's do, so a few hundred lines saves nothing.

## haiku

- **Handles:** — (untried)
- **Misses:** —
- **Brief:** —
