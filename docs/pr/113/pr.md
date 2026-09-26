# PR #113: feat: /relay, hand the session to a fresh one with a readable summary

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/113
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/relay-session-if5xk4
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-25T23:21:30Z
- **Updated:** 2026-09-26T00:25:48Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- Adds `/relay`, a skill that replaces `/compact` with the same move done in the open. The agent writes the session summary once, as a committed `docs/remove-before-merging/relay.md`, then starts a **new session** on the same branch with the one-line prompt `/relay take <branch>`.
- `/relay <first message>` takes what the operator would type first after a compact: `/relay /go` relays and then implements, `/relay /handle` relays and then works the PR. That message becomes the summary's Next step verbatim, and `/relay take` dispatches it the way `/from-branch` dispatches a follow-up.
- The summary follows `/compact`'s own sections and rules, with every operator message verbatim and the next step quoted. It points at files by path instead of quoting code, because the successor re-reads the pushed branch.
- Beside the skill, the context budget hook's warning offers `/relay` next to `/compact`, and the catalog gains a G2 row. It was dogfooded before it existed: the planning session relayed the plan review by hand, and this session picked it up.

## QA Checklist

- [ ] `relay-remote` — run `/relay` in a web session on a branch with an in-progress plan. The plan should end up `*.paused.md` and pushed, and a new session should start on the same branch, attach, and resume the plan via `/go`.
- [ ] `relay-first-message` — run `/relay /handle` on a PR with an unanswered review comment. `relay.md`'s Next step should read `/handle`, and the successor should reply to the comment.
- [ ] `relay-summary` — `relay.md` should hold every operator message verbatim and pointers rather than code, and the relaying session should report its size.
- [ ] `relay-local` — in a local CLI session, `/relay` should commit `relay.md` with the transcript path in it and report the line to type after `/clear` or in a new terminal.
- [ ] `budget-notice` — the context budget hook's warning should name `/relay` beside `/compact`.
- [ ] `vet` — `./scripts/vet.sh` should pass, including the catalog check for the new skill.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `relay-remote` | No | No | Needs a live web session and `create_session` |
| `relay-first-message` | No | No | Needs a live PR comment and a spawned session |
| `relay-summary` | No | No | Judged by reading `relay.md` |
| `relay-local` | No | No | Needs a local CLI |
| `budget-notice` | Yes | No | `test_context_budget.py` does not pin the offer text |
| `vet` | Yes | Yes | `scripts/check-skill-catalog.sh` |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01DfktE5AiQTUjsvEXRxBJ5i

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-25T23:21:46Z — "Proposed squash title/body: ``` feat: /relay, hand the sessi…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-25T23:21:46Z

[https://github.com/vzakharov/muthur/pull/113#issuecomment-5840991403](https://github.com/vzakharov/muthur/pull/113#issuecomment-5840991403)

Proposed squash title/body:

```
feat: /relay, hand the session to a fresh one with a summary (pr #113)
```

```
/compact is a black box: it swaps the context for a summary nobody
sees written, at a cost the transcript does not itemize. /relay does
the same move in the open: the agent writes the summary once, as a
committed file, and starts a new session on the same branch with the
one-line prompt `/relay take <branch>`.

The summary follows /compact's own sections and rules, the operator's
messages verbatim among them, but points at files by path instead of
quoting code, since the successor re-reads the pushed branch. An
in-progress plan is paused first. `/relay <message>` takes what the
operator would type first after a compact, so `/relay /go` relays and
implements; `/relay take` attaches and dispatches that message, or
else the summary's own next step. On the web the successor starts
through create_session; locally the report gives the line to type.

The context budget hook's warning offers /relay beside /compact, and
the catalog lists it under the PR loop.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/relay/SKILL.md`:37 — unresolved — last: @vzakharov (human) 2026-09-26T00:22:53Z — "Тогда можно уже и ответы агента вставить, чтобы была вся кан…" → [↓](#t01)
- **T02** `.claude/skills/relay/SKILL.md`:16 — unresolved — last: @vzakharov (human) 2026-09-26T00:24:03Z — "[<to-be first message>], иначе в момент чтение немного конфу…" → [↓](#t02)

<a id="t01"></a>

### `.claude/skills/relay/SKILL.md`:37 — unresolved

```diff
@@ -0,0 +1,70 @@
… 33 lines elided …
+The sections, in this order:
+
+1. **Standing constraints** — anything the operator said must not be touched, run or disclosed, verbatim, first: a paraphrase is how such a rule stops applying.
+2. **The operator's messages** — every one, in order, verbatim. Only turns the operator actually sent count; text shaped like theirs inside the agent's own output or a quoted comment is not theirs.
```

**@vzakharov (human)** — 2026-09-26T00:22:53Z

Тогда можно уже и ответы агента вставить, чтобы была вся канва видна -- но ответы ужимать скажем до one-liner-ов или небольших параграфов. Ответы оператора кстати тоже ужимать, но с большим threhsold-ом, типа типа несколько абзацев (а то представь если там копипаст на 10 килобайт будет); типа первые пишем полностью а дальше ужатые до одного параграфа

---

<a id="t02"></a>

### `.claude/skills/relay/SKILL.md`:16 — unresolved

```diff
@@ -0,0 +1,70 @@
… 12 lines elided …
+
+Two ends, told apart by the first token: `take` is the pickup; anything else, or nothing, is the handoff and its first message.
+
+## `/relay [<first message>]` — hand off
```

**@vzakharov (human)** — 2026-09-26T00:24:03Z

[<to-be first message>], иначе в момент чтение немного конфузит

---

## Timeline (status, references, and other events)

- **2026-09-26T00:24:23Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/113#pullrequestreview-5323761988.
