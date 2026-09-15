# Sweep the skills for minority-entry sections worth colocating

Closes #69.

Three of the six candidate sites in the issue survive the criterion; three do
not, and one of those three no longer exists. The sweep also turns up one site
the issue's table missed and confirms that its script acceptance item is
already satisfied by a widening that landed after the issue was filed.

## The criterion, as applied

From the issue, unchanged. Extract when all three hold:

1. The section fires on a **trigger statable precisely enough in the resident
   pointer** that a session knows whether to load the sidecar without reading it.
2. The trigger is the **minority** case across runs of that skill.
3. What stays behind is a **real pointer** — a non-triggering session needs
   nothing else, including whatever guard keeps it from firing unprompted.

## Verdicts

| Site | Lines | Verdict |
|---|---|---|
| `/plan` § "If the session is already in native plan mode" | 17 of 146 | **extract** → `plan/native-plan-mode.md` |
| `/squash-message` Step 2 — working-file selection | 28 of 330 | **extract** → `squash-message/working-file.md` |
| `/take-issue` § "Video attachments" *(not in the issue's table)* | 13 of 72 | **extract** → `take-issue/video-frames.md` |
| `/go` § "Argument shape" — the canary | 9 of 103 | decline — win under indirection cost |
| `/issue` Step 3 — the split machinery | — | decline — already done, elsewhere |
| `/from-branch` § "Argument shape" + § "Failure modes" | 26 of 125 | decline — neither half is a minority entry |
| `/tend-prose` — the four lens sections | 143 of 319 | decline — inverted, as the issue suspected |

### Extract 1 — `/plan` § "If the session is already in native plan mode"

Lines 20–36 move to `.claude/skills/plan/native-plan-mode.md`, beside the
`exit-dialog.md` the section already `cp`s.

It passes all three. The trigger is binary and externally announced: the harness
names a plan file under `/root/.claude/plans/`, and `Edit`/`Write` refuse as
read-only. Most `/plan` entries are bare prose in an accept-edits session, so
plan mode is the minority. A session not in plan mode needs nothing the section
carries — the only thing outside it that depends on it is `/plan` Part 1's
ordering, which the pointer states.

What makes this the strongest of the three: `.claude/hooks/plan-mode-notice.sh`
**is** the trigger detector. It fires on every prompt while the mode is on and
already names the section by heading, so it repoints at the sidecar and the
resident pointer shrinks to the local-CLI case the hook does not cover (the hook
is remote-only by design).

Resident pointer keeps: the condition, the tell, that the exit is plan mode's
own rather than an override of it, and the load instruction. Sidecar takes: the
three numbered steps, the `exit-dialog.md` `cp` and its continued-work caveat,
the rejection escape hatch, and the "exiting is not the go-ahead" clause.

### Extract 2 — `/squash-message` Step 2, working-file selection

Lines 99–126 move to `.claude/skills/squash-message/working-file.md`: what to do
when **neither** working file is on disk.

The trigger is a `test -f`, decided before anything is read. The tracked file
lives from PR-open until CI goes green, so the majority run finds it and edits
it; absence is the first creation and the post-sweep restore. Criterion 3 is
what makes the split clean — the presence branch is four lines and carries the
whole majority path (it is the working file, it is a live doc rather than a
blank sheet, Step 5 commits it).

Sidecar takes: the draft-vs-ready fork that decides whether to create the tracked
file, the restore-from-history recipe, the `tmp/` fallback for a branch no
PR-opening lane ever ran on, and the lifecycle paragraph. Step 5's three cleanup
bullets stay resident — only the *selection* moves, not what happens afterwards.

### Extract 3 — `/take-issue` § "Video attachments" (beyond the issue's table)

Lines 45–57 move to `.claude/skills/take-issue/video-frames.md`.

Found by sweeping the frequently-loaded skills rather than the table. It passes
more cleanly than two of the table's entries: the trigger is `file` reporting a
video, most issues have none, and `/take-issue` runs on every issue-carrying
prompt via `/task`, `/plan` and `/go`. Resident pointer keeps the two facts a
non-triggering session needs — exported attachments may have no extension, so
`file` them — plus the load instruction.

### Decline 1 — `/go`'s canary

Nine lines of 103, against a resident pointer of two or three. Net saving is
noise, and the split runs through the middle of one argument: two of the four
canary bullets describe the **normal** entries (`/go <target>` as the first
prompt, bare `/go` mid-session), so the resident half would have to restate the
permission it grants them. Paying an indirection to save six lines is the wrong
trade.

### Decline 2 — `/issue` Step 3

The section is gone. `/issue` is now a 31-line redirect, and the split machinery
it described lives in `.claude/skills/plan/carving.md` — itself a colocated
sidecar, extracted by the very pattern this issue generalizes. Nothing to do;
recorded because the issue's table still lists it at ~52 of 140.

### Decline 3 — `/from-branch`

Both halves fail, for opposite reasons.

§ "Argument shape" fires every run: parsing the target and the follow-up is the
first thing the skill does.

§ "Failure modes to call out" is seven lines holding six unrelated triggers, so
there is no single condition a pointer can state — "load this if something goes
wrong" is precisely the silent skip the issue's counter-force section warns
about, since you cannot tell you are in a failure mode until you read it. One of
the six is worse than merely resident: "target branch already checked out — skip
Steps 2–4" is load-bearing on a **normal** path, and `/go`'s canary cites it by
heading to explain why an already-checked-out attach degrades into a silent
no-op.

### Decline 4 — `/tend-prose`

The issue's suspicion is confirmed by the arithmetic. The default full sweep
needs all four lenses and `/go` Step 3 invokes it bare on every implementation
session, so per-lens sidecars would make the majority run read four extra files
for the same tokens, to save ~107 lines on the minority single-lens run.
Criterion 2 is inverted; nothing to extract.

## The script

**Acceptance item 2 is already satisfied.** `scripts/check-skill-catalog.sh`
assertion 1 matches `@\.claude/[A-Za-z0-9/_-]+\.md` — path-agnostic since it was
written, and today it validates `@.claude/skills/plan/carving.md` and
`@.claude/voice/voice.md` alongside the `SKILL.md` references. The issue's claim
that it "only matches `@.claude/skills/<name>/SKILL.md`" describes a narrower
regex than the one in the tree. Record this in the PR and change nothing there.

**What the sweep actually needs is the reverse direction.** Assertion 1 catches a
pointer whose target is missing; it cannot catch a sidecar nothing points at.
That is the failure this sweep multiplies — an extraction whose pointer was
never written, or was deleted by a later edit to the resident file — and its
symptom is identical: the agent follows the surviving prose and never learns
what they missed.

Add **assertion 5**: every `.md` beside a `SKILL.md` under `.claude/skills/*/`
must be named somewhere in the search surface, by `@`-reference or by bare path
or basename. The looser match is deliberate — `exit-dialog.md` is reached by a
`cp` with no `@` on it, and is correctly referenced.

## The catalog

No new rows. Each sidecar joins its skill's **Pulls in** column, which is the
closure column — "siblings it cannot work without" is exactly what a sidecar is.

The issue states the precedent as "a sidecar that travels with its skill gets no
row of its own", citing `exit-dialog.md` and `analyst-rules.md`. `carving.md`
contradicts it with a row of its own. The discriminator that actually holds
across all three: a sidecar gets a row when an adopter faces a **separate
decision** about it — carving is a workflow a project may not want, while an exit
dialog and a fan-out's analyst rules are internals of a skill already decided on.
All three new sidecars are internals, so none gets a row. The `carving.md`
discrepancy is left alone and noted in the PR rather than repaired here.

## Open question

**1. Should `/take-issue` Step 0 point at the new `native-plan-mode.md`?**
Step 0 is a ten-line stop-and-tell on the same trigger as Extract 1, and today it
prescribes a *different* recovery: switch mode by hand and send any reply, where
`/plan` takes `ExitPlanMode`'s own exit. Unifying them would improve a session
that reaches `/take-issue` via `/task` or `/go` in plan mode, which currently
dead-ends.

- **(a) Leave it — recommended, and in force in this plan.** It is a behavior
  change to a gate, not an extraction, and folding it into a sweep hides it.
- (b) Repoint Step 0 at the sidecar, making `/plan` the single owner of the
  recovery.

If (b), say so and it lands in the same PR.

## Steps

1. Extract `/plan` § "If the session is already in native plan mode" →
   `plan/native-plan-mode.md`; write the resident pointer; repoint
   `.claude/hooks/plan-mode-notice.sh` at the sidecar.
2. Extract `/squash-message` Step 2's absent-file branch →
   `squash-message/working-file.md`; write the resident pointer; check Step 5's
   restored-file bullet still resolves.
3. Extract `/take-issue` § "Video attachments" → `take-issue/video-frames.md`;
   write the resident pointer.
4. Add assertion 5 to `scripts/check-skill-catalog.sh`.
5. Add the three sidecars to their skills' **Pulls in** columns in
   `.claude/skills/update-muthur/catalog.md`.
6. Run `./scripts/vet.sh`; confirm assertions 1 and 5 both pass over the new
   references.

## DRY notes

- **The three sidecars share no content**, so nothing is extracted *into* a
  common home. Each is a contiguous span lifted out of one skill and left beside
  it; the pattern is shared, the prose is not.
- **The one real duplication the sweep surfaces is the plan-mode recovery**,
  stated once in `/plan` and once, differently, in `/take-issue` Step 0. Extract
  1 does not resolve it — the open question above does, and its recommendation is
  to leave the two standing. Forcing a shared home now would mean silently
  changing what `/take-issue` tells the operator, which is a behavior change
  wearing a refactor's clothes.
- **`.claude/hooks/plan-mode-notice.sh` stops duplicating a heading and starts
  citing a file.** It currently names `/plan`'s section by title, which is a
  citation that breaks silently when the heading is reworded. Pointing it at
  `native-plan-mode.md` puts it under assertion 1 — the reference becomes
  machine-checked rather than prose.
- **Assertion 5 is new, not a generalization of an existing check.** Assertion 1
  walks references to files; assertion 5 walks files to references. They share
  the `sources` array already built at the top of the script and nothing else,
  so the reuse is the array, not a helper — extracting a common "is this path
  mentioned" function for two callers with opposite directions would be net
  negative.
- **No new rows in the catalog**, so no row-shaped duplication of the
  descriptions that already live in each skill's frontmatter.
