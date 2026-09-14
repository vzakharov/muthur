> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Give the loop an entry rule for untracked work, and move the split decision into `/plan`

Two changes to where the loop's entry decisions are made. They are separable in
principle and cohesive in practice: both are about a call currently made by the
skill that happens to be holding the work rather than by the skill that is in a
position to make it, and they touch the same five files.

**Builds on this branch's own change**, which makes `/issue` hand every issue to
`/task`. The plan is written against the tree as `issue-plan-call.completed.md`
leaves it, and implementing it grows this PR rather than opening another.

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
  prose, `/plan` creates it through `/propose-issue` — the one issue in a carve
  worth deduping, since the umbrella is the one somebody else may already have
  filed. **A dedupe hit stops the turn and reports it** rather than silently
  adopting the found issue: somebody else being on this work is exactly what
  changes the operator's judgment, and it is invisible from the dedupe result.
  Children are created directly. The parent stays open as a grouping artifact and
  is never what the PR closes; the first slice is a child, never the parent — the
  rule `/issue` states today, carried over unchanged.

What this buys beyond tidiness: **untracked work becomes splittable at all.**
Today the carve lives only inside a skill you reach by already having an issue
number, so "add an admin page" typed bare has no path to one.

### When the issues are filed

Within a `/plan` turn the order is:

1. carve decision, proposed in prose, stopping for approval — creating nothing;
2. file the parent (when there isn't one) and every child;
3. rename the branch to lead with the first child's number;
4. write the plan file;
5. publish via `/pr`.

Steps 2–3 are in that order because `/pr` Step 4 reads the closing issue off the
**branch slug**, and `/plan` Part 1 renames the branch before writing the plan
file, which is named after the slug. **That read is itself under review** — the
operator means to drop the issue number from branch slugs, and if it goes, `/pr`
needs another place to read `Closes #N` from (`docs/issue/<n>/` on the branch is
the cheap candidate; see "Settled in review"). Nothing in this plan changes with
it: filing stays at step 2 on its own merit, which is that the carve's approval
and the tracker state land in the same turn the operator reviews the plan.

The gate protecting the tracker is `/issue` Step 3's existing one — propose in
prose, create nothing until the operator agrees — and it moves into `/plan`
unchanged, so no issue is filed ahead of the operator either way.

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

`/plan` cites the G3 file conditionally. For a G2-only adopter the carve is the
plan naming its slices, and nothing else: no fallback procedure is written for
what they do with a list they can't file. Precedent for the conditional edge is
`/finalize`, whose **Requires** column already reads "**conditionally** `/issue`
(G3)".

### The carve is not covered by a conditional go-ahead

`/task` outcome 3 — plan, then go — writes the plan straight to `*.in-progress.md`
under the conditional go-ahead and implements in the same session, so a carve
discovered inside it would file issues with no gate in the turn. The carve's own
propose-and-stop covers this already; the one clause `/plan` adds is that
`/task`'s conditional go-ahead does **not** extend to it. The go-ahead was scoped
to the task as described, and a carve is the finding that the task wasn't that.

## Files

| File | Change |
| --- | --- |
| `CLAUDE.md` | § "Plan mode & questions in web sessions": replace the planning-session default with Part A's three rows; keep the `/from-branch` / `/handle` continued-work bullet as the launch-vs-continued line |
| `.claude/skills/issue/SKILL.md` | delete Step 3; renumber; Step 4 loses the split exception |
| `.claude/skills/issue/splitting.md` | **new** — the G3 filing half, moved verbatim from Step 3 |
| `.claude/skills/plan/SKILL.md` | new section: the carve bar, the plan-file shape, the propose-and-stop gate and the ordering, the clause excluding the carve from `/task`'s conditional go-ahead, the conditional cite |
| `.claude/skills/task/SKILL.md` | one line: `/task` is where a launch-time directive lands |
| `.claude/skills/update-muthur/catalog.md` | `/issue` and `/plan` rows re-described; `/plan` gains a conditional G3 edge |

Verified with `./scripts/check-skill-catalog.sh` (every `@`-reference resolves,
one catalog row per skill).

**Not itself split-worthy**, by the bar this plan moves: six files, one seam, one
PR.

## Settled in review

On the thread at `.claude/skills/task/SKILL.md`:14:

- **`/propose-issue` runs on the parent only**, children created directly — and a
  dedupe hit stops and reports instead of adopting the match.
- **A G2-only adopter gets the plan naming its slices and nothing more.** Working
  around a tracker they declined is theirs to solve, not this repo's.
- **Outcome 3 needs a clause, not a procedure** — the carve's own gate already
  holds; only the scope of `/task`'s conditional go-ahead needed stating.

## Still open

**Does the issue number stay in the branch slug?** The operator means to remove
it. It is the mechanism this branch's own change installed: `/pr` Step 4 reads the
number off the slug precisely because no parameter threads it any more, and that
read is what keeps a split closing the chosen child rather than a parent mentioned
in a commit body. Removing it needs a replacement or an accepted loss:

- **(a) `/pr` reads `docs/issue/<n>/` off the branch** — already committed at
  `/issue` Step 2, survives a rename, and covers the split if the carve exports
  the chosen child beside the parent. Keeps the no-threading win.
- (b) Re-thread the `<issue>` parameter — undoes this branch's third change.
- (c) Drop `Closes #N` and close issues by hand.

Three sites state the rule: `/issue` § "Branch name", `/pr`'s `<issue>` parameter
line, `/pr` Step 4. Small enough to ride this PR, but it edits this PR's own diff,
so it waits for the operator rather than being folded in. **Nothing else in this
plan depends on the answer** — filing at plan time survives either way.

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

- `/handle`'s missing note that a compaction boundary does not discharge the
  invocation, and `/pr`'s environment note about `gh pr edit` being unusable
  here. Both are separate one-liners.
- Any change to what `/go` does with a plan that carries a carve. The first
  slice is an ordinary plan by the time `/go` sees it.
