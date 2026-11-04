# Relay 1 — steer sticky-comment writes to `scripts/pr-comment.sh`

## 1. Standing constraints

None stated.

## 2. The conversation

**Operator** (opening prompt, verbatim):

> Придумай, как сделать, чтобы агенты не упускали из виду scripts/pr-comment.sh,
> и предложи это (по обычному маршруту /task).
>
> Что случилось (в vzakharov/vovazakharov.com, ветка
> claude/unsquatted-share-popover-64vlb6, PR #248). Сессию подхватили через
> `/relay take`. В Next step сводки было «refresh the squash proposal to mention
> the footer». Агент поправил
> docs/remove-before-merging/<slug>/squash-message.md и сам собрал команду
> `gh api repos/.../issues/<n>/comments` для поиска комментария и
> `gh api -X PATCH .../issues/comments/$id -F body=@...`, сцепив её через
> `cd … && id=$(…) && gh api …`. Классификатор auto-режима её отклонил (External
> System Writes). Агент выдал оператору фразу для разрешения именно этого PATCH
> вместо того, чтобы вызвать `scripts/pr-comment.sh squash <n> <file>`. Этот
> скрипт существует ровно для этого: у него узкий интерфейс, на который есть
> allow-правило. /squash-message агент не загружал, а сводка relay не называла
> ни скилл, ни скрипт.
>
> Шов здесь в том, что скрипт достижим только через Step 4 /squash-message и шаг
> 7 /finalize. Агент, который обновляет sticky-комментарий вне этих скиллов
> (после relay, по просьбе оператора, по памяти), о нём не знает. Варианты,
> которые стоит взвесить, но не ограничиваться ими:
>
> - PreToolUse-хук на Bash в духе уже существующего «Did you forget?» (он
>   перенаправляет cat/sed на Read): ловит `gh api … issues/…/comments` с
>   POST/PATCH (или `gh pr comment`), тело которых начинается с маркера
>   sticky-комментария (`Proposed squash`, `<!-- finalize-attestation`), и
>   указывает на scripts/pr-comment.sh;
> - /relay: Next step, который трогает squash-предложение или аттестацию,
>   называет скилл или скрипт;
> - правило CLAUDE.md про ответ на отказ auto-режима: прежде чем просить у
>   оператора фразу, проверить, нет ли в репо одобренного узкого скрипта для
>   этого действия.
>
> Решение должно жить в muthur, чтобы оно дошло до всех репо, которые его
> переняли. Ссылка на сессию, где это произошло:
> https://claude.ai/code/session_01DaohkDLDRgbyc3cZFB9iJW

**Agent**: routed via `/task` → plan and hand off (the operator asked for a
proposal; two forks left open). Wrote the draft plan, opened draft PR #260,
posted the squash proposal with `scripts/pr-comment.sh`, and asked two questions
with recommendations: (1) the denial clause in CLAUDE.md and the Stop hook both
(recommended) or the Stop hook only; (2) the hook denies once (recommended) or
always. Ended with the `/go claude/sticky-comment-nudge` handoff block. (A
keepalive wake then parked the session into this file.)

**Operator**: «это не feat: а fix:»

**Agent**: agreed — the agents were already meant to reach the script, so this
closes a gap. Retitled PR #260 to `fix: …`, re-posted the squash proposal, and
switched the plan's commit list to `fix:`.

**Operator**: «а как план предполагает отличать редактуру поддерживаемого
коммента (squash/attestation) от например редактуры коммента-ответа на ревью
(или лбього другого)?»

**Agent**: explained that the plan tells them apart by the marker the script
itself keys on, read from the new body. Review replies go to `pulls/…` paths,
which the hook never matches. The one real gap is a PATCH of the sticky comment
with a markerless body. Closing it would need a GET of the edited comment. The
agent recommended against that, as a network call per edit.

**Operator**: «ну пусть лезет, команда редактуры коммента не такая частая»

**Agent**: revised the plan so the hook also fetches the comment an edit
targets: a literal id, `--edit-last`, or MCP `comment_id`. The fetch goes
through `gh` from the payload's cwd. A failed fetch or an unreadable `$id`
counts as no marker. Added tests with a stub `gh` on `PATH`. Updated the squash
proposal; a first post briefly carried an over-width line before it was fixed.
(verbatim in Last agent turn)

## 3. Intent

Make agents reach `scripts/pr-comment.sh` whenever they post or edit the squash
proposal or the finalize attestation, from any entry point, with the fix living
in muthur so adopters inherit it. The operator wanted a proposal, not an
immediate implementation.

## 4. Decisions

- **The hook is the primary layer.** It runs `PreToolUse`, before auto mode's
  classifier, so the agent is redirected before any denial. It beat relying on
  prose alone, because the incident's agent never loaded the skill that names
  the script.
- **The hook fires when either side of the write is provably sticky.** The new
  body counts when it is inline or a readable `body=@file`/`--body-file` that
  leads with a marker. The edited comment counts when it is fetched by GET and
  leads with a marker. Whatever it cannot prove passes, so ordinary comments and
  review replies are never nagged. The operator chose the fetch over avoiding
  the network call: «ну пусть лезет, команда редактуры коммента не такая
  частая».
- **The change is typed `fix:`, not `feat:`**, by the operator's call.
- **The GitHub MCP comment tools are covered too**, as the other door to the
  same write.
- **The shell parser and the deny-once record are extracted** from
  `file-tools-nudge.py` into a shared module and `session_state.py`. The
  hyphenated hook file cannot be imported.
- **The markers are duplicated in the hook**, and a test pins them to the
  script's `case`. Parsing the shell script for data at runtime was rejected.
- **`/squash-message`'s description is not widened.** It is always loaded, and
  the incident's agent had the words and still didn't load it.

## 5. Errors and dead ends

One `scripts/pr-comment.sh` post went out after `check-squash-message.sh` had
failed on an over-width line (a formatter had joined two lines). It was fixed
and re-posted at once: always run the check and read its result before posting.

## 6. State

- Branch `claude/sticky-comment-nudge`, pushed. Head `e283121` (plus this
  summary's commit).
- Draft PR https://github.com/vzakharov/muthur/pull/260.
- Plan: `docs/plans/sticky-comment-nudge.draft.do-not-implement.md`, still a
  draft with no go-ahead given.
- Squash proposal: comment posted at
  https://github.com/vzakharov/muthur/pull/260#issuecomment-6631797844. Working
  file `docs/remove-before-merging/squash-message.md`. The PR title is
  `fix: steer hand-rolled sticky-comment writes to scripts/pr-comment.sh`.
- Estimate:
  - This session: 1 h senior architect ("choosing which of three intervention
    points carries the fix needs judgement of the loop as a whole") + 0.5 h
    senior prompter ("the plan's rule wording has to be pinned before anyone
    implements it").
  - Remainder handed on: 6 h senior developer ("a PreToolUse hook that parses gh
    invocations and resolves body files, with the shared shell parser pulled out
    of an existing hook and tests for both") + 1.5 h senior prompter ("the rule
    clauses in CLAUDE.md and /relay change agent behaviour on every session and
    must be worded to fire without over-firing").
- Nothing running and no subscriptions.

## 7. Pointers

- The plan file above. It holds the whole design, the tests list, the DRY notes
  and the commit order.
- `scripts/pr-comment.sh`: the script and its markers.
- `.claude/hooks/file-tools-nudge.py`: the sibling hook whose parser and
  deny-once mechanic get extracted. Its tests are in
  `scripts/test_file_tools_nudge.py`.
- `.claude/hooks/permission-denied-phrase.sh`: the Stop-hook reason that gets
  the narrow-script sentence.
- `.claude/settings.json` (the `PreToolUse` groups) and
  `scripts/multi-repo-hooks.py` (the hook list) are the wiring sites.
- The update-muthur catalog `.claude/skills/update-muthur/catalog/g2-pr-loop.md`
  needs an entry for the new hook.
- Incident session: https://claude.ai/code/session_01DaohkDLDRgbyc3cZFB9iJW
- This session: https://claude.ai/code/session_01DaohkFr1NFWfQeAuZeSDAj

## 8. Next step

Wait for the operator. Two plan questions are still open: whether the denial
clause goes in both CLAUDE.md and the Stop hook (recommended) or the Stop hook
only, and whether the hook denies once (recommended) or always. After that, a
go-ahead: `/go claude/sticky-comment-nudge`.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

````text
Пропустил, что проверка упала, и выложил кривую версию. Сейчас исправлю.

Добавил это в план, коммит `e283121`. Теперь комментарий считается sticky, если маркер стоит хотя бы с одной стороны правки: в новом теле или в том комментарии, который правят.

Какой комментарий правят, хук узнаёт GET-запросом через `gh` из того же `cwd`, так что `{owner}/{repo}` подставляются так же, как в самой команде. Запрос делается, когда цель видна прямо в команде:
- числовой id в `issues/comments/<id>`;
- `gh pr comment --edit-last` (последний комментарий твоего пользователя в этом PR);
- `comment_id` в MCP-инструменте `update_issue_comment`.

Есть два случая, когда хук на ответ GitHub не опирается:
- **Запрос упал или не уложился в несколько секунд.** Тогда считается, что маркера нет, и правка проходит.
- **id не задан литералом** (`$id`). Тогда хук ничего не запрашивает. Инцидент он всё равно ловит: тело в той команде начиналось с маркера.

В тесты добавил случаи:
- PATCH squash-комментария телом без маркера отклоняется;
- такой же PATCH обычного комментария проходит;
- `--edit-last`, если последний комментарий — это аттестация, отклоняется;
- ответ на ревью проходит, и хук ничего не запрашивает;
- упавший запрос пропускает правку.

`gh` в тестах подменяется заглушкой первой в `PATH`, а не моками внутренних функций хука.

Squash-предложение обновил. Правда, сначала я выложил версию со строкой длиннее 72 символов: проверка упала, а я этого не заметил. Сразу перевыложил исправленную, сейчас в PR правильная версия.

Чтобы начать реализацию, открой новую сессию с:

```
/go claude/sticky-comment-nudge
```
````
