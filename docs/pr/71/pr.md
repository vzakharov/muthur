# PR #71: feat: the entry ladder routes on change-or-not, and the carve moves into /plan

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/71
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/task-skill-ukv536
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-12T14:26:37Z
- **Updated:** 2026-09-14T23:30:05Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

Two changes to where the loop's entry decisions get made — both about a call
made by whichever skill happened to be holding the work, rather than by the skill
in a position to make it.

- **The plan-or-not call has its own front door: `/task <what to do>`.** The
  invocation is a conditional go-ahead scoped to that one task, and the skill
  picks between three outcomes: plan and hand off, plan and then implement,
  implement with no plan. The name is a noun on purpose — skills trigger on
  description matching before their body loads, so a verb-named entry is readable
  as an instruction and collides with `/plan`'s approval gate.
- **The entry ladder reads whether the prompt asks for a change to this
  codebase.** The old default sent every opening prompt to `/plan`, questions
  included, so it was already being overridden by unstated judgment. Two rows
  now: asks for a change → `/task`; asks for no change → answer it. In doubt,
  read it as the second — being wrong there costs one turn, being wrong the other
  way commits a diff nobody asked for.
- **An issue number is a detail of the prompt, not a destination.** `/task`,
  `/plan` and `/go` all take `<what to do> #<N>` and export the thread first, so
  `/issue` loses its entry-point role and becomes `/take-issue`: pure transport,
  three callers, decides nothing. The old name survives as a redirect that runs
  `/plan` on the argument and names `/task` and `/go` as the same-shape
  alternatives — or names `/propose-issue`, where there is no number to take.
- **The carve moves into `/plan`, whole.** `/issue` Step 3 decided the split
  before anything had read the code. `/plan` now owns the bar, the plan-file
  shape that names the proposed parent and children, the read-only dedupe through
  `/propose-issue` Steps 1–2, and the filing procedure itself. It creates
  nothing: `/go` files the list on the go-ahead that flips the plan, so a plan
  turn that ends unapproved leaves the tracker as it found it. What this buys
  beyond tidiness is that **untracked work becomes splittable at all** — "add an
  admin page" typed bare previously had no path to a carve.
- **`/task` becomes a question, a draft, and a question.** The gate call cannot
  be answered before the thing it judges exists, so it moves after the plan file.
  Every planning route now produces a draft, which is what lets a carve found
  mid-plan need no recovery rule — and what leaves a dead session in a state a
  later `/handle` reads as awaiting a go-ahead rather than as claimed.
- **The issue number leaves the branch slug.** `/pr` Step 4 read it there, which
  forced the number to exist before `/plan` renamed the branch — filing at plan
  time, which the carve's new home no longer does. The PR body carries it
  instead: the caller's `<issue>` or `docs/issue/<n>/` on the branch, and
  `Closes #<tbd>` where a carve has yet to file its children.
  `/propose-issue` Step 3 fills the marker in, being the one place an issue is
  ever created; `/squash-message` never carries it into permanent history.
- **The catalog carries the group caveat.** `/plan` is G2 and the issue skills
  are G3, so a `/plan` that states the filing reaches across a group line. It
  states it anyway — the carve is one procedure, and cutting it at the line would
  leave the G2 half stopping where its reader needs the next sentence. `/plan`
  joins `/finalize` in § "Closure is not optional": strip the filing half, keep
  the carve, and decide for yourself where the slices live.

Eleven files in the second change, plus the citations that repoint with the
rename. `./scripts/check-skill-catalog.sh` passes all four assertions, which is
what proves none was missed — it fails on a dangling `@`-reference and on a skill
without exactly one catalog row, and both `/take-issue` and the `/issue` redirect
need rows.

## QA Checklist

- [ ] `route-change` — Open a fresh session with "add an admin page". It reaches `/task` and reports the plan-or-not call in its first sentence, with `plan` offered as the one-word override.
- [ ] `route-question` — Open a fresh session with "what do we need to add an admin page?". It answers in chat: no plan file, no branch work, anything it produced along the way left in `tmp/`.
- [ ] `number-anywhere` — Run each of `/task`, `/plan` and `/go` with a prompt ending in `#<N>`. Each exports the thread to `docs/issue/<n>/` and commits it before doing anything else, and none of them routes differently because of the number.
- [ ] `task-draft` — Run `/task` on work that needs a plan but not the operator's gate. It writes `docs/plans/<slug>.draft.do-not-implement.md` with the banner, then flips it through `/go` Step 1 in a commit quoting the `/task` prompt — the draft state exists in history rather than being skipped.
- [ ] `carve-proposes` — Run `/plan` on work obviously beyond one PR. The plan file names a parent and children with dedupe results beside them, and nothing is created on GitHub. Check the tracker afterwards.
- [ ] `carve-files` — Give that plan a go-ahead. `/go` files parent and children through `/propose-issue`, links each child via `sub_issues`, and replaces the PR body's `Closes #<tbd>` with the child's real number.
- [ ] `no-closes` — Open a PR for work with no issue behind it. The body ends with no `Closes` line at all, and nothing reads the branch slug for one.
- [ ] `stub-fork` — Run `/issue fix the sidebar #847`, then `/issue rework the settings area`. The first runs `/plan` and names `/task` and `/go`; the second names `/propose-issue` and stops without filing.
- [ ] `catalog` — Run `./scripts/check-skill-catalog.sh`. It reports OK.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `route-change` | manual-only | — | Whether an agent reads the ladder correctly is a judgment call, not an assertion |
| `route-question` | manual-only | — | The row the old default swallowed; only a real session shows it |
| `number-anywhere` | manual-only | — | Three skills, one rule; the export is observable on the branch |
| `task-draft` | manual-only | — | The reordering's point is a state in history, visible in `git log` |
| `carve-proposes` | manual-only | — | The assertion that matters is a negative one about GitHub |
| `carve-files` | manual-only | — | Writes to the tracker; needs a disposable parent to run against |
| `no-closes` | manual-only | — | Confirms the slug read is gone rather than merely unused |
| `stub-fork` | manual-only | — | Both branches of the redirect, including the one that must not file |
| `catalog` | unit | ✅ | `scripts/check-skill-catalog.sh`, which `scripts/vet.sh` runs |

---

## Comments

### Comment by @vzakharov (agent) on 2026-09-12T14:27:29Z

