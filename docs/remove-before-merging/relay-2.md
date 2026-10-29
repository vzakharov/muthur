# Relay 2 — steno (parked)

## 1. Standing constraints

None stated by the operator.

## 2. The conversation

**Operator (launch prompt):**
`/relay take claude/haiku-edit-relay — первая версия режима готова в PR #254, дальше переименование в steno, прогноз по волнам и журнал «прогноз против факта» на cost-ledger`

**Agent:** picked up relay 1 and resumed the paused plan. It renamed the mode to
steno and dictated the rename to Haiku as a second dogfood: 29 of 30 items
applied, one skipped after a formatter re-wrap. It rewrote `steno.md` around
waves and the "notice, don't touch" brief, added `delegation.py --forecast` and
the wave rows on `cost-ledger`, and filed the first row. Then it ran `/polish`
and refreshed the PR body, title and squash proposal. The report declined
`/polish`'s one open `/dry` call, a shared current-transcript helper, and closed
on: «Если всё устраивает, дальше `finalize`.» (verbatim in Last agent turn)

No operator message followed; the keepalive's last wake parked the session.

## 3. Intent

An experimental, default-off `/go` mode (steno) where Opus dictates every edit
and a Haiku subagent applies them. It is turned on only when a forecast says it
pays, and the forecasts are calibrated over time against measured costs.

## 4. Decisions

- **Name: steno** — `MUTHUR_STENO`, `.claude/skills/go/steno.md`. Vova steered
  it: «по названию, думаю лучше отталкиваться от "стенографировать"». "Relay"
  was out because it collides with `/relay`.
- **Wave** — one dictation: dictate → Haiku applies → review. The forecast
  prices a wave as two delegator context re-reads plus Haiku's run, and direct
  editing as one re-read per turn. Output is left out of both, since the edits'
  text costs the same either way.
- **Ledger rows for waves** go on the existing `cost-ledger` branch under
  `.claude/costs/delegations/<YYYY-MM>/<agent-id>.json`, outside `sessions/` so
  `report.py` does not double-count them. A second auto-branch was the
  alternative; Vova never chose between them, and the recommendation stood.
- **Rows are written at weighing time**, not at forecast time.
  `delegation.py <agent-id> --turns n --waves w` records the forecast priced at
  the launch context beside the measured figures. The plan had "forecast writes,
  weighing completes"; the agent id is unknown before launch, so one write
  replaced two.
- **Haiku run in the forecast**: the mean of measured rows, the row being
  weighed left out, seeded at $0.06.
- **Declined /dry call**: a shared `current_transcript` helper for `oriented.py`
  and `delegation.py`. Two callers that handle a missing transcript differently
  make it a small saving.

## 5. Errors and dead ends

- The formatter re-wraps a Markdown paragraph after each Haiku edit, so a later
  anchor that spans a line break in the same paragraph goes stale. This is now a
  rule in `steno.md` § "The list".
- `delegation.py`'s in-session replay ($0.75 for 5 turns) overstates direct cost
  when the delegator has already read the files. The forecast's direct side
  ($0.165) counts re-reads only. Both figures are on the row, for calibration.

## 6. State

- Branch `claude/haiku-edit-relay`, head 73b61b7 pushed before this summary's
  commit.
- PR #254 is open as a draft, MERGEABLE/CLEAN, retitled "feat: steno — an opt-in
  /go mode where Haiku applies dictated edits", with the body refreshed and the
  squash proposal comment updated.
- Plan: `docs/plans/haiku-edit-relay.completed.md`. Item 7 (the `haiku` entry in
  `delegation-model-capabilities.md`) waits on #253.
- Ledger: `cost-ledger` holds the first wave row,
  `delegations/2026-10/a0ab1855b74695b6e.json`.
- Estimate: 1 h senior prompter + 2.5 h senior developer + 1 h senior analyst,
  kept: this session did the whole remainder. Nothing is handed on beyond
  `/finalize`.
- Nothing is running; the keepalive has stopped.

## 7. Pointers

- `.claude/skills/go/steno.md` — the procedure.
- `.claude/costs/delegation.py`, `.claude/costs/lib/delegations.py`,
  `.claude/costs/test_delegation.py` — the forecast and wave rows.
- `.claude/costs/CLAUDE.md` § "Where rows live" — the paragraph on steno rows.
- `git show origin/cost-ledger:.claude/costs/delegations/2026-10/a0ab1855b74695b6e.json`
  — the first row.
- `docs/remove-before-merging/squash-message.md`.
- This session: https://claude.ai/code/session_01DaohkC8CqD2FqWtVHR6BSe;
  predecessor: https://claude.ai/code/session_01DaohkFQukaJRLHFoDBRyP8 (relay 1
  is `docs/remove-before-merging/relay-1.md`).

## 8. Next step

Wait for the operator. The report proposed `finalize` as the next step; it has
not been approved.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Прогноз и журнал волн написаны. Проверяю их на живой сессии.

Прогноз и журнал запушены, первая строка уже лежит на `cost-ledger`. Осталось: squash-сообщение, план, `/polish` и тело PR.

Step 3: polish.

Вова, всё из списка готово и запушено, кроме пункта 7. Он ждёт #253, потому что #253 переписывает запись про `haiku` в `delegation-model-capabilities.md`. PR остаётся черновиком:

https://github.com/vzakharov/muthur/pull/254

**Что сделано:**
- **Название.** Режим теперь steno: включается `MUTHUR_STENO=on`, процедура лежит в `.claude/skills/go/steno.md`. Старое «relay» в хуке, тестах, `/go` и каталоге заменено.
- **Волны.** `steno.md` считает расходы по волнам, а не по правкам. Волна — это «продиктовал → Хайку применил → проверил». Каждая волна дважды перечитывает мой контекст и платит за прогон Хайку. Прямая правка перечитывает контекст один раз за ход, зато находки по пути ловит бесплатно.
- **Бриф Хайку.** Было «не трогай, что заметил», стало «не трогай, но перечисли в отчёте».
- **Прогноз.** `delegation.py --forecast --turns N --waves W` считает обе цены по текущему контексту и говорит, какой вариант дешевле.
- **Журнал «прогноз против факта».** Отдельной автоветки нет: журнал живёт на `cost-ledger`, в папке `delegations/<месяц>/<agent-id>.json`. Это рядом с `sessions/`, поэтому `report.py` не засчитает траты дважды. Строку пишет взвешивание волны с флагом `--waves`. Следующие прогнозы берут цену прогона Хайку как среднее по измеренным волнам.

**Повторный догфуд.** Переименование я сам отдал Хайку списком из 30 правок, с якорями из grep, без чтения файлов целиком. 29 применены точно. Одну он честно пропустил: форматтер после предыдущей правки переложил переносы строк в абзаце, и якорь съехал. Хайку сам подсказал, как её доделать. Правило «второй якорь в том же абзаце — короткая фраза внутри одной строки» записано в `steno.md`.

**Первая строка журнала:** прогноз $0.127 за волну, факт $0.117. Для калибровки по одной точке астролог бы обрадовался, а статистик пока нет.

**Ещё:**
- `/polish` сделал две мелкие правки.
- Он же предложил вынести поиск транскрипта текущей сессии в общий хелпер для `oriented.py` и `delegation.py`. Я бы не стал: вызывающих два, и отсутствие транскрипта каждый обрабатывает по-своему.
- Тело PR, заголовок и предложение для squash обновлены.
- Тесты `test_delegation.py` и `test_go_delegation.py` проходят. Полный `vet.sh` я не гонял, это работа `/finalize`.

Если всё устраивает, дальше `finalize`.
```
