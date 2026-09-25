# Eating an elephant

What to do once `@.claude/skills/plan/SKILL.md` § "Splitting work across
sessions" has picked the elephant — that section holds the choice and the
principle both shapes share. The plan is written here and kept by
`@.claude/skills/go/SKILL.md`, which eats one bite per session and pauses.

## The plan's shape

Two sections, and neither looks back:

- **`## Rest of the elephant`** — the job still to eat, coarse, in whatever
  form reads best for it. What a bite takes leaves it. This section is what
  marks a plan as an elephant for `/go`.
- **`## This bite`** — what the open bite builds, detailed to what it needs: a
  line when it is plain, a page with its own DRY notes when it has a reuse call
  or a shape to settle. It exists while a bite is open — written when a session
  takes the bite, deleted when the bite is done. A stop mid-bite strikes what
  is built and renames it `## Rest of the bite`, which is what the next session
  finds. The plan may write the first one, so the operator reviews it at the
  approval gate.

**The plan is the current contract at every moment.** Each pause rewrites it
to what is true now: the bite gone or cut to its rest, the rest of the elephant
reworded where the work found it wrong or learned what it needs. It carries
no progress diary and no log of where the work departed from it — each resume
pays for every line the plan holds, and how the plan got to its current text
is what git history and the PR's review are for.

## Taking a bite

The session that claims the plan writes `## This bite` before building:

1. **A bite already in the plan goes first, as written** — the rest a stop
   mid-bite left, or the first bite the plan wrote. Its detail was paid for by
   the session that wrote it; only the operator's review changes it.
2. **On top of it, take from the elephant as much as fits**, detailed the same
   way, moving what it takes out of `## Rest of the elephant`. In doubt, take
   less: a bite cut too small costs one more pause, which is one more review,
   and one cut too big costs a stop mid-bite whose rest survives in the plan.

## A bite

- leaves `vet` green and lands whole — nothing half-built that the next bite
  has to finish before anything works;
- is sized to finish, `/polish` included, before the context budget's warning
  line (`CONTEXT_BUDGET_WARN`, `.claude/context-budget/CLAUDE.md`) — so a
  bite's end normally comes before the hook says anything, and a notice
  arriving mid-bite means the bite was cut too big;
- is one per session: the pause is for the operator's review, not for saving
  tokens, so a session that finishes its bite early stops there.

What a pause does — at a bite's end or forced mid-bite by the budget — is
`/go` Step 2's.
