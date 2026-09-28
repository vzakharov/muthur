# PR #109: feat: cold-cache guard, and a context budget priced off the warm-up

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/109
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/cold-cache-guard-ytr7vo
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-24T18:45:32Z
- **Updated:** 2026-09-28T07:55:11Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- Adds a hook pair that stops the first prompt after the prompt cache has expired, before it reaches the model, and prices the three ways on: carry on, `/compact`, or a new session, with how many requests the cheaper ones take to pay back. A blocked prompt makes no API request, so the stop itself costs nothing.
- Two sources of "cold": `SessionStart` on resume, which in the web client carries `prompt_cache_likely_expired`, `context_tokens` and friends, and the transcript's last response time, for a cache that expires while the process never restarts.
- The cost model lives in `.claude/costs/lib/restart.py`, priced from `.claude/costs/prices.json`. A new session is costed from this session's own warm-up — every response up to its first edit, commit or finished answer — with the calculator's estimates only before that point.
- The context budget's warning line moves off its fixed 200k to where a new session starts paying for itself within `CONTEXT_BUDGET_REQUESTS` (default 100) requests; the notice gives the break-even counts for a new session and for `/compact`. The line is cached per session, so the bash hook runs Python only while the warm-up is an estimate. The 300k pause stays fixed.
- Replaces the probe hook this branch used to establish how the web client renders a block and what `SessionStart` receives. The guard is catalog group G9, opt-in.

Plan: `docs/plans/cold-cache-guard.completed.md`

## QA Checklist

- [ ] `cold-return` — Leave a session over 1 h, then send a message: it is blocked with the idle time, the token count and the three prices.
- [ ] `resend` — Click Edit prompt and send the same message again: it goes through.
- [ ] `compact` — On a blocked return, send `/compact`: it runs without a block.
- [ ] `stop-word` — On a blocked return, a message containing `!pass` goes through first time.
- [ ] `warm` — Messages within the hour are never blocked.
- [ ] `small` — A session whose re-cache would cost under $0.30 is never blocked.
- [ ] `off` — `COLD_CACHE_GUARD=off` in `.claude/settings.local.json`'s `env` disables it.
- [ ] `priced-warn` — In a long session, the context budget warning arrives below 200k once the session has edited or committed, and names how many more requests a new session and `/compact` take to pay back.
- [ ] `fixed-warn` — With `CONTEXT_BUDGET_WARN` set, the warning arrives at that line instead.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `cold-return` | integration | ✅ | `test_a_cache_past_its_ttl_is_stopped_with_the_prices`, `test_a_resume_the_client_calls_expired_is_stopped_on_its_figures` |
| `resend` | integration | ✅ | `test_the_second_prompt_of_a_cold_spell_passes` |
| `compact` | integration | ✅ | `test_commands_and_the_stop_word_pass` |
| `stop-word` | integration | ✅ | `test_commands_and_the_stop_word_pass` |
| `warm` | integration | ✅ | `test_a_warm_cache_passes` |
| `small` | integration | ✅ | `test_a_cheap_recache_passes` |
| `off` | integration | ✅ | `test_off_disables_both_halves` |
| `priced-warn` | integration | ✅ | `ThePricedWarnLine` in `test_context_budget.py`; how the notice reads in the web client is manual |
| `fixed-warn` | integration | ✅ | `test_a_fixed_warn_line_set_by_hand_wins` |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01W5Z6hYnVH1dMZ9VQFNBpyH

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-24T18:45:54Z — "Proposed squash title/body: ``` feat: cold-cache guard, and…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-24T18:45:54Z

