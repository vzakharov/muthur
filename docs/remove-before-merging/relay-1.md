# Relay 1 — agent active time and speedup (parked)

## Standing constraints

None stated.

## The conversation

1. **Operator** (opening prompt):

   > давай запоминать время, которое агент реально потратил: 1- при начале
   > работы хук, начать считать 2- при ответе юзеру хук, перестать считать 3- в
   > леджере также просчитывать и указывать во сколько раз быстрее
   > "человеческой" прикидки получается (складывая все человеческие по данной
   > сессии) 4- в общем отчёте соответственно то же (там где считалось) 5-
   > keepalive watcher надо исключать, но другие фоновые задачи -- нет
   >
   > если что-то упускаю, дай знать

   **Agent:** routed via `/task` → plan and hand off. Renamed the branch, wrote
   the draft plan, opened draft PR #238. Proposed deriving the clock from
   transcript timestamps at the `Stop` hook instead of hook-held state (resume
   in a fresh container empties `tmp/`, `Stop` does not fire on an interrupted
   turn, background tasks end with no hook). Asked four numbered questions:
   background-task time counted while the agent idles; wall-clock vs summed
   agent-seconds for parallel work; whether the keepalive's parking wake counts;
   plain hours vs senior-hours for the ratio. Listed misses: permission-prompt
   waits count as work, old rows have no clock, the ratio is only as good as the
   estimate.

2. **Operator:**

   > 1 насколько будет программно сложно сделать типа "считать до 20 минут",
   > если дольше, останавливаем и считаем что агент пошёл на перекур. если для
   > этого нужно поднимать новую задачу на 20 минут (в конце которой сбросить)
   > то не надо 2а wall time, конечно 3 засчитать с момента пробуждения до
   > момента парковки 4 с весом грейдов, да. или это математически невозможно?

   **Agent:** collapsed the plan to those answers and pushed it. The 20-minute
   cap is plain arithmetic over timestamps at `Stop`, with no timer and no extra
   task; any record from the main or a subagent transcript counts as a sign of
   life. Flagged its one cost: a silent `run_in_background` command longer than
   20 minutes is cut to 20 (offered to exempt such commands on request; no
   answer yet). Grade weighting is possible but changes the figure's meaning to
   senior-hours per agent hour (multipliers are pay rates, not speed); the row's
   value is a write-time snapshot and the report re-rates it. Raised the
   estimate to 7 h senior developer + 1 h senior editor. (verbatim in Last agent
   turn)

## Intent

Measure the wall-clock time the agent actually works per session, and show in
each ledger row and in `report.py` how many senior-hours of the human estimate
each agent hour buys. Exclude the cache keepalive's idle watcher; keep every
other background task.

## Decisions

- **The clock is derived from the transcript at `Stop`, not kept in hook
  state.** Beat a `UserPromptSubmit` start mark + `Stop` delta in `tmp/`, which
  breaks on a fresh-container resume, an interrupted turn, and background tasks
  that end without a hook. The operator did not object.
- **Wall-clock union** for parallel work (operator: "2а wall time, конечно"),
  beating summed agent-seconds.
