# Relay 1 — Opus checkpoint review for sessions on a weaker model

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator (Vova, @vzakharov):**

   > давай если сессия запущена на слабой модели (не Опусе), она после каждой
   > отсечки лупа (/plan, если есть; /go; любые последующие /go и /handle;
   > /finalize) создаёт подагента на _Опусе_ с вопросом: "на твой, проходит ли
   > проверку качества то, что я сделал", с вариантами ответа (в порядке от всё
   > хорошо до всё плохо) да / нет, внеси такие-то правки [указывая не verbatim,
   > > а по сути] и покажи мне ещё раз (не знаю, правда, можно ли писать
   > подагенту который уже отчитался -- в противном случае придётся создавать
   > нового) / нет, я исправил, можешь продолжать работать дальше / нет, я
   > исправил, работа сложновата для тебя, поэтому после этих правок релей в
   > новую сессию на Опусе / нет, я не могу исправить по тем или иным причинам
   > (например, ограничение возможностей подагентов как таковых), релей сразу
   >
   > подагент также может править
   > https://github.com/vzakharov/muthur/blob/main/.claude/skills/go/delegation-model-capabilities.md
   > по результатам

   **Agent:** routed through `/task` (rung 1); wrote a plan, judged Step 3 "no"
   (every fork carried a recommendation), implemented, polished, opened draft PR
   #251. Reported the design, that `SendMessage` does continue a finished
   subagent, and two calls taken without asking: only Sonnet/Haiku count as
   weaker (Opus and Fable skip), and `revise` is capped at two rounds. (verbatim
   in Last agent turn)

## Intent

Sessions on a weaker model get an Opus quality check at each loop cutoff, with
five graded verdicts ending in escalation to an Opus session via `/relay`; the
reviewer may update `delegation-model-capabilities.md`.

## Decisions

