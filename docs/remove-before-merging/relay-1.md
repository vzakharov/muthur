# Relay 1 — "Show viewed" off by default on the review board

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator:** "Show viewed в ревью борде должно быть выключенным по
   умолчанию"

   **Agent:** Routed it as rung 1 → `/task` → planless `/go` (a one-file fix
   plus its test). Found the default was already off since #272; the filter came
   back on through legacy board docs whose `hideViewed: false` (written as the
   pre-#272 default on every board write) #272 read inverted as
   `showViewed: true`. Fixed it by no longer reading `hideViewed`, renamed the
   branch, ran `/polish`, opened draft PR #274 with the squash proposal and a
   review board. Reported it all in Russian. (verbatim in Last agent turn)

## Intent

The review board's "Show viewed" filter starts unchecked for every viewer,
including those whose board docs predate #272.

## Decisions

- **Drop the legacy `hideViewed` read entirely** rather than keep inverting it.
  Its `false` cannot be told from the old default, and its `true` equals the new
  default, so reading it can only do harm. The accepted cost: a viewer who
  deliberately showed viewed files before #272 sees the filter off once.
- **Keep the legacy `whitespace` inverted read**: its old default (`true`)
  inverts onto the new default (`showWhitespace: false`), so it carries no such
  ambiguity.
- **Kept the `hideViewed: true` beside `showViewed: true`** in the test "a board
  doc's show-side flag wins over a legacy one", which the polish subagent
  offered to drop. It guards against reading `hideViewed` again.

## Errors and dead ends

None.

## State

- Branch `claude/review-board-hide-viewed-default-9uyvw8` (renamed from
  `claude/festive-hypatia-9uyvw8`), head `2c88fce`, pushed, clean.
- Draft PR https://github.com/vzakharov/muthur/pull/274, open, mergeable, no
  checks reported yet. Not finalized, no vet run.
- Squash proposal posted on the PR, tracked at
  `docs/remove-before-merging/squash-message.md`.
- Review focus at `docs/remove-before-merging/review-focus.json`; board sticky
  comment posted on the PR.
- No plan file (planless).
- Estimate: 1.5 h middle developer — "tracing why a default already flipped
  still shows on means reading the old writer's persisted shape; the fix and its
  migration tests are routine once found". The whole task was done here; nothing
  remains to hand on.

### Watches

https://claude.ai/artifact/QhYpKRAVAa9CByN3wJnRCY

## Pointers

- `.claude/artifacts/src/review-board/entities/file/model/docs.ts` —
  `boardDocSchema` and `boardPrefsOf`, the fix.
- `.claude/artifacts/src/review-board/entities/file/model/docs.test.ts` — the
  legacy-flag tests.
- `git show f7dff8e` — #272, which introduced the inverted legacy read; the old
  writer's default is
  `git show f7dff8e^:.claude/artifacts/src/review-board/entities/file/model/store.ts`
  (its `initial: { whitespace: true, hideViewed: false, … }`).
- Transcript: https://claude.ai/code/session_01RAikuvDpeFwo6XTMwkdBT4

## Next step

Wait for the operator. The PR is ready for their review; `/finalize` (or
`/merge`) when they ask.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Код говорит, что «Show viewed» уже выключен по умолчанию — проверяю, откуда тогда он включается.

Теперь тесты.

Проверки зелёные. Ставлю оценку трудозатрат и переименовываю авто-ветку до первого коммита.

Ветки на remote нет, PR тоже нет, так что переименование только локальное.

Запушено. Дальше по `/go` идут `/polish` и `/pr`.

PR открыт. Дальше squash-предложение и доска ревью (авто-доска включена: `MUTHUR_AUTO_REVIEW_BOARD=on`).

Теперь доска ревью: авто-публикация включена, а sticky-комментария ещё нет.

Доска опубликована и уже на подписке. Вешаю на PR sticky-комментарий со ссылкой на неё.

Вова, галочка «Show viewed» включалась из-за старых сохранённых настроек, а не из-за дефолта. Дефолт выключили ещё в #272, но доска до сих пор слушала, что ей когда-то шептал старый код.

**Почему так было.** Код до #272 при каждом сохранении доски записывал все настройки целиком, вместе с дефолтным `hideViewed: false`. Достаточно было хоть раз сдвинуть диапазон или переключить пробелы, и это `false` оседало в базе. А #272, заботясь о «выборе зрителя», переворачивал его в «показывать просмотренные». Так галочка снова оказывалась включённой.

**Что изменилось.** Старый `hideViewed` больше не читается совсем. Его `false` не отличить от дефолта, а `true` говорит то же, что новый дефолт. Старый `whitespace` по-прежнему читается перевёрнутым: его прежний дефолт совпадает с новым, так что там проблемы нет. Цена у этого одна: кто до #272 сам включал показ просмотренных, один раз увидит галочку снятой.

Тесты пройдены, типы и линт чистые. Правка в `docs.ts`, к ней обновлён `docs.test.ts`.

Ветку переименовал в `claude/review-board-hide-viewed-default-9uyvw8`. Squash-предложение висит комментарием на PR. Доска этого PR подписана на комментарии, адресованные мне.

Доски уже открытых PR собраны со старым кодом. Исправление попадёт в них, только когда их пересоберут после мержа.

https://github.com/vzakharov/muthur/pull/274

https://claude.ai/artifact/QhYpKRAVAa9CByN3wJnRCY
```
