# Relay 1 — edit relay (to be renamed "steno")

## 1. Standing constraints

None stated by the operator.

## 2. The conversation

**Operator (via `/task`, sent from another session):** Vova's request, verbatim:

> интересно бы как вариант попробовать режим "опус перечисляет все необходимые
> правки с указанием файлов и передаёт их хайку": экономим раунд-трипы на каждом
> эдите. давай попробуем начать сессию завести (и сразу задогфудить) такой
> экспериментальный режим (в отличие от остальных энв должен быть default-off)

with pointers to `delegation.md`, `go-delegation.py`, the `haiku` entry in PR
#253 and vzakharov/vovazakharov.com PR #230.

**Agent:** plan-then-go; wrote the plan, opened draft PR #254, flipped it, wrote
`edit-relay.md`, then dogfooded: the hook switch, tests, `/go` Step 2 and the
catalog went to a Haiku subagent as one 16-item list — 16/16 applied exactly,
tests green, review changed nothing. Polished. Reported the cost as "a draw at
best" ($0.20 relay vs ~$0.19 direct, assuming one parallel turn).

**Operator:** почему ты называешь это "релей"? это же не то что у нас под этим
подразумевается? или я что-то упустил

**Agent:** admitted the collision with `/relay`; proposed **dictation**.

**Operator:** ещё поидеируем давай

**Agent:** listed candidates (dictation, amanuensis, stenographer/typist, punch
list, redline, errata, golem), grepped for collisions; recommended dictation for
the mode and "punch list" for the artifact.

**Operator:** > Столько же стоил бы один ход с параллельными Edit, и
edit-relay.md прямо называет этот случай невыгодным.

хм, а разве ты не гонял бы это по очереди: Edit (вывод, запись в кеш) -- чтение
кеша -- Edit (вывод, запись в кеш) -- и так times the number of edits?

**Agent:** agreed; recomputed: 16 sequential ≈ $0.61, per-file 4 turns ≈ $0.26,
parallel ≈ $0.19, relay ≈ $0.25; break-even ≈ 4 turns; realistic direct (5–8
turns) makes the relay 1.5–2× cheaper. Proposed fixing the PR body and the
"parallel Edit" paragraph.

**Operator:** так.. но и это тоже же ты сам можешь подсчитать? типа, какой-то
скриптик, ты ему на вход даёшь массив из (последовательных) массивов
(параллельных) строк xs/s/m/l/xl (по размеру правки) -- он сравнивает цену для
тебя и для хайку. если с хайку выгоднее, передаёшь. Хотя непонятно как оно может
быть НЕ выгоднее... hmmm

**Agent:** edit size barely matters (the text is paid as output once either
way); what matters is the delegator's turn count and context size against a
near-fixed relay fee (~$0.11). Break-even ~8 turns at 50k, ~4 at 125k, ~2–3 at
200k. Proposed `delegation.py --forecast --turns N` instead of the
array-of-arrays input.

**Operator:** а ты факторил-ин "править после хайку" и "что делать с штуками
которые обнаруживаются только по ходу выполнения"?

**Agent:** only half; discoveries were not factored. Proposed counting _waves_
(decide → Haiku → review), each paying the fixed fee, with discoveries becoming
the next wave; and a brief change from "fix nothing you notice" to "touch
nothing, but list it in the report". Asked to proceed.

**Operator:** согласен

по названию, думаю лучше отталкиваться от "стенографировать"

и ещё я думаю нам нужна автоветка типа cost-ledger, где прогноз будет
сравниваться с фактом, и потом через какое-то время, когда будет достаточно
данных, мы сможем откалибровать это всё

**Agent:** hit the context-budget warning; recorded all of it in the paused plan
and relayed. (verbatim in Last agent turn)

## 3. Intent

An experimental, default-off `/go` mode where Opus decides every edit and a
Haiku subagent applies them, worth turning on only when it actually saves money
— decided by a forecast, and calibrated over time by comparing forecasts with
measured costs.

## 4. Decisions

- **Name:** built on «стенографировать». Recommended: **steno** (`MUTHUR_STENO`,
  `.claude/skills/go/steno.md`). "Relay" is out — it collides with `/relay`.
  Dictation was the agent's earlier pick; Vova steered to stenography.
- **Hook:** extend `go-delegation.py` (a `files()` picking from two switches),
  not a second hook. With delegation off and steno on, the steno file and the
  model notes arrive.
- **No worktree, foreground Haiku**: it edits the session's tree, so nothing to
  merge.
- **Cost model in waves**, not edits — see the paused plan, item 2.
- **"Notice, don't touch"** in the brief — plan item 3.
- **Forecast** via `delegation.py --forecast --turns <n> --waves <w>` — plan
  item 4.
- **Forecast-against-fact rows**: recommended on the existing `cost-ledger`
  branch under its own tree, through `ledger.py`; a second branch is the
  alternative — plan item 5. Not yet confirmed by Vova which; the recommendation
  stands unless he says otherwise.

