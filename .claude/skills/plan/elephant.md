# Eating an elephant

What to do once `@.claude/skills/plan/SKILL.md` § "Splitting work across
sessions" has picked the elephant — that section holds the choice and the
principle both shapes share. The plan is written here and kept by
`@.claude/skills/go/SKILL.md`, which builds one chunk per session and pauses.

## The plan's shape

- **Steps** — the whole job, coarse, as a checklist. A step is ticked when it
  is done.
- **`## Next chunk`** — what the next session builds, detailed to what that
  chunk needs: a line when it is plain, a page with its own DRY notes when it
  has a reuse call or a shape to settle. This section is what marks a plan as
  an elephant for `/go`. At plan time it is the first chunk.

**The plan is the current contract at every moment.** Each pause rewrites it
to what is true now: ticks on the steps done, steps reworded where the work
found them wrong, `## Next chunk` replaced. It carries no progress diary and no
log of where the work departed from it — each resume pays for every line the
plan holds, and how the plan got to its current text is what git history and
the PR's review are for.

**The session that pauses writes the next chunk**, because it has just built
what that chunk stands on. The operator reads it during the pause, so a
direction that is wrong costs a paragraph rather than a session.

## A chunk

- leaves `vet` green and lands whole — nothing half-built that the next chunk
  has to finish before anything works;
- is sized to finish, `/polish` included, before the context budget's warning
  line (`CONTEXT_BUDGET_WARN`, `.claude/context-budget/CLAUDE.md`) — so a
  planned chunk end normally comes before the hook says anything, and a notice
  arriving mid-chunk means the chunk was cut too big;
- is one per session: the pause is for the operator's review, not for saving
  tokens, so a session that finishes its chunk early stops there.

What a pause does — planned or forced by the budget — is `/go` Step 2's.
