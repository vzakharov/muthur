> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Give the loop an entry rule for untracked work, and move the split decision into `/plan`

Two changes to where the loop's entry decisions are made. They are separable in
principle and cohesive in practice: both are about a call currently made by the
skill that happens to be holding the work rather than by the skill that is in a
position to make it, and they touch the same five files.

**Depends on #71**, which makes `/issue` hand every issue to `/task`. This plan
assumes that landed; it is written against the post-#71 tree.

## Part A — an entry rule for prose that names no skill

CLAUDE.md § "Plan mode & questions in web sessions" currently says to treat a new
session as a planning session, with exceptions for "no plan", `/from-branch`,
`/handle`, and an issue title ending in `#N`. Every other opening prompt formally
routes to `/plan` — including a question, which no agent has ever written a plan
file for. The ladder is already being overridden by unstated judgment.

Replace the default with a three-way read on **whether the request asks for a
change to this codebase**:

| Opening prompt | Routes to |
| --- | --- |
| asks for a change, untracked — "add an admin page" | `/task` |
| asks for a change, carries an issue number — "add an admin page #55" | `/issue` |
| asks for no change — "what do we need to add an admin page?" | nothing: answer it |

Three things the wording has to get right:

- **The test is the expected deliverable, not the grammar.** "Analyse the latest
  market trends" is an imperative and still lands in row 3, because nothing in
  this repo changes as a result. (In a repo whose product *is* documents or
  research, the same sentence lands in row 1 — the test reads the repo, not the
  sentence.)
- **Row 3 is a stated bucket, not a gap.** Left unstated, the old default
  swallows it and questions route to `/plan` again. It says: answer the question;
  no skill covers this by design. Where the read was wrong, the operator's next
  message is a directive and lands in row 1 — one turn, not a wasted plan file.
- **`let's …` is a token collision.** It is on `/plan` § "The approval gate"'s
  go-ahead list, so "let's add an admin page" is a directive at launch and an
  approval mid-session. The rule keys on launch-vs-continued, which the ladder's
  last bullet already separates.

**What this costs, stated plainly in the ladder itself:** today the operator opts
into the agent's plan-or-not call by typing `/task`; under this rule the agent
makes that call on every new session that asks for a change. The gate does not
disappear — `/task` Question 1 routes gate-worthy work back to `/plan` — it moves
from *always* to *when the questions say so*.

## Part B — the split decision moves from `/issue` to `/plan`

`/issue` Step 3 decides the carve before anything has read the code, and `/issue`
Step 4 then carries the exception that a split "skips the call and plans". Both
go away:

- **`/issue` becomes transport**, the shape `/pr` already has: export, commit,
  hand to `/task` with `<issue>` = the number the eventual PR must close. No
  wording change to how `Closes #N` is planted.
