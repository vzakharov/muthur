# Relay 1 — checkpoint reviewer procedure (plan under operator review)

## 1. Standing constraints

None stated by the operator. From the PR review, one standing instruction for
the rewrite: «Белых медведей не оставляй когда будешь убирать» — no negations of
removed things left behind in the prose (`/tend-prose negation`).

## 2. The conversation

**Operator, message 1 (Russian, verbatim):**

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

**Agent (Sonnet 5.5), condensed:** routed through `/task`, chose a plan, renamed
the auto-branch to `claude/checkpoint-reviewer-procedure-wcfux3`, wrote the
plan, opened draft PR 257, posted the squash proposal, ran the old-procedure
Opus checkpoint review of the plan (look 1 `revise`, look 2 `fixed`), then
parked the session at the context-budget line.

**Operator, message 2:** `отревьюил` — and left 8 review threads on PR 257.
Verbatim, each with its thread id for the replies (REST comment id):

- **T01** (4422879711, `docs/remove-before-merging/squash-message.md`:1): «это
  fix:»
- **T02** (4422891028, same file :18): «у нас бывает хук на запуск скилла (когда
  агент создаёт подагента-ревьюера)? тогда можно это делать программно без
  необходимости гонять опус туда-сюда вообще»
- **T03** (4422905393, plan :49): «опять же, мы не можем программно отказывать в
  запуске подагента, если там есть что-то кроме этого текста?»
- **T04** (4422947154, plan :53): «хм, не понял, о чём это. Я предполагал что у
  нас будет как в polish: будет отдельный вид коммитного префикса, от которого
  будет смотреть опус. к слову, крамольная мысль.. а что если нам просто
  завернуть всё это в polish? т.е. а) polish всегда делает опус, б) последним
  шагом он проверяет не конкретные вещи (как в dry/tend-prose), а всё вместе (но
  желательно не читая весь дифф ещё раз, конечно). тогда много из механики
  схлопывается, остаётся лишь точно так же поправить скилл polish -- чтобы
  агенты вызывали их с минимум текста (типа просто `/polish <some token arg>`, а
  всё остальное подагент уже смотрел в соответствующем ранбуке.»
- **T05** (4422954136, plan :69): «на самом деле я это сам сказал и сам теперь
  сомневаюсь. Можно сказать _можешь_ смотреть в транскрипт, но требовать -- с
  учётом того что процедура теперь ясна -- может и не надо? просто пусть
  поступает по своему deliberation. (Белых медведей не оставляй когда будешь
  убирать)»
- **T06** (4422968773, plan :74): «cheaper to do или если нет уверенности, что
  описать можно в таком виде, что более слабая модель поймёт (исходя из того что
  мы знаем о её слабостях so far, как общих из model-delegation-capabilities*,
  так и выясненных сейчас) *сам этот файл надо тоже переименовать и перенести,
  так как он теперь, получается, относится не только к delegation.»
- **T07** (4422975074, plan :145): «а, то, с чего я начал» (on the plan's "The
  hook enforces the one-line launch" heading — his own original idea)
- **T08** (4422979646, plan :198): «ну вот нет: to the extent possible должно
  быть воспроизведено, типа "Proceed with the reviewer role per <plan.md>, as if
  it was already implemented"» (on the plan's "Dogfood" item 1: the plan review
  should run the way the real flow will, not "the old procedure")

**Agent, this turn:** ran `/handle` (draft plan plus unanswered feedback means
plan-review lane: revise the plan, reply on every thread, push, re-emit the
`/go` block; no flip, no source). Exported the PR (`docs/pr/257/pr.md`,
committed as 9326536), read the 8 threads, read `/polish`'s `SKILL.md` and
`passes.md`, and worked out the reading below. Then the context-budget pause
line arrived before any plan edit or reply was made. **Nothing has been answered
on GitHub yet and the plan file is unchanged since f6f9a4c.** The last reply is
verbatim in Last agent turn.

## 3. Intent

Same as message 1: the Opus review of a weaker session's work must not depend on
the weaker model's brief. The operator's review now steers the _shape_: reuse
`/polish`'s existing machinery rather than building a parallel cutoff mechanism,
let the harness refuse bad launches programmatically, and make the dogfood
reproduce the real flow.

## 4. Decisions (the agent's reading of the threads, to carry out)

- **Fold the review into `/polish` (T04), recommended.** `/polish` already runs
  its passes in a fresh subagent with a minimal prompt (`@passes.md` to follow,
  the argument verbatim, the plan), already has a branch-local commit prefix
  `polish:` whose newest commit is the **floor** the next run reads from (empty
  `polish: nothing to change` commit when a run changes nothing), and already
  resolves the scope diff itself. So: "the last cutoff" is the polish floor, not
  a transcript scan; the plan's `--cutoffs`, route markers, `skill_entry`
  import, first-parent head logic and `sys.path` insert all go away. `passes.md`
  gains a third pass, the **review**, run last: it checks the work as a whole
  against the operator's request, the plan and `CLAUDE.md`, and what the session
  told the operator against the diff, **without re-reading the whole diff** (it
  works from the earlier passes' findings, the commit list and stat, opening
  diffs only where needed). A session below Opus has `/polish` run on Opus (a);
  the review pass's report ends with `VERDICT: <one>`, the same five verdicts,
  recorded with the same `checkpoint-review.py verdict` command.
- **`/plan` has no polish run today.** Recommended: the `/plan` publish step
  runs `/polish` too when the session is below Opus (`/dry` has nothing to find
  on a plan; `/tend-prose` reads its prose; the review pass is the point).
- **Hook on `Agent` (T02, T03, T07):** `checkpoint-review.py` already has a
  `PreToolUse` registration on `Bash`; add one on `Agent`. For a weaker session
  it (a) refuses a polish launch whose prompt is anything but the launch line
  `Proceed per \`.claude/skills/polish/passes.md\``(optionally followed by one`Argument:
  <the operator's /polish argument,
  verbatim>`line, since`/polish`takes focus guidance and`full`), and (b) forces `model:
  "opus"`on it through the hook's`updatedInput`. Because the launch is recognised by its own first line, the wrong-denial worry from the review looks (an operator's own Opus `Agent`call) goes away. **Unverified, so the first step of`/go`is a spike in`tmp/`:** that a `PreToolUse`hook on`Agent`may rewrite`updatedInput`(fallback: deny with the exact call) and whether a`SubagentStart`
  hook can inject context. T02's "no Opus back and forth" is answered by the
  first; not pre-injecting the log is deliberate because of T05.
