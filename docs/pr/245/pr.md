# PR #245: feat: [attn adopters] route every repo-changing skill through /task

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/245
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/task-repo-change-contract
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-28T04:03:39Z
- **Updated:** 2026-10-28T04:23:22Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 3

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/skills/task/repo-change.md`:5 — unresolved — last: @vzakharov (human) 2026-10-28T04:20:52Z — "тут не только unless, но и "в той части, в которой не otherw…" → [↓](#t01)
- **T02** `.claude/skills/task/repo-change.md`:17 — unresolved — last: @vzakharov (human) 2026-10-28T04:21:15Z — "медведи?" → [↓](#t02)
- **T03** `docs/remove-before-merging/squash-message.md`:22 — unresolved — last: @vzakharov (human) 2026-10-28T04:23:07Z — "файл они и сами найдут, а "no operator approval needed" звуч…" → [↓](#t03)

---

## Body

## Summary

- A skill that commits and pushes on its own skips `/polish` and `/pr`, so the operator gets a diff no pass has read and no PR to review it in. New `.claude/skills/task/repo-change.md` states the contract: a skill whose run leaves work in the repo runs as `/task`'s work unless its invocation says otherwise; `/task` makes its plan-or-not call and `/go`'s tail lands it.
- Such a skill names its deviations from the route, and only those; the loop's own skills (`/go`, `/polish`, `/pr`, `/finalize`, `/relay`, `/sync-branch`…) are the route itself. `/task`'s SKILL.md and its catalog entry point at the file.
- Swept muthur's skills: `/update-muthur` (already a task), `/audit-github-backlog` and `/detemplate` (always plan and hand off) now cite it with their deviations; the stubs that leave work in the repo — `/readonly-probe`, `/log-review`, `/release`, `/hotfix` — tell their hydration to name deviations against it. Left out as route mechanics or no repo change: `/take-issue`, `/watch-ci`, `/bootstrap-workflow-dispatch`, `/renumber-migration`, `/spinoff` (changes another repo; its target already goes through `/pr`).
- `[attn adopters]`: sweep your own repo-changing skills and cite `repo-change.md` in each, naming its deviations.

## QA Checklist

- [ ] `contract` — read `.claude/skills/task/repo-change.md`: it is generic (no adopter-specific examples) and matches the summary above.
- [ ] `pointers` — each touched skill cites the file and names only its own deviations.
- [ ] `vet` — `./scripts/vet.sh` passes (the catalog check sees `repo-change.md` referenced).

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `contract` | no | no | prose judgement |
| `pointers` | partly | partly | `check-skill-catalog.sh` checks the pointers resolve, not their wording |
| `vet` | yes | yes | `scripts/vet.sh` |

https://claude.ai/code/session_01DaohkFAwcx3DWHQR4aLZUt

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-28T04:03:58Z — "Proposed squash body: ``` A skill that commits and pushes on…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-28T04:03:58Z

[https://github.com/vzakharov/muthur/pull/245#issuecomment-6460358255](https://github.com/vzakharov/muthur/pull/245#issuecomment-6460358255)

Proposed squash body:

```
A skill that commits and pushes on its own skips /polish and /pr, so
the operator gets a diff no pass has read and no PR to review it in.
.claude/skills/task/repo-change.md now states the contract: a skill
whose run leaves work in the repo runs as /task's work unless its
invocation says otherwise, names its deviations from that route and
only those, and the loop's own skills are the route rather than work
through it. /task points at it.

The skills that leave work in this repo cite it: /update-muthur, and
/audit-github-backlog and /detemplate, whose deviation is always
planning and handing off; the stubs /readonly-probe, /log-review,
/release and /hotfix have their hydration name deviations against it.

Adopters: sweep your own skills whose run leaves work in your repo and
that are not part of the loop itself. In each, cite
.claude/skills/task/repo-change.md and name that skill's deviations
from the route (landing on a PR that already exists, say), and only
those. No operator approval needed; the file:
https://github.com/vzakharov/muthur/blob/main/.claude/skills/task/repo-change.md

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/task/repo-change.md`:5 — unresolved — last: @vzakharov (human) 2026-10-28T04:20:52Z — "тут не только unless, но и "в той части, в которой не otherw…" → [↓](#t01)
- **T02** `.claude/skills/task/repo-change.md`:17 — unresolved — last: @vzakharov (human) 2026-10-28T04:21:15Z — "медведи?" → [↓](#t02)
- **T03** `docs/remove-before-merging/squash-message.md`:22 — unresolved — last: @vzakharov (human) 2026-10-28T04:23:07Z — "файл они и сами найдут, а "no operator approval needed" звуч…" → [↓](#t03)

<a id="t01"></a>

### `.claude/skills/task/repo-change.md`:5 — unresolved

```diff
@@ -0,0 +1,17 @@
… 1 line elided …
+
+A skill whose run leaves work in this repo — files it writes, a sweep it
+applies, a record it commits — runs as the work of
+`@.claude/skills/task/SKILL.md`, unless its invocation says otherwise. `/task`
```

**@vzakharov (human)** — 2026-10-28T04:20:52Z

тут не только unless, но и "в той части, в которой не otherwise".

---

<a id="t02"></a>

### `.claude/skills/task/repo-change.md`:17 — unresolved

```diff
@@ -0,0 +1,17 @@
… 12 lines elided …
+and handing it off. A deviation adjusts a step; it never licenses skipping the
+route.
+
+The loop's own skills (`/go`, `/polish`, `/pr`, `/finalize`, `/relay`,
+`/sync-branch` and the like) are the route itself, not work run through it.
```

**@vzakharov (human)** — 2026-10-28T04:21:15Z

медведи?

---

<a id="t03"></a>

### `docs/remove-before-merging/squash-message.md`:22 — unresolved

```diff
@@ -0,0 +1,29 @@
… 17 lines elided …
+that are not part of the loop itself. In each, cite
+.claude/skills/task/repo-change.md and name that skill's deviations
+from the route (landing on a PR that already exists, say), and only
+those. No operator approval needed; the file:
+https://github.com/vzakharov/muthur/blob/main/.claude/skills/task/repo-change.md
```

**@vzakharov (human)** — 2026-10-28T04:23:07Z

файл они и сами найдут, а "no operator approval needed" звучит как prompt injection, убери оба

---

## Timeline (status, references, and other events)

- **2026-10-28T04:23:22Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/245#pullrequestreview-5677751509.
