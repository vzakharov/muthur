# Relay 1 — checkpoint reviewer procedure

## 1. Standing constraints

None stated by the operator.

## 2. The conversation

**Operator (the only message, Russian, verbatim):**

> давай пофиксим (и сразу задогфудим) принцип "опус ревьюит более слабые модели"
> (b2079f0). проблема: слабые модели пишут постановку задачу субагенту как им
> бог на душу положит. нужно: 1- полная процедура для контроля записана в
> отдельном файле 2- в процедуре написано что опус должен а- посмотреть
> последнюю отсечку (см. ниже) б- посмотреть полный лог (для начала --
> программно извлечь вопросы и ответы, для этого должен быть отдельный скрипт)
> родительского агента в- вполнить проверку г- ответить вердиктом 3- основной
> агент (на соннете/хайку) вызывает подагента с единственной командой: "Proceed
> per `<path>.md`"; то есть всю процедуру Опус читает отсюда, и не зависит ни от
> чего что ему скажет раздающий агент
>
> первым догфудом будет проверка опусом самого написанного файла и связанных с
> ним изменений (или, в случае если Соннет решит идти через план, ревью самого
> плана).

**Agent (Sonnet 5.5), condensed:** routed through `/task` (rung 1), chose a plan
(shared transcript helpers are a live reuse call), renamed the auto-branch to
`claude/checkpoint-reviewer-procedure-wcfux3` before the first commit, wrote the
plan, opened draft PR 257, posted the squash proposal, and ran the old-procedure
checkpoint review of the plan with an Opus subagent: look 1 `revise`, look 2
`fixed`. Stopped at the plan because the context budget warning (~183k) came
before the implementation could fit; no source is written. Its closing report,
with the `/go` handoff block, is the last reply (verbatim in Last agent turn).

## 3. Intent

Take the Opus checkpoint reviewer's brief out of the weaker session's hands. The
reviewer reads one procedure file, derives the request, the last cutoff and the
parent's log itself, and the session's launch prompt is exactly
``Proceed per `.claude/skills/go/checkpoint-reviewer.md` ``. First dogfood: the
Opus review of the plan (done, old procedure) and then of the implementation at
the end of `/go` (the first review by the new procedure).

## 4. Decisions

- **Plan, not direct work**: several parts that only make sense together and a
  real reuse call (transcript helpers shared by `relay-last-reply.py`,
  `extract-session-images.py` and the new script).
- **The reviewer picks the cutoff, the script does not**: a `Read` of a
  `SKILL.md` counts as an entry (the hook's `entered_skill`), and a session
  reads one to research it as often as to run it. The alternative, trusting the
  last marker, was wrong in this very session.
- **Hook gate on `Agent`, narrowed**: denies an Opus call whose prompt names the
  checkpoint review without being the launch line, and the launch line sent to a
  non-Opus model. Beaten alternatives: trust the procedure alone (the shape that
  failed); deny every Opus `Agent` call while a review is pending (blocks the
  operator's own requests, since pending lasts from skill entry to verdict).
- **`COMMAND_ENVELOPE` is copied, not imported** from
  `.claude/costs/lib/identity.py`: the costs tree is a separate shipping group;
  a test holds the two patterns equal.
- **Operator-message shapes**: a `user` record and a `queued_command`
  attachment, both `origin.kind == "human"`; a subagent hand-back is the
  attachment with `origin.kind == "peer"`.

## 5. Errors and dead ends

- First review found the cutoff-by-last-marker flaw, the missing mid-turn and
  command-envelope shapes, a missing `--first-parent`, and a missing DRY account
  of three other transcript readers. Second look found the gate still denied too
  much; the reviewer fixed it itself (f6f9a4c).
- The hook has marked `go` and `finalize` pending in the planning session
  because the planning session read their `SKILL.md`s; nothing changed about
  that marking.

## 6. State

- Branch `claude/checkpoint-reviewer-procedure-wcfux3`, head after this summary
  is pushed, PR https://github.com/vzakharov/muthur/pull/257 (draft), base
  `main`.
- Plan: `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`.
  Still a draft; the go-ahead has not been given.
- Squash proposal posted as a comment on PR 257 and tracked in
  `docs/remove-before-merging/squash-message.md`.
- Nothing is running; the cache keepalive watcher has ended.
- Estimate: this session's `1.5 h senior architect` (plan and its review looks).
  Remainder handed on, which the successor sets: `3 h middle developer` (a
  stdlib transcript-extraction script, a shared lib refactor, hook enforcement
  and tests) and `2 h senior prompter` (the reviewer procedure is prose a weaker
  model's brief must not be able to bend).

## 7. Pointers

- Plan above; the code it changes: `.claude/hooks/checkpoint-review.py`,
  `.claude/hooks/skill_entry.py`, `.claude/skills/go/checkpoint-review.md`,
  `scripts/relay-last-reply.py`, `scripts/extract-session-images.py`,
  `scripts/test_checkpoint_review.py`, `.claude/settings.json`.
- Transcript format: `.claude/costs/CLAUDE.md` § "Reading a transcript".
- The review's commit that edited the capabilities file: fa4484d.
- Predecessor session: https://claude.ai/code/session_01RAikutax5eGF92PkSppyCn

## 8. Next step

Wait for the operator. When they give the go-ahead for the plan: `/go` (the
session starts from `/relay take`, then `/go` flips the draft, quoting their
words). The successor's operator is expected to type `/go` with this branch.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

````text
Вова, реализацию я отдаю новой сессии: у этой контекст уже за предупредительной линией (~190k), а скрипт, общая библиотека, хук, процедура и тесты в оставшийся запас не влезают. Поэтому план остаётся черновиком (`*.draft.do-not-implement.md`), кода нет, и PR https://github.com/vzakharov/muthur/pull/257 пока содержит только план. `/relay` не запускал: всё, что нужно новой сессии, уже записано в плане.

**Ревью плана Opus-ревьюером** (старая процедура, два взгляда):
- **Первый взгляд — `revise`.** Он нашёл пять проблем:
  - Скрипт принял бы исследовательское чтение `SKILL.md` за вход в скилл. В этой сессии последним «входом» оказался бы `finalize`, хотя мы планировали. Теперь отсечку выбирает сам ревьюер по логу, а скрипт показывает путь входа.
  - Сообщения оператора, присланные посреди хода, лежат в транскрипте другой записью (`queued_command`), и скрипт их терял.
  - Печатная команда вроде `/plan` приходит в обёртке `<command-name>`, и скрипт её не распознал бы.
  - Коммит «на тот момент» надо искать с `--first-parent`, иначе после слияния базы `<from>` будет неверным.
  - В DRY-заметках не хватало трёх существующих читателей транскрипта.
- **Второй взгляд — `fixed`.** Ворота на вызов `Agent` у меня всё ещё блокировали любой Opus-вызов во время висящего ревью. Ревьюер сам сузил их: отклоняется Opus-вызов, в чьём промпте упомянуто checkpoint review, если промпт не равен строке запуска, и строка запуска, отправленная не на Opus. Я привёл в соответствие описание PR и предложение squash-сообщения.

Старый бриф, составленный из одних фактов, сработал, но ревьюеру пришлось самому искать, где лежит транскрипт родителя, как выглядят его записи и какие входы в скиллы считать отсечками. Именно это новая процедура должна давать по умолчанию, так что первым догфудом станет ревью реализации.

Чтобы реализовать в новой сессии:

```
/go claude/checkpoint-reviewer-procedure-wcfux3
```

Ветку я переименовал с `claude/awesome-faraday-wcfux3` (как требует `/pr`).
````
