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

Replace the default with a two-way read on **whether the request asks for a
change to this codebase**:

| Opening prompt | Routes to |
| --- | --- |
| asks for a change — "add an admin page", with or without a `#55` | `/task` |
| asks for no change — "what do we need to add an admin page?" | nothing: answer it |

**An issue number is not a third row.** A `#<N>` in the prompt means the thread is
exported and committed before anything else happens — by whichever skill received
the prompt, which is `/task` here and `/plan` or `/go` where the operator named
one. What it does not mean is a different destination: a tracked task is owed the
plan-or-not call exactly as an untracked one is, and the number changes what the
session has read, not where it goes. This ladder is the rule's home; `/task`,
`/plan` and `/go` carry a pointer to it rather than a copy of it.

Four things the wording has to get right:

- **The test is the expected deliverable, not the grammar.** "Analyse the latest
  market trends" is an imperative and still lands in row 2, because nothing in
  this repo changes as a result. (In a repo whose product *is* documents or
  research, the same sentence lands in row 1 — the test reads the repo, not the
  sentence.)
- **Row 2 is a stated bucket, not a gap.** Left unstated, the old default
  swallows it and questions route to `/plan` again. It says: answer the question;
  no skill covers this by design. Where the read was wrong, the operator's next
  message is a directive and lands in row 1 — one turn, not a wasted plan file.
- **`let's …` is a token collision.** It is on `/plan` § "The approval gate"'s
  go-ahead list, so "let's add an admin page" is a directive at launch and an
  approval mid-session. The rule keys on launch-vs-continued, which the ladder's
  last bullet already separates.
- **In doubt, read it as row 2.** The rows are not symmetric in what a wrong read
  costs: row 2 read as row 1 mutates and commits against a request that wanted an
  answer, and undoing it is a revert the operator has to ask for. Row 1 read as
  row 2 costs one turn — the answer lands, the operator says "now do it", and
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

- **`/issue` becomes transport, and stops being an entry point.** What is left
  after Step 3 goes is export and commit — so the handoff to `/task` goes too, along
  with § "Branch name", whose one contribution this plan removes anyway. The skill
  no longer decides anything, which is what takes it out of the operator's hands:
  its callers are `/task`, `/plan` and `/go`, each running it first when the prompt
  carries a `#<N>`, and the number they pass on as `<issue>` is what the eventual PR
  must close. No wording change to how `Closes #N` is planted. Its argument shape
  gains the third form the ladder sends it — the number is the argument, surrounding
  prose is the operator's own summary, and the export outranks it, which is the rule
  already there as "do not start solving the task from the title alone".
- **And it takes the name that says which half it is: `/take-issue`.** The noun
  names the argument but not the operation, and this repo has two operations on
  that argument. Nothing in the naming rule objects: it bars names that double as
  go-ahead tokens, and "take" is not one — naming a skill after its argument is the
  stronger guarantee that rule offers, not the convention the repo follows, which
  is why `/propose-issue` sits under it without being an exception. "Take" over
  "read", "fetch", "load" or "import": those name the export step, and the skill's
  contract to its callers is that the issue has been taken onto the branch —
  exported, committed, and there for a later session to re-read. `/track-` is what
  `/propose-issue` does.
- **The old name becomes a stub that forwards to `/plan`.** `/issue` cannot forward
  to `/take-issue`, which is no longer something an operator calls, so it forwards to
  one of the four skills that replaced it and actually runs it: given a `#<N>` it
  invokes `/plan <the surrounding prose> #<N>`, and says in one line that `/task` and
  `/go` take that same shape — the first hands the plan-or-not call back to the
  agent, the second skips it. Given no number there is nothing to take, and the prose
  is an unfiled unit of work: that reading is `/propose-issue`, which the stub names
  rather than runs, filing being the one of the four that writes to the tracker.
  `/plan` is the default because it is where `/issue` sent work for as long as the
  name meant anything, and because the deprecated name says nothing about which
  reading was meant — so the guess should be the one that costs a round trip rather
  than an unreviewed diff. It is the `/implement` pattern with a fork in it, kept for the
  muscle memory and for the handoff blocks already written.
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
- **The parent.** Arriving from `/take-issue`, it exists already. Arriving from bare
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
  that put one there are a `/take-issue` call, where the number is known, and a carve,
  where the children do not exist yet — and only the second writes
  **`Closes #<tbd>`**. The marker means "an issue is coming and its number belongs
  here", which is a durable state on the branch rather than something lost with
  the turn; it is never a stand-in for not having looked.
