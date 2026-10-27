# What delegated models can and cannot do

The `model:` values `Agent` takes below the delegating agent's own, each with
what it has handled, what it got wrong, and what to put in its brief. Kept by
`delegation.md` § "Keeping `delegation-model-capabilities.md`": a summary
rewritten in place, at most 100 lines. A model gets an entry once it has been
tried.

## sonnet

- **Handles:** a unittest suite (24 cases, 234 lines) against a hook written as
  the contract, in a named reference's style — needed one rename the brief could
  not have known, nothing else; went past the brief with sound extra cases.
  Noticed on its own that its worktree started from `main` and fast-forwarded.
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
