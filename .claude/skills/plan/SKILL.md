---
description: Plan on disk instead of in the plan-mode UI — write the plan to a git-tracked file under docs/plans/ whose name doubles as the approval gate, publish it as a draft PR so it can be reviewed as a diff, and ask clarifying questions as numbered prose instead of AskUserQuestion. Use whenever you would otherwise enter plan mode or call AskUserQuestion (ExitPlanMode); mandatory in a remote/web session, where both of those UIs lose answers.
---

## Why this skill exists

A plan on disk is a different artifact from a plan in an approval dialog:

- **Reviewable on another machine, on the operator's schedule.** The plan rides the branch, so it is pulled and read in the same tools as code, hours later.
- **Room for sections plan mode has nowhere to put** — notably the mandatory `## DRY notes`, which forces the reuse-vs-duplication call to be argued before any code exists rather than discovered in review.
- **The filename is the approval gate**, and the `git mv` that clears it is a commit — so *when* approval arrived and *in whose words* outlives the session.
- **Reviewable as a diff, not just as a file.** The plan is published as a draft PR (§ "Publishing the plan"), so feedback arrives as inline comments and threads — the surface already in use for code — instead of chat prose.
- **Approval carries into the next session.** The turn ends with a copyable `/go <branch>` line, so implementation starts from a recorded decision instead of re-litigating it.
- **Questions as numbered prose stay in the transcript** — tersely answerable ("1b, 2a"), and re-readable after a context wipe.

**Origin.** The skill began as a workaround for a bug in Claude Code's web/remote sessions, which is why web/remote is where this path is *mandatory* rather than merely better: there, plan mode and `AskUserQuestion` silently lose the answers given to prompts they re-emit after a session idles, and the stack grows with the idle. Operators run many concurrent web sessions, so prompts idle routinely — the loss is the normal case, not an edge one. CLAUDE.md § "Plan mode & questions in web sessions" describes the failure and owns where this skill is mandatory vs. optional; the tracking issue carries its exact wording and current status: **https://github.com/anthropics/claude-code/issues/72704**

None of the value above depends on that bug, so fixing it upstream does not retire the skill.

## If the session is already in native plan mode

