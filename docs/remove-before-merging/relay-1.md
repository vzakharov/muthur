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
   everything", so the cache expired with no park.

4. **Operator** (mid-turn):

   > ну то есть она бы и так и так протухла, так как keepalive держит максимум
   > 110 минут -- речь не об этом, а о том, что было на выходе этого протухания
   > (ничего, в отличие от ситуации когда "ветка не знает")

   **Agent:** confirmed the fix targets the output of going cold; implemented,
   polished, opened draft PR #232, posted the squash proposal. Then the
   keepalive wake parked the session (`relay-1.md`, first version) with the
   caption "PR ждёт твоего ревью, дальше finalize".

5. **Operator:**

   > я уже отревьюил, плюс "PR ждёт твоего ревью, дальше finalize" в качестве
   > затравки новой сессии звучит так себе. "Ты" для неё будет именно агент.
   > Возможно это более общая проблема, не от этого диффа, но поправить её лучше
   > в этом же пиаре

   **Agent:** ran `/handle #232`. Two review threads: T01 (keepalive
   `CLAUDE.md`:20, "возможно медведь?", re-check for more bears since the PR's
   point is removing something, and add that note to tend-prose's bear section)
   and T02 (squash: "это таки не фикс"). Cut four bears, added the tend-prose
   paragraph, made the relay caption address nobody, retitled the PR `feat:`,
   polished, refreshed the PR body and squash proposal, replied on both threads.
   (verbatim in Last agent turn)

## Intent

When a session goes idle and its cache is about to expire, it must always leave
a park (summary with the last reply verbatim + a pasteable `/relay take` line),
whether or not the branch alone would let a fresh session continue. The point is
the output of going cold, not keeping the session alive longer. The caption on
that line must read correctly to both the operator and the successor agent.

## Decisions

- **Drop the "branch suffices" skip from the keepalive hook** rather than
  parking immediately at a boundary turn's end: the watcher's wake parks after
  ~an hour, so an operator returning sooner keeps the warm session.
- **A parked summary is rewritten, never deleted**, when its operator returns.
- **The `/relay take` caption addresses nobody** (relay `SKILL.md` Step 3): the
  successor reads it as its first message, so a "you" names it to itself.
- **Bears from a removal are judged against the resulting file with the diff
  closed** (tend-prose lens 4); close calls go to the operator. The agent judged
  its own T01 call unreliable for exactly that reason.
- **The PR is `feat:`**, per T02 — nothing was broken. Earlier commit subjects
  stay `fix:`; the squash replaces them.
- "Bear" / "медведь" = tend-prose's negation lens (polar bear): prose that
  denies a removed thing.

## Errors and dead ends

- The first park's caption, "PR ждёт твоего ревью", addressed the operator in a
  line the successor reads — the defect fixed in ff8d35e.

## State

- Branch `claude/keepalive-always-parks-9khkys`, pushed; PR
  https://github.com/vzakharov/muthur/pull/232 — draft, open, title
  `feat: always park an idle session; relay captions address nobody`.
- Review replies posted on both threads (left unresolved for the operator).
- `main` has advanced (`c9ec8c5`, #234, touches the keepalive test and skill
  prose) — not merged in; `/finalize`'s base merge handles it.
- No plan file. Polish ran through 83b3a2e; vet passed except prettier on this
  file, fixed with it.
- Estimate: 2.5 h senior prompter + 0.5 h middle developer; nothing handed on
  beyond `/finalize`.

## Pointers

- `.claude/keepalive/hooks/keepalive.py`, `.claude/keepalive/test_keepalive.py`,
  `.claude/keepalive/CLAUDE.md`.
- `.claude/skills/relay/SKILL.md` — Step 3 (caption), § "When the summary goes
  stale".
- `.claude/skills/tend-prose/SKILL.md` — lens 4's removal paragraph.
- `docs/pr/232/pr.md` — the last export; re-run
  `python3 scripts/export-github-item.py 232`.
- Transcript: https://claude.ai/code/session_01DaohkD2amc2dynSfpzvst3

## Next step

Wait for the operator: their replies on the two threads, or `finalize`.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

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
