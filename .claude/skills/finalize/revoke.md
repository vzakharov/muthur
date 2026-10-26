# Revoke

Loaded by `@.claude/skills/finalize/SKILL.md` for `/finalize revoke`, which runs
this and nothing else.

`/finalize revoke` withdraws the attestation explicitly, for a finalized branch
going back to work. A work commit past the attested SHA already reopens the
branch for the cost ledger; this is the operator saying so before one exists.

1. Rewrite the attestation comment in a file — the marker replaced with
   `<!-- finalize-attestation revoked -->`, the body with when and why it was
   revoked, the footer kept — and post it with
   `scripts/pr-comment.sh attestation --update-only <n> <file>`, spelled as
   `/finalize` step 7 spells it. Exit `3` (`absent`) → nothing was attested; say
   so and stop.
2. `gh pr ready --undo`, so the PR reads as work in progress again.
3. `rm -f tmp/costs/finalized/<branch>`, the ledger's cache of the attested SHA.

Report the three in a line each. The next `/finalize` replaces the revoked
comment like any other.