- **The transcript is optional (T05):** the review pass _may_ run
  `python3 scripts/session-qa.py` to read the parent's questions and answers
  (kept, as the "для начала" script, but now only Q/A plus an optional
  `--tools`; no cutoff markers). The runbook says "you can", not "read all of
  it". Keep the mid-turn `queued_command` operator-message shape and the
  command-envelope unwrap from the first review; keep
  `scripts/lib/transcript.py` and the `relay-last-reply.py` /
  `extract-session-images.py` extraction with its DRY notes (incl. the three
  other readers and the `COMMAND_ENVELOPE` copy held equal by a test).
- **Fix rule (T06):** the review pass fixes itself what is cheaper to do than to
  describe **or** what it cannot describe in a form the session's model is known
  to follow (judged from the capabilities file's Misses and what the review just
  saw); `revise` only for what is describable that way.
- **Rename and move `delegation-model-capabilities.md` (T06):** it now serves
  the polish review as well as delegation. Recommended home
  `.claude/model-capabilities.md` (not under `go/`); find every reference with
  `grep -rn delegation-model-capabilities` (docs, `go/delegation.md`,
  `go-delegation.py`, the catalog under `.claude/skills/update-muthur/`, the
  100-line cap in `scripts/vet.sh`, tests) and update them in one commit.
- **Dogfood (T08):** run the plan review as the real flow will: an Opus subagent
  whose prompt is "Proceed with the reviewer role per
  `docs/plans/checkpoint-reviewer-procedure.<state>.md`, as if it was already
  implemented", and say so in the plan's Dogfood section instead of "the old
  procedure". The implementation is then reviewed by the real `/polish` flow at
  the end of `/go`.