- **One shared procedure, `.claude/skills/go/checkpoint-review.md`**, with a
  pointer paragraph in `/plan` (after publishing, before handoff), `/go` (end of
  Step 3, before `/pr`) and `/finalize` (after the quality passes, before step
  1's vet). Beat: a hook delivering it only on weaker models — no hook payload
  reliably carries the serving model.
- **`/finalize` placement before vet**, because every later step vouches for a
  frozen diff. Beat: at the end of `/finalize`, where a fix would void the
  attestation.
- **`/handle` gets no pointer**: its lanes run `/go` or `/plan`, so one review
  per run.
- **"Weaker" = Sonnet, Haiku** by serving model (system prompt line, else
  `get_session` `last_served_model`). Open to the operator: whether Fable should
  be reviewed too.
- **`revise` capped at two rounds**; the third look must fix or escalate. Open
  to the operator.
- **Verdict names:** `pass`, `revise`, `fixed`, `fixed, relay`, `relay`.
  `fixed, relay` → finish the skill, then `/relay` with no argument (successor
  waits for the operator); `relay` → `/relay` now with the findings as its
  argument (plus the skill to re-run when the cutoff was `/finalize`).
- **`/relay` Step 3** gained the escalation exception: pass `model` as the Opus
  id from the system prompt's list of current model ids; locally
  `claude --model opus "<the line>"`.
- **Capabilities file**: the reviewer folds findings into the session model's
  Handles/Misses; `delegation.md` § "Keeping …" names the checkpoint as a second
  source. The file's own header sentence saying so was cut as a duplicate
  (polish's `/dry` call, settled by the agent).

## Errors and dead ends

None.

## State

- Branch `claude/opus-checkpoint-review-p4nmuv` (renamed from
  `claude/dreamy-ramanujan-p4nmuv` before the first commit), head `040b5e7`
  before this summary, pushed.
- Draft PR https://github.com/vzakharov/muthur/pull/251; squash proposal posted
  as a comment and tracked at `docs/remove-before-merging/squash-message.md`.
- Plan `docs/plans/opus-checkpoint-review.completed.md`.
- Not vetted (that is `/finalize`'s). Nothing running; no PR subscription.
- Estimate: 3 h senior prompter + 1 h senior architect; all of it this
  session's, nothing handed on.

## Pointers

- `.claude/skills/go/checkpoint-review.md` — the procedure.
- `.claude/skills/{plan,go,finalize,relay}/SKILL.md` — the pointers and the
  relay exception.
- `.claude/skills/go/delegation.md`, `delegation-model-capabilities.md`.
- `.claude/skills/update-muthur/catalog/g2-pr-loop.md` — catalog entry.
- Transcript: https://claude.ai/code/session_01DaohkDGvyPHkmGezpudcWA

## Next step

Wait for the operator — in particular their answers to the two open calls
(Fable; the two-round `revise` cap), or `finalize`.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Привет, Вова. Это первая ступень лестницы — просьба изменить сам цикл, так что иду через `/task`.

Читаю `/relay` и концы `/plan`, `/handle`, `/finalize`, чтобы понять, куда врезать проверку Опусом.

Пишу файл плана.

Публикую план через `/pr`.

Пишу предложение squash-сообщения для PR.

Пишу саму процедуру.

Теперь указатели в трёх скилах и исключение в `/relay`.

Дописываю каталог и коммичу реализацию.

Step 3 `/go` — `/polish`.

Тело PR и squash-предложение уже описывают то, что в итоге получилось, — обновлять там нечего.

Вова, готово: сессия на Sonnet или Haiku теперь на каждой отсечке цикла зовёт подагента на Опусе, и тот выносит один из пяти вердиктов. Всё запушено в черновой PR, но живьём на слабой модели ещё не прогонялось — это пункты QA-чеклиста в PR.

https://github.com/vzakharov/muthur/pull/251

**Про твой вопрос, можно ли писать подагенту, который уже отчитался:** можно. `SendMessage` по id агента продолжает его разговор, и вся история у него сохраняется. Поэтому после `revise` сессия отправляет «покажи ещё раз» тому же ревьюеру, а не заводит нового.

**Что сделано:**
- Процедура лежит одна, в `.claude/skills/go/checkpoint-review.md`. В `/plan`, `/go` и `/finalize` по абзацу, где сказано, в какой момент она запускается.
- **`/plan`** — после публикации плана, до блока передачи.
- **`/go`** — после полировки, до `/pr`, чтобы описание PR рассказывало уже проверенный дифф. `/handle` проходит через `/go` или `/plan`, поэтому получает одну проверку, а не две.
- **`/finalize`** — сразу после полировки, до прогона `vet.sh`. Всё, что идёт дальше (vet, слияние с базой, attestation, `and merge`), ручается за дифф, который уже не меняется. Правка ревьюера после любого из этих шагов эти поручительства бы обнулила.
- **Вердикты:** `pass` / `revise` / `fixed` / `fixed, relay` / `relay`. После двух раундов `revise` ревьюер обязан либо доделать сам, либо эскалировать: на третьем круге объяснять слабой модели дороже, чем исправить самому.
- **Релей на Опус:** `/relay` по умолчанию наследует модель, а эскалация теперь передаёт `model` с id Опуса. При `fixed, relay` сессия сначала доделывает шаги скила, потом передаёт работу, и Опус-преемник ждёт твоего следующего слова. При `relay` она передаёт сразу, и находки ревьюера становятся первым сообщением преемника.
- **`delegation-model-capabilities.md`:** ревьюер дописывает туда «Handles»/«Misses» модели сессии по уже существующим правилам этого файла.

**Два решения, которые я принял сам, — поправь, если не так:**
1. «Слабые» — это Sonnet и Haiku. На Опусе и Fable проверка не запускается: заставлять Fable сдавать экзамен Опусу — как просить профессора показать домашку аспиранту. Хотя я не уверен, что Fable выше Опуса, так что если нужно и её проверять — скажи.
2. Не больше двух раундов `revise`.

Где-то посередине пришло предупреждение о бюджете контекста (~170k токенов). Я не стал передавать сессию: оставшееся (каталог, полировка, закрытие плана) спокойно помещалось в запас.

Сама эта сессия на Опусе, так что собственную проверку честно пропустила. Ирония оценена.
```