- **`/propose-issue` Step 3 fills it in**, being the one place an issue is ever
  created. Whoever creates the issue is the only party that can know the number
  the moment it exists, and routing every slice through that skill is what keeps
  the rule in one home.
- **`docs/issue/<n>/` serves the first origin and only it.** It exists only where
  `/take-issue` exported a thread, which is precisely the path where the number was
  never in doubt; a resumed session reads it there instead of off the slug. Work
  that *creates* its issue has no export, which is what the marker covers.

None of these reads the session's own memory, which is what the slug was standing
in for. `/issue` Step 2 commits the export before any planning precisely so a
resumed session — after a handoff, a compaction boundary, a parallel session —
re-reads the branch rather than the turn that created it, and `#<tbd>` extends the
same principle to a number that does not exist yet.

### Group closure

The catalog puts `/plan` in **G2** and `/take-issue` / `/propose-issue` in **G3**, so
a `/plan` that states the filing reaches across a group line. **It states it
anyway, in full** — the carve is one procedure, and cutting it at the group line
would leave the G2 half stopping exactly where its reader needs the next sentence.

What a G2-only adopter does instead — keep the remaining slices in the plan file,
in a backlog doc, in whatever tracker they do use — is theirs to decide, and this
repo writes no degradation path for it. The catalog is where they are told that,
rather than discovering it: `/plan` joins `/finalize` in § "Closure is not
optional", whose bullet already reads "reaches into G3 and G5 conditionally …
strip the two citations, or adopt the groups". One more citation, same instruction
— strip the filing half, keep the carve, and decide for yourself where the slices
live. `/plan`'s **Requires** gains the conditional G3 edge `/finalize`'s already
carries.

Concretely, on "rebuild the settings area, it's three separate screens": the plan
file specs the first screen in full, describes the other two in a paragraph each,
and lists all three under the heading that proposes them. With G3, `/go` reads that
list on the go-ahead and files it — parent, three children, `sub_issues` links —
and the PR for screen one carries `Closes #<child>`. Without G3, that list is
where the three screens sit until the adopter moves them somewhere they chose.

### `/task` decides the gate after the plan is written

Making the plan file the gate would leave one route uncovered. `/task` outcome 3
— plan, then go — writes straight to `*.in-progress.md` under the conditional
go-ahead and enters `/go` at its Step 2, so there is no draft state and no gate; a
carve found there files a parent and children off a one-line prompt.

What closes it is a reordering rather than a recovery rule. `/task` asks both its
questions before the work exists, and the gate question is the one that cannot be
answered there: it judges what the operator would want to rule on from the single
line that asked for it. So it moves after the plan, and the skill becomes a
question, a plan, and a question:

1. **Does this task get a plan?** Either reason counts — writing it down would
   change what you build, or there is something here the operator may need to rule
   on. No → `/go` § "Planless entry", where the diff is the plan.
2. **Write it as a draft**, banner and all, like every other plan.
3. **Does the operator need to look?** No → enter `/go` at **Step 1**, which flips
   the draft in a commit quoting the `/task` prompt. Yes → end at `/plan`'s handoff
   block, and the next session flips it.

All three outcomes survive; two of them stop being decided in advance and become
the two ends of one route, forking where the plan exists to fork on. Step 1 is
deliberately over-inclusive — being wrong costs a file `/finalize` sweeps, so a
close call writes one — and step 3 is the call that costs a round trip.

A carve found while writing that plan then needs no procedure: the file is already
a draft carrying its banner, the session does not flip it, and it hands off. What
made outcome 3 special was the skipped state, so restoring the state retires the
special case rather than adding one.

The draft is also the better state to be interrupted in. A session that dies
between writing the file and flipping it leaves something a later `/handle` reads
as awaiting a go-ahead, so it asks for one it already had — one round trip. What
that replaces is an `*.in-progress.md` claiming a live session holds the plan right
now, which is the reading someone has to untangle by hand.

## Files

