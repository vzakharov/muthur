> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Give the loop an entry rule for untracked work, and move the split decision into `/plan`

Two changes to where the loop's entry decisions are made. They are separable in
principle and cohesive in practice: both are about a call currently made by the
skill that happens to be holding the work rather than by the skill that is in a
position to make it, and they touch the same files.

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

Four things the wording has to get right:

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
- **In doubt, read it as row 3.** The rows are not symmetric in what a wrong read
  costs: row 3 read as row 1 mutates and commits against a request that wanted an
  answer, and undoing it is a revert the operator has to ask for. Row 1 read as
  row 3 costs one turn — the answer lands, the operator says "now do it", and
  whatever the answer produced along the way is sitting in `tmp/`, to be moved to
  a tracked location if it turns out to be wanted. So the tie goes to answering,
  and work done while answering stays in `tmp/` until asked for.

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
- **`/plan` gains the carve, and creates nothing.** When the task passes the bar,
  the plan specs the first slice in full, describes the remainder coarsely, and
  **names the issues it proposes to file** — parent and children — as part of the
  plan the operator is reviewing. The plan file is the proposal; the go-ahead is
  the approval; `/go` does the filing.
- **Every slice goes through `/propose-issue`**, parent and children alike, split
  across the two turns along the line that skill already has in it. `/plan` runs
  its Steps 1–2 — search and triage, read-only — for each proposed issue, and
  writes the matches into the plan; `/go` runs its Step 3 and creates what the
  operator approved. So a match is something the operator rules on while reviewing
  the carve, not an interruption after it, and a slice that turns out to be tracked
  already gets linked as the sub-issue instead of duplicated.
- **The parent.** Arriving from `/issue`, it exists already. Arriving from bare
  prose, the plan proposes one and `/go` creates it. It stays open as a grouping
  artifact and is never what the PR closes; the first slice is a child, never the
  parent — the rule `/issue` states today, carried over unchanged. **A match on the
  parent stops and reports** rather than being adopted like a child's: somebody
  else already tracking the whole umbrella is what changes the operator's
  judgment about whether to carve at all.

What this buys beyond tidiness: **untracked work becomes splittable at all.**
Today the carve lives only inside a skill you reach by already having an issue
number, so "add an admin page" typed bare has no path to one.

### Nothing is filed until the go-ahead

`/plan` carves, dedupes read-only, and writes the proposed parent and children
into the plan file. `/go` files them on the go-ahead that flips the plan, in the
same commit's neighbourhood as the flip. A `/plan` turn that ends unapproved
leaves the tracker exactly as it found it.

This needs no gate of its own — the plan file already **is** the gate, which is
what makes the carve's approval free rather than a second propose-and-stop layered
inside the planning turn.

**This requires the issue number to leave the branch slug**, which it does here.
`/pr` Step 4 reads the closing issue off the slug today, and `/plan` renames the
branch before writing the plan file, which is named after it — so a number the
slug must carry is a number that must exist by then, which is filing at plan time.
Renaming later is not available: the plan filename tracks the slug, and a rename
after the PR exists closes the PR. So the slug read goes, and the PR body carries
the number instead:

- **A `Closes` line appears only where the work is tracked, or is about to be.**
  Most PRs close no issue and carry no line, exactly as today. The two origins
  that put one there are an `/issue` call, where the number is known, and a carve,
  where the children do not exist yet — and only the second writes
  **`Closes #<tbd>`**. The marker means "an issue is coming and its number belongs
  here", which is a durable state on the branch rather than something lost with
  the turn; it is never a stand-in for not having looked.
- **`/propose-issue` Step 3 fills it in**, being the one place an issue is ever
  created. Whoever creates the issue is the only party that can know the number
  the moment it exists, and routing every slice through that skill is what keeps
  the rule in one home.
- **`docs/issue/<n>/` serves the first origin and only it.** It exists only where
  `/issue` exported a thread, which is precisely the path where the number was
  never in doubt; a resumed session reads it there instead of off the slug. Work
  that *creates* its issue has no export, which is what the marker covers.

None of these reads the session's own memory, which is what the slug was standing
in for. `/issue` Step 2 commits the export before any planning precisely so a
resumed session — after a handoff, a compaction boundary, a parallel session —
re-reads the branch rather than the turn that created it, and `#<tbd>` extends the
same principle to a number that does not exist yet.

### Group closure

The catalog puts `/plan` in **G2** and `/issue` / `/propose-issue` in **G3**, so
`/plan` cannot simply absorb issue-filing: an adopter who tracks no issues would
get a step they cannot run. Split the carve along that line:

- **G2, stated in `/plan`:** whether to carve, where the seams are, and the plan
  file's shape — first slice in full, remainder coarse.
- **G3, in `.claude/skills/issue/splitting.md`:** calling `/propose-issue` for
  each slice, the native `sub_issues` link and its two 422 traps, the ≥5-files
  granularity rule, and carrying an enumerated parent's verbatim reports and
  attachments into each child.

`/plan` cites the G3 file conditionally. For a G2-only adopter the carve is the
plan naming its slices, and nothing else: no fallback procedure is written for
what they do with a list they can't file. Precedent for the conditional edge is
`/finalize`, whose **Requires** column already reads "**conditionally** `/issue`
(G3)".

### The one case with no gate: outcome 3