## 5. Errors and dead ends

- Naming the mode "relay" without checking the repo's vocabulary.
- Calling the dogfood "a draw at best" by comparing against an idealized single
  parallel turn; Vova pointed out real direct work is sequential.
- Ignoring discoveries made during editing in the cost model; Vova caught it.
  Dogfood evidence: Haiku left a stale "silent under `MUTHUR_DELEGATION=off`"
  two lines from its own catalog edit, by the brief; `/polish` caught it.

## 6. State

- Branch `claude/haiku-edit-relay`, head 4055f9f, pushed.
- PR #254, open, draft.
- Plan: `docs/plans/haiku-edit-relay.paused.md` — its "Status" section lists
  items 1–7 left.
- This session's estimate: 3 h senior prompter (procedure prose) + 1.5 h middle
  developer (hook switch and tests) + 1 h senior analyst (dogfood weighing).
- Remainder handed on: 1 h senior prompter (rename and the waves section of
  `steno.md`, which must hold for a model that cannot interpret) + 2.5 h senior
  developer (forecast over transcripts and ledger rows under the costs
  subsystem's filing and concurrency rules) + 1 h senior analyst (a wave cost
  model calibratable from the rows it files).
- Keepalive watcher was running in this session; nothing else waits.

## 7. Pointers

- `docs/plans/haiku-edit-relay.paused.md` — the remaining work, with reasoning.
- `.claude/skills/go/edit-relay.md` — the procedure to rename and extend.
- `.claude/hooks/go-delegation.py`, `scripts/test_go_delegation.py`.
- `.claude/costs/delegation.py` and `.claude/costs/CLAUDE.md` (ledger filing
  rules), `.claude/costs/ledger.py`, `.claude/costs/prices.json`.
- `docs/remove-before-merging/squash-message.md` — squash proposal to rename.
- Dogfood subagent id `a44002a392a64dcef` (16 items, $0.06 Haiku, brief $0.14).
- Predecessor transcript:
  https://claude.ai/code/session_01DaohkFQukaJRLHFoDBRyP8

## 8. Next step

Resume the paused plan: `/go` from its Step 1, working items 1–6 of the plan's
Status in order (rename to steno first; Vova: «по названию, думаю лучше
отталкиваться от "стенографировать"»; «нам нужна автоветка типа cost-ledger, где
прогноз будет сравниваться с фактом»). Dogfood steno again where a batch
qualifies, this time with structural anchors in files not yet read, and the
"notice, don't touch" brief.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Честно — наполовину. Правку после Хайку я учёл только как «пропущенный пункт стоит мне хода», и то по одному прогону, где правок не понадобилось. Находки по ходу работы я не учёл вообще, а это, похоже, главный расход.

**Почему находки важнее.** Когда правлю сам, следующую правку я пишу, глядя на результат предыдущей. Тест упал, форматтер сдвинул текст, рядом в соседней строке нашлось устаревшее утверждение — всё это я ловлю на месте. Relay требует решить всё заранее, вслепую, и сам этого замечания лишает. Хайку по брифу ничего сверх списка не трогает, да и по заметкам из #253 одинаковые дефекты в других местах не ищет.

**Это видно на нашем же догфуде.** В каталоге Хайку поправил строку о хуке, а в той же записи осталось «silent under `MUTHUR_DELEGATION=off`», хотя при включённом relay это уже неправда. Он оставил её строго по брифу. Ещё в список ушла моя ошибка в обосновании («relay picks its model from them»). Обе вещи поймал только `/polish` следующим проходом. Правь я сам, первую, скорее всего, заметил бы на месте. Вторую — не уверен.

**Как это меняет расчёт.** Считать надо не правки, а волны. Волна — это «решил → отдал Хайку → проверил диффом и тестами». Всё найденное становится пунктами следующей волны, и каждая волна снова платит фиксированные ~$0.11. Получается:

- **relay** ≈ волны × ($0.11 + прогон Хайку) + мои ходы на мелкие починки;
- **сам** ≈ ходы × (контекст × $0.2/M), находки по пути почти бесплатны.

Отсюда relay хорош для хвоста работы, где дизайн уже устоялся и правки механические. Для работы, где каждый шаг учит следующему, он плох. Порог в 4 хода из прошлого ответа верен только для одной волны.

**Что можно сделать дешевле.** В брифе поменять «не трогай то, что заметил» на «не трогай, но перечисли в отчёте». Строчка в отчёте почти ничего не стоит, а часть замечания возвращается. Насколько Хайку вообще способен замечать, неизвестно: #253 говорит, что сам он не ищет. Стоит проверить следующим догфудом.

Если согласен, прогноз в `delegation.py` будет принимать не число правок, а оценку «ходов сам» и «волн через Хайку», а `edit-relay.md` получит раздел про волны и про «перечисли, не трогай». Делать так, вместе с переименованием?
```