| File | Change |
| --- | --- |
| `CLAUDE.md` | § "Plan mode & questions in web sessions": replace the planning-session default with Part A's two rows plus the `#<N>` export-first line; keep the `/from-branch` / `/handle` continued-work bullet as the launch-vs-continued line. § "Working with skills": `/take-issue` moves from the entry points to the mechanical pieces, and `/issue` joins `/implement` as a redirect |
| `.claude/skills/take-issue/SKILL.md` | **renamed from `issue/`**; delete Steps 3 and 4 and § "Branch name"; what remains is the mode gate, the export and the commit; the argument shape admits prose around the number and says the export outranks it; a closing line that its callers are `/task`, `/plan` and `/go`, and that it returns to them |
| `.claude/skills/issue/SKILL.md` | **new** — deprecation stub: with a `#<N>`, forward to `/plan` and report that `/task` and `/go` take the same shape; with none, name `/propose-issue` and stop |
| `.claude/skills/pr/SKILL.md` | Step 4 reads `docs/issue/<n>/` instead of the slug, and writes `Closes #<tbd>` on a carve whose children are not filed yet; no line at all where no issue is involved; the `<issue>` parameter line follows |
| `.claude/skills/propose-issue/SKILL.md` | say that Steps 1–2 and Step 3 may run in different turns; Step 3 fills any `#<tbd>` on the branch and in the PR body |
| `.claude/skills/squash-message/SKILL.md` | never carry `#<tbd>` into the title or the `Closes` trailer — omit the reference until it resolves |
| `.claude/skills/plan/SKILL.md` | new section, absorbing `/issue` Step 3 whole: the carve bar, the plan-file shape including the proposed issues, the read-only dedupe, and the filing half — `/propose-issue` per slice, the `sub_issues` link and its two 422 traps, the ≥5-files granularity rule, an enumerated parent's verbatim reports; plus the `#<N>` pointer |
| `.claude/skills/go/SKILL.md` | file the issues the approved plan proposes, before the work; plus the `#<N>` pointer |
| `.claude/skills/task/SKILL.md` | the two questions become a question, a draft, and a question — the gate call moves after the plan file exists, and its "no" branch enters `/go` at Step 1 rather than writing `*.in-progress.md`; plus the `#<N>` pointer and one line that `/task` is where a launch-time directive lands |
| `.claude/skills/finalize/SKILL.md` | the **Requires** column's conditional G3 edge repoints to `/take-issue` |
| `.claude/skills/update-muthur/catalog.md` | `/take-issue` and `/plan` rows re-described, a row added for the `/issue` stub; `/plan` gains a conditional G3 edge and joins `/finalize` in § "Closure is not optional"'s conditional-reach bullet |

Every other `/issue` citation repoints with the rename.
`./scripts/check-skill-catalog.sh` is what proves none was missed: it fails on a
dangling `@`-reference and on a skill without exactly one catalog row — and both
the renamed skill and the stub need rows, which is what makes the stub's omission a
failure rather than an oversight.

**Not itself split-worthy**, by the bar this plan moves: eleven files, one seam,
one PR.

## Settled in review

On the thread at `.claude/skills/task/SKILL.md`:14:

- **`/propose-issue` runs on the parent only**, children created directly — and a
  dedupe hit stops and reports instead of adopting the match.
- **A G2-only adopter is owed no degradation path.** Working around a tracker they
  declined is theirs to solve, not this repo's.
- **`/task` writes the draft before it decides the gate.** Every planning route
  now produces a draft, and the "does the operator need to look?" call is made with
  the plan in hand rather than forecast from the prompt. No route reaches `/plan`
  without the gate, so the carve needs no recovery rule of its own.

On the review of this file:

- **`/plan` proposes the issues; `/go` files them.** Nothing reaches the tracker
  before the go-ahead, and the plan file is the gate that makes it so.
- **In doubt, read a prompt as asking for no change.** Answer it, keep whatever
  the answer produced in `tmp/`, and move it somewhere tracked only if asked.
- **The issue number leaves the branch slug**, and `/pr` Step 4 stops reading it
  there. The PR body carries it instead — the number where a `/take-issue` call knows
  it, `#<tbd>` where a carve has yet to file it, and no line at all on the PRs
  that close nothing, which is most of them. This rides this PR, the sites being
  ones it already edits.
