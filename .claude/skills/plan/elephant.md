# Eating an elephant

What to do once `@.claude/skills/plan/SKILL.md` § "Splitting work across
sessions" has picked the elephant — that section holds the choice and the
principle both shapes share. The plan is written here and kept by
`@.claude/skills/go/SKILL.md`, which eats one bite per session and pauses.

## The plan's shape

Three sections, in this order — the order the work runs, so the session taking
a bite reads what it builds before where the job goes after it:

- **`## Eaten so far`** — what the bites before this one built, coarse, at
  the altitude of the rest of the elephant: what now exists and what the next
  bite can build on, never how it got built. The session taking a bite starts
  from it, so it has to stand on its own without the PR or the history. Each
  bite folds itself in at its end; the section appears with the first one.
- **`## This bite`** — what the open bite builds, detailed to what it needs: a
  line when it is plain, a page with its own DRY notes when it has a reuse call
  or a shape to settle. It exists while a bite is open — written when a session
  takes the bite, folded into `## Eaten so far` when the bite is done. A stop
  mid-bite folds in what is built and renames the rest `## Rest of the bite`,
  which is what the next session finds. The plan may write the first one, so
  the operator reviews it at the approval gate.
- **`## Rest of the elephant`** — the job still to eat, coarse, in whatever
  form reads best for it. What a bite takes leaves it. This section is what
  marks a plan as an elephant for `/go`.

**The plan is the current contract at every moment.** Each pause rewrites it
to what is true now: the bite folded into what is eaten or cut to its rest,
the rest of the elephant reworded where the work found it wrong or learned what
it needs. What is eaten is kept as what exists, not as a diary of sessions, and
the plan logs no departures from itself — each resume pays for every line the
plan holds, and how the plan got to its current text is what git history and
the PR's review are for.

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
