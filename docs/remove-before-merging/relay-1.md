# Relay 1 — review board title, Show-viewed default

Parked by the cache keepalive's last wake, not by the operator.

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator:** «давай небольшой fix: ревью борды -- название борды должно
   упоминать название ветки и если доступно номер PR»

   **Agent:** Routed via `/task` → planless `/go` (small change, every file
   nameable). Renamed the branch to `claude/review-board-title-o422ih`, added
   `pr` to the board payload (collector reads
   `gh pr view --json number,baseRefName`), `boardTitle(branch, pr)` feeding
   both the page `<title>` (HTML-escaped) and the toolbar heading. Polish, draft
   PR #272, squash proposal, focus file, board published.

2. **Operator (board comment, thread dd5d0f9b…):** «почему у нас Show viewed по
   дефолту включен?»

   **Agent (thread reply):** Not a decision but an artifact of the inversion:
   #265 had an opt-in "Hide viewed" defaulting off; #269 flipped the label to
   "Show viewed" (`!hideViewed`) but kept the stored default `false`. Offered to
   flip both defaults to true.

3. **Operator (board comment, same thread):** «оба Show должны быть по дефолту
   false, так и есть?»

   **Agent:** Read as a directive. Flipped `hideViewed` default to `true` in
   `entities/file/model/docs.ts` and `store.ts` (37df9da); replied in thread
   that "Show whitespace" was already off and "Show viewed" now is too. Polish
   (no change), PR body, squash proposal and focus refreshed, board republished.

4. **Operator:** «я не понимаю почему во всех схемах осталось hide...»

   **Agent:** `hideViewed` (and `whitespace`, meaning "ignore whitespace") are
   keys of the per-viewer board doc stored in the artifact's db; #269 inverted
   only the UI and deliberately kept the stored flags ("saved state keeping its
   old flags"). Proposed renaming to `showViewed` / `showWhitespace`, default
   `false`, migrating old docs on read (negating `hideViewed` / `whitespace`),
   as #269 migrated `viewedBlob` → `viewed`; asked «Сделать?»

   Then, after the polish report, the agent added that polish's one open `/dry`
   call — the filter defaults written twice, the schema fallback in `docs.ts`
   and the store's initial value in `store.ts` — dissolves into the same rename,
   and asked again (verbatim in Last agent turn).

## Intent

A board whose name says which branch and PR it reviews, and toolbar filters that
start off ("Show …" unchecked) on a fresh board. The operator is questioning the
inverted stored names (`hide…`) behind "Show …" controls.

## Decisions

- **Title format** `Review #<pr> · <branch>`, dropping the missing part;
  `Review board` when neither. Lives in `shared/review-data/title.ts`;
  positional `(branch, pr)` because the repo's `masd/no-pick-omit` lint forbids
  `Pick<ReviewData, …>`.
- **One `gh pr view` call** for PR number and base ref, parsed with zod
  (validate at boundary), rather than a second `gh` call.
- **Default flip, not rename** (so far): `hideViewed` default `true` in both
  places. The rename is proposed and unanswered.
- Polish's `/dry` question — extract the duplicated filter defaults into one
  constant? — was left open: the schema fallback applies to docs saved before
  the field existed, the store value to fresh boards; the rename would make both
  plain `false`.

## Errors and dead ends

- First `boardTitle` took `Pick<ReviewData, "branch" | "pr">`; lint rejected it
  (`masd/no-pick-omit`); changed to positional params.

## State

- Branch `claude/review-board-title-o422ih`, head and origin at afed5c7.
- PR https://github.com/vzakharov/muthur/pull/272 — open, draft, no CI checks
  reported.
- No plan file (planless `/go`).
- Working files on the branch: `docs/remove-before-merging/squash-message.md`
  (squash proposal, posted as PR comment), `review-focus.json` (board focus).
- Session estimate: 1.5 h middle developer — the title field, the default flip
  and their tests. Remainder, if the rename is approved: about 1 h middle
  developer, a stored-doc key rename with migrate-on-read and its test.

### Watches

https://claude.ai/artifact/DBP8WHAnfZgbrH656PKfVr

## Pointers

- `.claude/artifacts/src/review-board/entities/file/model/docs.ts` — board prefs
  schema (`whitespace`, `hideViewed`, `focusOnly`) and the `viewedBlob` →
  `viewed` migrate-on-read precedent (`filePrefsOf`).
- `.claude/artifacts/src/review-board/entities/file/model/store.ts` — the
  store's initial board prefs and `sameBoard`.
- `.claude/artifacts/src/review-board/pages/board/board/ui/mount-board.ts` —
  inverts the flags for the toolbar (`showWhitespace: !board.whitespace`,
  `showViewed: !board.hideViewed`) and writes them back.
- `.claude/artifacts/src/review-board/pages/board/toolbar/ui/toolbar.ts` — the
  "Show whitespace" / "Show viewed" checkboxes.
- `.claude/skills/review-board/SKILL.md` — publishing and comment handling.
- Predecessor transcript:
  https://claude.ai/code/session_016Z4TKon3MX7sAopCE4t4eC

## Next step

The operator's last question, «я не понимаю почему во всех схемах осталось
hide...», was answered with a proposal to rename the stored keys to `showViewed`
/ `showWhitespace` (default `false`, old docs migrated on read) and «Сделать?» —
unanswered. Wait for the operator; on a yes, implement it through `/go` §
"Planless entry", add a migration test, then `/pr` (which refreshes the squash
proposal and republishes the board).

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Ответил в треде. Дальше обновляю тело PR, squash-предложение и доску под новый коммит.

Добавляю новый дефолт в focus-файл и пересобираю доску.

PR #272 обновил: в описании и в squash-предложении появился новый дефолт для «Show viewed», доска перепубликована по той же ссылке. Polish ничего не поменял.

Он нашёл одно место, которое стоит решить вместе с твоим вопросом про `hide…`. Дефолт фильтров записан дважды: в `docs.ts` это значение для сохранённых настроек, где поля ещё нет, в `store.ts` — для свежей доски. Поэтому мою правку пришлось вносить в оба места. Если переименовать в `showViewed`/`showWhitespace` с миграцией при чтении, оба дефолта станут обычными `false`. Их тогда можно держать одной константой, и путаница с двойным отрицанием тоже уйдёт.

Так что вопрос прежний: переименовываю? Скажи «да» — сделаю.
```
