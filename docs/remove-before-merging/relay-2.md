# Relay 2 — Opus checkpoint review: the hook and the procedure rework

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator (Vova, @vzakharov)** — the session's opening prompt:

   > /relay take claude/opus-checkpoint-review-p4nmuv — шесть доработок проверки
   > Опусом одобрены и расписаны в плане на паузе, дальше хук и правки процедуры

   **Agent:** attached, read `relay-1.md`, took the remainder estimate, resumed
   the paused plan and built all six: the procedure rework in
   `checkpoint-review.md` and the `/plan`, `/go`, `/finalize` pointers; the hook
   `.claude/hooks/checkpoint-review.py` with `skill_entry.py` shared with
   `go-delegation.py`; 25 tests; the catalog entries; polish (no changes); plan
   flipped to completed; PR body and squash proposal refreshed. Reported three
   deviations, one declined DRY call, and the two questions still open.
   (verbatim in Last agent turn)

## Intent

Weaker-model sessions get an Opus quality check at each loop cutoff, with five
graded verdicts ending in escalation to an Opus session — enforced by a hook
rather than left to the weaker model's judgement.

## Decisions

- **`verdict <session> <skill> <verdict>` clears only that skill**, not the
  whole pending set: `/go`'s entry by `Read` lands before `/plan`'s pending
  review clears, so a set-wide clear would drop `/go`'s review.
- **An entry is marked whatever the model; the gate checks the model.** A typed
  first prompt arrives before any reply records one in the transcript.
- **`fixed, relay` is renamed `fixed-relay`** — one token for the command.
- **The model is the latest non-sidechain, non-`<synthetic>` assistant entry's
  `message.model`**; weaker = names `sonnet` or `haiku`.
- **Declined:** a shared hook-I/O helper (`say`, payload read, `emit`) across
  `checkpoint-review.py`, `go-delegation.py` and `file-tools-nudge.py` — the
  polish subagent raised it; it reaches past this PR's files. Offered to Vova as
  a separate task.
- **Still open to Vova:** Fable exempt (currently yes)? Two `revise` rounds
  enough?

## Errors and dead ends

None in this session. Predecessor's wrong `Claude-Session` trailers on `a674f55`
and `b1970c9` stand; history is not rewritten.

## State

- Branch `claude/opus-checkpoint-review-p4nmuv`, pushed, head `6df8e81` before
  this summary.
- Draft PR https://github.com/vzakharov/muthur/pull/251, mergeable `CLEAN`;
  squash proposal comment edited from
  `docs/remove-before-merging/squash-message.md`.
- Plans: both `*.completed.md`; nothing actionable.
- Not vetted (`/finalize`'s job). Hook never exercised live on a weaker model.
  No PR subscription; nothing running.
- Estimate: this session 3 h middle developer + 1 h senior prompter, the whole
  remainder relay-1 handed on; nothing handed further.

## Pointers

- `.claude/hooks/checkpoint-review.py`, `.claude/hooks/skill_entry.py`,
  `scripts/test_checkpoint_review.py`, `.claude/settings.json` (three wirings).
- `.claude/skills/go/checkpoint-review.md`; pointers in
  `.claude/skills/{plan,go,finalize}/SKILL.md`.
- `docs/plans/opus-checkpoint-review-gate.completed.md` § "Done" — the
  deviations.
- `docs/remove-before-merging/relay-1.md` — the earlier conversation.
- Transcript: https://claude.ai/code/session_01DaohkErDzQLANWgn2tnDGB

## Next step

Wait for the operator. Pending with them: the two open questions above, and
whether to run `finalize` on #251.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Сначала проза процедуры (бриф, `fixed` как исключение, место в `/go`), потом сам хук с тестами.

Now the shared entry helper, then the hook.

Хук подключён. Теперь тесты в стиле `test_go_delegation.py`.

Picked up automatically. Tidying one helper's placement, then the catalog.

Хук и тесты запушены (25 тестов зелёные). Дальше обязательные проходы `/polish`.

Now `/pr` refresh.

Вова, все шесть доработок сделаны и запушены. Плана на паузе больше нет: он теперь `opus-checkpoint-review-gate.completed.md`.

https://github.com/vzakharov/muthur/pull/251

**Что теперь происходит.** Слабая модель больше не решает сама, проводить ли проверку Опусом. Это делает хук `.claude/hooks/checkpoint-review.py`. Он берёт из транскрипта модель, которая дала последний ответ. Если это Sonnet или Haiku:
- при входе в `/plan`, `/go` или `/finalize` хук сам выдаёт процедуру проверки;
- пока вердикт не записан, хук не даёт закрыть этот этап: переименовать черновик плана, пометить план `*.completed.md` или сделать `gh pr ready`.

Вердикт записывается командой `verdict`. Сессия может забыть процедуру, но мимо закрытой двери не пройдёт.

**Остальные пять пунктов:**
- ревьюер всегда получает твою просьбу дословно, и только факты, без мнения сессии о своей работе;
- `fixed` теперь исключение: ревьюер правит сам только то, что дешевле сделать, чем описать;
- если отчёт ревьюера пришёл отдельным сообщением на следующем ходу, сессия ждёт его и второго ревьюера не запускает;
- в `/go` проверка идёт до пометки `*.completed.md`, так что после вердикта `relay` план остаётся на паузе, а не притворяется готовым;
- `MUTHUR_CHECKPOINT_REVIEW=off` всё это выключает.

На хук 25 тестов, они проходят. Тесты `go-delegation` тоже проходят: определение входа в скилл я вынес в общий `skill_entry.py`.

**Где я отошёл от плана:**
- **Команда `verdict` указывает скилл и снимает проверку только с него.** Иначе вышло бы так: `/go` читает свой `SKILL.md` раньше, чем записан вердикт по `/plan`, и один `pass` снял бы обе проверки.
- **Вход в скилл запоминается при любой модели, а модель проверяется только при попытке закрыть этап.** Если `/go` набран первым же сообщением, ответа ещё нет, и узнать модель неоткуда.
- **`fixed, relay` теперь `fixed-relay`**, чтобы это было одно слово в команде.

**Чего не делал:**
- Прогон `polish` нашёл ещё одно повторение: три хука одинаково читают входные данные и одинаково печатают ответ. Общий модуль для этого я не делал: пришлось бы трогать `file-tools-nudge.py`, который в этом PR не участвует. Если хочешь, это отдельная задача.
- `vet.sh` я не запускал, это работа `/finalize`.
- Сам я сейчас на Опусе, так что на этой сессии хук ничего не перекрыл. Живьём на Sonnet он ещё не проверен; в QA-чеклисте PR это первый пункт.

Два вопроса всё ещё за тобой: проверять ли Fable (сейчас не проверяем) и хватает ли двух раундов `revise`. Дальше — `finalize`.
```