- **`/task` is untouched.** Work that needs a carve already satisfies Question 1
  ("the scope is itself the question", "costs far more to produce than to
  describe"), so it routes to `/plan` without a special case.
- **`/plan` gains the carve.** When the task passes the bar, the plan specs the
  first slice in full and describes the remainder coarsely, and the slices are
  filed as issues.
- **The parent.** Arriving from `/issue`, it exists already. Arriving from bare
  prose, `/plan` creates it: it stays open as a grouping artifact and is never
  what the PR closes. Either way the first slice is a child, never the parent —
  the rule `/issue` states today, carried over unchanged.

What this buys beyond tidiness: **untracked work becomes splittable at all.**
Today the carve lives only inside a skill you reach by already having an issue
number, so "add an admin page" typed bare has no path to one.

### The ordering constraint that fixes when issues are filed

`/pr` Step 4 reads the closing issue off the **branch slug**, and `/plan` Part 1
requires the branch renamed **before** the plan file is written, the file being
named after the slug. So within a `/plan` turn the order is forced:

1. carve decision, proposed in prose, stopping for approval — creating nothing;
2. file the parent (when there isn't one) and every child;
3. rename the branch to lead with the first child's number;
4. write the plan file;
5. publish via `/pr`.

This settles the question of whether filing waits for `/go`: it cannot. Deferring
it leaves step 3 with no number and costs the PR its `Closes`. The gate that
protects the tracker is `/issue` Step 3's existing one — propose in prose, create
nothing until the operator agrees — and it moves into `/plan` unchanged, so no
issue is filed ahead of the operator either way.

### Group closure

The catalog puts `/plan` in **G2** and `/issue` / `/propose-issue` in **G3**, so
`/plan` cannot simply absorb issue-filing: an adopter who tracks no issues would
get a step they cannot run. Split the carve along that line:

- **G2, stated in `/plan`:** whether to carve, where the seams are, and the plan
  file's shape — first slice in full, remainder coarse.
- **G3, in `.claude/skills/issue/splitting.md`:** creating the parent and the
  children, the native `sub_issues` link and its two 422 traps, the ≥5-files
  granularity rule, and carrying an enumerated parent's verbatim reports and
  attachments into each child.

`/plan` cites the G3 file conditionally. For a G2-only adopter the carve degrades
to its plan-file half: the plan names the slices and nothing is filed. Precedent
for the conditional edge is `/finalize`, whose **Requires** column already reads
"**conditionally** `/issue` (G3)".

### The outcome-3 hole

`/task` outcome 3 — plan, then go — writes the plan straight to `*.in-progress.md`
under the conditional go-ahead and implements in the same session. A carve
discovered *inside* that plan would file issues and start a multi-PR programme
with no operator gate. So `/plan` states the recovery: discovering a split while
running outcome 3 sends the task back to the gate. It is Question 1's "the scope
is itself the question", answered late.

## Files

| File | Change |
| --- | --- |
| `CLAUDE.md` | § "Plan mode & questions in web sessions": replace the planning-session default with Part A's three rows; keep the `/from-branch` / `/handle` continued-work bullet as the launch-vs-continued line |
| `.claude/skills/issue/SKILL.md` | delete Step 3; renumber; Step 4 loses the split exception |
| `.claude/skills/issue/splitting.md` | **new** — the G3 filing half, moved verbatim from Step 3 |
| `.claude/skills/plan/SKILL.md` | new section: the carve bar, the plan-file shape, the forced ordering, the outcome-3 recovery, the conditional cite |
| `.claude/skills/task/SKILL.md` | one line: `/task` is where a launch-time directive lands |
| `.claude/skills/update-muthur/catalog.md` | `/issue` and `/plan` rows re-described; `/plan` gains a conditional G3 edge |

Verified with `./scripts/check-skill-catalog.sh` (every `@`-reference resolves,
one catalog row per skill).

**Not itself split-worthy**, by the bar this plan moves: six files, one seam, one
PR.

## Open questions

1. **Does the parent go through `/propose-issue`?** It is the one issue in a
   carve worth deduping — "add an admin page" may already be filed, which is
   worth knowing before creating a second umbrella.
   - **(a) Parent only — recommended.** Children are created directly; deduping
     each against the whole backlog is a round-trip per slice for a near-always
     empty result.
   - (b) Nothing goes through it — `/plan` creates the parent directly.
   - (c) Everything goes through it.
2. **What does a G2-only adopter get?**
   - **(a) The plan-file half — recommended.** The plan names the slices; nothing
     is filed; the operator does what they like with the list.
   - (b) Splitting is G3-only, and `/plan` says nothing about carving without a
     tracker.

Both are written into the plan with the recommended option in force, so silence
resolves them.

## DRY notes

- **The carve criteria move, they are not copied.** `/issue` Step 3 is deleted
  outright, not summarized into a pointer — the criteria have one home after this
  (`/plan`), and the filing mechanics have one home (`issue/splitting.md`). The
  failure mode being avoided is the convention stated twice, which CLAUDE.md
  § "Writing things down" names as the finding rather than the fix.
- **"First slice in full, remainder coarse" goes to `/plan` only.** It is a
  plan-shape rule, so `issue/splitting.md` does not restate it.
- **No shared issue-creation helper.** `/propose-issue` already owns
  dedupe-then-create for *one* issue. Extracting a common creator over it and the
  child loop would force the dedupe round-trip onto every child, which is exactly
  what question 1(a) rejects — the two call sites want different behavior, so the
  duplication is a straight `gh api` loop and stays local to `issue/splitting.md`.
- **CLAUDE.md stays the single home of routing.** `/task` and `/issue` point at
  the ladder rather than restating its rows; only `/task` gains the one line that
  says a launch-time directive lands there.
- **Polar-bear watch on the diff.** Deleting `/issue` Step 3 must not leave a
  sentence anywhere saying the split no longer happens there. `/tend-prose
  negation` runs over the result.

## Out of scope

- Rebasing or stacking on #71 — this lands after it.
- `/handle`'s missing note that a compaction boundary does not discharge the
  invocation, and `/pr`'s environment note about `gh pr edit` being unusable
  here. Both are separate one-liners.
- Any change to what `/go` does with a plan that carries a carve. The first
  slice is an ordinary plan by the time `/go` sees it.
