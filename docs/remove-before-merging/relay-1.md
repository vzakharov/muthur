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

   **Agent:** routed through `/task`; planned, implemented, polished, opened
   draft PR #251. Said `SendMessage` continues a finished subagent; named two
   calls taken unasked: only Sonnet/Haiku are weaker (Opus, Fable skip), and
   `revise` is capped at two rounds. Then the keepalive parked the session.

2. _(Not the operator: a cross-session message from
   `session_01DaohkCDf1JN4Vapypm9WVz`, which compared this task's runs on Haiku
   — vzakharov/muthur#250 — Sonnet — vzakharov/muthur#252 — and Opus, #251, at
   Vova's request «опусовской сессии передай всё, что ей стоит передать для
   улучшения». Six improvements; #250 and #252 are closed in favour of #251.)_

   **Agent:** did not act on a peer's message; recorded the six in the parked
   summary and asked Vova for a go-ahead. Admitted a wrong `Claude-Session` link
   in `a674f55`.

3. **Operator:**

   > ты же мог перепроверить, но да :)

   **Agent:** took it as the go-ahead for all six; verified the claims (#252's
   `review-gate.md`, `message.model` in the transcript), revised the estimate,
   designed the hook, then hit the context budget's pause line and wrote the
   paused plan. (verbatim in Last agent turn)

## Intent

Weaker-model sessions get an Opus quality check at each loop cutoff, with five
graded verdicts ending in escalation to an Opus session; now made enforceable by
a hook rather than left to the weaker model's own judgement.

## Decisions

- **Shipped in #251:** one procedure `.claude/skills/go/checkpoint-review.md`;
  pointers in `/plan` (after publishing, before handoff), `/go` (Step 3),
  `/finalize` (after the passes, before vet); `/handle` via those; verdicts
  `pass` / `revise` / `fixed` / `fixed, relay` / `relay`; `/relay` Step 3 starts
  an escalation on the Opus id from the system prompt's model-id list; the
  reviewer keeps `delegation-model-capabilities.md`.
- **The follow-up's design** is the paused plan's — read it rather than
  re-deriving: `docs/plans/opus-checkpoint-review-gate.paused.md`. Its key
  calls: model from the transcript's last `message.model`; pending set per
  cutoff skill in `tmp/checkpoint-review/<session>`; PreToolUse deny on the
  draft flip (`plan` pending), the `*.completed.md` flip (`go` pending) and
  `gh pr ready` (`finalize` pending); a `verdict` subcommand clears them; switch
  `MUTHUR_CHECKPOINT_REVIEW=off`. Beat: a Stop hook (would block legitimate turn
  ends and the reviewer's hand-back), a verdict commit (a `pass` leaves nothing
  to commit).
- **Still open to Vova:** Fable exempt? Two `revise` rounds enough?

## Errors and dead ends

- Two commits carry a wrong `Claude-Session` trailer: `a674f55` (the comparing
  session's id) and `b1970c9` (a typo). History is not rewritten. This session's
  id is `session_01DaohkDGvyPHkmGezpudcWA`.

## State

- Branch `claude/opus-checkpoint-review-p4nmuv`, pushed; head before this
  summary `b1970c9`.
- Draft PR https://github.com/vzakharov/muthur/pull/251; squash proposal at
  `docs/remove-before-merging/squash-message.md` (describes #251 as shipped, not
  the hook yet).
- Plans: `opus-checkpoint-review.completed.md` (inert),
  `opus-checkpoint-review-gate.paused.md` (actionable, nothing built).
- Not vetted. No PR subscription; nothing running.
- Estimate: this session 3 h senior prompter + 1 h senior architect. Remainder
  handed on: 3 h middle developer ("a stdlib hook reading the serving model from
  an undocumented transcript format, holding per-session state, and denying tool
  calls, with a unittest suite in the house style") + 1 h senior prompter ("the
  procedure's brief, verdict and placement wording a weaker model follows
  unaided, rewritten around a hook that now decides who runs it").

## Pointers

- `docs/plans/opus-checkpoint-review-gate.paused.md` — what to build.
- `.claude/skills/go/checkpoint-review.md`, the pointers in
  `.claude/skills/{plan,go,finalize}/SKILL.md`, `/relay` Step 3.
- `.claude/hooks/go-delegation.py`, `.claude/hooks/session_state.py`,
  `scripts/test_go_delegation.py` — the hook and test style to follow.
- #252's procedure:
  `git show origin/claude/opus-quality-gate-tmds1o:.claude/skills/go/review-gate.md`.
- Comparison notes: `writing/notes/weak-driver-opus-gate.md` in
  vzakharov/vovazakharov.com#230.
- Transcript: https://claude.ai/code/session_01DaohkDGvyPHkmGezpudcWA

## Next step

Resume the paused plan `docs/plans/opus-checkpoint-review-gate.paused.md` — the
operator's go-ahead for it is «ты же мог перепроверить, но да :)».

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Вова, сессия, которая сравнивала прогоны на Haiku, Sonnet и Опусе, прислала шесть доработок для https://github.com/vzakharov/muthur/pull/251. Пишет, что по твоей просьбе. Я ничего не трогал: просьба пришла от соседней сессии, а не от тебя. Записал всё в сводку парковки `docs/remove-before-merging/relay-1.md` как ждущее твоего «да».

Из шести главное:
- **Пункт 2 — настоящий баг в моей версии.** В `/go` проверка идёт после того, как план переименован в `*.completed.md`. Если ревьюер ответит `relay`, преемник увидит план «завершённым», хотя работа не доделана.
- **Пункт 1 — бриф ревьюера всегда несёт твою исходную просьбу дословно.** Сейчас при наличии плана в брифе только путь к нему. На Haiku так и вышло: она неправильно поняла вердикты в своём плане, а Опус дважды поставил пятёрку, сверяя работу с этим же планом.
- **Пункт 5 — модель определять хуком, а не самой сессией.** Мой план отверг хук на ложной посылке, что хук не видит, какая модель сейчас отвечает. На деле видит: в транскрипте у каждого ответа модели записано, какая модель его дала. Это меняет устройство проверки сильнее остальных пунктов.

Скажи «давай» — сделаю все шесть или только те, что назовёшь. Твои два открытых вопроса остаются за тобой: проверять ли Fable и хватит ли двух раундов `revise`.

В последнем коммите (`a674f55`) я по ошибке указал в строке `Claude-Session` ссылку на ту, сравнивающую, сессию вместо этой. История не переписывается, так что это остаётся как есть.
```
