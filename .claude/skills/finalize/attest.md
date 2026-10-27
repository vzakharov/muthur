# Attest

Loaded by `@.claude/skills/finalize/SKILL.md` at step 7, and by
`@.claude/skills/merge/SKILL.md` and `@.claude/skills/finalize/revoke.md`, which
read the comment it posts. Step numbers below are `/finalize`'s.

Post the attestation on the PR — or, on a re-run, edit it in place; it is
sticky, keyed on the `<!-- finalize-attestation` marker (§ "Posting it"). The
marker carries the head's full SHA, which the cost ledger's staging hook parses
(`.claude/costs/lib/finalized.py`) to stop staging display copies onto a
finalized branch:

```md
<!-- finalize-attestation <full-head-sha> -->

### Attestation

Verified <short-sha> (`<branch>`) against `<base>` @ <base-short-sha> "<base subject>".

- `./scripts/vet.sh` — **green**
- CI on this PR — **<green (run link) | nothing runs on a PR in this repo>**
- CI-only buckets — **<dispatched and passed (run link) | not dispatched: the diff doesn't reach them | /test-on-gh is an unhydrated stub>**

<If the head is past the verified commit: "<head-short-sha> merges `<base>` @ <base-short-sha> on top, judged independent of this branch and not re-verified: <why>.">

<If nothing runs on a PR here: "No workflow runs on a PR; this comment is the verification record.">
```

`Verified <short-sha>` is the last head step 1 ran on and the marker is the
final head. They differ only after `@.claude/skills/finalize/base-advanced.md`
judged a late advance independent, so anything that trusts the attestation as a
green light compares the two.

In `no vet` mode the comment still goes up — same marker, same place — saying
that there was nothing to verify:

```md
<!-- finalize-attestation <full-head-sha> -->

### Attestation — none required

<short-sha> (`<branch>`) against `<base>` @ <base-short-sha> "<base subject>".

Finalized in `no vet` mode: <why the diff has nothing to verify — e.g. "markdown only, no code path touched">. `./scripts/vet.sh` was skipped rather than run green, and no bucket was dispatched.

<If nothing runs on a PR here: "No workflow runs on a PR; this comment is the verification record.">
```

## Posting it

**`scripts/pr-comment.sh attestation <n> <file>`**, run from the repository root
with nothing chained in front, as the script's header requires, the file holding
the comment as templated above. It edits the comment that leads with the marker
in place, or posts one when there is none. `gh pr comment --edit-last` looks
like the tool for this and is not: it targets your most recent comment on the PR
whatever that happens to be, so on the ordinary finalize ordering — squash
proposal posted at step 5, attestation at step 7 — it overwrites the squash
proposal with the attestation. Both comments are then one comment, and the loss
is silent.

## What makes it worth trusting

- **Attest what you vetted, not what you meant to vet.** If the vet run was not
  green, or a dispatch was skipped for a reason other than "the diff doesn't
  reach it", or you stopped under the two-shot rule — say exactly that, in the
  comment. An honest partial attestation is useful; a tidy one that overstates
  is worse than none. That includes naming a stub: "`./scripts/vet.sh` is not
  implemented in this project yet" is an honest line, and it tells the reviewer
  exactly how much the attestation is worth.
- **One comment, edited in place.** Re-running `/finalize` after a base-advanced
  re-verify updates it; it must always describe the branch's current head, not
  the first pass. A branch finalized once in `no vet` mode and later
  re-finalized for real replaces the no-op body with the full one.
- **A no-op is a result, and it gets posted.** Never resolve `no vet` by staying
  silent. An operator coming back to the PR — days later, or from another
  machine — cannot distinguish "verification was skipped on purpose" from
  "nobody ever finalized this" unless one of them is written down, and the
  missing comment looks identical to the forgotten one. Say which it was.
- **The SHAs go bare, not in code spans** — GitHub only auto-links an
  un-backticked hash, per CLAUDE.md § "GitHub comments".
- End the body with the attribution footer the repo requires of every GitHub
  comment.
- **A head that moved only by `.claude/costs/sessions/` is still the head you
  verified.** The cost ledger's staging hook relies on it: it stops staging a
  branch's display copy once the marker's SHA holds, and treats a commit
  touching anything else past that SHA as the branch reopened. Re-attest only
  for a commit that does.