- **Idle cap**: a gap longer than 20 minutes between consecutive records counts
  as 20 (operator's "пошёл на перекур"). It needs no timer task, which the
  operator ruled out if it had been needed.
- **Keepalive**: the watcher's interval and renewal wakes are excluded; the
  parking wake counts from wake to the end of `/relay park` (operator: "3
  засчитать с момента пробуждения до момента парковки"), told apart by its
  running the `relay` skill.
- **`speedup` is grade-weighted**: `senior_hours(estimate)` ÷ active hours
  (operator: "4 с весом грейдов, да"), beating plain hours. Stored in the row as
  a write-time snapshot under the then-current rates; `report.py` re-rates from
  the parts.

## Errors and dead ends

None.

## State

- Branch `claude/agent-active-time-9rexw4`, renamed from
  `claude/focused-brown-9rexw4`.
- Draft PR https://github.com/vzakharov/muthur/pull/238, with the squash
  proposal comment posted and tracked in
  `docs/remove-before-merging/squash-message.md`.
- Plan: `docs/plans/agent-active-time.draft.do-not-implement.md`, still a draft.
  No go-ahead has been given.
- Nothing running. The keepalive watcher fired and parked this session.
- Estimate: this session revised to 1.5 h senior developer, for the design work.
  The remainder handed on is 6 h senior developer ("deriving wall-clock
  intervals from transcript turns, background tasks and subagent files has edge
  cases (interrupts, resumes, overlaps, idle cap, keepalive park) that need
  tested, judged handling inside an existing ledger contract") + 1 h senior
  editor ("the ledger's CLAUDE.md is a dense contract document; the new measure
  needs its limits stated as precisely as the rest").

## Pointers

- `docs/plans/agent-active-time.draft.do-not-implement.md` is the plan. Its
  first implementation step is to capture live record shapes (a background
  task's completion notice, `TaskStop`, an interrupted turn) into fixtures.
- `.claude/costs/CLAUDE.md` is the ledger's contract, and
  `.claude/keepalive/CLAUDE.md` with `hooks/keepalive.py` holds the watcher's
  `MARK`/`TASK` constants.
- This session's transcript:
  https://claude.ai/code/session_01DaohkB4R6fKQiSpfm6BJrN

## Next step

Wait for the operator. The plan awaits a go-ahead
(`/go claude/agent-active-time-9rexw4`). One question is still open: whether
silent `run_in_background` commands should be exempt from the 20-minute cap. The
plan applies the cap to them.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages,
usually unneeded but harmless; the reply proper is usually its last
paragraphs.

````text
Обновляю тело PR и предложенный squash-текст под твои ответы.

Всё четыре ответа внёс в план, кода по-прежнему нет.

**1. Предел в 20 минут почти ничего не стоит, и отдельная задача на 20 минут не нужна.** Время всё равно считается задним числом по меткам в транскрипте, когда срабатывает `Stop`. Поэтому правило сводится к арифметике: любая пауза между двумя записями сессии дольше 20 минут засчитывается как 20. Признаком жизни считается любая запись, в том числе из транскриптов субагентов. Заодно это лечит висящий запрос разрешения: ночь ожидания превращается в 20 минут, а не в восемь часов.

Цена у правила одна, и её стоит знать. Фоновая команда, которая долго молчит, тоже режется. Двухчасовой прогон тестов через `run_in_background` ничего не пишет в транскрипт до самого уведомления о завершении, поэтому засчитается как 20 минут. Фоновый агент так не пострадает: он пишет каждый шаг в свой транскрипт. Если это не годится, скажи, и молчащим фоновым задачам предел снимем.

**2. Время по часам: принято.** Три параллельных агента по 10 минут дают 10 минут.

**3. Парковку засчитываю от пробуждения до конца `/relay park`.** Холостые продления кэша, то есть однострочные ответы, по-прежнему исключены. Парковку от продления отличаю по тому, что в ней запускается скилл `relay`.

**4. Математически возможно, но меняется смысл числа.** Вместо «во сколько раз быстрее» получается «сколько senior-часов по оценке агент выдаёт за час работы». Множители грейдов в `rates.json` — это цена часа, а не скорость. Поэтому 10 часов джуна (×0.4) идут как 4 senior-часа, а 2 часа staff (×1.4) — как 2.8. Если вся оценка — senior developer, число в точности равно «во сколько раз быстрее».

Из этого следует одна деталь. Ускорение в строке — снимок на момент записи, как и доллары по `pricesAsOf`. Отчёт пересчитывает его по текущей таблице ставок, так что подкрученный множитель сдвигает всю историю одинаково.

Оценку задачи поднял с 6 до 7 часов senior developer: добавились чтение транскриптов субагентов и предел пауз.

https://github.com/vzakharov/muthur/pull/238

Чтобы реализовать, начни новую сессию с:

```
/go claude/agent-active-time-9rexw4
```
````
