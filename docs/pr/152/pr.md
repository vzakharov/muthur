# PR #152: fix: /go releases the plan when a turn ends blocked on the operator

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/152
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/pause-on-question-snf6z4
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-06T12:13:47Z
- **Updated:** 2026-10-06T13:00:26Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/skills/go/SKILL.md`:99 — unresolved — last: @vzakharov (human) 2026-10-06T13:00:10Z — "не понял что тут хотим сказать изменением. Если вопрос ждёт…" → [↓](#t01)

---

## Body

## Summary

- `/go`'s "Stopping partway releases the plan" gains a third trigger: a turn that ends blocked on an operator decision. The plan goes to `*.paused.md` with the open question recorded beside what is done and what is left, so no `*.in-progress.md` claim outlives the turn that held it (the stale claim seen on vzakharov/vovazakharov.com#104).
- The answer resumes the plan through Step 1's `*.paused.md` case, in this session or another: flip back to `*.in-progress.md`, record the answer, build on it.
- An elephant stopped mid-bite by such a question takes the existing mid-bite path; planless work holds no claim, so a blocked turn there writes no file; the `/relay` offer stays with budget pauses only.

## QA Checklist

- [ ] `blocked-pause` — Run `/go` on a plan whose text leaves a fork open; confirm the turn that asks the question ends with the plan renamed to `*.paused.md`, the question recorded in it, and the rename pushed.
- [ ] `resume-same` — Answer the question in the same session; confirm the first commit flips the plan back to `*.in-progress.md` with the answer recorded before any source edit.
- [ ] `resume-fresh` — Answer instead from a fresh session with `/go <branch>`; confirm Step 1 picks the paused plan up rather than stopping on a claim.
- [ ] `planless` — Run `/go <task>` that hits a blocking question; confirm no plan file is written and no `/relay` is offered.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `blocked-pause` | manual-only | — | Agent behavior under a skill's prose; no harness drives a session end to end |
| `resume-same` | manual-only | — | As above |
| `resume-fresh` | manual-only | — | As above |
| `planless` | manual-only | — | As above |

Fixes #149

https://claude.ai/code/session_01SobKqCH27C377H23jjJVM1

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-06T12:13:59Z — "Proposed squash title/body: ``` fix: #149 /go releases the p…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-06T12:13:59Z

[https://github.com/vzakharov/muthur/pull/152#issuecomment-6015990495](https://github.com/vzakharov/muthur/pull/152#issuecomment-6015990495)

Proposed squash title/body:

```
fix: #149 /go releases the plan when a turn blocks on the operator (pr #152)
```

```
/go released a plan to *.paused.md only when the operator asked it to
stop or the context budget hook fired, so a turn that ended on a
question to the operator left the plan *.in-progress.md: a claim no
session was holding. Whoever answered in a fresh session, or followed
one that died waiting, found Step 1 stopping on it.

A turn blocked on an operator decision is now a third trigger. The plan
is renamed to *.paused.md with the open question recorded beside what
is done and what is left, and the answer resumes it through Step 1's
paused case, in the same session or another. An elephant blocked
mid-bite takes the existing mid-bite path; planless work holds no
claim, so a blocked turn there writes no file; the /relay offer stays
with budget pauses.

Fixes #149

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/go/SKILL.md`:99 — unresolved — last: @vzakharov (human) 2026-10-06T13:00:10Z — "не понял что тут хотим сказать изменением. Если вопрос ждёт…" → [↓](#t01)

<a id="t01"></a>

### `.claude/skills/go/SKILL.md`:99 — unresolved

```diff
@@ -81,16 +81,24 @@ Commit/push discipline is already governed by CLAUDE.md — don't reinvent it he
… 8 lines elided …
+- a turn that ends blocked on an operator decision — a question the work cannot proceed past without their answer.
+
+Record in the plan file what is done and what is left, and the open question when there is one, `git mv` it to `docs/plans/<slug>.paused.md`, commit and push. No format is prescribed for that record …
+
+**The answer resumes a blocked plan through Step 1's `*.paused.md` case**, in this session as in any other: `git mv` it back to `*.in-progress.md` and record the answer before building on it.
 
 **An elephant pauses at every bite's end, and the record is the plan's own sections** (`@.claude/skills/plan/elephant.md` § "The plan's shape"). Two ways to get there:
 
 - **The bite is done** — fold `## This bite` into `## Eaten so far`, at that section's altitude, and reword `## Rest of the elephant` where the work found it wrong or learned what it needs, while this session still holds that context; then run Step 3 and Step 4, which leave the plan `*.paused.md`. Stop there, budget left or not — the operator reviews between bites — and end the turn with the handoff block below.
-- **A stop mid-bite** — the budget notice or the operator: fold what is built into `## Eaten so far`, rename `## This bite` to `## Rest of the bite` and leave the rest as written, then the `git mv`, commit and push above. Skip Step 3: `/polish` scopes itself from the last `polish:` commit, so the next bite's end covers this half too.
+- **A stop mid-bite** — the budget notice, the operator, or a question that blocks the turn: fold what is built into `## Eaten so far`, rename `## This bite` to `## Rest of the bite` and leave the rest as written, then the `git mv`, commit and push above. Skip Step 3: `/polish` scopes itself from the last `polish:` commit, so the next bite's end covers this half too.
 
-**Work with no plan behind it gets one here**, written straight to `docs/plans/<slug>.paused.md`: the task as asked, what is done (with its commits), what is left, and the decisions a successor would otherwise re-litigate. There is no draft stage — the work is already under way on a go-ahead, and `*.paused.md` is the state Step 1 resumes from.
+**Work with no plan behind it gets one here**, written straight to `docs/plans/<slug>.paused.md`: the task as asked, what is done (with its commits), what is left, and the decisions a successor would otherwise re-litigate. There is no draft stage — the work is already under way on a go-ahead, and `*.paused.md` is the state Step 1 resumes from. A turn blocked on a question is the exception: with no claim to release, it writes no file, and the question waits in the conversation.
```

**@vzakharov (human)** — 2026-10-06T13:00:10Z

не понял что тут хотим сказать изменением. Если вопрос ждёт ответа, об этом тоже надо записать в плане

---

## Timeline (status, references, and other events)

- **2026-10-06T13:00:26Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/152#pullrequestreview-5428715618.