- **T01:** the change is a `fix:`. Retitle PR 257 to `fix: …` (REST `PATCH`, see
  `/pr` Step 5; ≤72 chars), update the squash proposal's body to the new design,
  and use `fix:` for the implementation commits.
- **Superseded in the plan:** `checkpoint-reviewer.md` as a standalone file and
  the whole cutoff-by-transcript design; the reviewer's own file is now the
  review pass in `.claude/skills/polish/passes.md`. `checkpoint-review.md`
  shrinks to the session's side (who runs it, the launch line, what to do per
  verdict, recording) or merges into `polish/SKILL.md`.

## 5. Errors and dead ends

- The two review looks (old procedure) found: a research `Read` of a `SKILL.md`
  counts as a skill entry; mid-turn operator messages are `queued_command`
  attachments; the typed-command envelope; `--first-parent`; three other
  transcript readers; an over-wide Agent gate. Most of the cutoff findings stop
  mattering once the floor replaces transcript cutoffs.
- A subagent with `run_in_background: false` still returned asynchronously via a
  hand-back message in this harness; wait for it.

## 6. State

- Branch `claude/checkpoint-reviewer-procedure-wcfux3`, base `main`, PR
  https://github.com/vzakharov/muthur/pull/257 (draft, title still `feat:`).
- Plan: `docs/plans/checkpoint-reviewer-procedure.draft.do-not-implement.md`,
  last edited f6f9a4c; still a draft, no go-ahead given. Per `/handle`, the
  operator's `отревьюил` is feedback on the plan: stay in plan mode.
- Pushed head carries the PR export commit 9326536; this summary is the commit
  after it.
- Nothing is running.
- Estimate: this session 2 h senior architect (plan, two review looks, the
  analysis above). Remainder handed on, set by the successor:
  `1 h senior architect` (rewrite the plan to the folded design),
  `2.5 h middle developer` (session-qa.py, lib/transcript.py refactor, Agent
  hook, rename, tests) and `1.5 h senior prompter` (the review pass in
  `passes.md`, the session-side note).

## 7. Pointers

- `.claude/skills/polish/SKILL.md` and `passes.md` — the machinery to extend
  (floor, scope, empty marker commit, subagent launch).
- `.claude/hooks/checkpoint-review.py` (gate, `verdict` command, `PreToolUse` on
  `Bash` already registered in `.claude/settings.json`),
  `.claude/skills/go/checkpoint-review.md` (current session-side text),
  `.claude/skills/go/delegation-model-capabilities.md` (to rename).
- PR export with all 8 threads: `docs/pr/257/pr.md`. Reply API:
  `gh api repos/vzakharov/muthur/pulls/257/comments/<id>/replies -F body=@<file>`
  with the thread ids in § 2; replies in Russian, the footer `---` +
  `_Generated by [Claude Code](https://claude.ai/code)_`, SHAs bare; never
  resolve a thread.
- Transcript format: `.claude/costs/CLAUDE.md` § "Reading a transcript".
- Predecessor: https://claude.ai/code/session_01RAikutax5eGF92PkSppyCn

## 8. Next step

The operator's request is the review they just left (`отревьюил`): continue
`/handle`'s plan-review lane. In order: (1) rewrite the plan to the folded
`/polish` design per § 4 (single approach, rejected alternatives in one
paragraph, a `## DRY notes` section, no negations of removed things); (2) run
the plan review as T08 asks and record its verdict with
`python3 .claude/hooks/checkpoint-review.py verdict <session-id> plan <verdict>`
(the hook marks plan pending on entering `/plan`; a plan-review turn that edits
the plan should re-read `plan/SKILL.md` only if needed); (3) reply to each of
the 8 threads, retitle the PR to `fix:`, refresh PR body and the squash
proposal, push; (4) end with `/plan` § "Handing off"'s
`/go claude/checkpoint-reviewer-procedure-wcfux3` block. Do not flip the plan or
touch source.

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