- **Both parent and children go through `/propose-issue`**, which is what lets the
  `#<tbd>` fill-in have a single home — and gets the children deduped for free,
  at plan time where the operator rules on any match before approving.
- **`/issue` becomes `/take-issue`**, and stops being something an operator calls.
  The naming rule bars a name that doubles as a go-ahead token, which "take" is not;
  naming a skill after its argument is the stronger guarantee it offers rather than
  the convention the repo follows. Part B is what decides that it renames at all — a
  skill reduced to transport can no longer carry a name that does not say which of
  the two operations on an issue it performs.
- **An issue number is a detail of the prompt, not a destination.** `/task`, `/plan`
  and `/go` all take `<what to do> #<N>`, each exporting the thread first, so the
  entry ladder loses a row and `/take-issue` becomes a mechanical piece with three
  callers. The old `/issue` keeps working, as a stub that runs `/plan` on the same
  argument and names `/task` and `/go` as the other two readings of it — or names
  `/propose-issue`, where there is no number to take.
- **The carve is one procedure in `/plan`, not two files on a group line.** `/plan`
  states the filing as well, and the adopter who declined G3 strips that half and
  decides for themselves where the slices live — told so by the catalog's closure
  bullet, where `/finalize` already stands for the same reason.

Nothing is left open. The plan is waiting on a go-ahead, not on an answer.

## DRY notes

- **The carve criteria move, they are not copied.** `/issue` Step 3 is deleted
  outright, not summarized into a pointer — criteria and filing mechanics alike have
  one home after this, and it is `/plan`. The failure mode being avoided is the
  convention stated twice, which CLAUDE.md § "Writing things down" names as the
  finding rather than the fix.
- **One issue-creation site: `/propose-issue`.** Parent and children both go
  through it rather than the children through a local `gh api` loop, because the
  `#<tbd>` fill-in has to live wherever issues are born and two birthplaces means
  two copies of that rule — the convention stated twice that CLAUDE.md § "Writing
  things down" calls the finding. What `/plan` states beside the call is what is
  genuinely about the parent-child *relation* rather than about creating an issue:
  the `sub_issues` link and its two 422 traps, the granularity rule, and carrying
  an enumerated parent's verbatim reports into each child.
- **`/propose-issue` is split across turns, not forked into two variants.** `/plan`
  runs Steps 1–2 and `/go` runs Step 3, which the skill's own numbering already
  separates; neither turn needs a mode flag, and nothing is duplicated by the
  split.
- **CLAUDE.md stays the single home of routing.** `/task` points at the ladder
  rather than restating its rows, and gains the one line that says a launch-time
  directive lands there. `/take-issue` states no routing at all now — it is called,
  it does not dispatch.
- **The `#<N>` rule has one home and three pointers.** CLAUDE.md's ladder states
  that a number in the prompt means export first; `/task`, `/plan` and `/go` each
  carry a line pointing at `/take-issue` rather than a copy of what it does. Three
  callers is what a mechanical piece looks like, and the alternative — the receiving
  skill describing the export — is the convention stated three times.
- **The `/issue` stub restates nothing.** It looks for a `#<N>` and hands the whole
  argument on unchanged; the lines it prints are names and the case each covers, not
  argument shapes. Those stay with the skills that own them, and the stub goes stale
  only if one of those four skills disappears.
- **Polar-bear watch on the diff.** Deleting `/issue` Step 3 must not leave a
  sentence anywhere saying the split no longer happens there. `/tend-prose
  negation` runs over the result.

## Out of scope

- `/handle`'s missing note that a compaction boundary does not discharge the
  invocation, and `/pr`'s environment note about `gh pr edit` being unusable
  here. Both are separate one-liners.
- **How to read a PR export**, which nothing currently says. `/handle` Step 2 calls
  it "the whole thread" and `/finalize` calls it "the full thread", so the only
  stated guidance points at reading a file that passes a thousand lines by the third
  review round. The rule that works is diff-first — `git diff` the regenerated
  export against the committed one and read the threads that moved — and it belongs
  in `/handle` Step 2 beside the tail test, which is already the thing that decides
  what to read.
- Anything `/go` does with a carve beyond filing the proposed issues first. Past
  that the first slice is an ordinary plan.