Plan mode is reached two ways, neither of which asks the agent: the operator switches mode in the UI, or types `/plan` — a **built-in slash command**, so the keystroke renders in the client and never arrives. Either way the session is held to read-only work, so the recovery is keyed on **being in plan mode**, not on how it got there. (The operator's own entry to this skill is bare prose: `plan: <task>`, or just the task.)

**The tell:** the harness announces plan mode and names a plan file under `/root/.claude/plans/<slug>.md`; `Edit`/`Write` anywhere else refuse as read-only.

**This is plan mode's own exit, not an override of it.** Its instructions end with "this supercedes any other instructions you have received" — and they also make the harness plan file writable and end the turn at `ExitPlanMode`, which is the path below. What conflicts is the rival procedure injected alongside the restriction, a phased workflow on `Explore`/`Plan` subagents plus `AskUserQuestion`, and both are moot once the exit lands.

1. **Take the exit immediately — and ask for it.** The restriction gates `Edit`/`Write`, not Bash, so the plan file is reachable from inside plan mode; writing it there takes the operator's approval instead of asking for it. Spend the click only on a turn that has something to write, though: a question answerable from reading is answerable from inside plan mode.
2. **Copy the dialog's text into the harness plan file**: `mkdir -p "$(dirname <the path the harness named>)" && cp .claude/skills/plan/exit-dialog.md <that path>` — the directory does not exist until something creates it, so don't drop the `mkdir`. `ExitPlanMode` takes no plan argument, it renders that file, and `cp` overwrites — which re-entry needs, the harness handing back the same path with the previous exit's text still in it. Append at most one line naming the task and nothing further: the dialog is where the operator decides whether to spend the click, not where they review a plan.

   `exit-dialog.md` describes the click a **new** session's exit buys — writing the plan file. A session that arrived on continued work (`/from-branch`, `/handle`) is buying something else, usually write access to finish it, and says so rather than shipping copy that misdescribes the decision.
3. **Call `ExitPlanMode` bare**, then **run this skill from the top.** The deliverable is `docs/plans/<slug>.draft.do-not-implement.md` — not an answer in chat prose, and not the harness plan file's content carried over. That file is scaffolding for the dialog; it is never the plan.

**Rejecting the approval is the escape hatch**, and `exit-dialog.md` says so outright. Being in plan mode states no intent — reflex and a UI switch both land there — so the dialog is the first moment the operator is actually asked, and it has nowhere to type. A rejection, or "stay in plan mode" in chat, means run plan mode's own workflow and don't re-raise the exit.

**Exiting plan mode is not the go-ahead**, however the approval reads — it comes back as "you can now start coding", in accept-edits mode. It authorizes writing the plan file and nothing past it; the `do-not-implement` gate is untouched and still needs the token from § "The approval gate".

## Part 1 — Plan instead of plan mode

A `/plan` session's deliverable is the **plan file on a draft PR**, not code. The operator reviews it from another machine, often hours later, and begins implementation in a **different** session via `/go <branch>` (`@.claude/skills/go/SKILL.md` routes that through `/from-branch`, which attaches to the branch and finds the plan under `docs/plans/`) — the handoff works because the plan file rides the branch. So a plan turn ends in a handoff, not a continuation; same-session implementation is the rare exception.

**A `#<N>` in the argument means the thread is read first.** Load and follow `@.claude/skills/take-issue/SKILL.md` with the whole argument before planning anything — it exports the thread and its attachments to `docs/issue/<n>/`, commits them, and hands back the number. CLAUDE.md § "Plan mode & questions in web sessions" is the home of that rule; `/task` and `/go` carry the same pointer, because which of the three receives the prompt is the operator's choice and changes nothing about the export.

Do **exactly what you would do in plan mode** — same research, same rigor, same "don't touch code until approved" discipline. The _only_ difference is where the plan goes and how it's approved:

- Instead of presenting the plan via `ExitPlanMode`, **write it to `docs/plans/<branch-slug>.draft.do-not-implement.md`** (one file per session; name it after the current branch's task slug, or the issue number when working an issue — e.g. `docs/plans/1234.draft.do-not-implement.md`). The slug comes off the branch, so a harness auto-branch is renamed **before** the plan file is written, per CLAUDE.md § "Git conventions" — rename afterwards and the file keeps a slug naming nothing. The `.draft.do-not-implement.md` suffix is load-bearing: it is the on-disk marker that this plan has **not** been approved, visible in every `ls`, tool-call path, and `git status` so you can't drift past the gate without noticing. This directory is **not** gitignored on purpose: it rides the branch so the operator can pull and review the plan from another machine. Follow the repo's usual plan-content expectations, including the `## DRY notes` section CLAUDE.md requires.
- **Make line 1 of the file a banner** that restates the gate:
  ```
  > ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.
  ```
- Then **commit it and publish it** (§ "Publishing the plan" below), **end the turn with the handoff block** (§ "Handing off") and stop — do not start implementing.
- **The in-session path is the exception, not the default.** If a literal go-ahead token does arrive in _this_ session, "The approval gate" below governs it unchanged — and on approval you hand off to `@.claude/skills/go/SKILL.md`, whose Step 1 performs the flip that unlocks source edits (`git mv` the plan to `docs/plans/<branch-slug>.in-progress.md`, drop the draft banner, quote the go-ahead in the commit) as its first action, before any source edit. That flip is the on-record receipt that approval was given, so don't front-run it here; the mechanics live in `/go` to avoid two copies drifting apart. The gate is exactly as strict on this path as on any other; it just fires rarely.

### Carving a task into issues

Some work is too big for one PR, and the plan is where that gets decided — it is the first moment anyone has read the code. A carve produces two things: a plan file that specs one slice and describes the rest, and a list of issues the plan **proposes**. Nothing is filed here. `/go` files them on the go-ahead that flips the plan, so a plan turn that ends unapproved leaves the tracker exactly as it found it. The plan file is already the gate, which is what makes the carve's approval free rather than a second propose-and-stop layered inside the planning turn.

**The bar is high.** Do **not** carve because:

- the task touches several files (most do)
- you can imagine a "phase 1 / phase 2" framing (most things admit one)
- decomposition feels tidy

Default to taking the task whole. Carve only when the size is obviously beyond a single PR and the seams are real, not invented. **Genuinely large** means multiple unrelated subsystems, weeks of work, or distinct deliverables that ship independently — not "many files" or a tidy phase breakdown.

Deciding **not** to carve is not a gate and never becomes one: say so in a line and write the plan. Do not ask whether the task looks big enough, and do not offer a carve you don't think is warranted — the operator disagrees in the plan review, which costs them a sentence, whereas a question here costs a round trip on every task.

**Only the next slice has to be manageable.** Spell out the immediate work in full and give a **coarse** view of what follows — smaller than the original umbrella, but not fully decomposed. Parked slices are placeholders and ordering hints, not mini-specs; you owe no implementation DAG and no per-child plans up front.

#### What the plan file carries

Under a heading of its own, the plan names every issue it proposes — the parent and each child — with a title and a one-line scope each, in dependency order, saying which child this plan specs. That list is the proposal the operator approves by approving the plan.

**Dedupe each proposed issue read-only, and write the matches into the list.** Run `@.claude/skills/propose-issue/SKILL.md` Steps 1–2 — search and triage, which touch nothing — for every slice, and record what they found beside the slice it matched. So a duplicate is something the operator rules on while reviewing the carve, not an interruption after it, and a slice already tracked gets linked as the sub-issue instead of filed twice.

**A match on the parent stops and reports.** Somebody else already tracking the whole umbrella is what changes the operator's judgment about whether to carve at all, which is a different question from whether one child is a duplicate.

**The parent.** Arriving from `/take-issue` it exists already. Arriving from bare prose the plan proposes one and `/go` creates it. It stays open as a grouping artifact and is never what the PR closes — **every slice is a child, the first included.** Filing children 2..n and doing slice 1 "under the parent" leaves the PR nothing to close and makes the parent both umbrella and work item. The parent closes once its children are done, which is the operator's call.

Because the children do not exist yet, the PR for this slice carries **`Closes #<tbd>`** — `@.claude/skills/pr/SKILL.md` Step 4 owns that marker and `/propose-issue` Step 3 fills it in.

#### What `/go` does with the list

It runs `/propose-issue` Step 3 once per slice, parent and children alike, creating what the operator approved. Three things belong to the parent-child *relation* rather than to creating an issue, so they are stated here rather than in that skill:

**Link each child natively — mandatory.** `Part of #<parent>` prose is a pointer for humans, not a relation GitHub can track. Keep that line in the child's body, and **also** attach it through the sub-issues API — the GitHub MCP `sub_issue_write` tool (`method: "add"`, `issue_number: <parent>`, `sub_issue_id: <child's database id>`), or plain `gh`:

```bash
REPO=<owner>/<repo>
PARENT=<parent issue number>
for n in <child issue numbers…>; do
  cid=$(gh api "repos/$REPO/issues/$n" --jq '.id')
  gh api "repos/$REPO/issues/$PARENT/sub_issues" -F sub_issue_id=$cid
done
```

Two traps, either of which 422s: `sub_issue_id` is the child's numeric **database `id`**, not its issue number; and it must be sent with **`-F`**, not `-f`, which would send the integer as a string.

Without the relation the parent has no machine-readable notion of its children, so "the parent closes when its children are done" is unverifiable and the umbrella silently rots. Skipping the native link breaks the carve; it is not an omitted nicety.

**Size each slice so it is worth its own PR.** One child ships as one PR — that mapping is fixed; don't bundle several children into one PR or carve one child across several. The lever is the **granularity of the carve itself**: each child should be **substantial enough to justify a PR**, roughly **≥5 files of real change**. A prospective child touching only **1–3 files is too fine a cut** — group it with the other small, cohesive items into a single child that, taken together, is PR-worthy (within it, one commit per underlying item keeps the diff readable). A QA roundup of six small defects is usually one or two children, not six.

- **Group by cohesion, not just to hit a count.** Bundle items that sit in the same area or move together — several modal tweaks, a cluster of responsive-CSS fixes.
- **Keep blocked or uncertain items as their own child** even when small. A fix needing an environment or investigation this run can't cover — a value to pixel-match against a running deployment, a root cause needing in-browser repro, an item someone else marked *in progress* — gets its own deferred child with a note on what it's blocked on. Grouping merges trivial *ready* fixes; it never justifies shipping a guess.

**Carry an enumerated parent's reports into each child.** When the parent reads as an **enumeration of distinct bugs or requests** — a QA roundup, a bullet list of unrelated defects — copy each original item's **verbatim text and its attachments** into the child that covers it, so the child carries the reporter's own words and screenshots rather than your paraphrase. (Distinct from the other reason to carve: a **single cohesive problem statement** merely too vast for one PR has no per-item original text to distribute, so don't force it.)

- Put the original text and attachments in the child's **body** at creation; if the bodies already exist without them, post them as a **comment** on each child instead.
- **Reuse the parent's attachment URLs** so images and videos render: GitHub serves them at `https://github.com/user-attachments/assets/<asset-id>`, and the exporter rewrites those to `docs/issue/<n>/attachments/<asset-id>.<ext>` — so the **filename stem is the asset id**. Reconstruct the original URL from it, or read the parent's raw body through the API where the `user-attachments` links are intact, rather than re-uploading. Screenshots use `<img …>`; a bare video URL on its own line auto-embeds.
- Quote the reporter verbatim, in a blockquote, attributed, keeping related items grouped under the child they map to.
- **When unsure** whether the parent is an enumeration or one cohesive problem, **ask the operator** — in the plan's questions, where every other fork goes.

### Publishing the plan

Once the plan file is committed, invoke `@.claude/skills/pr/SKILL.md` with no args — load and follow it; do **not** inline-copy its steps. Its plan-open mode is what a branch carrying one plan commit and no PR reaches. `/pr` owns the `gh` mechanics; `/plan` owns only the decision to publish.

The trigger lives here rather than in `/pr` because this is where a plan becomes pushed, so **every** entry into planning gets a PR. CLAUDE.md § "Plan mode & questions in web sessions" names a bare `/plan` as the default entry for a new web session — more common than a prompt naming an issue — and hanging PR-creation off `/pr` would leave exactly that entry on a PR-less branch.

### Handing off — end the plan turn with a copyable `/go` block

Get the branch with `git branch --show-current` and substitute the real name. Introduce the block with wording that **names the new session** — `To implement — start a new session with:`, or an unmistakable equivalent. That lead-in is what carries the session model to the operator; a bare "To implement:" reads as an offer to do it here, which is the misreading the block exists to remove. Emit the command in a fenced block containing **only** the command — no language tag, nothing else inside the fence — so it can be copied verbatim:

````
```
/go claude/add-usage-charts-k3n2af
```
````

- Emit it at the end of **every** turn that leaves the plan in a reviewable, complete state — the turn that first writes the plan, and any later turn that revises or collapses it (Part 3). One block per turn, as the last thing in the reply.
- **Print the PR URL alongside it**, outside the fence — the plan is published by the time the block goes out, and the URL is where the operator reads and comments on it.
- **Open questions don't hold the block back when they carry recommendations.** Part 2 requires every fork to name a recommended option _and_ the plan file to be written with that option already in force, so implementing it unanswered is the same as adhering to the recommendations. Emit the block alongside the questions: an answer that differs revises the plan, and silence is a valid resolution. Hold the block only for a fork with no recommendation, where the plan has nothing executable to say until the operator picks — handing over a command to implement a genuinely unresolved fork invites implementing the wrong one.
- **Never** close a plan turn with "Want me to implement it?", "Shall I proceed?", "Ready for me to start?", or any equivalent. Two reasons: the plan session does not implement, so there is nothing to ask; and a turn that ends on that question trains the agent to read the operator's _next_ message as an answer to it, so a correction ("actually, do X instead") gets taken as assent and code starts getting written. The handoff block is the structural fix that the approval gate's "a suggestion is a plan revision" and Part 3's "picking an option is not a signal to implement" can only exhort.
- The block is built for a session that does not exist yet, which is why the lead-in names it. Pasting it back into _this_ session is a recognizable mistake with its own guard — see `@.claude/skills/go/SKILL.md` § "Argument shape" for the canary that catches it.

### The approval gate

**Only start implementing when the operator's message literally contains a go-ahead token** — "go ahead", "let's go ahead", "implement", "let's implement", or an unmistakable equivalent ("ship it", "do it", "proceed", "lgtm go"). Until such a token arrives, you are still in the planning conversation, no matter how the exchange evolves.

**A review comment is never a go-ahead.** Publishing the plan gives suggestions a second channel — an inline comment proposing a different approach is a plan revision, which `@.claude/skills/handle/SKILL.md` Step 2 routes — but what unlocks source edits is only ever an invocation: `/go`, or a `/handle` that finds no unanswered feedback. Review prose has too many ways to read as assent to carry that weight.

- **A suggestion to do something differently is a plan revision, not a go-ahead.** When the operator proposes an alternative approach, tweak, or "how about we…", that means **update the plan file (or discuss it) to reflect the new direction** — it does **not** mean start coding with the suggestion folded in. Reflect the change in the plan and wait for the token.
- **The exception is a combined message:** if the same message pairs a suggestion _with_ a go-ahead token — e.g. "let's do X instead of Y and implement", "go ahead, but use Z" — then apply the suggestion and proceed. The token is what unlocks implementation; the suggestion just adjusts what you implement.
- **When unsure whether a reply is approval, treat it as not-yet-approved** — and resolve the ambiguity by re-emitting the handoff block, not by asking for a yes. A false start costs more than one more round-trip: reverting speculative code and re-aligning is worse than handing the command over again.
- Approval is scoped to the plan as it stands when the token is given. A go-ahead on Monday's plan doesn't authorize a materially different Tuesday reshaping — re-confirm if the plan changed since.
- The `*.draft.do-not-implement.md` → `*.in-progress.md` rename is the **single act** that unlocks source edits, and it belongs at the moment of the go-ahead — as the first thing you do after it, not retroactively once code is already written. If you catch yourself about to edit source while the file still says `do-not-implement`, that is the gate firing: stop and check whether the go-ahead token actually arrived.

This gate applies to the **initial** transition from planning to implementing. Once you're past it and actively implementing an approved plan, the "Scope" section below governs: follow-ups are handled directly, including code changes the operator asks for, without reopening a plan cycle.

### Plan file lifecycle

The plan file carries its state in its name, and moves through it by `git mv` (the base slug never changes):

1. `docs/plans/<slug>.draft.do-not-implement.md` — written here, awaiting the operator's go-ahead.
2. `docs/plans/<slug>.in-progress.md` — flipped as the first post-go-ahead action (above). **The name is a claim: a session has this plan open right now**, so it is not a file another session may pick up. `@.claude/skills/go/SKILL.md` owns implementing against it, and owns the one escape hatch for a session that died still holding it.
3. `docs/plans/<slug>.paused.md` — a session stopped partway, recorded what is done and what is left, and released the plan. This is the resumable state, and the one a later `/go` continues from.
4. `docs/plans/<slug>.completed.md` — flipped by `/go` once implementation and its quality passes are done, just before it hands the PR to `/pr`.

Every state still matches `docs/plans/*.md`, so consumers that glob the directory (`/go`, `/from-branch`, `/handle`, `/finalize`, `/tend-prose`) keep working unchanged.

**The predicate the states exist to answer:**

> **Implementation has begun** iff `docs/plans/` holds at least one file that is not `*.draft.do-not-implement.md` — that is, any `*.in-progress.md`, `*.paused.md` or `*.completed.md`.

It is deliberately broader than a branch carrying nothing but a draft plan, where "are we still planning?" is obvious. The broad form also reads the mixed branch — one plan completed, then a follow-up draft opened, with a review touching both the new plan and the shipped code. A draft plan being present is the tell that the branch is back in planning, whatever sits beside it. `/handle` Step 2 reads review feedback against this.

The plan file is a working artifact, not a deliverable: it rides the branch for review but must **never land on the trunk**. `@.claude/skills/finalize/SKILL.md` deletes the entire `docs/plans/` tree in the last commit before `gh pr ready` (any suffix — `git rm -r docs/plans/`), so the add-then-delete pair cancels out in the squash — the same lifecycle as `docs/issue/`. Do **not** delete it yourself mid-task; leave that to finalization.

## Part 2 — Questions as numbered prose instead of AskUserQuestion

When you would otherwise call `AskUserQuestion`, **ask the same questions, with the same options you'd have offered** — just render them as prose in your chat reply instead. Preserve the fast-answer affordance: **number each question and letter each option**, and state which option is the default/recommended, so the operator can reply tersely (e.g. "1b, 2a, 3-default") without typing prose back. This keeps the whole exchange in the durable transcript rather than in the flaky question UI.

**A recommendation is a commitment, not a lean.** Write the plan file with the recommended option already in force as its single approach — the same collapse Part 3 performs when the operator picks — so an open question degrades into "the recommendation stands" instead of a blocked fork, and the plan is implementable as written no matter which questions go unanswered. That is what lets the handoff block go out with questions still open (Part 1) and lets `/go` proceed without the answers (`@.claude/skills/go/SKILL.md` § "Step 1"). A fork you can't recommend either way is the exception, and it does block: say so explicitly in the plan rather than picking silently.

## Part 3 — When the operator picks an option

Whenever the operator resolves one of the option forks you presented — by choosing an option, in whatever words ("the recommended one", "B", "the retry approach", "not the fixed cap") — **rewrite the plan so the chosen option _is_ the plan**: written as the single approach, in the imperative, as if it had never been one of several. No special keyword is required; a plain choice is the trigger. This is the one sanctioned plan rewrite, distinct from the "don't churn the plan after approval" rule in Part 1 (which forbids re-editing per code change during implementation — collapsing a resolved fork _before_ implementing is expected and wanted).

**Picking an option is not a signal to start implementing.** Collapse the plan and then stop — and here "stop" means ending the turn with the handoff block (Part 1 § "Handing off"), same as any other turn that leaves the plan reviewable. Unless the operator's message _also_ explicitly asks you to begin (e.g. "pick B and implement it"), a bare choice means "record this decision," not "go" — when in doubt, hand the command over instead of writing code.

**Delete the rejected options' exposition to save context** — the plan gets re-read on every resume, so carrying dead alternatives is a standing tax. You may keep a brief note of what was rejected, but cap it at **one paragraph covering _all_ rejected options for that fork** (per fork), stating just what was ruled out and the one-line why (especially when the "why" is a hard finding worth not rediscovering). Drop the per-option cost/mechanics detail entirely. If several independent forks were resolved, each may keep its own one-paragraph note.

Then commit and push the rewritten plan (this refresh is explicitly wanted, so it's not the churn Part 1 warns against).

## Scope

This is a **web/remote-session** workaround, and it applies to **new** sessions — see CLAUDE.md ("Plan mode & questions in web sessions") for exactly when it's mandatory vs. optional. It is **not** for continued work: once a plan has been approved and you're implementing, handle the operator's follow-ups directly — answer their questions in chat **and implement any code changes they ask for** — without re-writing the plan file or reopening a plan cycle.

A `/from-branch` or `/handle` launch counts as continued work, not a new session: both attach to an existing branch or PR to resume work started elsewhere, so **do not open a plan cycle for them** — even though it's the first message of the session. Follow the embedded follow-up (or wait for the operator's) directly. The only exception is if that follow-up explicitly asks you to plan a fresh, separable piece of work.
