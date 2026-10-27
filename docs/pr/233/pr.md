# PR #233: feat: /go delegates clear sub-tasks to weaker models in worktrees

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/233
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/go-delegation-c22yxb
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-27T02:38:25Z
- **Updated:** 2026-10-27T03:28:23Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 4

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/hooks/file-tools-nudge.py`:1 — unresolved — last: @vzakharov (human) 2026-10-27T03:22:24Z — "упустил, это о чём?" → [↓](#t01)
- **T02** `.claude/hooks/go-delegation.py`:1 — unresolved — last: @vzakharov (human) 2026-10-27T03:24:23Z — "из сессии: > Ловит все три пути входа: вызов через Skill, чт…" → [↓](#t02)
- **T03** `.claude/skills/go/delegation.md`:30 — unresolved — last: @vzakharov (human) 2026-10-27T03:26:26Z — "лучше всё-таки не record of а summary of, а то это не в ту с…" → [↓](#t03)
- **T04** `.claude/skills/go/delegation.md`:83 — unresolved — last: @vzakharov (human) 2026-10-27T03:27:35Z — "так... я тут задумался, не детерминировано ли это значение и…" → [↓](#t04)

---

## Body

## Summary

- `/go`'s execution step gains delegation: the Opus agent hands sub-tasks it judges clear and judgement-free to `sonnet`/`haiku` subagents in their own git worktrees, then reviews them from its own tree, fixes what needs fixing, and squash-merges them with the model named in the commit.
- After each run it sets, by eye, what the subagent cost (task-notification token and tool-use counts at `.claude/costs/prices.json` rates) against what doing it in-session would have cost, and folds the verdict into `.claude/skills/go/delegation-model-capabilities.md` — the per-model record of what each model handled, missed, and how to brief it, rewritten in place and capped at 100 lines by `scripts/vet.sh`.
- The notes are written impersonally — an entry names the kind of work, never the task — with lessons that hold for every model in their own section (first: Sonnet 5.5 reads its cache at Opus 5.5's rate, so a small sub-task saves nothing delegated). Adopters take the file as it stands, and `/update-muthur` Step 5 folds the source's file into theirs lesson by lesson on every sync, keeping their own lessons and the cap; the `/go` catalog entry states that disposition.
- The procedure lives in a sidecar, `.claude/skills/go/delegation.md`; `SKILL.md` Step 2 carries one conditional pointer. `.claude/hooks/go-delegation.py` delivers both files as context the first time `/go` enters a session — a `Skill` call, a `Read` of its `SKILL.md`, or a typed `/go` — so the agent spends no round trip on them. `MUTHUR_DELEGATION=off` silences it, and `/go` reads as if delegation had never been written.
- Dogfooded on this branch: the hook's test suite was written by a `sonnet` subagent in a worktree and squash-merged after review (93138033). The run seeded the notes — including that at that size it cost more than writing it in-session, and that a worktree starts from the default branch.

## QA Checklist

- [ ] `hook-on` — with `MUTHUR_DELEGATION` unset, invoke `/go` in a new session: `delegation.md` and `delegation-model-capabilities.md` arrive as hook context, once per session.
- [ ] `hook-off` — with `MUTHUR_DELEGATION=off`, the same invocation brings no delegation context.
- [ ] `entries` — the hook fires on a `Skill` call for `go`/`implement`, on a `Read` of `.claude/skills/go/SKILL.md`, and on a typed `/go` prompt; nothing else triggers it.
- [ ] `cap` — `scripts/vet.sh` fails when `delegation-model-capabilities.md` exceeds 100 lines.
- [ ] `dogfood` — the branch history shows a sub-task delegated to a weaker model in a worktree and squash-merged with the model named.
- [ ] `sync-merge` — `/update-muthur` Step 5 tells an adopter's sync to fold `delegation-model-capabilities.md` in lesson by lesson rather than port or skip it, and no entry in the notes names a task, branch or file.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `hook-on` | partly | yes | `scripts/test_go_delegation.py`; the live session check is manual |
| `hook-off` | yes | yes | same test |
| `entries` | yes | yes | same test |
| `cap` | yes | no | one shell line in `vet.sh`; check by hand |
| `dogfood` | no | — | read the log |
| `sync-merge` | no | — | read the paragraph |

https://claude.ai/code/session_01DaohkBA8QFBvya49vxK4Ez

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-27T02:38:42Z — "Proposed squash body: ``` An Opus agent running /go spends i…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-27T02:38:42Z