[https://github.com/vzakharov/muthur/pull/109#issuecomment-5820113322](https://github.com/vzakharov/muthur/pull/109#issuecomment-5820113322)

Proposed squash title/body:

```
feat: cold-cache guard, and a context budget priced off the warm-up (pr #109)
```

```
Coming back to a session after its prompt cache expired, the first
message re-caches the whole conversation, and nothing shows the price
before it is paid. A SessionStart/UserPromptSubmit hook pair now stops
that first message before it reaches the model and prices the three
ways on: carry on, /compact, or a new session, with how many requests
the cheaper ones take to pay back. A blocked prompt makes no request,
so the stop is free; resending, a /-command or !pass goes through.

Cold is read from two sources: SessionStart on resume, which carries
prompt_cache_likely_expired and context_tokens, and the transcript's
last response time, since the cache also expires while the process
never restarts. Rates come from .claude/costs/prices.json, and the
transcript's first response gives the warm prefix every session shares,
which the expiry leaves cached. A new session is costed from this
session's own warm-up: every response up to its first edit, commit or
finished answer, priced as billed.

The same model, in .claude/costs/lib/restart.py, moves the context
budget's warning line off its fixed 200k to where a new session starts
paying for itself within CONTEXT_BUDGET_REQUESTS (default 100)
requests, and the notice gives the break-even counts for a new session
and for /compact so the agent can weigh them against the work left.
The line is cached per session, so the bash hook starts Python only
while the warm-up is still an estimate; the 300k pause stays fixed.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/cold-cache/CLAUDE.md`:33 — unresolved — last: @vzakharov (human) 2026-09-28T07:42:09Z — "просто `!` (не `!pass`) -- должно расцениваться равносильно…" → [↓](#t01)
- **T02** `.claude/cold-cache/CLAUDE.md`:32 — unresolved — last: @vzakharov (human) 2026-09-28T07:45:26Z — "тут не уверен; например, стандартен запуск /go после плана,…" → [↓](#t02)
- **T03** `.claude/context-budget/CLAUDE.md`:4 — unresolved — last: @vzakharov (human) 2026-09-28T07:47:05Z — "а то где было 300к почему динамически не считаем? какие могу…" → [↓](#t03)
- **T04** `.claude/costs/lib/restart.py`:1 — unresolved — last: @vzakharov (human) 2026-09-28T07:51:00Z — "поскольку мейн теперь предлагает только /relay (который объе…" → [↓](#t04)
- **T05** `.claude/skills/update-muthur/catalog.md`:1 — unresolved — last: @vzakharov (human) 2026-09-28T07:54:48Z — "кажется, этот файл надо разбивать, по принципу того как разб…" → [↓](#t05)

<a id="t01"></a>

### `.claude/cold-cache/CLAUDE.md`:33 — unresolved

```diff
@@ -0,0 +1,39 @@
… 29 lines elided …
+  passes — so resending the refused prompt (Edit prompt, send) carries on. A new
+  response and a new gap re-arm it.
+- **What always passes:** a prompt starting with `/`, so `/compact` and every
+  other command can run; a prompt containing `!pass`; a session whose re-cache
```

**@vzakharov (human)** — 2026-09-28T07:42:09Z

просто `!` (не `!pass`) -- должно расцениваться равносильно повторению предыдущего промпта 1-в-1

---

<a id="t02"></a>

### `.claude/cold-cache/CLAUDE.md`:32 — unresolved

```diff
@@ -0,0 +1,39 @@
… 28 lines elided …
+  `tmp/cold-cache/<session_id>.blocked`, and a prompt against the same id
+  passes — so resending the refused prompt (Edit prompt, send) carries on. A new
+  response and a new gap re-arm it.
+- **What always passes:** a prompt starting with `/`, so `/compact` and every
```

**@vzakharov (human)** — 2026-09-28T07:45:26Z

тут не уверен; например, стандартен запуск /go после плана, /handle после исполнения, /finalize и т.п. Их пропускать по умолчанию как раз не надо. Кажется, нужно пропускать только /compact, /clear и /relay (если на твоей ветке такого ещё нет, посмотри можно ли безболезненно ребазнуть на мейн), потом всякие /usage / /context -- посмотри, какой исчерпывающий список должен быть

---

<a id="t03"></a>

### `.claude/context-budget/CLAUDE.md`:4 — unresolved

```diff
@@ -1,7 +1,7 @@
… 1 line elided …
 
 `hooks/post-tool-context-budget.sh` tells the agent when its session's context
-crosses 200k tokens (a warning) and 300k (the pause), so work is left resumable
+crosses the warning line and 300k tokens (the pause), so work is left resumable
```

**@vzakharov (human)** — 2026-09-28T07:47:05Z

а то где было 300к почему динамически не считаем? какие могут быть подходы тут?

плюс я оставил бы вариант с захардкоженными 200/300 под фича-флагом, на случай если вот всё это что мы тут напрограммировали не будет работать идеально

---

<a id="t04"></a>

### `.claude/costs/lib/restart.py`:1 — unresolved

```diff
@@ -0,0 +1,221 @@
+"""What each way on from a session costs — carry on, `/compact`, or a new
```

**@vzakharov (human)** — 2026-09-28T07:51:00Z

поскольку мейн теперь предлагает только /relay (который объединение /compact и new session) по сути, нужно считать из расчёта его. Кроме того, кажется, orientation тоже нужно отсчитывать по-другому для сессий, начавшихся с `/relay take` -- по сути, это будет уже reorientation.

(orientation -- тоже на мейне, возможно его у тебя тоже нет.)

что-то получаются достаточно drastic в сумме пересмотры, давай сделаем новый план на этой ветке про всё это.

---

<a id="t05"></a>

### `.claude/skills/update-muthur/catalog.md`:1 — unresolved

**@vzakharov (human)** — 2026-09-28T07:54:48Z

кажется, этот файл надо разбивать, по принципу того как разбили ADOPTING (8f0f29a). Тут уже не будем, но надо завести тикет

---

## Timeline (status, references, and other events)

- **2026-09-24T19:03:38Z** @vzakharov renamed from «feat: cold-cache guard hook» to «feat: cold-cache guard, and a context budget priced off the warm-up».
- **2026-09-28T07:55:10Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/109#pullrequestreview-5335349953.
