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
always. Ended with the `/go claude/sticky-comment-nudge` handoff block.
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
- **The hook only fires when it can prove a sticky body.** That means an inline
  body or a readable `body=@file`/`--body-file` leading with a marker.
  Unresolved bodies pass, so the hook never nags about ordinary comments.
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

None.

## 6. State

- Branch `claude/sticky-comment-nudge`, pushed. Head `d74be37` (plus this
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

Wait for the operator. They will review PR #260 and answer the two open
questions or give a go-ahead (`/go claude/sticky-comment-nudge`).

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

````text
Привет, Вова. Это ступень 1 лестницы: просьба меняет сам muthur (хук, правило или скилл), так что иду через `/task`.

Создаю ветку и пишу план.

План закоммичен, публикую его через `/pr`.

Теперь squash-предложение — через `/squash-message`.

Написал план и отдаю его тебе на одобрение, а не реализую сразу: ты просил предложение, и в нём осталось два выбора за тобой. Если хочешь без ревью, скажи `go`, и я начну реализацию в этой сессии.

**Почему агент прошёл мимо скрипта.** `scripts/pr-comment.sh` упомянут только в `/squash-message` и `/finalize`. Если агент правит sticky-комментарий откуда-то ещё (из Next step после relay, по просьбе, по памяти), он о скрипте просто не узнаёт. И на ручном пути нет ничего, что вернуло бы его к скрипту.

**Что предлагаю, от сильного к слабому:**

1. **`PreToolUse`-хук `sticky-comment-nudge.py`.** Это главный слой, и только он один остановил бы инцидент на #248. Хук ловит запись комментария через `gh api …issues/…/comments` (POST/PATCH или поле `body`), `gh pr comment` и MCP-инструменты `add_issue_comment`/`update_issue_comment`, если тело начинается с маркера. Тело читается и инлайн, и из `body=@файл`: файл хук открывает и проверяет первые байты. Хук отказывает один раз и называет точную команду `scripts/pr-comment.sh squash <n> <file>`. Он срабатывает до классификатора, так что до отказа и до фразы для оператора дело не доходит. Повтор той же команды проходит, как у «Did you forget?». Тело, которое хук не может прочитать (`body=@$f`), он пропускает, чтобы не задевать чужие комментарии.
2. **Одна фраза в CLAUDE.md** в пункт про отказ auto-режима: прежде чем просить фразу, проверить, нет ли в `permissions.allow` узкого скрипта для этого действия. Список allow сам служит реестром, поэтому правило подхватит и будущие скрипты. Та же фраза идёт в Stop-хук.
3. **`/relay`:** если в Next step есть действие, которым владеет скилл, он этот скилл называет. Например, «refresh the squash proposal» превращается в `/squash-message update-only`.

Повторов кода не будет: парсер шелла и механизм «отказать один раз» я вынесу из `file-tools-nudge.py` в общий модуль. Маркеры будут жить константой в хуке, а тест проверит, что они совпадают с теми, что в скрипте.

**Вопросы. Рекомендации уже заложены в план, так что молчание тоже ответ:**

1. Слой 2 ставить и в CLAUDE.md, или только в Stop-хук? Рекомендую в оба места. Сам по себе Stop-хук в этом инциденте промолчал бы: фраза в ответе уже стояла в блоке кода, а такой ответ он считает выполненным.
2. Отказывать один раз или всегда? Рекомендую один раз, иначе скрипт становится единственной дорогой даже тогда, когда ломается именно он.

План и черновой PR: https://github.com/vzakharov/muthur/pull/260. Предложение для squash я там уже повесил тем самым скриптом. Он отработал на ура, что в этой истории звучит даже немного обидно.

Для реализации начни новую сессию с:

```
/go claude/sticky-comment-nudge
```

Ждёт твоего ответа.
````
