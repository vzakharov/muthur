# Relay 1 — the keepalive always parks

## Standing constraints

None stated.

## The conversation

1. **Operator** (with a screenshot of another session's final report, a
   vovazakharov.com session that paused its plan
   `multi-app-sliced-design.paused.md`, asked two questions, and did not relay
   because "the branch knows everything"):

   > давай парковать всегда, даже если "ветка всё знает", потому что даже в
   > таких случаях последняя сессия иногда наговорит всякого, на которое легче
   > (было бы) ответить напрямую, чем лезть в файлы.

   **Agent:** routed rung 1 → `/task`, went planless; began tracing which rule
   let that session end with no park.

2. **Operator** (mid-turn):

   > нe и просто скопипастить готовый `/relay take` легче, чем идти в пиар,
   > оставлять там ревью, вручную писать `/handle` итп

   **Agent:** noted that the park's ready `/relay take` line is exactly that.

3. **Operator** (mid-turn, answering the agent's "which rule let that session
   avoid it"):

   > никакое не позволило, она как раз протухла

   **Agent:** agreed — the watcher was skipped because the branch "knew
   everything", so the cache expired with no park; that skip is what gets
   removed.

4. **Operator** (mid-turn):

   > ну то есть она бы и так и так протухла, так как keepalive держит максимум
   > 110 минут -- речь не об этом, а о том, что было на выходе этого протухания
   > (ничего, в отличие от ситуации когда "ветка не знает")

   **Agent:** confirmed the fix targets the output of going cold: with the
   watcher always running, its last wake parks and leaves the summary plus the
   `/relay take` line. Then implemented, polished, opened draft PR #232 and
   posted the squash proposal. (verbatim in Last agent turn)

## Intent

When a session goes idle and its cache is about to expire, it must always leave
a park (summary with the last reply verbatim + a pasteable `/relay take` line),
whether or not the branch alone would let a fresh session continue. The point is
the output of going cold, not keeping the session alive longer.

## Decisions

- **Drop the "branch suffices" skip from the keepalive hook** rather than
  parking immediately at a boundary turn's end: the watcher's wake parks after
  ~an hour, so an operator returning sooner keeps the warm session, and one who
  doesn't still gets the park. Stop word ("стоп"/"stop") remains the only skip.
- **Parked summary is never deleted on return, only rewritten** (relay § "When
  the summary goes stale"), for the same reason: the last agent turn is what the
  operator answers next. `/relay take`'s "file gone" case now only means
  `/finalize` swept it.
- Branch renamed from `claude/affectionate-brown-9khkys` before the first
  commit; the old name never existed on the remote.

## Errors and dead ends

None.

## State

- Branch `claude/keepalive-always-parks-9khkys`, pushed; head before this
  summary `d37dfd9`.
- PR https://github.com/vzakharov/muthur/pull/232 — draft, open, no CI checks
  reported. Squash proposal posted as a comment and tracked at
  `docs/remove-before-merging/squash-message.md`.
- No plan file (planless `/go`). `/polish` ran (commit `ce60997`); vet passed.
- Estimate: 1.5 h senior prompter (judging which stop conditions to drop, prose
  kept consistent across four files) + 0.5 h middle developer (small hook change
  and test). Nothing handed on beyond `/finalize`.
- No PR subscription, no scheduled check-in, no keepalive watcher.

## Pointers

- `.claude/keepalive/hooks/keepalive.py` — `context()`, the hook text.
- `.claude/keepalive/test_keepalive.py` — the updated assertion.
- `.claude/keepalive/CLAUDE.md` — the "It runs after every turn" bullet.
- `.claude/skills/relay/SKILL.md` — § "When the summary goes stale", Step 2,
  `/relay take` step 2.
- `.claude/skills/update-muthur/catalog/g10-cache-keepalive.md`.
- Transcript: https://claude.ai/code/session_01DaohkD2amc2dynSfpzvst3

## Next step

Wait for the operator — the PR awaits their review; `finalize` when they say so.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages,
usually unneeded but harmless; the reply proper is usually its last
paragraphs.

```text
Это просьба изменить сам цикл агента (rung 1), так что иду через `/task`. Сначала гляну, где живёт правило «ветка всё знает».

Учёл и второе сообщение: готовая строка `/relay take` из парковки как раз и решает это — копируешь и всё.

Решение: делаю напрямую, без плана — правка в пяти известных файлах, развилок нет. Скажи `plan`, и напишу план.

Ветка переименована (на remote старой не было). Теперь правки.

Теперь relay: устаревшая сводка больше не удаляется, только переписывается — иначе тот же «ничего на выходе».

Vet зелёный. Коммичу и пушу, потом `/polish` и `/pr`, это хвост `/go`.

Polish прошёл. Открываю PR.

Пишу предложение для squash-коммита и вешаю его комментарием на PR.

Вова, готово: черновик PR открыт, теперь сессия паркуется всегда, даже если ветка «всё знает».

https://github.com/vzakharov/muthur/pull/232

**Почему та сессия ничего не оставила.** Хук keepalive не просил запускать вотчер, если ветка и PR уже позволяли новой сессии продолжить. Вотчера не было, значит не было и пробуждения, а парковку делает именно оно. Кэш протух молча: ни сводки, ни последнего ответа дословно, ни готовой строки `/relay take`.

**Что поменял:**
- **Вотчер запускается после каждого хода.** Пропускается он теперь только если ты сам скажешь «стоп». Последнее пробуждение паркует сессию, и в итоге у тебя есть одна строка, которую можно скопировать, вместо похода в PR, ревью и `/handle` вручную.
- **Сводку парковки больше не удаляют.** Раньше, если ты возвращался в запаркованную сессию и в ней ничего не оставалось незакрытым, сводку удаляли. Это был тот же «пустой выход», так что теперь её только переписывают. Пропасть она может только при чистке в `/finalize`.
- Под это поправил `keepalive.py` и его тест, `.claude/keepalive/CLAUDE.md`, `/relay` и запись в каталоге.

Vet и тесты keepalive проходят. `/polish` поменял одну формулировку, `/dry` ничего не нашёл. Предложение для squash-коммита висит комментарием на PR, заголовок — `fix: the keepalive always parks, even when the branch holds all the work`. Хук уже работает в новой редакции, по крайней мере в этой сессии: на последний ход он прислал инструкцию без исключения «ветка всё знает».

Иронично, но этой сессии новое правило тоже касается: сейчас запущу вотчер, и через час она сама себя запаркует.

Вотчер запущен.
```
