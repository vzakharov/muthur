# PR #108: feat: #107 route the first change-asking turn, wherever it falls

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/108
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/mid-session-routing-jgtiin
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-24T17:49:53Z
- **Updated:** 2026-09-24T18:16:16Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **The gap:** the routing ladder fired only on a session's opening prompt, and "continued work" began once a plan was being implemented. A session that opened with a question and then turned into changes was neither, so `/task`'s plan-or-not call, `/polish` and `/pr` never ran.
- **The rule:** the first turn that asks for a change is a routing point wherever it falls, tested by the same expected-deliverable rule applied per turn (a file in the repo is the switch; something in `tmp/` is not), and a session is continued work once routed. The `let's …` collision and the "no plan" override now key on routing rather than on launch. The `CLAUDE.md` edit sits in `.claude/staged/CLAUDE.md.staged`; `/finalize` swaps it in.
- **Pointers updated:** `/task`'s intro, `/plan`'s § "Scope", and the header of `prompt-route-notice.sh`.
- **The hook's behaviour is unchanged:** it still fires only on the first prompt. Telling a change-asking follow-up from a question means reading the conversation, and a notice on every later prompt would cost a Q&A session context on every turn.

## QA Checklist

- [ ] `question-then-change` — open a session with a question ("what would it take to add X?"), let it answer, then ask "ok, add it": the agent says it is routing to `/task`, makes the plan-or-not call, and ends with `/polish` and a draft PR.
- [ ] `tmp-not-switch` — in a question session, ask for something whose answer lands only in `tmp/` (a probe, a spike): no routing happens.
- [ ] `routed-followup` — after a `/task`-routed change, ask for a further tweak: it is handled directly, with no second `/task` call and no plan cycle.
- [ ] `lets-draft` — with a draft plan waiting, "let's go" is still read as approval; in a session that hasn't been routed, "let's add X" routes to `/task`.
- [ ] `hook-first-only` — the route notice appears on the opening prompt only, not on later prompts.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `question-then-change` | manual-only | — | Agent judgment over a live conversation |
| `tmp-not-switch` | manual-only | — | Agent judgment over a live conversation |
| `routed-followup` | manual-only | — | Agent judgment over a live conversation |
| `lets-draft` | manual-only | — | Agent judgment over a live conversation |
| `hook-first-only` | integration | — | Feed the hook a payload whose transcript holds an assistant turn and assert it prints nothing; behaviour unchanged here |

Closes #107

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-24T17:50:04Z — "Proposed squash title/body: ``` feat: #107 route the first c…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-24T17:50:04Z

[https://github.com/vzakharov/muthur/pull/108#issuecomment-5819250504](https://github.com/vzakharov/muthur/pull/108#issuecomment-5819250504)

Proposed squash title/body:

```
feat: #107 route the first change-asking turn, wherever it falls (pr #108)
```

```
The routing ladder fired only on a session's opening prompt, and
continued work began once a plan was being implemented. A session that
opened as a question and then turned into changes was neither: it was
never routed, so /task's plan-or-not call, /polish and /pr never ran,
and the operator found commits with no PR behind them.

The first turn that asks for a change is now a routing point wherever
it falls, judged by the ladder's expected-deliverable test applied to
that turn: a file landing in the repo is the switch, something left in
tmp/ is not. A session is continued work once routed, and the `let's`
collision and the "no plan" override key on routing rather than on
launch. /task, /plan's Scope and the route-notice hook's header follow.

The hook still fires on the first prompt only. Telling a change-asking
follow-up from a question takes reading the conversation, so that call
is the agent's; a notice on every later prompt would cost a Q&A session
context on every turn.

Closes #107

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-09-24T18:16:13Z — "я бы сказал это fix, так как изначальный intent был именно т…" → [↓](#t01)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,33 @@
+Proposed squash title/body:
+
+```
+feat: #107 route the first change-asking turn, wherever it falls (pr #108)
```

**@vzakharov (human)** — 2026-09-24T18:16:13Z

я бы сказал это fix, так как изначальный intent был именно такой (и на опыте многие агенты это понимали и без дополнительных пояснений. но вот не все)

---

## Timeline (status, references, and other events)

- **2026-09-24T18:16:16Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/108#pullrequestreview-5308386270.
