# Relay 1 — review board skips files GitHub hides in diffs

## Standing constraints

None stated by the operator.

## The conversation

1. **Operator (via `/task`)**: "The review board's collector should leave off
   every changed file that `.gitattributes` marks `linguist-generated` — the
   same mechanism GitHub uses to collapse generated files in a PR diff. […] Port
   the same idea here, in this repo's own style and conventions, so the
   adopter's next /update-muthur sync takes this repo's version and drops its
   divergence. […] Also worth deciding here (the adopter left it out): whether
   the review-board skill should say that a generated file is marked in
   `.gitattributes` with `linguist-generated=true` to keep it off the board, and
   whether a focus entry naming a generated path needs a clearer error than 'not
   among the changed files'." (Condensed: the rest was the adopter's reference
   implementation, from vzakharov/vovazakharov.com commit 8b6af84d:
   `generated.ts` with `CHECK_GENERATED` and `generatedPaths()`, a filter in
   `collect()`, and `generated.test.ts`.)
   - **Agent**: went planless. Implemented the filter, a clearer focus error and
     a skill paragraph. Ran `/polish` (one wording fix) and `/pr`, which opened
     draft PR #273 with its squash proposal. Answered both open questions with
     yes.
2. **Operator**: "а где доска?)"
   - **Agent**: explained that `/pr` builds the first board only when
     `MUTHUR_AUTO_REVIEW_BOARD` is set, and it is unset here. Wrote the focus
     file, built and published the board, posted the sticky comment and
     confirmed the watch.
3. **Operator**: "так, ну "generated" было именно в преемнике; в общем случае
   это могут быть и другие файлы, или нет? -- нужно использовать терминологию
   гитхаба."
   - **Agent**: agreed and renamed everything to GitHub's "hidden by default in
     diffs": the module, identifiers, focus error, skill, PR title and body,
     squash proposal and focus. Republished the board. (verbatim in Last agent
     turn)

## Intent

A port of the adopter's divergence into the template, written in this repo's
conventions, so vovazakharov.com's next `/update-muthur` takes this version. The
operator wants the feature named in GitHub's terms, by its effect: a file
"hidden by default in diffs". It is not limited to generated output.

## Decisions

- **Planless** (task Step 1 no): the change is small and holds in the head.
- **Name by effect, not attribute**: `hidden-in-diffs.ts` with
  `CHECK_HIDDEN_IN_DIFFS` and `hiddenInDiffs()`. `linguist-generated` appears
  only as the literal key. The operator asked for this, citing GitHub's docs
  ("Customizing how changed files appear on GitHub": "hidden by default in
  diffs").
- **Focus error**: a focus entry naming a hidden path throws "hidden by default
  in diffs (linguist-generated in .gitattributes), so it is off the board; mark
  what produces it instead". It beat the misleading "not among the changed
  files". `parseFocus` takes a third argument, `hiddenInDiffs`.
- **Skill paragraph**: added to `.claude/skills/review-board/SKILL.md` Step 1.
  It is the only place agents learn about the filter.
- **Attributes read from HEAD** (`--source=HEAD`, git ≥ 2.40) so the board stays
  built from git alone.

## Errors and dead ends

The first naming ("generated") was the adopter's word. The operator corrected it
(message 3).

## State

- Branch `feat/review-board-skip-generated`, pushed. Head is f6f8690e before
  this relay commit.
- PR #273, draft, open: "feat: keep files GitHub hides in diffs off the review
  board". The squash proposal comment is current, tracked in
  `docs/remove-before-merging/squash-message.md`. The review-board sticky
  comment is posted.
- No plan file. `/polish` ran once (accaa04), before the rename commit.
- `.claude/artifacts/vet.sh` passes. `/finalize` has not run.
- Estimate unchanged (this session did the whole task): 1.5 h middle developer
  "a small git-plumbing filter with a pure parser and tests, inside an existing
  collector whose shape it follows" + 0.5 h senior prompter "the skill line and
  the focus error must state the convention where an adopting agent meets it".
  Nothing is handed on.

### Watches

https://claude.ai/artifact/JiBRsTGhEYzjykXZ1XcvQi

## Pointers

- `.claude/artifacts/src/review-board/scripts/hidden-in-diffs.ts` (+
  `.test.ts`), `collect.ts` (`readHidden`, `collect()`), `focus.ts`
  (`parseFocus`).
- `.claude/skills/review-board/SKILL.md` Step 1, the paragraph on files hidden
  in diffs.
- `docs/remove-before-merging/review-focus.json`, `squash-message.md`.
- Adopter's original: vzakharov/vovazakharov.com 8b6af84d on
  `claude/cube-wesl-trial`.
- Transcript: https://claude.ai/code/session_01DaohkFq4ZNqzKfiYJuj4Sh

## Next step

Wait for the operator. Nothing is pending. The PR awaits their review, and
`/finalize` when they ask.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
The board is rebuilt with the new names. Last step: updating the PR description.

Да, в общем случае это не только сгенерированные файлы. В документации GitHub пометка `linguist-generated` означает «hidden by default in diffs» («скрыт по умолчанию в диффах»), и ею помечают что угодно: lockfile, вендорный бандл, снапшоты. «Generated» было словом из шейдеров адоптера. Сам GitHub зовёт так и атрибут, но говорить надо о его эффекте. Переименовал, vet проходит:

- **Код.** Модуль теперь `hidden-in-diffs.ts`, внутри `CHECK_HIDDEN_IN_DIFFS` и `hiddenInDiffs()`. Слово `linguist-generated` осталось только там, где это буквальное имя атрибута. В тестах среди помеченных файлов теперь есть и `pnpm-lock.yaml`, а не одни сгенерированные.
- **Ошибка focus.** Теперь звучит так: «hidden by default in diffs (linguist-generated in .gitattributes), so it is off the board; mark what produces it instead».
- **Скилл.** С доски уходит всё, что GitHub скрывает по умолчанию в диффах, с примерами: сборка, lockfile, вендорный бандл.
- **PR.** Заголовок теперь `feat: keep files GitHub hides in diffs off the review board`. Описание, предложение для squash и focus обновлены под новые слова.

Доска пересобрана по той же ссылке: https://claude.ai/artifact/JiBRsTGhEYzjykXZ1XcvQi

Одна оговорка: адоптер при следующем `/update-muthur` получит другие имена, чем в своём расхождении (`generated.ts` → `hidden-in-diffs.ts`). Ему придётся взять нашу версию целиком, а не слить свою. Именно этого мы и хотели, но удивиться он может.
```