[https://github.com/vzakharov/muthur/pull/71#issuecomment-5646501641](https://github.com/vzakharov/muthur/pull/71#issuecomment-5646501641)

Proposed squash title/body:

```
feat: route the entry ladder on change-or-not, carve in /plan (pr #71)
```

```
Two of the loop's entry decisions were made by whichever skill happened
to be holding the work rather than by the one in a position to make it.
A new session's opening prompt routed to /plan by default — questions
included, which no agent has ever written a plan file for — and /issue
decided whether to split before anything had read the code.

The ladder now reads one thing: does the prompt ask for a change to
this codebase? It does, and the work goes to /task; it does not, and
the answer is the deliverable. In doubt the second row wins, being
wrong there costing a turn where being wrong the other way commits a
diff nobody asked for. /task is reordered around the same observation:
its gate question judges the plan, so it is asked once the plan exists.
The skill is a question, a draft, and a question, and every planning
route through it produces a draft — which leaves a session that died
mid-turn in a state a later /handle reads as awaiting a go-ahead rather
than as held by a session that is gone.

/plan owns the carve, whole: the bar, the plan-file shape that names
the parent and children it proposes, the read-only dedupe, and the
filing procedure itself. It creates nothing — the plan file is already
the gate, so /go files the list on the go-ahead that flips it, and a
plan turn that ends unapproved leaves the tracker as it found it. This
is what makes untracked work splittable at all: the criteria lived
inside a skill reached by already having an issue number.

An issue number is therefore a detail of the prompt, not a destination.
/task, /plan and /go all take <what to do> #<N> and export the thread
first, so the skill that reads one is reduced to transport and takes
the name that says which half it is, /take-issue; /issue stays as a
redirect. The number also leaves the branch slug, which had forced it
to exist before /plan renamed the branch — /pr writes Closes #<tbd>
where a carve has yet to file its children, and /propose-issue fills it
in when it creates them.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

### `docs/plans/issue-plan-call.draft.do-not-implement.md`:18 — resolved

```diff
@@ -0,0 +1,143 @@
+> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
+
+# Let `/issue` make the plan-or-not call
+
+## Why
+
+`/issue` hands every issue to `/plan`, unconditionally. The rationale currently
+on this branch says the issue's own existence answers the plan-or-not call —
+filing one costs something, so anything filed cleared the bar.
+
+That reads well and is wrong. Filing an issue is evidence the work is worth
+**tracking**, which is a different property from being worth **deliberating**.
+The two come apart constantly, and this repo's own backlog has the case:
+[#72](https://github.com/vzakharov/agent-project-boilerplate/issues/72) — "drop
+the working-artifact rows from the catalog's Never table" — is filed because it
+surfaced during a downstream review and would otherwise be lost, not because
+anyone needs a page about it before the two rows come out. Routing it through
+`/plan` buys a plan file, a draft PR, a handoff block and a second session, for
```

**@vzakharov (human)** — 2026-09-12T14:45:46Z

a draft PR is always the case though

**@vzakharov (agent)** — 2026-09-12T14:55:56Z

Right — both lanes end at `/pr` and both open a draft, so the PR was never part of the delta. Cost list is now the plan file, the handoff block and the second session, in 1edf8d3.

---

### `docs/plans/issue-plan-call.draft.do-not-implement.md`:46 — resolved

```diff
@@ -0,0 +1,143 @@
+> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
+
+# Let `/issue` make the plan-or-not call
+
+## Why
+
+`/issue` hands every issue to `/plan`, unconditionally. The rationale currently
+on this branch says the issue's own existence answers the plan-or-not call —
+filing one costs something, so anything filed cleared the bar.
+
+That reads well and is wrong. Filing an issue is evidence the work is worth
+**tracking**, which is a different property from being worth **deliberating**.
+The two come apart constantly, and this repo's own backlog has the case:
+[#72](https://github.com/vzakharov/agent-project-boilerplate/issues/72) — "drop
+the working-artifact rows from the catalog's Never table" — is filed because it
+surfaced during a downstream review and would otherwise be lost, not because
+anyone needs a page about it before the two rows come out. Routing it through
+`/plan` buys a plan file, a draft PR, a handoff block and a second session, for
+a change whose whole description is its title.
+
+So `/issue` should run the same two questions `/task` runs, once it has read the
+thread.
+
+## What this changes
+
+`/task` becomes the single home of the call, and both entry points reach it:
+`/task <what to do>` for untracked work, `/issue <n>` after its export and split
+steps. The questions are not restated in `/issue`.
+
+The obstacle is parameter threading. `/task`'s outcomes dispatch to `/plan` and
+`/go`, and issue work carries two things a bare task does not: `<issue>` (the
+number the eventual PR must close) and the export path
+(`docs/issue/<n>/issue.md`). Outcome 1 is already fine — `/plan` takes both from
+its caller today. **Outcome 2 is not**: `/go` § "Planless entry" enters with a
+task and nothing else, and its Step 4 loads `/pr` *with no args*, so `/pr`'s
+`<issue>` caller parameter never gets set and the PR opens without `Closes #N`.
+The issue then stays open after its own fix merges.
+
+### Step 1 — Give `/task` a caller-parameters section
+
+Add one to `.claude/skills/task/SKILL.md`, modelled on the one
+`@.claude/skills/pr/SKILL.md` already carries:
+
+- `<issue>` — the number the eventual PR must close. Passed through to whichever
+  outcome runs.
+- `<export>` — the issue export path, passed to `/plan` as context.
```

**@vzakharov (human)** — 2026-09-12T14:47:16Z

isn't it always the same though (deterministically derived from issue)?

**@vzakharov (agent)** — 2026-09-12T14:55:58Z

Yes — `docs/issue/<n>/issue.md` for the `<issue>` in hand, so anything holding the number holds the path. Dropped as a parameter in 1edf8d3; the DRY notes now say it is derived.

---

### `docs/plans/issue-plan-call.draft.do-not-implement.md`:57 — resolved

```diff
@@ -0,0 +1,143 @@
+> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
+
+# Let `/issue` make the plan-or-not call
+
+## Why
+
+`/issue` hands every issue to `/plan`, unconditionally. The rationale currently
+on this branch says the issue's own existence answers the plan-or-not call —
+filing one costs something, so anything filed cleared the bar.
+
+That reads well and is wrong. Filing an issue is evidence the work is worth
+**tracking**, which is a different property from being worth **deliberating**.
+The two come apart constantly, and this repo's own backlog has the case:
+[#72](https://github.com/vzakharov/agent-project-boilerplate/issues/72) — "drop
+the working-artifact rows from the catalog's Never table" — is filed because it
+surfaced during a downstream review and would otherwise be lost, not because
+anyone needs a page about it before the two rows come out. Routing it through
+`/plan` buys a plan file, a draft PR, a handoff block and a second session, for
+a change whose whole description is its title.
+
+So `/issue` should run the same two questions `/task` runs, once it has read the
+thread.
+
+## What this changes
+
+`/task` becomes the single home of the call, and both entry points reach it:
+`/task <what to do>` for untracked work, `/issue <n>` after its export and split
+steps. The questions are not restated in `/issue`.
+
+The obstacle is parameter threading. `/task`'s outcomes dispatch to `/plan` and
+`/go`, and issue work carries two things a bare task does not: `<issue>` (the
+number the eventual PR must close) and the export path
+(`docs/issue/<n>/issue.md`). Outcome 1 is already fine — `/plan` takes both from
+its caller today. **Outcome 2 is not**: `/go` § "Planless entry" enters with a
+task and nothing else, and its Step 4 loads `/pr` *with no args*, so `/pr`'s
+`<issue>` caller parameter never gets set and the PR opens without `Closes #N`.
+The issue then stays open after its own fix merges.
+
+### Step 1 — Give `/task` a caller-parameters section
+
+Add one to `.claude/skills/task/SKILL.md`, modelled on the one
+`@.claude/skills/pr/SKILL.md` already carries:
+
+- `<issue>` — the number the eventual PR must close. Passed through to whichever
+  outcome runs.
+- `<export>` — the issue export path, passed to `/plan` as context.
+- Absent both (the bare `/task <what to do>` case), the outcomes behave exactly
+  as they do now, so the ordinary path reads as if the section weren't there.
+
+Then state in each of the three outcomes what it forwards.
+
+### Step 2 — Thread `<issue>` through `/go`'s planless entry
+
+In `.claude/skills/go/SKILL.md`:
+
+- § "Planless entry" gains `<issue>` as an optional caller parameter alongside
+  the task text.
```

**@vzakharov (human)** — 2026-09-12T14:48:34Z

just to pass to /pr, right? I'd hate to have our skills repeat the prose about how issues are handled multiple times

**@vzakharov (agent)** — 2026-09-12T14:56:08Z

Just to pass to `/pr`, yes — and your objection killed the step. Threading it would have put issue-handling prose in `/task` and `/go`, neither of which has any business knowing what an issue is, to move a number `/pr` can already work out. What landed instead is one clause in `/pr` itself: let its existing inference read the issue-number-leading branch slug that `/issue` mandates. One skill knows about issues, which is the arrangement you asked for. 1edf8d3

---

### `.claude/skills/issue/SKILL.md`:134 — resolved

```diff
@@ -131,7 +131,7 @@ Load and follow `@.claude/skills/plan/SKILL.md`, passing what the issue asks in
 
 `/plan`'s deliverable is the plan file, published as a draft PR by its § "Publishing the plan", and the copyable `/go <branch>` block. **That is normally where this run ends.** Do not implement here: `/go` runs in a later session and hands the finished work back to `/pr` to refresh.
 
-The **only** waiver is the operator explicitly saying no plan is needed, which routes to `@.claude/skills/go/SKILL.md` § "Planless entry". It is not this skill's to grant on its own judgement.
+The **only** waiver is the operator explicitly saying no plan is needed, which routes to `@.claude/skills/go/SKILL.md` § "Planless entry". It is not this skill's to grant on its own judgement — the plan-or-not call `@.claude/skills/task/SKILL.md` makes for untracked work is already answered here by the issue existing. Filing one costs something, so work that was worth filing cleared the bar the call tests for.
```

**@vzakharov (human)** — 2026-09-12T14:50:43Z

wait (this is the first comment alphabetically, but I created it after the ones on the new plan), but if /issue already has a path to hand it over to /go's planless entry, (I usually wrote smth like "/issue ... no plan"), means the absence or absence of an issue param for the go skill never played a role, it worked fine through agents' own judgment/deliberation?

**@vzakharov (agent)** — 2026-09-12T14:56:09Z

You are right, and the plan was wrong. `/pr` § "Caller parameters" says the explicit `<issue>` beats inference *for a split issue* — a stray parent reference in a commit body closing the umbrella — and nothing else; absent it, Step 4 infers from what the PR and commits reference. I quoted that line in the plan without following it through, and wrote "the PR opens without `Closes #N`" instead. So the waiver path worked because there was no gap to notice.

The one hole left is that the inference reads commits but not the branch, which is where `/issue` guarantees the number lives. That is now a one-clause change in `/pr` and the plan is two steps shorter: 1edf8d3

---

### `.claude/skills/task/SKILL.md`:14 — resolved

```diff
@@ -11,7 +11,9 @@ The decision this skill makes, before any other: **does this task get a plan, an
 
 **The prompt is a conditional go-ahead.** It authorizes implementation *on condition that* the agent judges the operator's gate unnecessary, scoped to the task in that message and to that message alone.
 
-`/task <what to do>` is the invocation, and so is the prose it stands in for — `plan or go: <task>`, "plan this or just do it". It is the untracked-work sibling of `/issue`: same handover, a task in place of an issue number.
+`/task <what to do>` is the invocation, and so is the prose it stands in for — `plan or go: <task>`, "plan this or just do it". `/issue` is the other way in: it reads the thread first and then hands the work here, so the call is made once, in one place, whether or not the work is tracked. The mention stays bare rather than an `@`-reference — this skill ships to adopters who track no issues at all, and nothing here needs that file read.
```

**@vzakharov (human)** — 2026-09-12T15:26:20Z

> and so is the prose it stands in for — `plan or go: <task>`, "plan this or just do it"

these are polar bears -- no operator would normally write "plan or go" if this wasn't a lane of the /plan skill previously.

what I think though, is that any invocation that sounds like a directive rather than a question (e.g. "let's create ..." or even just simply "create ..." versus "what does our repo say about..."). This sounds pretty intuitive, right? Currently muthur provides no entry for requests that sound like "do this", and an adopting repo's agent would be at its own judgment as to what to do next (just work on the auto branch? invoke some skill?)

**@vzakharov (agent)** — 2026-09-12T15:34:59Z

Both prose forms cut in 87de4cd, frontmatter and body. You're right that
nobody reaches for "plan or go" unprompted — it was only ever the name of the
`/plan` page this moved out of, so listing it as an invocation advertised the
old home.

On the directive rule: agreed, and I think the gap is actually two.

The narrow one is that the ladder has no exit for a **question**. CLAUDE.md
says to treat a new session as a planning session, with exceptions only for
"no plan", `/from-branch`, `/handle`, and an issue title ending in `#N` — so a
session opened with "what does our repo say about the vet exit rule?" formally
routes to `/plan`. No agent actually writes a plan file for that, which is the
tell: it's already running on judgment the ladder doesn't state.

The wide one is your rule proper — directive → `/task` rather than → `/plan`.
That one changes the loop's default posture: today the operator opts into the
agent's call by typing `/task`, and under the rule the agent makes it on every
new session unless told otherwise. The gate doesn't disappear, since Question 1
routes genuinely gate-worthy work back to `/plan` — it moves from *always* to
*when the questions say so*. I think that's the right trade, and I think it's
too big to arrive as a review-round patch on this PR: it rewrites the routing
ladder and changes what every session opened in this repo does.

One trap for whoever writes it: `let's …` is on `/plan` § "The approval gate"'s
token list, so "let's create X" is a directive at launch and a go-ahead
mid-session. The rule has to key on which, and the ladder's last bullet already
draws that line ("only new sessions, not continued work").

Happy to file it as an issue or take it straight to `/plan` — say which.

**@vzakharov (human)** — 2026-09-14T09:57:03Z

here are my thoughts, not necessarily perfect:

1- the distinction should be not between directives vs questions -- I take that back. The distinction should be something that modifies codebase vs something that doesn't. Example: 'analyze the latest market trends' is a directive but does not automatically entail modifying the codebase (unless the codebase itself is doc/research-focused).

2- the precedence of calling skills should be more or less as following:

"add an admin page" = /task
"add an admin page #..." = /issue
"what do we need to add an admin page?" = none, muthur does not cover this by design (at least at this point)

3- now, there's a more interesting question, what if a task itself is splittable -- currently not something even envisioned? "add an admin page" in a repo where there's no admin functionality at all (as opposed to say pre-existing api endpoints that just have to be wired in UI) is a task that might require more than a single PR could provide, according to the criteria _now_ mentioned in the /issue skill.

So what I think is: the splitting decision *does not* belong in the issue skill, it should be part of `/plan` (because if something requires splitting it is obviously _not_ just `/go`).

So my suggestion is to make `/issue` a transport-only skill, like we once did for `/pr`: it downloads the issue, "plants" the requirement to "Closes #[its number]" down the line (just like it does now -- so no new wording in this regard), and then submits it to `/task`.

`/task` decides if it's worth planning -- just like it does now. If it is worth planning, it submits it to `/plan` -- note that the splitting does *not* happen at this stage -- it is the next skill's work.

So, when `/plan` receives a task that passes the splitting criteria, it makes the splitting part of the plan (just like it works now I think, but now it's phrased in the wrong skill):
1- Describes what's done on the very first digestible subtask
2- Describes how the other tasks are split out into issues.

NOW, a new part that must be here is: when we already have an issue that this was originally run from, we can call put the new subissues (including the first one -- which is *always* a subissue, not the parent issue) under it. When we start with just `add an admin page`, we now need to *create* the parent issue, and *then* create the issues under it. The parent issue will not be closed, so it's at this point just a grouping artifact.

Note that in this case it would be virtually identical (in end result) to creating an issue based on the task, and calling the (pre-this-change) "/issue #[its number]". But the internal mechanics is different.

Also note that when I say "create the issue", the agent will likely reach to `/propose-issue` by default. I'm not ready to say at this point whether it's a good thing (e.g. someone else has already thought of this task and created it as an issue -- good thing to know before we start) or a bad thing (conflation of concerns).

So, I'd want you to weigh in on all of that. Then, if you don't find hard stoppers, let's /plan it right away.

**@vzakharov (agent)** — 2026-09-14T10:06:47Z

No hard stoppers, so it's planned: https://github.com/vzakharov/muthur/pull/74

Where I agree outright:

**Codebase-modifying vs. not** is the better cut, and it survives your own
counter-example — "analyse the latest market trends" is an imperative and still
lands outside, because the test reads the repo rather than the sentence. One
condition: the third bucket has to be *written down* as a bucket. Left implicit,
today's default ("treat a new session as a planning session") swallows it and
questions route to `/plan` again, which is exactly where we are now.

**`/issue` as transport** removes a special case rather than relocating one. Step
4's "a split issue is the one case that skips the call and plans" exists only
because Step 3 carved before `/task` ever saw the work; with the carve in
`/plan`, Question 1 already covers it.

And the win your comment doesn't claim: **untracked work becomes splittable at
all.** The carve currently lives only behind an issue number, so "add an admin
page" typed bare has no path to one.

Four findings.

**1 — The ordering is forced, and it settles when the issues get filed.** `/pr`
Step 4 reads the closing issue off the branch slug, and `/plan` renames the
branch *before* writing the plan file. So filing cannot wait for `/go`: defer it
and the rename has no number to use and the PR loses its `Closes`. Inside the
plan turn: carve + approval → file parent and children → rename the branch to
lead with the first child → write the plan → publish. The gate protecting the
tracker is `/issue` Step 3's existing propose-and-stop, which rides along
unchanged, so nothing is written ahead of you either way.

**2 — Group closure.** `/plan` is G2; `/issue` and `/propose-issue` are G3. So
`/plan` can't absorb the filing wholesale — an adopter who declined G3 inherits a
step they can't run. The carve splits on that line: G2 keeps the decision and the
plan-file shape (first slice in full, remainder coarse), G3 keeps the filing —
parent, children, the native `sub_issues` link with its two 422 traps, the
≥5-files granularity rule, and carrying an enumerated parent's verbatim reports
and attachments. That half goes to `.claude/skills/issue/splitting.md`, cited
conditionally. Precedent: `/finalize`'s **Requires** already reads "conditionally
`/issue` (G3)".

**3 — `/task` outcome 3 is a hole.** "Plan, then go" writes straight to
`*.in-progress.md` under the conditional go-ahead and implements in the same
session. A carve discovered inside *that* plan would file issues and open a
multi-PR programme with no operator gate anywhere. `/plan` needs the recovery
stated: discovering a split while running outcome 3 sends the task back to the
gate. It's Question 1's "the scope is itself the question", answered late.

**4 — `/propose-issue`: the parent only.** Both your instincts are right and they
don't collide, because they're about different issues. The dedupe is worth
exactly one round — "add an admin page" may already be filed, and a second
umbrella is the expensive mistake. For the children it's a round-trip per slice
against a near-always-empty result, on issues just carved out of a parent nobody
else has seen. Parent through `/propose-issue`, children created directly. And
when the dedupe hits, the untracked path converges on the tracked one exactly as
you predicted.

One thing unchanged from before: `let's …` is still on `/plan` § "The approval
gate"'s token list, so the rule keys on launch-vs-continued rather than on the
words. The ladder's last bullet already draws that line.

The plan carries two open questions (the `/propose-issue` scope above, and what a
G2-only adopter gets), both written with the recommendation in force, so silence
resolves them. It lands after this PR — it edits the same two files again.

**@vzakharov (agent)** — 2026-09-14T13:06:05Z

Correction to my last reply: the plan rides **this** branch, not a new PR. #74 was a misread of "let's /plan it right away" and is closed; the plan is `docs/plans/split-in-plan.draft.do-not-implement.md` here, at 2e9ee4c. Everything above about the design stands — only the link changed.

One consequence worth naming: implementing it grows this PR into both changes rather than leaving #71 landable on its own.

**@vzakharov (human)** — 2026-09-14T13:22:24Z

> defer it and the rename has no number to use

not an issue (pardon the pun), I was meaning to remove the directive to include issue number from branch names for a while as I see no use in it anyway

> Group closure. /plan is G2; /issue and /propose-issue are G3

if an adopted accepted plan but not issue, they'll have to rework around that somehow -- i.e. by suggesting to keep the rest of work, undone in this pr (the one that would otherwise would be posted as an issue) in-repo. But ultimately it's not muthur's problem to solve.

> /task outcome 3 is a hole. "Plan, then go" writes straight to
*.in-progress.md under the conditional go-ahead and implements in the same
session.

can you explain again, maybe on an example? I do understand that the decision to "plan then go" could bear a risk, but it's there whether issues or opened or not. Then again, I consider close-to-none the probability of an agent deciding to "plan then go" for an issue they split into subissues.

> And
when the dedupe hits, the untracked path converges on the tracked one exactly as
you predicted.

so it's fine, is that what you're saying? I'd add that, in case a dedupe hits, the agent should stop and report because maybe that'll change the operator's judgment. (E.g. someone else is onto this task.)

**@vzakharov (agent)** — 2026-09-14T13:27:50Z

Three of four land; the first one has a hook in it worth seeing before you pull.

**1 — Dropping the number from branch slugs.** You're right that it dissolves the
ordering constraint: without the slug read there is nothing forcing the issues to
exist before the rename, so filing becomes a choice rather than a forcing. The
hook is that the slug read is *this PR's third bullet*. `/pr` Step 4 reads the
branch precisely because #71 removed the threaded `<issue>` parameter, and the
branch was the one place left that knew which issue the work closes — including
the split case, where the slug carries the chosen child and a commit body might
cite the parent. Pull the number and `Closes #N` falls through to "any issue the
PR or a commit references", which is the guess that bullet exists to stop.

So it's not a free deletion — it needs a replacement or an accepted loss. Cheapest
replacement, and it keeps the no-parameter-threading win: **`/pr` reads the number
off `docs/issue/<n>/` on the branch.** It's already committed at `/issue` Step 2,
it survives a rename, and the split case works if the carve exports the chosen
child alongside the parent — which it may as well, the child being what the
session actually reads. The alternatives are re-threading the parameter (undoes
this PR) or dropping `Closes` and closing by hand.

Three sites state the rule: `/issue` § "Branch name", `/pr`'s `<issue>` parameter
line, `/pr` Step 4. Small enough to ride this PR rather than be its own — but it
edits this PR's own diff, so I'd rather you said which way than have me fold it in
on a read of one sentence. Say the word and it goes in; say nothing and the plan
keeps the ordering as written, which stays correct either way (filing before the
rename is still *allowed*, just no longer forced).

**2 — Group closure.** Taken, and it closes the plan's open question 2. `/plan`
states the carve and names the slices; the filing half sits in
`.claude/skills/issue/splitting.md` and is cited conditionally; a G2-only adopter
gets the plan naming its slices and no procedure telling them what to do about it.
No degradation story written — you're right that it isn't muthur's to solve.

**3 — Outcome 3, with the example.** `/task add rate limiting to the API`. Q1: no
— the shape is standard, no fork, nothing irreversible. Q2: yes — several parts,
order matters. That's outcome 3: plan straight to `*.in-progress.md` and implement
in the same session, no gate anywhere. Now the carve lives in `/plan`, so while
writing that plan the agent finds it isn't one PR — middleware, a shared counter
store, per-tenant config, an admin surface. Under today's wording it files a
parent and four children and starts on the first. Nine words in, five issues out,
and unlike an oversized PR you can't decline it by not merging — someone has to go
close them.

But your probability estimate is right and it shrinks the fix to nothing: the
carve already stops for approval (finding 1's propose-and-stop, riding over from
`/issue` Step 3), and that gate holds inside outcome 3 as well as anywhere else.
The only thing needed is one clause saying `/task`'s conditional go-ahead does
*not* cover it — the go-ahead was scoped to the task as described, and a carve is
the discovery that the task wasn't that. Not a recovery procedure. Plan amended
down to that.

**4 — Dedupe hit.** Agreed, and better than "it converges": stop and report rather
than adopt the found issue silently. Somebody else being on it is exactly the
thing that changes your judgment, and it's invisible from the dedupe result alone.
In the plan now.

Plan updated at 51dce2c: both open questions closed, the outcome-3 section cut
down to the clause, the dedupe stop added, and the slug question moved to a
"Still open" section as the only thing left to decide.

**@vzakharov (human)** — 2026-09-14T13:36:57Z

> /pr Step 4 reads the
branch precisely because https://github.com/vzakharov/muthur/pull/71 removed the threaded <issue> parameter

I can't imagine a situation where the pr skill can *not* find out which issue we're talking about; /pr is called in the same session that writes the plan; this session knows what issue it's working on. In a situation where the issue itself would be created during implementation, the PR can start with a Closes #<tbd> to be filled out at whatever point the tbd becomes known.

Am I missing something, or is this actually a no-problem we keep revisiting just because we once started?

> /task add rate limiting to the API. Q1: no
— the shape is standard, no fork, nothing irreversible.

well judging by "you can't decline it by not merging — someone has to go
close them" it already makes it *kind of* irreversible (or at least not easily reversible).
Then again, I don't mind having a "if you took `plan and go` and during planning discovered splitting is needed, revert to `plan and wait for approval`"

**@vzakharov (agent)** — 2026-09-14T13:39:44Z

You're right, it's a no-problem — but the reason you gave isn't the one that
makes it one, and the difference matters for where the number gets read.

**"This session knows what issue it's working on" is the thing this loop declines
to rely on.** `/issue` Step 2 commits the export *before any planning* for exactly
that reason, in its own words: so an agent resuming the branch — after a context
wipe, a handoff, or in a parallel session — re-reads the thread instead of
re-deriving it. `/pr` in the common path is indeed called by the session that
planned; the inference ladder exists for `/handle`, `/from-branch`, and the turn
after a compaction boundary, where there is no such session.

**It's still a no-problem, because the slug was never the only durable carrier.**
`docs/issue/<n>/` is on the branch, committed at Step 2, same durability class,
and it survives a rename — which the slug does not. I reached for the slug because
#71 was already editing `/pr` Step 4 and the slug was the thing in front of me. So
yes: revisiting because we once started.

**And `Closes #<tbd>` covers the case the export directory doesn't** — a child
that doesn't exist when the PR opens. Cleaner than the placeholder even: `/pr`
omits the line, and whoever files the issue writes it in. The PR body is the
durable carrier, and nothing has to be known before the branch is named. That is
strictly better than today, because it drops the requirement that the number exist
before the rename — which was the whole constraint.

So the slug number goes and it unblocks Part B. `/pr` SKILL.md joins the plan's
files; `/issue` § "Branch name" loses the requirement. I checked whether anything
else reads the number off the slug — `/squash-message`'s title format takes it off
the PR body's `Closes`, so it rides along rather than being a fourth site.

**On outcome 3** — your framing is sharper than mine and it makes the rule smaller.
I'd filed it under Question 1's "the scope is itself the question"; you're pointing
at the irreversibility clause, and you're right that filing issues is exactly that:
outward-facing, and nobody declines it by not merging. So the recovery isn't a new
rule at all — it's Question 1 firing on information that arrived after it was
answered. Stated that way in the plan now, which costs a sentence instead of a
section.

Plan at 7b70952. It has no open questions left — it's waiting on a go-ahead, not
on an answer. One heads-up since you're mid-read: "Still open" is gone, folded
into "Settled in review", and the "Nothing is filed until the go-ahead" section
now carries the two `Closes` paths instead of the blocker.

**@vzakharov (agent)** — 2026-09-14T14:01:18Z

Caught. The export only exists where `/issue` exported a thread — which is exactly
the path where the number was never in doubt. Work that *creates* its issue has no
export, and that is Part B's whole population. I had the two paths in the plan but
ordered backwards, with the shortcut presented as the mechanism.

Flipped: **`#<tbd>` is the mechanism, the export read is the shortcut** — and,
per your follow-up, scoped rather than universal. Writing it "whenever `/pr`
cannot name the issue" would have stamped it on every PR that closes nothing,
which is most of them. It appears only where an issue is involved: an `/issue`
origin, where the number is known and gets written; or a carve, where the children
don't exist yet and `#<tbd>` holds the slot. Everything else carries no `Closes`
line, exactly as today. The marker means "an issue is coming and its number belongs
here" — never "I didn't look".

**Where the fill-in lives: `/propose-issue`, as you say, and it should be the only
place an issue is ever created.** That's what makes it a single home rather than a
rule copied into every creation site. Which answers your footnote:

**Yes — children through `/propose-issue` too, and it makes the design smaller.**
I argued the opposite two rounds ago on the grounds that deduping each child is a
round-trip against a near-always-empty result. That was wrong twice over. The
round-trip isn't paid at `/go` time at all: your `/plan`-proposes-`/go`-files split
already lets the skill break along its own numbering — `/plan` runs Steps 1–2
(search and triage, read-only) for every slice and writes the matches into the
plan; `/go` runs Step 3 on what was approved. So a match is something you rule on
while reviewing the carve, not an interruption after it. And "near-always-empty" is
doubtful anyway: granular issues outnumber umbrellas, so a *child* colliding with
something already filed is likelier than the parent doing so — and when it hits,
the right move is to link the existing issue as the sub-issue rather than duplicate
it. Better behaviour, not just cheaper.

The parent keeps the stop-and-report, since a match there bears on whether to carve
at all rather than on one slice.

`issue/splitting.md` then keeps only what's about the parent-child *relation* — the
`sub_issues` link and its two 422 traps, the granularity rule, carrying an
enumerated parent's verbatim reports into each child — and not creation.

**On `/squash-message` as the safety net:** it would notice, but I'd rather it not
be a second home for the rule. What it does need is the negative: never carry
`#<tbd>` into the title's `#<issue>` slot or the body's `Closes` trailer — omit the
reference until it resolves. That's in the files table.

Plan at 7f72ec9. The DRY note arguing against a shared creation site is gone, since
it argued from the dedupe cost that this removes.

---

### `.claude/skills/task/SKILL.md`:29 — resolved

```diff
@@ -24,6 +26,8 @@ Any one of these is a yes:
 
 None of these asks how important the change is. Importance is why the operator reviews the diff; the gate is for what reviewing a diff cannot undo.
 
+Nor does any of them ask how the task arrived. **A task that came in through `/issue` carries evidence that it is worth tracking, which is not evidence that it is large** — a two-row docs correction gets filed so it survives the review it surfaced in. Weigh the work described, not the formality of the thread describing it, or every issue plans and the call is decorative.
```

**@vzakharov (human)** — 2026-09-12T15:26:48Z

polar bear

**@vzakharov (agent)** — 2026-09-12T15:34:37Z

Agreed, cut in 87de4cd — along with the pointer at it in `/issue` Step 4.

It denied the *old* `/issue` behaviour (plan every issue) rather than
anything the current tree says: `/task` already declares that caller extras
ride through unread, so nothing in it invites reading an issue number as a
size signal. The trackable-vs-deliberating argument stays in the squash body,
where someone deciding whether this change is right will look for it.

---

### `docs/plans/split-in-plan.completed.md`:61 — resolved

```diff
@@ -0,0 +1,185 @@
+> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
+
+# Give the loop an entry rule for untracked work, and move the split decision into `/plan`
+
+Two changes to where the loop's entry decisions are made. They are separable in
+principle and cohesive in practice: both are about a call currently made by the
+skill that happens to be holding the work rather than by the skill that is in a
+position to make it, and they touch the same five files.
+
+**Builds on this branch's own change**, which makes `/issue` hand every issue to
+`/task`. The plan is written against the tree as `issue-plan-call.completed.md`
+leaves it, and implementing it grows this PR rather than opening another.
+
+## Part A — an entry rule for prose that names no skill
+
+CLAUDE.md § "Plan mode & questions in web sessions" currently says to treat a new
+session as a planning session, with exceptions for "no plan", `/from-branch`,
+`/handle`, and an issue title ending in `#N`. Every other opening prompt formally
+routes to `/plan` — including a question, which no agent has ever written a plan
+file for. The ladder is already being overridden by unstated judgment.
+
+Replace the default with a three-way read on **whether the request asks for a
+change to this codebase**:
+
+| Opening prompt | Routes to |
+| --- | --- |
+| asks for a change, untracked — "add an admin page" | `/task` |
+| asks for a change, carries an issue number — "add an admin page #55" | `/issue` |
+| asks for no change — "what do we need to add an admin page?" | nothing: answer it |
+
+Three things the wording has to get right:
+
+- **The test is the expected deliverable, not the grammar.** "Analyse the latest
+  market trends" is an imperative and still lands in row 3, because nothing in
+  this repo changes as a result. (In a repo whose product *is* documents or
+  research, the same sentence lands in row 1 — the test reads the repo, not the
+  sentence.)
+- **Row 3 is a stated bucket, not a gap.** Left unstated, the old default
+  swallows it and questions route to `/plan` again. It says: answer the question;
+  no skill covers this by design. Where the read was wrong, the operator's next
+  message is a directive and lands in row 1 — one turn, not a wasted plan file.
+- **`let's …` is a token collision.** It is on `/plan` § "The approval gate"'s
+  go-ahead list, so "let's add an admin page" is a directive at launch and an
+  approval mid-session. The rule keys on launch-vs-continued, which the ladder's
+  last bullet already separates.
+
+**What this costs, stated plainly in the ladder itself:** today the operator opts
+into the agent's plan-or-not call by typing `/task`; under this rule the agent
+makes that call on every new session that asks for a change. The gate does not
```

**@vzakharov (human)** — 2026-09-14T13:27:53Z

let's add an "if in doubt, err on the side of 'no-code-change'". When it's not 100% clear that something does or does not require a change, it's best to decide it isn't, provide the answer, possible generating some tmp files in the process, to then move them to tracked locations should the operator ask for it, rather than start mutating the repo and committing stuff around.

**@vzakharov (agent)** — 2026-09-14T13:33:31Z

In, as a fourth condition on the wording. The argument I wrote it on is that the
two wrong reads aren't symmetric: row 3 read as row 1 mutates and commits against
a request that wanted an answer, and undoing it is a revert you have to ask for;
row 1 read as row 3 costs one turn — the answer lands, you say "now do it", and
whatever the answer produced along the way is sitting in `tmp/` to be moved
somewhere tracked if it turns out to be wanted.

1de0fa3

---

### `docs/plans/split-in-plan.draft.do-not-implement.md`:69 — resolved

```diff
@@ -0,0 +1,185 @@
+> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
+
+# Give the loop an entry rule for untracked work, and move the split decision into `/plan`
+
+Two changes to where the loop's entry decisions are made. They are separable in
+principle and cohesive in practice: both are about a call currently made by the
+skill that happens to be holding the work rather than by the skill that is in a
+position to make it, and they touch the same five files.
+
+**Builds on this branch's own change**, which makes `/issue` hand every issue to
+`/task`. The plan is written against the tree as `issue-plan-call.completed.md`
+leaves it, and implementing it grows this PR rather than opening another.
+
+## Part A — an entry rule for prose that names no skill
+
+CLAUDE.md § "Plan mode & questions in web sessions" currently says to treat a new
+session as a planning session, with exceptions for "no plan", `/from-branch`,
+`/handle`, and an issue title ending in `#N`. Every other opening prompt formally
+routes to `/plan` — including a question, which no agent has ever written a plan
+file for. The ladder is already being overridden by unstated judgment.
+
+Replace the default with a three-way read on **whether the request asks for a
+change to this codebase**:
+
+| Opening prompt | Routes to |
+| --- | --- |
+| asks for a change, untracked — "add an admin page" | `/task` |
+| asks for a change, carries an issue number — "add an admin page #55" | `/issue` |
+| asks for no change — "what do we need to add an admin page?" | nothing: answer it |
+
+Three things the wording has to get right:
+
+- **The test is the expected deliverable, not the grammar.** "Analyse the latest
+  market trends" is an imperative and still lands in row 3, because nothing in
+  this repo changes as a result. (In a repo whose product *is* documents or
+  research, the same sentence lands in row 1 — the test reads the repo, not the
+  sentence.)
+- **Row 3 is a stated bucket, not a gap.** Left unstated, the old default
+  swallows it and questions route to `/plan` again. It says: answer the question;
+  no skill covers this by design. Where the read was wrong, the operator's next
+  message is a directive and lands in row 1 — one turn, not a wasted plan file.
+- **`let's …` is a token collision.** It is on `/plan` § "The approval gate"'s
+  go-ahead list, so "let's add an admin page" is a directive at launch and an
+  approval mid-session. The rule keys on launch-vs-continued, which the ladder's
+  last bullet already separates.
+
+**What this costs, stated plainly in the ladder itself:** today the operator opts
+into the agent's plan-or-not call by typing `/task`; under this rule the agent
+makes that call on every new session that asks for a change. The gate does not
+disappear — `/task` Question 1 routes gate-worthy work back to `/plan` — it moves
+from *always* to *when the questions say so*.
+
+## Part B — the split decision moves from `/issue` to `/plan`
+
+`/issue` Step 3 decides the carve before anything has read the code, and `/issue`
+Step 4 then carries the exception that a split "skips the call and plans". Both
+go away:
+
+- **`/issue` becomes transport**, the shape `/pr` already has: export, commit,
+  hand to `/task` with `<issue>` = the number the eventual PR must close. No
+  wording change to how `Closes #N` is planted.
+- **`/task` is untouched.** Work that needs a carve already satisfies Question 1
+  ("the scope is itself the question", "costs far more to produce than to
+  describe"), so it routes to `/plan` without a special case.
+- **`/plan` gains the carve.** When the task passes the bar, the plan specs the
+  first slice in full and describes the remainder coarsely, and the slices are
+  filed as issues.
+- **The parent.** Arriving from `/issue`, it exists already. Arriving from bare
+  prose, `/plan` creates it: it stays open as a grouping artifact and is never
```

**@vzakharov (human)** — 2026-09-14T13:29:11Z

nope -- arriving from bare prose, `/plan` *plans* to create it. If this is about that "go cannot go without an issue number" argument we discussed above,  you must've already edited this one.

**@vzakharov (agent)** — 2026-09-14T13:33:44Z

Not already edited — I'd gone the other way. Having lost the ordering argument I
kept filing at plan time anyway, on the grounds that the approval and the tracker
state land in the same turn. You're right that that's not a reason: the plan file
**is** the approval, so filing can wait for the thing that reads it. Changed.

`/plan` now carves, runs the dedupe read-only, and names the parent and children
it proposes in the plan; `/go` files them on the go-ahead. An unapproved `/plan`
turn leaves the tracker exactly as it found it, and the carve needs no
propose-and-stop of its own — the plan file already is one.

Two things fall out, one good and one you'll want to decide:

**It puts outcome 3's gap back.** With the plan file as the gate, every route is
covered except the one that skips the draft state: outcome 3 writes straight to
`*.in-progress.md`. So the recovery is stated again after all — a carve found
while running outcome 3 goes back to the gate as a draft. Cheap, and now it's the
only case rather than a clause about go-ahead scope.

**It makes the slug question a precondition, not a neighbour.** A number the slug
has to carry is a number that has to exist before `/plan` renames the branch —
which is filing at plan time. Renaming later isn't available: the plan filename
tracks the slug, and a rename after the PR exists closes the PR. So deferring the
filing needs the number out of the slug, and `Closes #N` needs somewhere else to
come from first. Part B doesn't land until that's answered; the plan says so now
instead of calling it independent.

1de0fa3

**@vzakharov (human)** — 2026-09-14T14:36:49Z

> outcome 3 writes straight to *.in-progress.md

why? why not let it write normally, and have the `/go`, which it calls right after, handle the rename as per usual? (I don't know the entire context, so maybe it's a poor idea.)

**@vzakharov (agent)** — 2026-09-14T14:48:24Z

Not a poor idea — it's better than what I wrote, and it deletes a rule instead of
adding one. Taken.

The reason outcome 3 skipped the draft was that the filename is a claim about
approval state, and outcome 3's work *is* approved, conditionally, so
`*.in-progress.md` looked like the only true name. What that misses is the thing
this whole section is about: during outcome 3 the approval status isn't actually
settled yet. The conditional go-ahead was scoped to the task as described, and a
carve is the discovery that the task wasn't that. So the draft state isn't
"awaiting the operator" here — it's "not yet established that this is cleared",
and the flip is where it gets established.

Which is exactly your version: write the draft, then enter `/go` at **Step 1**
rather than Step 2. Step 1 is already the `git mv`, and its commit already quotes
the go-ahead — here the `/task` prompt itself, which is a literal go-ahead like
any other. Cost is one `git mv`.

And then the recovery rule disappears. A carve found while writing that plan needs
no procedure at all: the file is already a draft carrying its banner, the session
doesn't flip it, it hands off. What made outcome 3 special was the skipped state,
so restoring the state retires the special case rather than patching around it.

One cost worth naming, and it points the safe way: a session interrupted between
writing the file and flipping it leaves a draft indistinguishable from one
awaiting you, so a later `/handle` asks for a go-ahead it technically already had.
One round trip, in the direction that doesn't file five issues.

7cd1194 — the section is now "Outcome 3 writes a draft too", and `/task`
SKILL.md joins the files table.

**@vzakharov (human)** — 2026-09-14T14:51:02Z

In that case we can even move `/task` "or go" decision to *after* the plan is written, so the fork becomes:

1- decide if plan is needed
2- write the plan
3- decide if approval is needed

or am I overengineering this?

> a session interrupted between
writing the file and flipping it

well that's arguably better than having a plan already marked as in progress by the time the session is interrupted

**@vzakharov (agent)** — 2026-09-14T15:07:00Z

Not overengineering — it's the same correction as the last one, one level up, and
I should have seen it there. The reason outcome 3 couldn't write `*.in-progress.md`
is that the filename claims an approval state before the thing that would settle it
exists. Question 1 has the identical defect: it asks what the operator would want to
rule on, from the one line that asked for it. That's a forecast, and the plan is the
thing that would settle it.

So yes to the three-step shape. Written into the plan as:

1. **Does this get a plan?** No → `/go` § "Planless entry".
2. **Write it as a draft**, banner and all.
3. **Does the operator need to look?** No → `/go` Step 1, which flips it quoting the
   `/task` prompt. Yes → the handoff block.

All three outcomes survive, but 1 and 3 stop being decided in advance — they're the
two ends of one route now, forking where there's something to fork on.

One thing that doesn't fold, and it's why step 1 keeps both sets of reasons rather
than just "would writing it down change what I build". A task can be tiny and still
need your eyes — "drop the staging database" teaches the agent nothing by being
written down, and is exactly what you'd want to see first. If step 1 asked only the
head-straightening question, that one routes to outcome 2 and does it. So step 1 is
"either reason counts", deliberately over-inclusive: getting it wrong costs a file
`/finalize` sweeps, and step 3 is the call that costs a round trip. Which is the
existing "a close Question 2 writes the file" rule, generalised to both.

> that's arguably better than having a plan already marked as in progress by the
> time the session is interrupted

Agreed, and that's now how the plan states it rather than as a cost. A draft is read
by the next `/handle` as awaiting a go-ahead — one round trip, asking for something
it already had. An `*.in-progress.md` says a live session is holding the plan right
now, which is the state someone has to untangle by hand.

7039c7e — the section is now "`/task` decides the gate after the plan is written".

---

### `docs/plans/split-in-plan.draft.do-not-implement.md`:77 — resolved

```diff
@@ -0,0 +1,185 @@
+> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
+
+# Give the loop an entry rule for untracked work, and move the split decision into `/plan`
+
+Two changes to where the loop's entry decisions are made. They are separable in
+principle and cohesive in practice: both are about a call currently made by the
+skill that happens to be holding the work rather than by the skill that is in a
+position to make it, and they touch the same five files.
+
+**Builds on this branch's own change**, which makes `/issue` hand every issue to
+`/task`. The plan is written against the tree as `issue-plan-call.completed.md`
+leaves it, and implementing it grows this PR rather than opening another.
+
+## Part A — an entry rule for prose that names no skill
+
+CLAUDE.md § "Plan mode & questions in web sessions" currently says to treat a new
+session as a planning session, with exceptions for "no plan", `/from-branch`,
+`/handle`, and an issue title ending in `#N`. Every other opening prompt formally
+routes to `/plan` — including a question, which no agent has ever written a plan
+file for. The ladder is already being overridden by unstated judgment.
+
+Replace the default with a three-way read on **whether the request asks for a
+change to this codebase**:
+
+| Opening prompt | Routes to |
+| --- | --- |
+| asks for a change, untracked — "add an admin page" | `/task` |
+| asks for a change, carries an issue number — "add an admin page #55" | `/issue` |
+| asks for no change — "what do we need to add an admin page?" | nothing: answer it |
+
+Three things the wording has to get right:
+
+- **The test is the expected deliverable, not the grammar.** "Analyse the latest
+  market trends" is an imperative and still lands in row 3, because nothing in
+  this repo changes as a result. (In a repo whose product *is* documents or
+  research, the same sentence lands in row 1 — the test reads the repo, not the
+  sentence.)
+- **Row 3 is a stated bucket, not a gap.** Left unstated, the old default
+  swallows it and questions route to `/plan` again. It says: answer the question;
+  no skill covers this by design. Where the read was wrong, the operator's next
+  message is a directive and lands in row 1 — one turn, not a wasted plan file.
+- **`let's …` is a token collision.** It is on `/plan` § "The approval gate"'s
+  go-ahead list, so "let's add an admin page" is a directive at launch and an
+  approval mid-session. The rule keys on launch-vs-continued, which the ladder's
+  last bullet already separates.
+
+**What this costs, stated plainly in the ladder itself:** today the operator opts
+into the agent's plan-or-not call by typing `/task`; under this rule the agent
+makes that call on every new session that asks for a change. The gate does not
+disappear — `/task` Question 1 routes gate-worthy work back to `/plan` — it moves
+from *always* to *when the questions say so*.
+
+## Part B — the split decision moves from `/issue` to `/plan`
+
+`/issue` Step 3 decides the carve before anything has read the code, and `/issue`
+Step 4 then carries the exception that a split "skips the call and plans". Both
+go away:
+
+- **`/issue` becomes transport**, the shape `/pr` already has: export, commit,
+  hand to `/task` with `<issue>` = the number the eventual PR must close. No
+  wording change to how `Closes #N` is planted.
+- **`/task` is untouched.** Work that needs a carve already satisfies Question 1
+  ("the scope is itself the question", "costs far more to produce than to
+  describe"), so it routes to `/plan` without a special case.
+- **`/plan` gains the carve.** When the task passes the bar, the plan specs the
+  first slice in full and describes the remainder coarsely, and the slices are
+  filed as issues.
+- **The parent.** Arriving from `/issue`, it exists already. Arriving from bare
+  prose, `/plan` creates it: it stays open as a grouping artifact and is never
+  what the PR closes. Either way the first slice is a child, never the parent —
+  the rule `/issue` states today, carried over unchanged.
+
+What this buys beyond tidiness: **untracked work becomes splittable at all.**
+Today the carve lives only inside a skill you reach by already having an issue
+number, so "add an admin page" typed bare has no path to one.
+
+### The ordering constraint that fixes when issues are filed
```

**@vzakharov (human)** — 2026-09-14T13:29:38Z

skipping as per discussion above

**@vzakharov (agent)** — 2026-09-14T13:33:52Z

Right to skip it — that section was already gone when you wrote this. It's now
"Nothing is filed until the go-ahead", rewritten again just now for the
plans-to-create point above, and the forced-ordering argument it used to carry
survives only as the reason the slug question blocks Part B.

1de0fa3

---

### `docs/pr/71/pr.md`:1 — resolved

**@vzakharov (human)** — 2026-09-14T14:39:01Z

this has gotten beyond unwieldy, let's cut to the current understanding (no narration), 300 lines max. Also seems to be worth adding for the plan to adapt the pr skill to never narrate (there's edit history + comment threads for that)

**@vzakharov (agent)** — 2026-09-14T14:48:25Z

Rewritten — the body is now 55 lines and says what the branch delivers, with the
history cut. Gone: what `/issue` "used to" do and the reasoning it used to rest
on, the earlier `/lets` name, what the `<issue>` parameter "did not read". Each of
those was a sentence about a decision rather than about the thing decided, and the
decision is in the threads.

The rule goes into the plan on `/pr` Step 4: **the Summary states what the branch
delivers, never how it came to deliver it.** It isn't a new rule — it's CLAUDE.md
§ "Key principles"'s present-tense-contract line, which already governs code
comments, applied to the one piece of prose `/pr` writes. Worth stating there
anyway, because `/pr`'s refresh mode invites exactly the failure: the body written
at plan time is a forecast, and reconciling a forecast reads as an
invitation to explain the delta rather than to replace it.

One thing I can't fix from here, in case it's what you were pointing at: this file
itself — `docs/pr/71/pr.md` — is 983 lines because it's a verbatim export of the
thread, regenerated by `scripts/export-github-item.py` rather than written. Cutting
it would mean the next agent resuming this branch reads a summary of the review
instead of the review. It's a working artifact under `docs/`, so `/finalize`
sweeps it and it never reaches the trunk; the diff bulk is temporary by
construction. If the noise in the PR's file list is the actual problem, the lever
is the export's location rather than its content, and that's a separate one-liner.

7cd1194

---

### `docs/plans/split-in-plan.completed.md`:1 — resolved

**@vzakharov (human)** — 2026-09-14T14:40:35Z

this looks good. Two last things:
1- is backward compatibility with a `/issue do this and that #<number>` session start prompt enabled by default, or does it need additional wording
2- should we rename `/issue` to `/read-issue` maybe, as a counterpart ot `/propose-issue`? (not insisting; besides the blast radius it means `1-` becomes a definitive "no" with a stub needed)

**@vzakharov (agent)** — 2026-09-14T14:48:26Z

**1 — It needs wording, and it's one line.**

Today `/issue`'s argument shape is `<number|url>`, a single token; the
prose-plus-number form is documented only as the *bare* launch prompt with no
slash command ("a prompt that reads like an issue title and ends in `#<N>`"). So a
literal `/issue do this and that #55` works only by an agent quietly discarding
the prose, which nothing tells it to do — and Part A's row 2 makes that form the
normal way in rather than an oddity, so it can't stay undocumented.

The line says: the number is the argument, any surrounding prose is your own
summary of it, and Step 1's export outranks that summary. That last clause is
already there as "do not start solving the task from the title alone" — the new
wording just extends it from the title to the prose you typed. `/issue` SKILL.md
is already in the files table, so this costs nothing extra.

**2 — I'd keep `/issue`, and the blast radius isn't the reason.**

A compat stub is cheap — `/implement` → `/go` is exactly that, and it's four
lines. The reason is the naming rule: CLAUDE.md § "Adding or renaming a skill"
says to name a skill after its argument *specifically* to keep it out of reach of
the instruction-token reading, and cites `/issue`, `/task` and `/pr` as the three
that do it. `/read-issue` is verb-led, so the rename would move `/issue` off the
rule and onto the exception. The symmetry is real, but it's symmetry with
`/propose-issue`, which is the one that doesn't follow the convention.

Second reason, smaller: after Part B, `/issue` doesn't only read. It exports,
commits, and hands to `/task` — reading is step one of three, so `/read-issue`
would name the least of what it does while `/issue` names what it takes.

If you want it anyway it's a separate PR, not this one: the citations run through
CLAUDE.md, `/task`, `/go`, `/plan`, `/finalize` and the catalog, and folding that
into a diff that already touches ten files makes both changes harder to read.
Noted in "Settled in review" as a no with the reasoning, so it's on the record
rather than forgotten.

7cd1194

**@vzakharov (human)** — 2026-09-14T14:55:16Z

> specifically to keep it out of reach of
the instruction-token reading, and cites /issue, /task and /pr as the three
that do it. /read-issue is verb-led, so the rename would move /issue off the
rule and onto the exception. The symmetry is real, but it's symmetry with
/propose-issue, which is the one that doesn't follow the convention.

yeah, exactly, we already have /propose-issue ignoring the condition. What's that rationale in that claude.md paragraph, again? I don't see how "read an issue" (or "fetch an issue", if that's a better verb) can do anything bad (we always read it, it's not like there's a case where we prefer NOT to read despite being called that).

I just feel like `/issue` in itself has always been ambiguous as to whether it means posting or reading, but the "judgmental coverage" of it made it kinda explicable. Now that it's pure transport, I'm not sure.

Renaming would also make it easier to write the stub for the old one (with a note to the operator that it's deprecated in favor of `/task`, `/plan` or `/go`)

**@vzakharov (agent)** — 2026-09-14T15:07:02Z

You're right and I misread the rule. It says:

> **Don't name a skill with a word the loop already uses as an instruction token.**
> […] a name that doubles as a go-ahead ("implement", "proceed", "ship it", "let's …")
> fires on prose that meant the token, not the skill. Where the skill takes an
> argument, naming it after the argument — `/issue`, `/task`, `/pr` — puts it out of
> reach of that reading **entirely**.

The prohibition is only over the go-ahead list. "read" isn't on it and can't get onto
it — there's no prose where "read the issue" means "go ahead". The second sentence
offers a *stronger* guarantee for skills that happen to take an argument, not the
convention: almost everything here is verb-led (`/propose-issue`, `/tend-prose`,
`/check-merge`, `/branch-rename`, `/squash-message`, `/watch-ci`). So `/propose-issue`
isn't ignoring the condition — it was never under it. I turned an escape hatch into a
rule and then called the rule's non-application an exception.

So: renamed, in this PR. Your framing is the deciding one — while `/issue` carried the
judgment, the noun covered it; once Part B makes it transport, the name has to say
which of the two operations on an issue it is, and `/propose-issue` / `/read-issue`
says it at a glance. "read" over "fetch": the skill's load-bearing rule is "do not start
solving the task from the title alone", which is about comprehension, not retrieval.

In scope rather than a separate PR, because Part B is precisely what makes the name
wrong. Splitting it means a second PR renaming the thing this one just redefined. Cost
is a directory rename, the stub, and the citation sweep —
`scripts/check-skill-catalog.sh` fails on any dangling `@`-reference, so nothing gets
missed silently. Twelve files now instead of ten.

**One question, on the stub.** You wrote "with a note to the operator that it's
deprecated in favor of `/task`, `/plan` or `/go`", and I read that two ways. What I've
written into the plan is the narrow one: `/issue` redirects to `/read-issue` and names
`/propose-issue` as the other reading, on the `/implement` model — because a bare
`/issue` is exactly the invocation that doesn't say which was meant. The wider reading
would be that `/issue` as an *entry point* is deprecated too, and the stub should point
at `/task` / `/plan` / `/go` instead. If that's what you meant it's a different stub and
a one-line fix; say which.

7039c7e

---

### `docs/plans/split-in-plan.draft.do-not-implement.md`:240 — resolved

```diff
@@ -216,6 +227,17 @@ On the review of this file:
 - **Both parent and children go through `/propose-issue`**, which is what lets the
   `#<tbd>` fill-in have a single home — and gets the children deduped for free,
   at plan time where the operator rules on any match before approving.
+- **A PR body states what the branch delivers, never how it came to.** The change
+  is visible in the diff and its history in the threads, so a body that recounts
+  what an earlier draft did spends the one surface a reader opens to catch up.
+  `/pr` Step 4 carries the rule; it is CLAUDE.md § "Key principles"'s
+  present-tense-contract line applied to the one piece of prose that skill writes.
+- **`/issue` keeps its name.** `/read-issue` would pair it with `/propose-issue`,
+  but CLAUDE.md § "Adding or renaming a skill" names a skill after its argument
+  precisely to keep it out of reach of the go-ahead tokens, and cites `/issue`,
+  `/task` and `/pr` as the pattern — so the rename would match the exception
+  rather than the rule, and would cost a `/implement`-style compat stub on top of
+  the citations.
```

**@vzakharov (human)** — 2026-09-14T14:56:16Z

polar bear unless we do decide to change it

**@vzakharov (agent)** — 2026-09-14T15:07:03Z

It was one — a bullet whose whole job was to deny a rename that wasn't happening, in a
section that otherwise records decisions. And we are changing it, so it's now the
decision rather than its denial:

> **`/issue` becomes `/read-issue`**, the old name kept as a compat stub. The naming
> rule bars a name that doubles as a go-ahead token, which "read" is not; naming a
> skill after its argument is the stronger guarantee it offers rather than the
> convention the repo follows. Part B is what decides it — a skill reduced to transport
> can no longer carry a name that does not say which of the two operations on an issue
> it performs.

The other bullet in that hunk — the `/pr` never-narrate rule — is gone entirely, per
the thread on the export.

7039c7e

---

### `docs/pr/71/pr.md`:1 — resolved

**@vzakharov (human)** — 2026-09-14T14:57:03Z

sorry I just now realized it was an automatic export, not something you've authored -- so my entire objection to its being unwiledy in the previous review was nonsensical, and pls revert any (ir)relevant changes you did following said objection.

**@vzakharov (agent)** — 2026-09-14T15:07:04Z

Reverted. The plan had grown two sites off that objection and both are gone in 7039c7e:
the `/pr` files-table row loses "the Summary states what the branch delivers and never
how it came to deliver it", and the "Settled in review" bullet that stated it as a rule
is deleted.

No harm done either way — the file reads as a review to a reader, so mistaking it for
authored prose is the export doing its job.

**One thing I didn't revert, so you can tell me to.** The PR body itself is still the
rewritten 55-line version. The text it replaced narrated its own drafting — what
`/issue` "used to" do, the earlier `/lets` name, what the `<issue>` parameter "did not
read" — and putting that back seemed like the one part of the reversion that costs
something rather than restoring a state you wanted. The general rule about `/pr` is out;
this body is just shorter. Say the word and I'll restore the previous text.

---

### `docs/plans/split-in-plan.draft.do-not-implement.md`:216 — resolved

```diff
@@ -157,49 +171,67 @@ what they do with a list they can't file. Precedent for the conditional edge is
 `/finalize`, whose **Requires** column already reads "**conditionally** `/issue`
 (G3)".
 
-### Outcome 3 writes a draft too
+### `/task` decides the gate after the plan is written
 
 Making the plan file the gate would leave one route uncovered. `/task` outcome 3
 — plan, then go — writes straight to `*.in-progress.md` under the conditional
 go-ahead and enters `/go` at its Step 2, so there is no draft state and no gate; a
 carve found there files a parent and children off a one-line prompt.
 
-The fix is smaller than a recovery rule: **outcome 3 writes a draft like every
-other plan and enters `/go` at Step 1.** That step is already the flip, and its
-commit already quotes the go-ahead — here the `/task` prompt itself. The draft
-costs one `git mv` and buys the invariant that no plan file claims approval before
-the thing that would reveal it lacks approval, the carve, has been written down.
+What closes it is a reordering rather than a recovery rule. `/task` asks both its
+questions before the work exists, and the gate question is the one that cannot be
+answered there: it judges what the operator would want to rule on from the single
+line that asked for it. So it moves after the plan, and the skill becomes a
+question, a plan, and a question:
+
+1. **Does this task get a plan?** Either reason counts — writing it down would
+   change what you build, or there is something here the operator may need to rule
+   on. No → `/go` § "Planless entry", where the diff is the plan.
+2. **Write it as a draft**, banner and all, like every other plan.
+3. **Does the operator need to look?** No → enter `/go` at **Step 1**, which flips
+   the draft in a commit quoting the `/task` prompt. Yes → end at `/plan`'s handoff
+   block, and the next session flips it.
+
+All three outcomes survive; two of them stop being decided in advance and become
+the two ends of one route, forking where the plan exists to fork on. Step 1 is
+deliberately over-inclusive — being wrong costs a file `/finalize` sweeps, so a
+close call writes one — and step 3 is the call that costs a round trip.
 
 A carve found while writing that plan then needs no procedure: the file is already
 a draft carrying its banner, the session does not flip it, and it hands off. What
 made outcome 3 special was the skipped state, so restoring the state retires the
 special case rather than adding one.
 
-What the draft state costs is one round trip in the safe direction: a session
-interrupted between writing the file and flipping it leaves a draft
-indistinguishable from one awaiting the operator, so a later `/handle` asks for a
-go-ahead it already had.
+The draft is also the better state to be interrupted in. A session that dies
+between writing the file and flipping it leaves something a later `/handle` reads
+as awaiting a go-ahead, so it asks for one it already had — one round trip. What
+that replaces is an `*.in-progress.md` claiming a live session holds the plan right
+now, which is the reading someone has to untangle by hand.
 
 ## Files
 
 | File | Change |
 | --- | --- |
 | `CLAUDE.md` | § "Plan mode & questions in web sessions": replace the planning-session default with Part A's three rows; keep the `/from-branch` / `/handle` continued-work bullet as the launch-vs-continued line |
-| `.claude/skills/issue/SKILL.md` | delete Step 3; renumber; Step 4 loses the split exception; § "Branch name" drops the issue-number requirement; the argument shape admits prose around the number and says the export outranks it |
-| `.claude/skills/pr/SKILL.md` | Step 4 reads `docs/issue/<n>/` instead of the slug, and writes `Closes #<tbd>` on a carve whose children are not filed yet; no line at all where no issue is involved; the `<issue>` parameter line follows; the Summary states what the branch delivers and never how it came to deliver it |
+| `.claude/skills/take-issue/SKILL.md` | **renamed from `issue/`**; delete Step 3; renumber; Step 4 loses the split exception; § "Branch name" drops the issue-number requirement; the argument shape admits prose around the number and says the export outranks it |
```

**@vzakharov (human)** — 2026-09-14T18:32:16Z

I don't think it should point at /take-issue, because /take-issue itself, unlike the former /issue, is transport-only. So we should forward the operator to /task, /go, or /plan, depending on their needs (like, literally say, this skill is deprecated, use this for this, that for that, yet another that for that)

**@vzakharov (agent)** — 2026-09-14T18:40:22Z

Taken, and it takes a row out of Part A with it. What I missed is that `/task [title]
#55` is the same shape as `/go [title] #55` and `/plan [title] #55` — so the number is
a detail of the prompt, not a destination. Row 2 was routing a launch prompt to a skill
the operator isn't meant to invoke, which is the contradiction you're pointing at.

So the ladder is two rows now — asks for a change → `/task`, with or without a `#55`;
asks for no change → answer it — plus one line: a `#<N>` means the thread is exported
and committed before anything else, by whichever of `/task`, `/plan` or `/go` received
the prompt. The rule's home is the ladder; the three carry a pointer, not a copy.

That cashes out through the rest of the skill. After Step 3 goes, what's left is export
and commit — so **Step 4 goes too**, along with § "Branch name", whose one contribution
this plan already removes. It stops dispatching entirely: it's called, it returns, and
it moves to the mechanical pieces in CLAUDE.md § "Working with skills" beside
`/branch-rename` and `/squash-message`.

And the stub is a map rather than a redirect, as you said — literally: `/task <what to
do> #<N>` to let the agent make the call, `/plan` or `/go` with the same shape to force
it either way, `/propose-issue` to file a new one. Which also disposes of the noun's old
ambiguity: the read-or-file question gets answered by naming both.

006d80d

---

### `docs/plans/split-in-plan.draft.do-not-implement.md`:218 — resolved

```diff
@@ -157,49 +171,67 @@ what they do with a list they can't file. Precedent for the conditional edge is
 `/finalize`, whose **Requires** column already reads "**conditionally** `/issue`
 (G3)".
 
-### Outcome 3 writes a draft too
+### `/task` decides the gate after the plan is written
 
 Making the plan file the gate would leave one route uncovered. `/task` outcome 3
 — plan, then go — writes straight to `*.in-progress.md` under the conditional
 go-ahead and enters `/go` at its Step 2, so there is no draft state and no gate; a
 carve found there files a parent and children off a one-line prompt.
 
-The fix is smaller than a recovery rule: **outcome 3 writes a draft like every
-other plan and enters `/go` at Step 1.** That step is already the flip, and its
-commit already quotes the go-ahead — here the `/task` prompt itself. The draft
-costs one `git mv` and buys the invariant that no plan file claims approval before
-the thing that would reveal it lacks approval, the carve, has been written down.
+What closes it is a reordering rather than a recovery rule. `/task` asks both its
+questions before the work exists, and the gate question is the one that cannot be
+answered there: it judges what the operator would want to rule on from the single
+line that asked for it. So it moves after the plan, and the skill becomes a
+question, a plan, and a question:
+
+1. **Does this task get a plan?** Either reason counts — writing it down would
+   change what you build, or there is something here the operator may need to rule
+   on. No → `/go` § "Planless entry", where the diff is the plan.
+2. **Write it as a draft**, banner and all, like every other plan.
+3. **Does the operator need to look?** No → enter `/go` at **Step 1**, which flips
+   the draft in a commit quoting the `/task` prompt. Yes → end at `/plan`'s handoff
+   block, and the next session flips it.
+
+All three outcomes survive; two of them stop being decided in advance and become
+the two ends of one route, forking where the plan exists to fork on. Step 1 is
+deliberately over-inclusive — being wrong costs a file `/finalize` sweeps, so a
+close call writes one — and step 3 is the call that costs a round trip.
 
 A carve found while writing that plan then needs no procedure: the file is already
 a draft carrying its banner, the session does not flip it, and it hands off. What
 made outcome 3 special was the skipped state, so restoring the state retires the
 special case rather than adding one.
 
-What the draft state costs is one round trip in the safe direction: a session
-interrupted between writing the file and flipping it leaves a draft
-indistinguishable from one awaiting the operator, so a later `/handle` asks for a
-go-ahead it already had.
+The draft is also the better state to be interrupted in. A session that dies
+between writing the file and flipping it leaves something a later `/handle` reads
+as awaiting a go-ahead, so it asks for one it already had — one round trip. What
+that replaces is an `*.in-progress.md` claiming a live session holds the plan right
+now, which is the reading someone has to untangle by hand.
 
 ## Files
 
 | File | Change |
 | --- | --- |
 | `CLAUDE.md` | § "Plan mode & questions in web sessions": replace the planning-session default with Part A's three rows; keep the `/from-branch` / `/handle` continued-work bullet as the launch-vs-continued line |
-| `.claude/skills/issue/SKILL.md` | delete Step 3; renumber; Step 4 loses the split exception; § "Branch name" drops the issue-number requirement; the argument shape admits prose around the number and says the export outranks it |
-| `.claude/skills/pr/SKILL.md` | Step 4 reads `docs/issue/<n>/` instead of the slug, and writes `Closes #<tbd>` on a carve whose children are not filed yet; no line at all where no issue is involved; the `<issue>` parameter line follows; the Summary states what the branch delivers and never how it came to deliver it |
+| `.claude/skills/take-issue/SKILL.md` | **renamed from `issue/`**; delete Step 3; renumber; Step 4 loses the split exception; § "Branch name" drops the issue-number requirement; the argument shape admits prose around the number and says the export outranks it |
+| `.claude/skills/issue/SKILL.md` | **new** — compat stub on the `/implement` model, pointing at `/take-issue` and naming `/propose-issue` as the other reading of the noun |
+| `.claude/skills/take-issue/splitting.md` | **new** — the G3 filing half, moved verbatim from Step 3 |
```

**@vzakharov (human)** — 2026-09-14T18:32:34Z

wait, why? didn't we move this to /plan?

**@vzakharov (agent)** — 2026-09-14T18:40:24Z

Half-moved, and you're right that the remainder is in the wrong place. The carve
*criteria* go to `/plan`; what this file holds is the G3 filing half — the
`/propose-issue` calls, the native `sub_issues` link and its two 422 traps, the ≥5-files
granularity rule, and carrying an enumerated parent's verbatim reports into each child.
That can't sit in `/plan`, which is G2: an adopter who tracks no issues would get a step
they can't run.

But it has no business under `take-issue/` either, and that's sharper now than when I
wrote it — after the change above, `/take-issue` is export-and-commit and nothing else,
so the file would live under a skill that never reads it. It's about creating a family
of issues, which is `/propose-issue`'s job.

Moved to `.claude/skills/propose-issue/splitting.md`. It's G3, it sits beside the skill
that does the creating, and pruning G3 takes it along instead of stranding it.

006d80d

---

### `docs/pr/71/pr.md`:1 — resolved

**@vzakharov (human)** — 2026-09-14T18:34:23Z

does the pr-export skill/script instruct the agent to only look at the diff after exporting? because if you routinely read it all at ones, at 1200+ lines, it's getting beyond manageable, I'm guessing

**@vzakharov (agent)** — 2026-09-14T18:40:25Z

No, nothing says that, and what little is stated points the wrong way: `/handle` Step 2
calls the export "the whole thread" and `/finalize` says a resuming agent "reads the
full thread from there". Neither anticipated the third review round.

What I actually do, which is why this hasn't bitten yet: regenerate the export, `git
diff` it against the committed copy, and read only the threads that moved — `grep` for
the headers to see which are `unresolved` with a `(human)` tail, then `sed` the line
ranges those sit in. I've never read this file end to end. But that's habit, not
procedure, and habit doesn't survive a context wipe, which is precisely the case the
committed export exists for.

So it's worth writing down, and `/handle` Step 2 is where — beside the tail test, which
is already the thing that decides what's worth reading. Added to the plan's "Out of
scope" as a named follow-up rather than folded in, since it has nothing to do with entry
routing and this diff is at twelve files.

006d80d

---

### `docs/plans/split-in-plan.draft.do-not-implement.md`:99 — resolved

```diff
@@ -63,27 +70,33 @@ from *always* to *when the questions say so*.
 Step 4 then carries the exception that a split "skips the call and plans". Both
 go away:
 
-- **`/issue` becomes transport**, the shape `/pr` already has: export, commit,
-  hand to `/task` with `<issue>` = the number the eventual PR must close. No
-  wording change to how `Closes #N` is planted. Row 2 sends it prose-plus-number,
-  which its argument shape says is `<number|url>`, so that shape gains the third
-  form: the number is the argument, surrounding prose is the operator's own
-  summary, and Step 1's export outranks it — the rule already there as "do not
-  start solving the task from the title alone".
+- **`/issue` becomes transport, and stops being an entry point.** What is left
+  after Step 3 goes is export and commit — so the handoff to `/task` goes too, along
+  with § "Branch name", whose one contribution this plan removes anyway. The skill
+  no longer decides anything, which is what takes it out of the operator's hands:
+  its callers are `/task`, `/plan` and `/go`, each running it first when the prompt
+  carries a `#<N>`, and the number they pass on as `<issue>` is what the eventual PR
+  must close. No wording change to how `Closes #N` is planted. Its argument shape
+  gains the third form the ladder sends it — the number is the argument, surrounding
+  prose is the operator's own summary, and the export outranks it, which is the rule
+  already there as "do not start solving the task from the title alone".
 - **And it takes the name that says which half it is: `/take-issue`.** The noun
   names the argument but not the operation, and this repo has two operations on
   that argument. Nothing in the naming rule objects: it bars names that double as
   go-ahead tokens, and "take" is not one — naming a skill after its argument is the
   stronger guarantee that rule offers, not the convention the repo follows, which
-  is why `/propose-issue` sits under it without being an exception. **The verb names
-  the invocation, not its first step.** A turn that starts here ends at a plan or at
-  a PR, so `/read-`, `/fetch-`, `/load-` and `/import-` all promise a read-only turn
-  the skill does not deliver — and `/track-` names what `/propose-issue` does. "Take"
-  is the verb the skill's own description already opens with, and it survives the
-  handoff: taking an issue on is what the whole chain does. The old name
-  stays as a compat stub the way `/implement` does, pointing at `/take-issue` and
-  naming `/propose-issue` as the other reading — a bare `/issue` being exactly the
-  invocation that does not say which was meant.
+  is why `/propose-issue` sits under it without being an exception. "Take" over
+  "read", "fetch", "load" or "import": those name the export step, and the skill's
+  contract to its callers is that the issue has been taken onto the branch —
+  exported, committed, and there for a later session to re-read. `/track-` is what
+  `/propose-issue` does.
+- **The old name becomes a stub that routes rather than redirects.** `/issue` cannot
+  forward to `/take-issue`, which is no longer something an operator calls; and the
+  bare noun never said which of the two operations was meant anyway. So the stub is a
+  three-line map: `/task <what to do> #<N>` to let the agent make the call, `/plan`
+  or `/go` with the same shape to force it either way, and `/propose-issue` to file
+  one. It is the `/implement` pattern with a fork in it, kept for the muscle memory
+  and for the handoff blocks already written.
```

**@vzakharov (human)** — 2026-09-14T21:21:39Z

let's make the stub invoke `/plan` (because that was what the previous `/issue` skill did), but also notify the operator that `/go` and `/task` with the same `<...> #<...>` format are options, too

**@vzakharov (agent)** — 2026-09-14T21:31:05Z

Done — with one correction to the parenthetical, which doesn't change the answer.

The old `/issue` handed to `/task`, not `/plan`: Step 4 is "Load and follow
`task/SKILL.md`", and only the split case went straight to `/plan`. So precedent
actually points at `/task`. I'm still taking `/plan`, on a different reason: a
deprecated name carries no signal about which of the four readings was meant, and
`/plan` is the one whose wrong guess costs a round trip rather than an unreviewed
diff.

So the stub forwards rather than prints a map: given a `#<N>` it runs `/plan` on the
same argument and says in one line that `/task` and `/go` take that shape too — the
first hands the plan-or-not call back to the agent, the second skips it. Given no
number there is nothing to take and the prose is an unfiled unit of work, which is
the `/propose-issue` reading; the stub names it and stops rather than running it,
filing being the one of the four that writes to the tracker.

b0f036d

**@vzakharov (agent)** — 2026-09-14T21:33:50Z

Withdrawn — you were right and I read the wrong tree. `git show origin/main:.claude/skills/issue/SKILL.md` has "## Step 4 — Hand over to `/plan`" and the chain line "`/issue` → `/plan` → draft PR"; the `/task` handoff is this PR's own earlier commit, shipped under `issue-plan-call.completed.md`. So I was quoting the branch back at you as precedent for what the branch does.

`/plan` is the default on precedent as well as on the fallback reason, then, and the plan now says so: it is where `/issue` sent work for as long as the name meant anything, and the deprecated name says nothing about which reading was meant, so the guess should be the one that costs a round trip rather than an unreviewed diff.

Nothing else moves — the stub's behaviour is what you asked for either way.

aff8005

---

### `docs/plans/split-in-plan.draft.do-not-implement.md`:184 — resolved

```diff
@@ -160,11 +173,16 @@ get a step they cannot run. Split the carve along that line:
 
 - **G2, stated in `/plan`:** whether to carve, where the seams are, and the plan
   file's shape — first slice in full, remainder coarse.
-- **G3, in `.claude/skills/take-issue/splitting.md`:** calling `/propose-issue` for
+- **G3, in `.claude/skills/propose-issue/splitting.md`:** calling `/propose-issue` for
   each slice, the native `sub_issues` link and its two 422 traps, the ≥5-files
   granularity rule, and carrying an enumerated parent's verbatim reports and
   attachments into each child.
 
+It sits beside `/propose-issue` rather than beside `/take-issue` because it is
+about creating a family of issues, which is that skill's job and no longer has
+anything to do with transport. It also means pruning G3 takes the file with the
+skill it belongs to, instead of stranding it under a skill that never reads it.
```

**@vzakharov (human)** — 2026-09-14T21:23:39Z

I still don't understand what it is, what we are splitting and why. Can you illustrate with some example maybe?

**@vzakharov (agent)** — 2026-09-14T21:31:06Z

Fair — the section said "split the carve along that line" in a plan whose whole
subject is splitting issues, so "split" read as the wrong noun. What is split is the
carve's **documentation**, not the work. Fixed in b0f036d, and an example added:

> "Rebuild the settings area, it's three separate screens." Both adopters get the
> same `/plan` turn, because judging the seams needs no tracker: the plan file specs
> the first screen in full, describes the other two in a paragraph each, and lists
> all three under the heading that proposes them.
>
> For an adopter who took G2 and no GitHub skills, that list **is** the tracking, and
> the turn ends there. For a G3 adopter `/go` reads the same list on the go-ahead and
> files it — parent, three children, `sub_issues` links — and the PR for screen one
> carries `Closes #<child>`.

So: one judgement, and a second half that only exists where there is somewhere to
file. G2 gets the half that is pure judgement (carve or not, where the seams are,
what shape the plan file takes); G3 gets the half that touches the tracker (the
`/propose-issue` calls, the two `sub_issues` 422 traps, the ≥5-files granularity
rule, carrying an enumerated parent's verbatim reports into each child). That is why
it is two files rather than one section in `/plan`: a G2-only adopter loading a
`/plan` that told them to file sub-issues would be reading a step they cannot run.

**@vzakharov (agent)** — 2026-09-14T21:56:30Z

Correcting this in c7ad688 — I misread your earlier "it's not muthur's problem to solve" as licence to omit the *degradation story* while still cutting the procedure along the group line. You meant the cut shouldn't happen at all.

So `splitting.md` is gone and `/plan` states the carve whole, filing included: `/propose-issue` per slice, the `sub_issues` link and its two 422 traps, the ≥5-files granularity rule, the enumerated parent's verbatim reports. Cutting it at G2/G3 left the G2 half stopping exactly where its reader needs the next sentence.

The caveat moves to the catalog, where it belongs: `/plan` joins `/finalize` in § "Closure is not optional"'s conditional-reach bullet, which already says "strip the two citations, or adopt the groups". A G2-only adopter strips the filing half and decides for themselves where the slices live — plan file, backlog doc, whatever tracker they do use — and this repo writes none of that for them.

Eleven files in the table now, not twelve.

---

### `.claude/skills/issue/SKILL.md`:19 — unresolved

```diff
@@ -1,142 +1,31 @@
 ---
-description: Take a GitHub issue — export and read the thread, split it when the scope demands, then hand the work over to `/task`, which decides whether it gets a plan. Invoke as `/issue <number|url>`; a prompt that reads like an issue title and ends in `#<N>`, with no slash command, is the same invocation.
+description: Compatibility redirect — the work `/issue` names is spread across four skills, so this one forwards. Invoke as `/issue <what to do> #<N>` and it runs `/plan`; with no number it names `/propose-issue` and stops. Kept because handoff blocks and muscle memory still say `/issue`.
 ---
 
-End state of this skill: the issue is exported and committed on the branch, any split is filed on GitHub as sub-issues, and the work has been handed to `@.claude/skills/task/SKILL.md` — which in an ordinary web session means either a plan file published as a draft PR with a copyable `/go <branch>` handoff, or the change itself under a PR when the call came back "no plan".
-
-The chain is `/issue` → `/task` → `/plan` → draft PR → (review loop via `/handle`) → `/go` → `/finalize`, with the `/plan` leg skipped on issues that don't need one. Everything past the handover is owned by the skill that runs it.
-
-## Step 0 — Mode gate: native plan mode is not supported
-
-If the session is in **native plan mode** — the launch banner or system prompt says so, `ExitPlanMode` is the offered exit, or an edit is refused for that reason — **stop before running anything below.** Tell the operator:
-
-- this flow is plan-**file**-based (`@.claude/skills/plan/SKILL.md`), and native plan mode cannot write the two artifacts it depends on: the export under `docs/issue/<n>/` and the plan under `docs/plans/`. Both must be committed and pushed, because the operator reviews from a different machine than the one you run on;
-- the plan-mode approval UI is unreliable in web sessions regardless (anthropics/claude-code#72704);
-- so switch to **accept-edits** or **auto** and send any reply — the run picks up from there; no re-invocation needed.
-
-Do not work around it, and do not fall back to a chat-only plan.
-
-## Step 1 — Export the issue locally (then read the export)
-
-**First command:** run the bundled exporter:
-
-```bash
-python3 scripts/export-github-item.py <issue-number|https://github.com/OWNER/REPO/issues/N> [--repo OWNER/REPO]
-```
-
-The script writes `docs/issue/<n>/issue.md` (body + comments + timeline) and downloads any image / file attachments referenced in the thread to `docs/issue/<n>/attachments/`.
-
-Consult the issue only through the export — never `gh issue view`, the GitHub MCP tools, or `WebFetch` in its place. `gh issue view` alone does **not** fetch attachments: GitHub's `private-user-images.githubusercontent.com` URLs require an authenticated request even when the issue is public, which is why the export script exists. `WebFetch` on a github.com issue page often fails outright in isolated environments. For a quick metadata check unrelated to the task at hand — labels, assignees, linked PRs — `gh issue view <n> --json title,body,labels,assignees,state,url` is still fine.
-
-**Then read** `docs/issue/<n>/issue.md` end to end, and **open the files under** `docs/issue/<n>/attachments/` when you need pixels (screenshots, mockups, design references).
-
-**Auth:** the script reads `$GH_TOKEN` (or `$GITHUB_TOKEN`) first, then falls back to `gh auth token`. One of those must be available. **Deps:** stdlib Python 3.9+ only — no `pip install` needed.
-
-**Repo:** if `--repo OWNER/REPO` is omitted and the argument isn't a full issue URL, the script reads `origin` from the current git checkout. Pass `--repo` explicitly when exporting an issue from a different repo than the one you're working in.
-
-If the export fails, **stop and report** — do not start solving the task from the title alone. Tell the user what failed and how to proceed. The script exits non-zero on every failure — auth, network, repo not found, or an attachment that wouldn't download — so check the status, not just the last line. A partial attachment failure still writes the Markdown and prints `Downloaded 2/3 attachment(s)` plus each URL it missed: the thread is there, but you'd be reading it with pixels missing.
-
-### Video attachments (screen recordings)
-
-Exported attachments may have no extension (the filename stem is the asset id), so `file docs/issue/<n>/attachments/<asset-id>` to spot videos (e.g. `ISO Media, Apple QuickTime movie`). You can read **images** but not play **videos**. Extract frames with `ffmpeg`, if it's available, and read the frames as images:
-
-```bash
-mkdir -p tmp/frames   # tmp/ is gitignored — never commit frames
-ffmpeg -y -i docs/issue/<n>/attachments/<asset-id> -vf fps=2 -q:v 3 tmp/frames/frame_%03d.jpg
-```
-
-- `fps=2` (two frames/sec) suits a short clip; lower to `fps=1` for long videos, raise to `fps=4` to catch a fast transient (a toast, a flashed error). Check length first with `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 <path>`.
-- Read first/middle/last frames, then bisect toward the moment of interest. Frame `N` ≈ `N / fps` seconds, so you can map a frame back to a timestamp and correlate it with logs.
-- Recovers visuals only (no audio) — usually enough for a UI/repro bug.
-
-## Step 2 — Commit the export
-
-```bash
-git add docs/issue/<n> && git commit -m "docs: #<n> export the issue"
-```
-
-Commit it **now**, before any planning. The export is the source of truth for what the issue says, so an agent resuming this branch — after a context wipe, a handoff, or in a parallel session — re-reads the thread instead of re-exporting it, and committing it up front means that holds even if the session dies mid-plan. Never commit it on the trunk or a promotion branch.
-
-`@.claude/skills/finalize/SKILL.md` deletes the whole `docs/issue/` tree in the last commit before `gh pr ready`, so this add and that delete cancel out in the squash. **You** must not delete it.
-
-## Step 3 — Split, if and only if the scope demands it
-
-The bar for splitting is high. Do **not** split because:
-
-- the issue mentions several files (most do)
-- you can imagine a "phase 1 / phase 2" framing (most things admit one)
-- decomposition feels tidy
-
-Default to taking the issue as-is. Only split when the size is obviously beyond a single PR and the seams between sub-tasks are real, not invented. **Genuinely large** means multiple unrelated subsystems, weeks of work, or distinct deliverables that ship independently — not "many files" or a tidy phase breakdown.
-
-**Only a split stops for an answer.** Deciding _not_ to split is not a gate and never becomes one: say so in a line and move on to Step 4. Do not ask whether the issue looks big enough, do not offer a split you don't think is warranted, and do not treat a large-feeling issue as a reason to check in. If the operator disagrees they say so in the plan discussion one step later, which costs them a sentence — whereas a question here costs a round-trip on every issue.
-
-For **truly** large work, only the **next** slice has to be manageable in this run (something you can plan and ship in one branch/PR). Sub-issues you park in the backlog may themselves stay large — they are placeholders and ordering hints, not mini-specs. You do **not** owe a full implementation DAG or per-child plans up front: spell out the **immediate** work in detail, and give a **coarse** view of what follows (smaller than the original umbrella, but not fully decomposed).
-
-### If the issue is split-worthy
-
-1. **Propose the split in your reply and stop for approval** — titles + one-line scope each, dependency order, and which child you take first. Create nothing yet.
-2. Once the operator approves — which may take a round or two of back-and-forth — create **one sub-issue per slice, the first one included** (see below), each linked natively to the parent.
-3. Comment on the parent listing the children and the ordering.
-4. `python3 scripts/export-github-item.py <first child>` and commit that export too. From here on, "the issue" means that child.
-
-The gate is there because filing sub-issues writes to the tracker on the operator's behalf and is awkward to undo — and because the carve is a judgement call they may want to make differently. It runs as prose in the chat rather than through a plan file: a split changes no files, so there is no diff to iterate over, and routing it through `/plan` would end the run at a `/go` handoff before any issue existed. Fold the enumeration-vs-cohesive question below into the same exchange when it's unclear.
-
-#### Every slice is a sub-issue, including the first
-
-Filing children 2..n and doing slice 1 "under the parent" leaves the PR nothing to close and makes the parent both umbrella and work item. So **every** slice gets its own sub-issue, the first included; the PR for the slice you take carries `Closes #<child>`, **never** the parent's number. The parent stays open as the umbrella and closes only once its children are done — the operator's call, not yours.
-
-#### Link each child natively — mandatory
-
-`Part of #<parent>` prose is a pointer for humans, not a relation GitHub can track. Keep that line in the child's body, and **also** attach it through the sub-issues API — the GitHub MCP `sub_issue_write` tool (`method: "add"`, `issue_number: <parent>`, `sub_issue_id: <child's database id>`), or plain `gh`:
-
-```bash
-REPO=<owner>/<repo>
-PARENT=<parent issue number>
-for n in <child issue numbers…>; do
-  cid=$(gh api "repos/$REPO/issues/$n" --jq '.id')
-  gh api "repos/$REPO/issues/$PARENT/sub_issues" -F sub_issue_id=$cid
-done
-```
-
-Two traps, either of which 422s: `sub_issue_id` is the child's numeric **database `id`**, not its issue number; and it must be sent with **`-F`**, not `-f`, which would send the integer as a string.
-
-Without the relation the parent has no machine-readable notion of its children, so "the parent closes when its children are done" is unverifiable and the umbrella silently rots. Skipping the native link breaks the split; it is not an omitted nicety.
-
-#### Carry the original reports into each sub-issue
-
-When the parent reads as an **enumeration of multiple distinct bugs/requests** — a QA roundup, a bullet list of unrelated defects, several separate "also this is broken" items — copy each original item's **verbatim text and its attachments** into the sub-issue that covers it, so the child carries the reporter's own words and screenshots, not just your paraphrase. (This is distinct from the other reason to split: a **single, cohesive problem statement** that's merely too vast for one PR — there, there's no per-item original text to distribute, so don't force it.)
-
-- Put the original text + attachments in the sub-issue **body** when you create it. If you already created the bodies without them, post them as a **comment** on each child instead.
-- **Reuse the parent's attachment URLs** so images/videos render: GitHub serves them at `https://github.com/user-attachments/assets/<asset-id>`, and the exporter rewrites those to local `docs/issue/<n>/attachments/<asset-id>.<ext>` — so the **filename stem is the asset id**. Reconstruct the original URL from it (or read the parent's raw body via the GitHub API, where the `user-attachments` links are intact) rather than re-uploading. Screenshots use `<img …>`, bare video URLs on their own line auto-embed.
-- Quote the reporter verbatim (blockquote), attributed, and keep related items grouped under the sub-issue they map to.
-- **When unsure** whether the parent qualifies as an enumeration (vs. one cohesive problem), **ask the operator** before deciding.
-
-#### Size the split so each sub-issue is worth its own PR
-
-**One sub-issue ships as one PR** — that mapping is fixed; don't bundle several sub-issues into one PR or carve one sub-issue across several. The lever you control is the **granularity of the split itself**: how finely you carve the parent into sub-issues. Carve it so each resulting sub-issue is **substantial enough to justify a PR** — roughly **≥5 files of real change**. A prospective sub-issue that would touch only **1–3 files is too fine a cut**: don't give it its own sub-issue/PR. Instead **group it with the other small, cohesive items into a single sub-issue** that, taken together, is PR-worthy (within that sub-issue, one commit per underlying item keeps the diff readable).
-
-A QA roundup of six small defects is usually **not** six sub-issues — it's one or two sub-issues that each bundle several related fixes, each shipping as one PR.
-
-- **Group by cohesion, not just to hit a count.** Bundle items that sit in the same area or move together (e.g. several modal/popup tweaks, a cluster of responsive-CSS fixes). When grouping, still carry each underlying item's verbatim report + attachments into the bundled sub-issue's body (per above), grouped item-by-item.
-- **Keep blocked/uncertain items as their own sub-issue** even when small. A fix that needs an environment or investigation this run can't cover — a value to pixel-match against a running deployment, a root cause needing in-browser repro, an event with no traceable source in the code, an item someone else marked _in progress_ — gets its **own deferred sub-issue with a note on what it's blocked on**, rather than being grouped into a batch you can finish. Grouping merges trivial _ready_ fixes; it never justifies shipping a guess.
-
-### If the issue is not split-worthy
-
-The usual case. Say so in a line, and go straight to Step 4 — there is nothing to approve.
-
-## Step 4 — Hand over to `/task`
-
-Load and follow `@.claude/skills/task/SKILL.md`, passing what the issue asks in **one line** plus the export path (`docs/issue/<n>/issue.md`), and `<issue>` = the number the eventual PR must close: the chosen child when you split, otherwise the issue itself, **never** the parent. The handover happens in this session, so the outcome it picks runs with the thread you just read still in context and the export on the branch. Don't paraphrase the issue back at yourself.
-
-That skill's two questions decide whether this issue gets a plan, and nothing about them is restated here.
-
-**A split issue is the one case that skips the call and plans.** Step 3 splits only when the work is obviously beyond a single PR, which is Question 1's first clause already satisfied, so a split hands straight to `@.claude/skills/plan/SKILL.md` rather than re-asking a judgement that is made.
-
-Where the call lands on a plan, its deliverable is the plan file, published as a draft PR by `/plan` § "Publishing the plan", and the copyable `/go <branch>` block — **and that is where the run ends**, with `/go` implementing in a later session. Where the call lands on implementing, the work happens in this session and ends at the PR `/go` opens over it.
-
-**Branch name:** `@.claude/skills/branch-rename/SKILL.md` owns the form, and the rename lands before `/plan` writes the plan file, whose name derives from the slug. This skill contributes one requirement: the slug leads with the issue number, e.g. `claude/847-fix-sidebar-scroll-<hash>`. `@.claude/skills/pr/SKILL.md` Step 4 reads that number back off the branch, so a slug without it costs the PR its `Closes #N`.
-
-**Reporting:** whichever skill ran the outcome reports its own results. Add only what this skill alone knows — which issue you took, whether you split it, and links to the children.
-
-**Split-only session:** if the operator says the run's deliverable is the sub-issues themselves, with no code to be written in it, stop after Step 3 and report — there is nothing to hand over.
+`/issue` is the name four skills stand behind. Reading an issue is
+`@.claude/skills/take-issue/SKILL.md`, which nothing but a skill calls; deciding
+what happens to one is spread across `/task`, `/plan`, `/go` and
+`/propose-issue`. So this name forwards on the one thing that distinguishes the
+cases rather than unconditionally: whether the argument carries an issue number.
+
+**With a `#<N>` in the argument:** load and follow
+`@.claude/skills/plan/SKILL.md`, passing the argument through unchanged —
+prose, number and all. Then say in one line that `/task` and `/go` take that
+same argument: `/task` hands the plan-or-not call back to the agent, and `/go`
+skips it.
+
+`/plan` is the default of the three because the name says nothing about which
+reading the operator meant, so the guess should be the one that costs a round
+trip rather than an unreviewed diff.
```

**@vzakharov (human)** — 2026-09-14T23:14:41Z

no, that's because that's what the pre-PR `/issue ... #<N>` used to invoke, so that's what the operator expects

---

### `.claude/skills/plan/SKILL.md`:70 — unresolved

```diff
@@ -39,21 +39,82 @@ Plan mode is reached two ways, neither of which asks the agent: the operator swi
 
 A `/plan` session's deliverable is the **plan file on a draft PR**, not code. The operator reviews it from another machine, often hours later, and begins implementation in a **different** session via `/go <branch>` (`@.claude/skills/go/SKILL.md` routes that through `/from-branch`, which attaches to the branch and finds the plan under `docs/plans/`) — the handoff works because the plan file rides the branch. So a plan turn ends in a handoff, not a continuation; same-session implementation is the rare exception.
 
+**A `#<N>` in the argument means the thread is read first:** load and follow `@.claude/skills/take-issue/SKILL.md` with the whole argument before planning anything, and plan against what it puts on the branch. CLAUDE.md § "Plan mode & questions in web sessions" is that rule's home.
+
 Do **exactly what you would do in plan mode** — same research, same rigor, same "don't touch code until approved" discipline. The _only_ difference is where the plan goes and how it's approved:
 
-- Instead of presenting the plan via `ExitPlanMode`, **write it to `docs/plans/<branch-slug>.draft.do-not-implement.md`** (one file per session; name it after the current branch's task slug, or the issue number when working an issue — e.g. `docs/plans/1234.draft.do-not-implement.md`). The slug comes off the branch, so a harness auto-branch is renamed **before** the plan file is written, per CLAUDE.md § "Git conventions" — rename afterwards and the file keeps a slug naming nothing. The `.draft.do-not-implement.md` suffix is load-bearing: it is the on-disk marker that this plan has **not** been approved, visible in every `ls`, tool-call path, and `git status` so you can't drift past the gate without noticing. This directory is **not** gitignored on purpose: it rides the branch so the operator can pull and review the plan from another machine. Follow the repo's usual plan-content expectations, including the `## DRY notes` section CLAUDE.md requires.
+- Instead of presenting the plan via `ExitPlanMode`, **write it to `docs/plans/<branch-slug>.draft.do-not-implement.md`** (one file per session, named after the current branch's task slug). The slug comes off the branch, so a harness auto-branch is renamed **before** the plan file is written, per CLAUDE.md § "Git conventions" — rename afterwards and the file keeps a slug naming nothing. The `.draft.do-not-implement.md` suffix is load-bearing: it is the on-disk marker that this plan has **not** been approved, visible in every `ls`, tool-call path, and `git status` so you can't drift past the gate without noticing. This directory is **not** gitignored on purpose: it rides the branch so the operator can pull and review the plan from another machine. Follow the repo's usual plan-content expectations, including the `## DRY notes` section CLAUDE.md requires.
 - **Make line 1 of the file a banner** that restates the gate:
   ```
   > ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
   ```
 - Then **commit it and publish it** (§ "Publishing the plan" below), **end the turn with the handoff block** (§ "Handing off") and stop — do not start implementing.
 - **The in-session path is the exception, not the default.** If a literal go-ahead token does arrive in _this_ session, "The approval gate" below governs it unchanged — and on approval you hand off to `@.claude/skills/go/SKILL.md`, whose Step 1 performs the flip that unlocks source edits (`git mv` the plan to `docs/plans/<branch-slug>.in-progress.md`, drop the draft banner, quote the go-ahead in the commit) as its first action, before any source edit. That flip is the on-record receipt that approval was given, so don't front-run it here; the mechanics live in `/go` to avoid two copies drifting apart. The gate is exactly as strict on this path as on any other; it just fires rarely.
 
+### Carving a task into issues
+
+Some work is too big for one PR, and the plan is where that gets decided — it is the first moment anyone has read the code. A carve produces two things: a plan file that specs one slice and describes the rest, and a list of issues the plan **proposes**. Nothing is filed here. `/go` files them on the go-ahead that flips the plan, so a plan turn that ends unapproved leaves the tracker exactly as it found it. The plan file is already the gate, which is what makes the carve's approval free rather than a second propose-and-stop layered inside the planning turn.
+
+**The bar is high.** Do **not** carve because:
+
+- the task touches several files (most do)
+- you can imagine a "phase 1 / phase 2" framing (most things admit one)
+- decomposition feels tidy
+
+Default to taking the task whole. Carve only when the size is obviously beyond a single PR and the seams are real, not invented. **Genuinely large** means multiple unrelated subsystems, weeks of work, or distinct deliverables that ship independently — not "many files" or a tidy phase breakdown.
+
+Deciding **not** to carve is not a gate and never becomes one: say so in a line and write the plan. Do not ask whether the task looks big enough, and do not offer a carve you don't think is warranted — the operator disagrees in the plan review, which costs them a sentence, whereas a question here costs a round trip on every task.
+
+**Only the next slice has to be manageable.** Spell out the immediate work in full and give a **coarse** view of what follows — smaller than the original umbrella, but not fully decomposed. Parked slices are placeholders and ordering hints, not mini-specs; you owe no implementation DAG and no per-child plans up front.
+
+#### What the plan file carries
```

**@vzakharov (human)** — 2026-09-14T23:17:24Z

This relates to split issues only, right? If yes, let's put this section into a colocated .md file so that a non-splitting plan doesn't have to add this to the session context

---

### `.claude/skills/plan/SKILL.md`:82 — unresolved

```diff
@@ -39,21 +39,82 @@ Plan mode is reached two ways, neither of which asks the agent: the operator swi
 
 A `/plan` session's deliverable is the **plan file on a draft PR**, not code. The operator reviews it from another machine, often hours later, and begins implementation in a **different** session via `/go <branch>` (`@.claude/skills/go/SKILL.md` routes that through `/from-branch`, which attaches to the branch and finds the plan under `docs/plans/`) — the handoff works because the plan file rides the branch. So a plan turn ends in a handoff, not a continuation; same-session implementation is the rare exception.
 
+**A `#<N>` in the argument means the thread is read first:** load and follow `@.claude/skills/take-issue/SKILL.md` with the whole argument before planning anything, and plan against what it puts on the branch. CLAUDE.md § "Plan mode & questions in web sessions" is that rule's home.
+
 Do **exactly what you would do in plan mode** — same research, same rigor, same "don't touch code until approved" discipline. The _only_ difference is where the plan goes and how it's approved:
 
-- Instead of presenting the plan via `ExitPlanMode`, **write it to `docs/plans/<branch-slug>.draft.do-not-implement.md`** (one file per session; name it after the current branch's task slug, or the issue number when working an issue — e.g. `docs/plans/1234.draft.do-not-implement.md`). The slug comes off the branch, so a harness auto-branch is renamed **before** the plan file is written, per CLAUDE.md § "Git conventions" — rename afterwards and the file keeps a slug naming nothing. The `.draft.do-not-implement.md` suffix is load-bearing: it is the on-disk marker that this plan has **not** been approved, visible in every `ls`, tool-call path, and `git status` so you can't drift past the gate without noticing. This directory is **not** gitignored on purpose: it rides the branch so the operator can pull and review the plan from another machine. Follow the repo's usual plan-content expectations, including the `## DRY notes` section CLAUDE.md requires.
+- Instead of presenting the plan via `ExitPlanMode`, **write it to `docs/plans/<branch-slug>.draft.do-not-implement.md`** (one file per session, named after the current branch's task slug). The slug comes off the branch, so a harness auto-branch is renamed **before** the plan file is written, per CLAUDE.md § "Git conventions" — rename afterwards and the file keeps a slug naming nothing. The `.draft.do-not-implement.md` suffix is load-bearing: it is the on-disk marker that this plan has **not** been approved, visible in every `ls`, tool-call path, and `git status` so you can't drift past the gate without noticing. This directory is **not** gitignored on purpose: it rides the branch so the operator can pull and review the plan from another machine. Follow the repo's usual plan-content expectations, including the `## DRY notes` section CLAUDE.md requires.
 - **Make line 1 of the file a banner** that restates the gate:
   ```
   > ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
   ```
 - Then **commit it and publish it** (§ "Publishing the plan" below), **end the turn with the handoff block** (§ "Handing off") and stop — do not start implementing.
 - **The in-session path is the exception, not the default.** If a literal go-ahead token does arrive in _this_ session, "The approval gate" below governs it unchanged — and on approval you hand off to `@.claude/skills/go/SKILL.md`, whose Step 1 performs the flip that unlocks source edits (`git mv` the plan to `docs/plans/<branch-slug>.in-progress.md`, drop the draft banner, quote the go-ahead in the commit) as its first action, before any source edit. That flip is the on-record receipt that approval was given, so don't front-run it here; the mechanics live in `/go` to avoid two copies drifting apart. The gate is exactly as strict on this path as on any other; it just fires rarely.
 
+### Carving a task into issues
+
+Some work is too big for one PR, and the plan is where that gets decided — it is the first moment anyone has read the code. A carve produces two things: a plan file that specs one slice and describes the rest, and a list of issues the plan **proposes**. Nothing is filed here. `/go` files them on the go-ahead that flips the plan, so a plan turn that ends unapproved leaves the tracker exactly as it found it. The plan file is already the gate, which is what makes the carve's approval free rather than a second propose-and-stop layered inside the planning turn.
+
+**The bar is high.** Do **not** carve because:
+
+- the task touches several files (most do)
+- you can imagine a "phase 1 / phase 2" framing (most things admit one)
+- decomposition feels tidy
+
+Default to taking the task whole. Carve only when the size is obviously beyond a single PR and the seams are real, not invented. **Genuinely large** means multiple unrelated subsystems, weeks of work, or distinct deliverables that ship independently — not "many files" or a tidy phase breakdown.
+
+Deciding **not** to carve is not a gate and never becomes one: say so in a line and write the plan. Do not ask whether the task looks big enough, and do not offer a carve you don't think is warranted — the operator disagrees in the plan review, which costs them a sentence, whereas a question here costs a round trip on every task.
+
+**Only the next slice has to be manageable.** Spell out the immediate work in full and give a **coarse** view of what follows — smaller than the original umbrella, but not fully decomposed. Parked slices are placeholders and ordering hints, not mini-specs; you owe no implementation DAG and no per-child plans up front.
+
+#### What the plan file carries
+
+Under a heading of its own, the plan names every issue it proposes — the parent and each child — with a title and a one-line scope each, in dependency order, saying which child this plan specs. That list is the proposal the operator approves by approving the plan.
+
+**Dedupe each proposed issue read-only, and write the matches into the list.** Run `@.claude/skills/propose-issue/SKILL.md` Steps 1–2 — search and triage, which touch nothing — for every slice, and record what they found beside the slice it matched. So a duplicate is something the operator rules on while reviewing the carve, not an interruption after it, and a slice already tracked gets linked as the sub-issue instead of filed twice.
+
+**A match on the parent stops and reports.** Somebody else already tracking the whole umbrella is what changes the operator's judgment about whether to carve at all, which is a different question from whether one child is a duplicate.
+
+**The parent.** Arriving from `/take-issue` it exists already. Arriving from bare prose the plan proposes one and `/go` creates it. It stays open as a grouping artifact and is never what the PR closes — **every slice is a child, the first included.** Filing children 2..n and doing slice 1 "under the parent" leaves the PR nothing to close and makes the parent both umbrella and work item. The parent closes once its children are done, which is the operator's call.
+
+Because the children do not exist yet, the PR for this slice carries **`Closes #<tbd>`** — `@.claude/skills/pr/SKILL.md` Step 4 owns that marker and `/propose-issue` Step 3 fills it in.
+
+#### What `/go` does with the list
```

**@vzakharov (human)** — 2026-09-14T23:17:36Z

why is this here, not in the go skill?

---

### `.claude/skills/pr/SKILL.md`:84 — unresolved

```diff
@@ -76,7 +76,12 @@ git diff --stat origin/<base>..HEAD
 - **Summary** — 2-4 bullets explaining _what_ changed and _why_. Pull from commit bodies, not just subjects.
 - **QA Checklist** — a `## QA Checklist` markdown checklist of how to verify the change end-to-end. For how to derive it, follow the "Derive the checklist" guidance in `@.claude/skills/qa-checklist/SKILL.md`, over whichever input this mode composes from.
 
-End the body with `Closes #N` (for `feat`/`refactor`/etc.) or `Fixes #N` (for `fix`). `N` is the caller's `<issue>` when one was passed. Absent that, read it off the **branch slug** where the slug leads with an issue number (`claude/847-fix-sidebar-scroll-<hash>` — the form `/issue` § "Branch name" mandates for every branch it opens), and only then fall back to any issue the PR or a commit references. The branch comes first because that number was put there by the skill that knew which issue the work closes, whereas a commit that happens to mention one may be citing it rather than closing it.
+**A `Closes` line appears only where the work is tracked, or is about to be.** Most PRs close no issue and carry no line. Two origins put one there:
+
+- **The caller passed `<issue>`**, or `docs/issue/<n>/` exists on the branch — a `/take-issue` call, where the number was never in doubt. End the body with `Closes #N` (for `feat`/`refactor`/etc.) or `Fixes #N` (for `fix`). The caller's parameter wins; the export directory is what a resumed session reads it off instead, after a handoff or a compaction boundary. Falling back to an issue a commit merely references is the last rung and the weakest: a commit that mentions a number may be citing it rather than closing it.
+- **A carve whose children are not filed yet** — `@.claude/skills/plan/SKILL.md` § "Carving a task into issues" proposes the issues and `/go` files them, so at plan-open time the number does not exist. Write **`Closes #<tbd>`**. The marker means "an issue is coming and its number belongs here", which is a durable state on the branch rather than something lost with the turn; `@.claude/skills/propose-issue/SKILL.md` Step 3 fills it in when it creates the child. It is never a stand-in for not having looked.
+
+Both rungs read the branch rather than the session's own memory, which is what lets a session resumed after a handoff or a compaction boundary get the number right.
```

**@vzakharov (human)** — 2026-09-14T23:18:24Z

If session memory *is* available, though, it's the first and easiest thing to read

---

### `.claude/skills/take-issue/SKILL.md`:68 — unresolved

```diff
@@ -0,0 +1,70 @@
+---
+description: Take a GitHub issue onto the branch — export the thread and its attachments, commit them, and hand the number back to whoever called. Invoke as `/take-issue <number|url>`; its callers are `/task`, `/plan` and `/go`, each running it first when the prompt carries a `#<N>`.
+---
+
+End state of this skill: `docs/issue/<n>/` holds the thread and its attachments, that export is committed on the branch, you have read it, and control is back with the caller — which is where every decision about the work is made.
+
+This skill decides nothing. It is the one place an issue gets pulled onto a branch, so its contract to its callers is that the issue has been **taken**: exported, committed, and there for a later session to re-read.
+
+## Argument shape
+
+The argument is an issue number or a full issue URL, optionally with prose around it — `fix the sidebar scroll #847` is the same invocation as `847`. The prose is the operator's own summary of the issue and is worth reading as a hint at what they care about, but **the export outranks it**: where the two disagree, the thread is what the work is against.
+
+## Step 0 — Mode gate: native plan mode is not supported
+
+If the session is in **native plan mode** — the launch banner or system prompt says so, `ExitPlanMode` is the offered exit, or an edit is refused for that reason — **stop before running anything below.** Tell the operator:
+
+- this flow is plan-**file**-based (`@.claude/skills/plan/SKILL.md`), and native plan mode cannot write the two artifacts it depends on: the export under `docs/issue/<n>/` and the plan under `docs/plans/`. Both must be committed and pushed, because the operator reviews from a different machine than the one you run on;
+- the plan-mode approval UI is unreliable in web sessions regardless (anthropics/claude-code#72704);
+- so switch to **accept-edits** or **auto** and send any reply — the run picks up from there; no re-invocation needed.
+
+Do not work around it, and do not fall back to a chat-only plan.
+
+## Step 1 — Export the issue locally (then read the export)
+
+**First command:** run the bundled exporter:
+
+```bash
+python3 scripts/export-github-item.py <issue-number|https://github.com/OWNER/REPO/issues/N> [--repo OWNER/REPO]
+```
+
+The script writes `docs/issue/<n>/issue.md` (body + comments + timeline) and downloads any image / file attachments referenced in the thread to `docs/issue/<n>/attachments/`.
+
+Consult the issue only through the export — never `gh issue view`, the GitHub MCP tools, or `WebFetch` in its place. `gh issue view` alone does **not** fetch attachments: GitHub's `private-user-images.githubusercontent.com` URLs require an authenticated request even when the issue is public, which is why the export script exists. `WebFetch` on a github.com issue page often fails outright in isolated environments. For a quick metadata check unrelated to the task at hand — labels, assignees, linked PRs — `gh issue view <n> --json title,body,labels,assignees,state,url` is still fine.
+
+**Then read** `docs/issue/<n>/issue.md` end to end, and **open the files under** `docs/issue/<n>/attachments/` when you need pixels (screenshots, mockups, design references).
+
+**Auth:** the script reads `$GH_TOKEN` (or `$GITHUB_TOKEN`) first, then falls back to `gh auth token`. One of those must be available. **Deps:** stdlib Python 3.9+ only — no `pip install` needed.
+
+**Repo:** if `--repo OWNER/REPO` is omitted and the argument isn't a full issue URL, the script reads `origin` from the current git checkout. Pass `--repo` explicitly when exporting an issue from a different repo than the one you're working in.
+
+If the export fails, **stop and report** — do not start solving the task from the title alone. Tell the user what failed and how to proceed. The script exits non-zero on every failure — auth, network, repo not found, or an attachment that wouldn't download — so check the status, not just the last line. A partial attachment failure still writes the Markdown and prints `Downloaded 2/3 attachment(s)` plus each URL it missed: the thread is there, but you'd be reading it with pixels missing.
+
+### Video attachments (screen recordings)
+
+Exported attachments may have no extension (the filename stem is the asset id), so `file docs/issue/<n>/attachments/<asset-id>` to spot videos (e.g. `ISO Media, Apple QuickTime movie`). You can read **images** but not play **videos**. Extract frames with `ffmpeg`, if it's available, and read the frames as images:
+
+```bash
+mkdir -p tmp/frames   # tmp/ is gitignored — never commit frames
+ffmpeg -y -i docs/issue/<n>/attachments/<asset-id> -vf fps=2 -q:v 3 tmp/frames/frame_%03d.jpg
+```
+
+- `fps=2` (two frames/sec) suits a short clip; lower to `fps=1` for long videos, raise to `fps=4` to catch a fast transient (a toast, a flashed error). Check length first with `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 <path>`.
+- Read first/middle/last frames, then bisect toward the moment of interest. Frame `N` ≈ `N / fps` seconds, so you can map a frame back to a timestamp and correlate it with logs.
+- Recovers visuals only (no audio) — usually enough for a UI/repro bug.
+
+## Step 2 — Commit the export
+
+```bash
+git add docs/issue/<n> && git commit -m "docs: #<n> export the issue"
+```
+
+Commit it **now**, before any planning. The export is the source of truth for what the issue says, so an agent resuming this branch — after a context wipe, a handoff, or in a parallel session — re-reads the thread instead of re-exporting it, and committing it up front means that holds even if the session dies mid-plan. Never commit it on the trunk or a promotion branch.
+
+`@.claude/skills/finalize/SKILL.md` deletes the whole `docs/issue/` tree in the last commit before `gh pr ready`, so this add and that delete cancel out in the squash. **You** must not delete it.
+
+## Step 3 — Return to the caller
+
+Hand back the export path (`docs/issue/<n>/issue.md`) and `<issue>` = `<n>`, the number the eventual PR must close. Where the caller's own procedure carves the work into slices, that number is the parent, and which number the PR closes is settled there rather than here — `@.claude/skills/plan/SKILL.md` § "Carving a task into issues" owns it.
```

**@vzakharov (human)** — 2026-09-14T23:20:38Z

it's not always the number to close; sometimes agents will need to take other issues for reference/information/etc.

---

### `.claude/skills/take-issue/SKILL.md`:70 — unresolved

```diff
@@ -0,0 +1,70 @@
+---
+description: Take a GitHub issue onto the branch — export the thread and its attachments, commit them, and hand the number back to whoever called. Invoke as `/take-issue <number|url>`; its callers are `/task`, `/plan` and `/go`, each running it first when the prompt carries a `#<N>`.
+---
+
+End state of this skill: `docs/issue/<n>/` holds the thread and its attachments, that export is committed on the branch, you have read it, and control is back with the caller — which is where every decision about the work is made.
+
+This skill decides nothing. It is the one place an issue gets pulled onto a branch, so its contract to its callers is that the issue has been **taken**: exported, committed, and there for a later session to re-read.
+
+## Argument shape
+
+The argument is an issue number or a full issue URL, optionally with prose around it — `fix the sidebar scroll #847` is the same invocation as `847`. The prose is the operator's own summary of the issue and is worth reading as a hint at what they care about, but **the export outranks it**: where the two disagree, the thread is what the work is against.
+
+## Step 0 — Mode gate: native plan mode is not supported
+
+If the session is in **native plan mode** — the launch banner or system prompt says so, `ExitPlanMode` is the offered exit, or an edit is refused for that reason — **stop before running anything below.** Tell the operator:
+
+- this flow is plan-**file**-based (`@.claude/skills/plan/SKILL.md`), and native plan mode cannot write the two artifacts it depends on: the export under `docs/issue/<n>/` and the plan under `docs/plans/`. Both must be committed and pushed, because the operator reviews from a different machine than the one you run on;
+- the plan-mode approval UI is unreliable in web sessions regardless (anthropics/claude-code#72704);
+- so switch to **accept-edits** or **auto** and send any reply — the run picks up from there; no re-invocation needed.
+
+Do not work around it, and do not fall back to a chat-only plan.
+
+## Step 1 — Export the issue locally (then read the export)
+
+**First command:** run the bundled exporter:
+
+```bash
+python3 scripts/export-github-item.py <issue-number|https://github.com/OWNER/REPO/issues/N> [--repo OWNER/REPO]
+```
+
+The script writes `docs/issue/<n>/issue.md` (body + comments + timeline) and downloads any image / file attachments referenced in the thread to `docs/issue/<n>/attachments/`.
+
+Consult the issue only through the export — never `gh issue view`, the GitHub MCP tools, or `WebFetch` in its place. `gh issue view` alone does **not** fetch attachments: GitHub's `private-user-images.githubusercontent.com` URLs require an authenticated request even when the issue is public, which is why the export script exists. `WebFetch` on a github.com issue page often fails outright in isolated environments. For a quick metadata check unrelated to the task at hand — labels, assignees, linked PRs — `gh issue view <n> --json title,body,labels,assignees,state,url` is still fine.
+
+**Then read** `docs/issue/<n>/issue.md` end to end, and **open the files under** `docs/issue/<n>/attachments/` when you need pixels (screenshots, mockups, design references).
+
+**Auth:** the script reads `$GH_TOKEN` (or `$GITHUB_TOKEN`) first, then falls back to `gh auth token`. One of those must be available. **Deps:** stdlib Python 3.9+ only — no `pip install` needed.
+
+**Repo:** if `--repo OWNER/REPO` is omitted and the argument isn't a full issue URL, the script reads `origin` from the current git checkout. Pass `--repo` explicitly when exporting an issue from a different repo than the one you're working in.
+
+If the export fails, **stop and report** — do not start solving the task from the title alone. Tell the user what failed and how to proceed. The script exits non-zero on every failure — auth, network, repo not found, or an attachment that wouldn't download — so check the status, not just the last line. A partial attachment failure still writes the Markdown and prints `Downloaded 2/3 attachment(s)` plus each URL it missed: the thread is there, but you'd be reading it with pixels missing.
+
+### Video attachments (screen recordings)
+
+Exported attachments may have no extension (the filename stem is the asset id), so `file docs/issue/<n>/attachments/<asset-id>` to spot videos (e.g. `ISO Media, Apple QuickTime movie`). You can read **images** but not play **videos**. Extract frames with `ffmpeg`, if it's available, and read the frames as images:
+
+```bash
+mkdir -p tmp/frames   # tmp/ is gitignored — never commit frames
+ffmpeg -y -i docs/issue/<n>/attachments/<asset-id> -vf fps=2 -q:v 3 tmp/frames/frame_%03d.jpg
+```
+
+- `fps=2` (two frames/sec) suits a short clip; lower to `fps=1` for long videos, raise to `fps=4` to catch a fast transient (a toast, a flashed error). Check length first with `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 <path>`.
+- Read first/middle/last frames, then bisect toward the moment of interest. Frame `N` ≈ `N / fps` seconds, so you can map a frame back to a timestamp and correlate it with logs.
+- Recovers visuals only (no audio) — usually enough for a UI/repro bug.
+
+## Step 2 — Commit the export
+
+```bash
+git add docs/issue/<n> && git commit -m "docs: #<n> export the issue"
+```
+
+Commit it **now**, before any planning. The export is the source of truth for what the issue says, so an agent resuming this branch — after a context wipe, a handoff, or in a parallel session — re-reads the thread instead of re-exporting it, and committing it up front means that holds even if the session dies mid-plan. Never commit it on the trunk or a promotion branch.
+
+`@.claude/skills/finalize/SKILL.md` deletes the whole `docs/issue/` tree in the last commit before `gh pr ready`, so this add and that delete cancel out in the squash. **You** must not delete it.
+
+## Step 3 — Return to the caller
+
+Hand back the export path (`docs/issue/<n>/issue.md`) and `<issue>` = `<n>`, the number the eventual PR must close. Where the caller's own procedure carves the work into slices, that number is the parent, and which number the PR closes is settled there rather than here — `@.claude/skills/plan/SKILL.md` § "Carving a task into issues" owns it.
+
+Then stop. Everything downstream — the plan-or-not call, the carve, the branch name, the PR — belongs to the caller.
```

**@vzakharov (human)** — 2026-09-14T23:20:51Z

the specifics are polar bears

---

### `.claude/skills/task/SKILL.md`:40 — unresolved

```diff
@@ -1,50 +1,73 @@
 ---
 description: >-
-  Take a task and decide for yourself whether it needs a plan before the work
-  exists, then run that call end to end — plan and hand off, plan and then
-  implement, or implement with no plan at all. Invoke as `/task <what to do>`.
-  The prompt is a conditional go-ahead scoped to that one task.
+  Take a task and decide for yourself whether it needs a plan, write the plan
+  when it does, and then decide whether the operator has to look — plan and hand
+  off, plan and then implement, or implement with no plan at all. Invoke as
+  `/task <what to do>`. The prompt is a conditional go-ahead scoped to that one
+  task.
 ---
 
-The decision this skill makes, before any other: **does this task get a plan, and does the plan block on the operator?** Two questions pick between three outcomes.
+The decision this skill makes, before any other: **does this task get a plan, and does the plan block on the operator?** Those are two questions with a plan file between them: the second judges the plan, so it is asked once the plan exists.
 
 **The prompt is a conditional go-ahead.** It authorizes implementation *on condition that* the agent judges the operator's gate unnecessary, scoped to the task in that message and to that message alone.
 
-`/task <what to do>` is the invocation. `/issue` is the other way in: it reads the thread first and then hands the work here, so the call is made once, in one place, whether or not the work is tracked. The mention stays bare rather than an `@`-reference — this skill ships to adopters who track no issues at all, and nothing here needs that file read.
+`/task <what to do>` is the invocation, and it is also where a launch-time directive lands: CLAUDE.md § "Plan mode & questions in web sessions" routes any opening prompt that asks for a change to this codebase here, so most tasks arrive without anyone typing the name. A `#<N>` in that prompt means the thread is exported and committed before anything else happens — `/take-issue` does that and hands the number back. Both mentions stay bare rather than `@`-references: this skill ships to adopters who track no issues at all, and nothing here needs those files read.
 
 **Anything a caller passes beyond the task — an `<issue>`, an export path — rides through unchanged to whichever outcome runs, and is never read here:** this skill knows what a task is and nothing else, and what the extras mean belongs to the skills at either end of them.
 
-## Question 1 — does the operator need to decide before the work exists?
+## Step 1 — Does this task get a plan?
 
-Any one of these is a yes:
+Either reason is enough on its own.
+
+**Writing it down would change what you build.** A plan is how an agent gets its own head straight, and that value needs no operator:
+
+- several parts whose order matters, or edits that only make sense landing together;
+- a live reuse call — the mandatory `## DRY notes` is the forcing function, and it earns the file whenever "shared or duplicated?" has a real answer to argue;
+- a shape you would otherwise discover halfway through, after building the first half against a different one.
+
+The test: if you can hold the whole change in your head and name every file it touches, the file buys nothing.
+
+**Or any of Step 3's four signs is even arguably present.** You are not deciding it yet — that is Step 3's call, made against the plan rather than against the line that asked for the work. Here you only notice that the question is live.
+
+**No to both → `@.claude/skills/go/SKILL.md` § "Planless entry"** with the task, where the diff is the plan.
+
+**This step is deliberately over-inclusive.** Being wrong costs a file `/finalize` sweeps, so a close call writes one.
+
+## Step 2 — Write it as a draft
+
+`@.claude/skills/plan/SKILL.md` Part 1, unchanged: `docs/plans/<slug>.draft.do-not-implement.md`, banner and all, published through `/pr` so the operator has a surface to read and interrupt on.
+
+**Every planning route produces a draft**, including the one that is about to implement without stopping. The state is not scaffolding to be skipped when you already know the answer: it is what a `/handle` reads if this session dies between writing the file and flipping it — a plan awaiting a go-ahead, which costs one round trip to re-give. The alternative, an `*.in-progress.md` claiming a live session holds the plan right now, is a reading someone has to untangle by hand.
```

**@vzakharov (human)** — 2026-09-14T23:22:47Z

> including the one that is about to implement without stopping

not sure but polar bear?

---

### `CLAUDE.md`:1 — unresolved

**@vzakharov (human)** — 2026-09-14T23:27:56Z

not sure the main bulk of the edits -- something that only pertains to session start -- belongs to CLAUDE.md. I'd rather have a *separate* session start hook (not the general `sesson-start.sh` one, as it's already split on main anyway) that sees if it's a skill-less call and feeds this to the context.

btw, two things to note if this DOES end with a `#<...>`

1- the decision on whether it involves code change can't be made before the issue is taken
2- seems like, instead of doing a round trip, we can export the issue right away with the script, put it where it belongs, and tell the agent it's already there, all they'll have to do is look. Let's /plan that

---

### `.claude/skills/update-muthur/catalog.md`:181 — unresolved

```diff
@@ -177,8 +177,9 @@ the project's first issue on the way through.
 
 | Item | What it does | Requires | Pulls in | Disposition |
 | --- | --- | --- | --- | --- |
-| `/issue` | Export and read a GitHub issue, split it into natively-linked sub-issues when the scope demands, then hand the work to `/task`, which makes the plan-or-not call on it — except a split, which always plans. | G2, `gh`, `scripts/export-github-item.py` | `/finalize`, `/pr`, `/plan`, `/task` (G2) | adopt |
-| `/propose-issue` | File a unit of work as an issue, deduping against what's already open. | G2, `gh`, `jq` | `/plan` (G2) | adopt |
+| `/take-issue` | Pull a GitHub issue onto the branch: export the thread and its attachments, commit them, hand the number back. Decides nothing — its callers are `/task`, `/plan` and `/go`, each running it first when the prompt carries a `#<N>`. | G2, `gh`, `scripts/export-github-item.py` | `/finalize`, `/plan` (G2) | adopt |
+| `/issue` | Redirect for the name `/take-issue` was split out of: with a `#<N>` it runs `/plan` on the argument and names `/task` and `/go` as the same-shape alternatives; with none it names `/propose-issue` and stops. | G2 | `/plan` (G2), `/propose-issue` | conditional — see below |
```

**@vzakharov (human)** — 2026-09-14T23:29:14Z

"do not take if this is the original adoption (only if it has been already adopted before)", same wording as with implement

---

## Timeline (status, references, and other events)

- **2026-09-12T14:50:45Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5186802965.
- **2026-09-12T15:09:19Z** @vzakharov renamed from «feat: give the plan-or-not call its own skill, /task» to «feat: give the plan-or-not call its own skill, and route /issue to it».
- **2026-09-12T15:27:12Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5186945235.
- **2026-09-14T10:05:19Z** @vzakharov cross-referenced this pull request from [#74 feat: route untracked work to /task, and move the split into /plan](https://github.com/vzakharov/muthur/pull/74).
- **2026-09-14T13:30:33Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5198256935.
- **2026-09-14T14:40:58Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5199032973.
- **2026-09-14T14:57:13Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5199246175.
- **2026-09-14T18:34:26Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5201405003.
- **2026-09-14T21:25:08Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5203027361.
- **2026-09-14T22:13:44Z** @vzakharov renamed from «feat: give the plan-or-not call its own skill, and route /issue to it» to «feat: the entry ladder routes on change-or-not, and the carve moves into /plan».
- **2026-09-14T23:30:05Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/71#pullrequestreview-5203785128.
