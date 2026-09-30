# PR #103: feat: /task gates on how far apart the alternatives land

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/103
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/switch-distance-gate-vqoi2a
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-23T13:56:21Z
- **Updated:** 2026-09-30T17:19:27Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- `/task` Step 3's third sign asked whether a step was "irreversible", which is never true on a git branch: any commit reverts. It now measures **distance**: build the plan's choice, picture the operator asking for the next-best option after reading the diff, and count what that switch rewrites.
- The sign keeps both of the old criterion's cases: work built on the choice before the PR is read grows the distance, and a step off the branch (a filed issue, a posted comment, a deploy) has nothing on the branch to rewrite, so it counts as farthest of all.
- The closing line of Step 3 now says the gate is for what a diff review could only change by rewriting the diff.

## QA Checklist

- [ ] `near` — Launch a session with a small task whose only fork is a default value or a name; the agent reports outcome 2 or 3 (no gate) and does not cite the distance sign.
- [ ] `far` — Launch a session with a task whose fork decides a data shape or file layout that later code reads; the agent's Step 3 call cites the distance sign and hands off at `/plan` § "Handing off".
- [ ] `off-branch` — Launch a task that files an issue or posts to an external service as part of the work; the agent treats that step as gate-worthy.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `near` | manual-only | — | Judgment call by the agent over prose; no harness to assert it |
| `far` | manual-only | — | Same |
| `off-branch` | manual-only | — | Same |

https://claude.ai/code/session_01AHFC2mYwySrewzifgqr4Yt

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-23T13:56:35Z — "Proposed squash title/body: ``` feat: /task gates on how far…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-23T13:56:35Z

[https://github.com/vzakharov/muthur/pull/103#issuecomment-5796158173](https://github.com/vzakharov/muthur/pull/103#issuecomment-5796158173)

Proposed squash title/body:

```
feat: /task gates on how far apart the alternatives land (pr #103)
```

```
/task Step 3 decides whether a plan waits for the operator, and one of
its signs asked whether a step was irreversible. On a git branch nothing
is: any commit reverts, so the sign never fired on what it was meant to
catch.

The sign now measures distance. Build the plan's choice, picture the
operator reading the diff and asking for the next-best option, and
count what that switch rewrites: a default value is a line apart, a
data shape later files read is the whole branch apart, and the gap
grows with each commit built on the choice before review. A step off
the branch (a filed issue, a posted comment, a deploy) has nothing on
the branch to rewrite and counts as farthest. The step's closing line
says the gate is for what a diff review could only change by rewriting
the diff.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/task/SKILL.md`:52 — unresolved — last: @vzakharov (human) 2026-09-30T17:19:17Z — "давай не будем давать какую-то подробную эвристику, что тако…" → [↓](#t01)

<a id="t01"></a>

### `.claude/skills/task/SKILL.md`:52 — unresolved

```diff
@@ -49,10 +49,10 @@ Now the plan exists, so the question is asked against it rather than forecast fr
… 1 line elided …
 - **The work costs far more to produce than to describe.** The plan is a page, the work is a day, and a wrong direction is caught for the price of the page.
 - **A fork carries no recommendation** — the exception in `@.claude/skills/plan/SKILL.md` Part 2. Guess wrong and most of the work is wasted; the plan is what makes the choice the operator's.
-- **A review round comes too late.** The step is irreversible or outward-facing, or later work builds on it before the PR is read.
+- **The alternatives land far apart.** Measure the gap: build the plan's choice, then picture the operator reading the diff and asking for the next-best option, and count what that switch rewrites. A default value is a line apart; a data shape every later file reads is the whole branch apart, and grows with each commit built on it before the PR is read. A step off the branch — a filed issue, a posted comment, a deploy — is not on the branch to rewrite, so it counts as farthest of all.
```

**@vzakharov (human)** — 2026-09-30T17:19:17Z

давай не будем давать какую-то подробную эвристику, что такое "far apart", иначе рискуем не додуматься до каких-то эдж кейсов. Думаю, агентам хватит собственных мозгов, чтобы оценить это в каждом конкретном случае, исходя из обстоятельств

---

## Timeline (status, references, and other events)

- **2026-09-30T17:19:27Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/103#pullrequestreview-5369620080.
