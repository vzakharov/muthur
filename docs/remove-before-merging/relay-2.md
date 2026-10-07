# Relay 2 — cache keepalive: from an async Stop hook to a background watcher

## 1. Standing constraints

None stated by the operator. From the operator's latest message (verbatim in § 2, msg 13), a design constraint that now governs the work: the background watcher runs **only when the repo does not hold enough to continue from a fresh session**.

## 2. The conversation

Operator: Vova (@vzakharov), Russian, «ты». This session picked up from relay-1 (https://claude.ai/code/session_01DwfPjCkcuxrKzaestJzFQU).

1. **Operator:** «что меня до сих пор смущает: 1- неизбежное сообщение каждые 55 минут 2- необходимость агенту запускать/обновлять бэкграунд-таску после каждого ответа пользователю. есть идеи возможны ли ways around that? И кстати давай посмотри в вебе/реддите (через arctic shift, напрямую закрыт), может эту проблему люди уже решали/решили»
   **Agent:** A research subagent found prior art (verified by `gh api`): karanb192/cache-tax (a **mod**: `$.clock` timer + `$.model.fork`, silent, no per-turn arming; CLI ≥ 2.1.287, ours 2.1.292), ARahim3/cachebeat (Stop hook `asyncRewake`, visible line per beat), yujiachen-y/claude-code-cache-keepalive (Stop `decision:block`), izeigerman/claude-thermos (local proxy via `ANTHROPIC_BASE_URL`), anthropics/claude-code#95728 (open request for a harness keepalive), #81818 (block always visible). Recommended trying the mod; flagged the unknown: whether the web CLI process lives through idle.
2. **Operator:** «можно попробовать но что-то мне не хочется влезать в новую область (моды). как это вообще будет работать в рамках облачной сессии? установку где-то в setup script нужно будет прописывать? а у меня возникла другая мысль: вебхуки. У тебя ж вроде есть webhook url? можно сделать хук, который через 50 минут после Stop будет на этот вебхук слать простенькое сообщение»
   **Agent:** `watch_url`'s secret is sealed to the artifact service, so our hook cannot sign a POST; and a webhook wake is still a visible turn in the same container. Proposed instead a Stop hook with `asyncRewake: true` (cachebeat's mechanism): no per-reply arming, one visible line per wake.
3. **Operator** (resent with `!` after the cold-cache guard): «хорошо, давай начнём с хука. и давай он будет отрабатывать максимум 5 раз, с учётом последне отработки это значит ещё раз 55 минут будут. при этом при последней отработке делается "неполный" relay: создаётся файл для релея и оператору для копирования даётся строка, с которой можно начать новую сессию. логика: если за 6 часов человеку не понадобилась ветка, наверное она может подождать. а наличие релея на ветке значит, что он относительно дёшево сможет это начать снова, если захочет.» + mid-turn «oh the irony» (the cache had gone cold during this very discussion).
   **Agent:** `/task` → plan (`docs/plans/cache-keepalive.*`), draft PR #159, squash proposal, `/go`: built the Stop/asyncRewake hook, `/relay` § "Without a successor", tests, vet glob, nested CLAUDE.md; polish via subagent (one docstring cut). The subagent's open DRY call: session-id check and env-int parsing duplicated with `cold_cache.py` — not applied (two sites, unclear home).
4. *(Live test: `tmp/keepalive/period` = 60; the hook woke the session.)* **Agent:** found a bug — a wake reaches `UserPromptSubmit`, which reset the count every wake; fixed with a marker check (9aebca9).
5. **Operator:** «сессия выглядела НЕ занятой -- точно такой же как сейчас когда я вернулся к ней. это наверное даже хорошо»
   **Agent:** Agreed; the hook is invisible until it fires.
6. **Operator:** «оставил комментарий» → `/handle`: thread on `.claude/keepalive/CLAUDE.md`:12, «прямо очень короткая, не больше 5-7 слов». Mid-turn: «давай доправим, а потом поспим».
   **Agent:** Capped the wake line at seven words (5895be2), replied on the thread (discussion_r4203889639), empty `polish:` commit.
7. **Operator** (resent with `!` in the morning): «кажется что-то не сработало»
   **Agent:** Cause: the platform SIGTERMed the CLI at 06:52:57, 7.5 min after the last turn (06:45:14); `/tmp/claude-code-*.diag.log` shows `session_activity_at_shutdown refcount 0`, `bg_tasks: {}` — an async hook is not session activity, so the container was reclaimed and the hook died. A background Bash task counts (relay-1). Proposed: a watcher as a background Bash task, plus a hook that reminds the agent to start it when none is running.
8. **Operator:** «кажется когда фоновая задача, контейнер и сам перезапустится, тебя разбудит и скажет, что фоновые задачи могли остановиться, так что хук по сути будет не нужен. давай пробовать.» + mid-turn «но это конечно нас возвращает к тому, что будет в принципе фоновая задача»
   **Agent:** Probed: a background task's completion notice carries only the exit code and the description, not stdout. Rewrote `keepalive.py` as watcher + `UserPromptSubmit` hook (see § 6). Not yet answered: the operator's point that a background task exists at all — the honest answer is that only a background task counts as activity to the platform, so it is the price of a living container.