Making the plan file the gate covers every route into `/plan` except one.
`/task` outcome 3 — plan, then go — writes straight to `*.in-progress.md` under
the conditional go-ahead, with no draft state and so no gate, and `/go` follows in
the same session. A carve discovered there would file a parent and children off a
one-line prompt.

So `/plan` states the recovery: **a carve discovered while running outcome 3 sends
the task back to the gate** — write the plan as a draft, file nothing, hand off.

This is not a new rule, which is why it costs a sentence. Filing issues is
outward-facing and awkward to undo — nobody declines it by not merging; somebody
closes five issues by hand — so it is Question 1's "a review round comes too late"
firing on information that only arrived once the planning started. Question 1 was
answered with the wrong task in view; the carve is the correction.

## Files

| File | Change |
| --- | --- |
| `CLAUDE.md` | § "Plan mode & questions in web sessions": replace the planning-session default with Part A's three rows; keep the `/from-branch` / `/handle` continued-work bullet as the launch-vs-continued line |
| `.claude/skills/issue/SKILL.md` | delete Step 3; renumber; Step 4 loses the split exception; § "Branch name" drops the issue-number requirement |
| `.claude/skills/pr/SKILL.md` | Step 4 reads `docs/issue/<n>/` instead of the slug, and writes `Closes #<tbd>` on a carve whose children are not filed yet; no line at all where no issue is involved; the `<issue>` parameter line follows |
| `.claude/skills/propose-issue/SKILL.md` | say that Steps 1–2 and Step 3 may run in different turns; Step 3 fills any `#<tbd>` on the branch and in the PR body |
| `.claude/skills/squash-message/SKILL.md` | never carry `#<tbd>` into the title or the `Closes` trailer — omit the reference until it resolves |
| `.claude/skills/issue/splitting.md` | **new** — the G3 filing half, moved verbatim from Step 3 |
| `.claude/skills/plan/SKILL.md` | new section: the carve bar, the plan-file shape including the proposed issues, the read-only dedupe, the outcome-3 recovery, the conditional cite |
| `.claude/skills/go/SKILL.md` | file the issues the approved plan proposes, before the work |
| `.claude/skills/task/SKILL.md` | one line: `/task` is where a launch-time directive lands |
| `.claude/skills/update-muthur/catalog.md` | `/issue` and `/plan` rows re-described; `/plan` gains a conditional G3 edge |

Verified with `./scripts/check-skill-catalog.sh` (every `@`-reference resolves,
one catalog row per skill).

**Not itself split-worthy**, by the bar this plan moves: ten files, one seam, one
PR.

## Settled in review

On the thread at `.claude/skills/task/SKILL.md`:14:

- **`/propose-issue` runs on the parent only**, children created directly — and a
  dedupe hit stops and reports instead of adopting the match.
- **A G2-only adopter gets the plan naming its slices and nothing more.** Working
  around a tracker they declined is theirs to solve, not this repo's.
- **Outcome 3 is the one route with no gate**, so it keeps a stated recovery: a
  carve found there goes back to the gate as a draft plan.

On the review of this file:

- **`/plan` proposes the issues; `/go` files them.** Nothing reaches the tracker
  before the go-ahead, and the plan file is the gate that makes it so.
- **In doubt, read a prompt as asking for no change.** Answer it, keep whatever
  the answer produced in `tmp/`, and move it somewhere tracked only if asked.
- **The issue number leaves the branch slug**, and `/pr` Step 4 stops reading it
  there. The PR body carries it instead — the number where an `/issue` call knows
  it, `#<tbd>` where a carve has yet to file it, and no line at all on the PRs
  that close nothing, which is most of them. This rides this PR, the sites being
  ones it already edits.
- **Both parent and children go through `/propose-issue`**, which is what lets the
  `#<tbd>` fill-in have a single home — and gets the children deduped for free,
  at plan time where the operator rules on any match before approving.

Nothing is left open. The plan is waiting on a go-ahead, not on an answer.

## DRY notes

- **The carve criteria move, they are not copied.** `/issue` Step 3 is deleted
  outright, not summarized into a pointer — the criteria have one home after this
  (`/plan`), and the filing mechanics have one home (`issue/splitting.md`). The
  failure mode being avoided is the convention stated twice, which CLAUDE.md
  § "Writing things down" names as the finding rather than the fix.
- **"First slice in full, remainder coarse" goes to `/plan` only.** It is a
  plan-shape rule, so `issue/splitting.md` does not restate it.
- **One issue-creation site: `/propose-issue`.** Parent and children both go
  through it rather than the children through a local `gh api` loop, because the
  `#<tbd>` fill-in has to live wherever issues are born and two birthplaces means
  two copies of that rule — the convention stated twice that CLAUDE.md § "Writing
  things down" calls the finding. What `issue/splitting.md` keeps is what is
  genuinely about the parent-child *relation* rather than about creating an issue:
  the `sub_issues` link and its two 422 traps, the granularity rule, and carrying
  an enumerated parent's verbatim reports into each child.
- **`/propose-issue` is split across turns, not forked into two variants.** `/plan`
  runs Steps 1–2 and `/go` runs Step 3, which the skill's own numbering already
  separates; neither turn needs a mode flag, and nothing is duplicated by the
  split.
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
- Anything `/go` does with a carve beyond filing the proposed issues first. Past
  that the first slice is an ordinary plan.
