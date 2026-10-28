# Relay 1 — keepalive watcher starts first (parked)

## Standing constraints

None stated.

## The conversation

1. Operator (via `/task`, verbatim in substance): fix the keepalive's
   `UserPromptSubmit` instruction ("As this turn's last action, start the cache
   keepalive's watcher …"). In vzakharov/vovazakharov.com the agent wrote its
   reply, made the watcher call as the last action, then wrote the same reply
   again once the result came back. Weigh (1) keep "last action" + "no text
   after the result" vs (2) start the watcher before the reply; update
   `test_keepalive.py` and the keepalive `CLAUDE.md`. «фикс новой сессией от
   muthur-а».
   - Agent: picked (2) without a plan; verified `watch_locked` recomputes the
     deadline on every transcript mtime change. Changed the instruction to
     "first action", added a test that a response written after the watcher
     starts replaces its deadline, ran `/polish`, opened draft PR #247, posted
     the squash proposal, retitled the PR.
2. Operator: «а всегда ли ты в начале уже хода знаешь, что нужен watcher?»
   - Agent: almost always — the hook's state and the operator's message decide
     it. Exceptions are turns that end the session: `/relay park` (already
     TaskStops; "запаркуй" visible up front), `/relay` handoff (gap, either
     order), proposed fixes for both.
3. Operator: «а в контексте #246 (вроде), который перестанет запускать вотчер
   после мерджа?»
   - Agent: #246 decides "landed" at prompt time too, so a mid-turn merge still
     leaves a watcher that wakes once to a one-line "stopped"; proposed a
     TaskStop line; noted #246/#247 textual conflicts.
4. Operator: «а это всегда в начале видно? например, я запускаю /finalize and
   merge (или что то же /merge), но сработает ли "and merge" видно только по
   результатам разрешения конфликтов итп»
   - Agent: no — so the stop belongs where the event happens: `merge.md` after a
     successful merge and `relay` Step 4, not the hook's start instruction.
     Proposed: park-skip in the hook now.
5. Operator: «но.. допустим ход идёт 15 минут, если мы запустим в начале, мы
   теряем 40 минут прогревания кеша. что если сказать на penultimate ходу?»
   - Agent: nothing is lost — the deadline follows the last response, not the
     watcher's start; "penultimate" is as unknowable as "last". Caveat: the
     watcher's ~1h57m lifetime runs from its start, so a turn over ~1h costs one
     early wake.
6. Operator: «добро. тогда делай правки как хотел, про #246 не парься, при
   мердже тот сам разберётся»
   - Agent: committed 5c673517 (park skip in the hook, TaskStop in `merge.md`
     and relay Step 4, the long-turn cost in keepalive `CLAUDE.md`), vet green,
     refreshed squash proposal and PR body.
7. Operator: «а я вот вижу что текущий вотчер уже 21 минуту как работает, то
   есть через 34 минуты он таки проснётся, а не через 55?»
   - Agent: computed live: "wake in 54.9 min" — deadline follows each response.
8. Operator: «окей, давай подождём 55 минут чтобы проверить :)»
   - Agent: agreed; warned the first wake parks by default (renewals 0).
     (verbatim in Last agent turn)

The wake came at 18:33:31 UTC, 54 min 57 s after the last response (17:38:34):
the experiment confirmed the deadline follows the last response.

## Intent

Remove the doubled reply caused by the watcher call closing a turn, without
losing cache warmth; have turns that end a session's work stop the watcher.
#246's conflicts are left to #246 («про #246 не парься»).

## Decisions

- **Watcher first, not last** (beat option 1 "no text after the result"): option
  1 fights the model's habit of closing with text every turn; first removes the
  gap. Safe because the deadline is re-read from the transcript.
- **Stops live where the event happens**: `merge.md` (after a merge) and relay
  Step 4 (handoff), since neither is knowable at turn start; a park ask is
  knowable, so the hook skips the start for it.
- **Accepted cost**: a turn over about an hour gets one early wake.

## Errors and dead ends

- Commit 46e4cd18's `Claude-Session` trailer names the vovazakharov.com session
  by mistake; left as is (no force-push), the squash drops it.

## State

- Branch `claude/keepalive-watcher-first`, PR #247 (draft, open), head before
  this summary 3ac6152e. No CI checks report on the branch.
- Squash proposal tracked in `docs/remove-before-merging/squash-message.md`,
  posted as a PR comment.
- Estimate unchanged (the whole task was done here): 1 h senior prompter + 0.5 h
  middle developer.
- No watcher running; parked.

## Pointers

- `.claude/keepalive/hooks/keepalive.py` (`context()`), `test_keepalive.py`,
  `.claude/keepalive/CLAUDE.md`
- `.claude/skills/finalize/merge.md` § "Merging",
  `.claude/skills/relay/SKILL.md` Step 4
- PR #246 (merge gate; overlaps the keepalive files)
- This session: https://claude.ai/code/session_01DaohkFEEZUxvAw33cjutCU

## Next step

Wait for the operator. The PR is ready for `/finalize` when they ask.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Вова, договорились, ждём. Watcher работает, и будить его не нужно.

Учти, что разбудит он не просто так. Продлений по умолчанию ноль (`MUTHUR_CACHE_KEEPALIVE_RENEWALS=0`), так что первое же пробуждение будет последним: я выполню `/relay park`, закоммичу сводку и отдам тебе строку `/relay take …`. Если хочешь просто посмотреть, что он проснулся вовремя, без паркинга, напиши «стоп» и запусти заново с period-файлом. Правда, тогда проверим уже не 55 минут.

Проснусь примерно через 55 минут после этого сообщения, плюс-минус 30 секунд опроса.
```