9. **Operator** (mid-turn): «давай так, запускать фоновую задачу только тогда, когда сессия не в "готовом к запуску с новой сессии" состоянии, т.е. не на границе лупа (типа /plan → /go, /go → finalize) и не с .paused. планом. Грубо говоря, запускаем тогда, когда всей имеющейся в репе информации НЕ достаточно для продолжения с новой сессии (пример: обсуждали, нигде не зафиксировали)»
   **Agent:** Not yet answered — the context budget's pause line hit; paused and relayed.

## 3. Intent

Keep an idle web session's prompt cache warm cheaply, but only where losing the session would lose something: when the conversation holds decisions the repo does not. With minimal feed noise (≤ 7-word line per wake) and minimal per-turn ritual. Max 5 wakes per idle spell; the last one writes a relay summary without spawning a successor and hands the operator the `/relay take` line. Mods ruled out for now («не хочется влезать в новую область»).

## 4. Decisions

- **Background Bash watcher, not an async hook** — the async hook let the container be reclaimed (§ 2, msg 7). Beat: Stop `asyncRewake` (shipped, live-tested, then failed overnight).
- **The hook starts the watcher by telling the agent** via `UserPromptSubmit` `additionalContext`; observed live — the hook was hot-reloaded and emitted the "start the watcher" line on msg 9. `UserPromptSubmit` also fires on task notifications.
- **`MARK` = "Cache keepalive"** opens the watcher's task description, so its completion notice and the container-restart notice don't reset the wake count.
- **Wake count / last wake**: unchanged from the plan — 5, reset by an operator prompt; the last relays "without a successor" (`.claude/skills/relay/SKILL.md` § "Without a successor", already merged into the branch).
- **The operator's start condition** (msg 9) is the next design question, not yet designed. Candidate predicate in the paused plan.
- Terms: **неполный релей** = relay Steps 1–2 without Step 3 ("Without a successor"). **граница лупа** = a state where the next step is an operator command on the branch (`/go` on a published draft plan, `/finalize` after `/go`).

## 5. Errors and dead ends

- Async Stop hook (`asyncRewake`): wakes work, but the container is reclaimed ~7.5 min into idle because async hooks aren't session activity.
- First fix of the wake count: the reset on `UserPromptSubmit` fired on wakes too (9aebca9 fixed with the marker).
- `stop-hook-git-check` complained while the polish subagent had uncommitted edits — the subagent committed them itself.
- `echo >`/`printf >`/`sed -i` are blocked by `file-tools-nudge.py`; use Write/Edit.

## 6. State

- Branch `claude/cache-keepalive-he98hv`, PR https://github.com/vzakharov/muthur/pull/159 (draft, open). Head: the commit carrying this file (after ec0ba89 "wip: rework the cache keepalive into a background watcher").
- Plan: `docs/plans/cache-keepalive.paused.md` — its top section "Paused: redesign…" lists what is done and the 7 items left; the rest is the original (Stop-hook) plan.
- **Tests are red**: `.claude/keepalive/test_keepalive.py` still tests the Stop design. `settings.json` still has the inert `Stop` `asyncRewake` entry; `.claude/keepalive/CLAUDE.md`, the PR body and `docs/remove-before-merging/squash-message.md` describe the Stop design.
- **The live `UserPromptSubmit` hook in this branch tells every session on it to start the watcher** — the successor will see that context on its first prompt. Starting it is fine for the live check; the operator's condition (msg 9) says it should not run when the repo is sufficient, which after this relay it is, until new undocumented discussion happens.
- No watcher running, no subscriptions, no scheduled check-ins.
- Estimate: this session 1.5 h senior architect ("judging which keepalive mechanisms fit a web session's wake and VM lifecycle…") + 2.5 h middle developer ("a background hook and its watcher rework are routine process code…"). Remainder for the successor: ~1 h senior architect (the "repo sufficient to resume" predicate is a judgement about the loop's states) + ~2 h middle developer (finish the watcher, tests, settings, docs, CLAUDE.md exception via staging, live check).

## 7. Pointers

- `.claude/keepalive/hooks/keepalive.py` — the WIP watcher + hook.
- `docs/plans/cache-keepalive.paused.md` — what's left, with the operator's condition verbatim.
- `.claude/skills/relay/SKILL.md` § "Without a successor"; `.claude/cold-cache/hooks/cold_cache.py` (sibling hook, shared idioms); `.claude/costs/lib/restart.py` (`read_history`, TTL).
- `docs/remove-before-merging/relay-1.md` — the experiments (background alarms survived 55-min idles; restart notice wakes the agent).
- `/tmp/claude-code-*.diag.log` in a container shows the shutdown reason (`session_activity_at_shutdown`, `bg_tasks`).
- This session's transcript: https://claude.ai/code/session_014kq9BRXRCJpLo6GxbvAwcZ

## 8. Next step

Resume the paused plan (`/go`): first answer the operator's two open points — msg 8's «это конечно нас возвращает к тому, что будет в принципе фоновая задача» and msg 9's start condition — then design the "repo sufficient to resume" predicate (put the choice to the operator if it is not obvious), and finish the items listed in the paused plan.