[https://github.com/vzakharov/muthur/pull/233#issuecomment-6432378019](https://github.com/vzakharov/muthur/pull/233#issuecomment-6432378019)

Proposed squash body:

```
An Opus agent running /go spends its own tokens on sub-tasks a cheaper
model could do as well: a test for a fixed contract, a mechanical
rename, a script whose interface is already settled. /go's execution
step now hands such judgement-free sub-tasks to sonnet or haiku
subagents, each in its own git worktree, then reviews the result as a
stranger's PR, fixes what needs fixing and squash-merges it into the
branch with the model named in the commit.

After each run the agent weighs, by eye, what the subagent cost at
.claude/costs/prices.json rates against doing it in-session, and folds
that verdict with what the model handled or missed into .claude/skills/
go/delegation-model-capabilities.md: a per-model summary rewritten in
place, capped at 100 lines by vet, plus lessons that hold for every
model - first, that Sonnet 5.5 reads its cache at Opus 5.5's rate, so
a sub-task of a few hundred lines saves nothing delegated.

Entries name the kind of work, never the task, so the notes hold in any
repo: adopters take the file as it stands, and /update-muthur folds the
source's file into theirs lesson by lesson on each sync rather than
porting or skipping it, keeping their own lessons and the cap.

The procedure lives in a sidecar, .claude/skills/go/delegation.md, and
SKILL.md carries one conditional pointer to it. A hook delivers both
files as context the first time /go loads in a session - through the
Skill tool, a Read of its SKILL.md, or a typed /go - so no round trip
is spent fetching them. MUTHUR_DELEGATION=off silences the hook, and
/go then reads as if delegation had never been written.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/hooks/file-tools-nudge.py`:1 — unresolved — last: @vzakharov (human) 2026-10-27T03:22:24Z — "упустил, это о чём?" → [↓](#t01)
- **T02** `.claude/hooks/go-delegation.py`:1 — unresolved — last: @vzakharov (human) 2026-10-27T03:24:23Z — "из сессии: > Ловит все три пути входа: вызов через Skill, чт…" → [↓](#t02)
- **T03** `.claude/skills/go/delegation.md`:30 — unresolved — last: @vzakharov (human) 2026-10-27T03:26:26Z — "лучше всё-таки не record of а summary of, а то это не в ту с…" → [↓](#t03)
- **T04** `.claude/skills/go/delegation.md`:83 — unresolved — last: @vzakharov (human) 2026-10-27T03:27:35Z — "так... я тут задумался, не детерминировано ли это значение и…" → [↓](#t04)

<a id="t01"></a>

### `.claude/hooks/file-tools-nudge.py`:1 — unresolved

**@vzakharov (human)** — 2026-10-27T03:22:24Z

упустил, это о чём?

---

<a id="t02"></a>

### `.claude/hooks/go-delegation.py`:1 — unresolved

**@vzakharov (human)** — 2026-10-27T03:24:23Z

из сессии:

> Ловит все три пути входа: вызов через Skill, чтение go/SKILL.md (так в него попадают /task, /handle, /from-branch) и набранный руками /go

а разве чтение go/SKILL.md не является общим для всех трёх? я бы не плодил форков если можно избежать

---

<a id="t03"></a>

### `.claude/skills/go/delegation.md`:30 — unresolved

```diff
@@ -0,0 +1,103 @@
… 26 lines elided …
+
+## Picking the model
+
+`delegation-model-capabilities.md` beside this file is the record of what each
```

**@vzakharov (human)** — 2026-10-27T03:26:26Z

лучше всё-таки не record of а summary of, а то это не в ту сторону будет клонить

---

<a id="t04"></a>

### `.claude/skills/go/delegation.md`:83 — unresolved

```diff
@@ -0,0 +1,103 @@
… 75 lines elided …
+- **What it cost** — from the task notification's `subagent_tokens` and tool-use
+  count: each turn re-reads the agent's context, so the bulk is cache reads over
+  a context growing toward that token count, plus its output.
+- **What doing it yourself would have cost** — the output tokens at your own
+  rate, plus your whole context re-read on every extra turn it would have taken,
+  plus what the work and its tool output would have added to that context for
+  the rest of the session. Charge the delegation with your brief and your review
+  too.
```

**@vzakharov (human)** — 2026-10-27T03:27:35Z

так... я тут задумался, не детерминировано ли это значение и нельзя ли его посчитать программно. единственное узкое место которое я вижу: у более сильной модели это могло занять меньше шагов

---

## Timeline (status, references, and other events)

- **2026-10-27T03:28:23Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/233#pullrequestreview-5661853668.
