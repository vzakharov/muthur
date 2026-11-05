# Relay 1 — parked

## Standing constraints

None stated.

## The conversation

1. **Operator** (via `/task`):

   > Объясни в доках для адоптеров, что адоптеру делать с `LICENSE` (MIT,
   > добавлен в dec7e753, #256). Сейчас про это в доках ничего нет. Чтобы не
   > потерять мысль, писал в закрытом vzakharov/muthur#261; там два пункта:
   >
   > 1. Решение по файлу. `LICENSE` нет ни в каталоге, ни в `catalog/never.md`,
   >    поэтому `/update-muthur` Step 4a натыкается на него как на путь, о
   >    котором ничего не решено, и каждый адоптер спрашивает своего оператора
   >    заново. Нужна запись в `never.md`, как у `README.md`: это лицензия
   >    самого muthur, её не вендорят, а у репозитория адоптера свои условия.
   > 2. Что MIT требует от вендоренных файлов. MIT просит сохранять copyright и
   >    permission notice во «всех копиях или существенных частях». Адоптеры
   >    берут скиллы и скрипты дословно, поэтому в `ADOPTING.md` или
   >    `docs/adopting/sync.md` нужна строка: распространяется ли на них это
   >    требование, и если да, где в дереве адоптера лежит уведомление
   >    (`NOTICE`, заголовок файла или строка в файле конвенций).
   >
   > Поводом стал синк metkain/metka до 3e94db8: там `LICENSE` отклонили как
   > лицензию шаблона.

   **Agent:** did it directly without a plan (override: `plan`). Opened draft PR
   #262. Asked the operator one open question: the path `.claude/LICENSE.muthur`
   was the agent's own pick, and a root `NOTICE` might read clearer since
   vendored files also live outside `.claude/` (e.g. `scripts/`) — a two-line
   amendment either way. Also flagged that the MIT reading is an interpretation,
   not legal advice, and that `Fixes #261` references an issue closed as
   `not_planned`. (verbatim in Last agent turn)

## Intent

Settle once, for every adopter, what happens to muthur's root `LICENSE`, and say
whether MIT's notice clause reaches vendored files and where the notice lives in
an adopting tree.

## Decisions

- **MIT does apply** to verbatim-vendored skills and scripts (substantial
  portions). Satisfied by one verbatim copy of `LICENSE` at
  `.claude/LICENSE.muthur` covering every file taken; beat per-file headers
  (touch every vendored file, break verbatim syncs) and a conventions-file line
  (doesn't carry the permission text). Root `NOTICE` was the runner-up — left to
  the operator as the open question above.
- **Home of the rationale** is the `LICENSE` entry in
  `.claude/skills/update-muthur/catalog/never.md`; `ADOPTING.md` Step 4 and
  `/detemplate` Step 5.2 state the action briefly.
- **`/detemplate` moves `LICENSE` to `.claude/LICENSE.muthur`** instead of
  deleting it with the other `never` entries, since a fork keeps muthur's files.
- **`/update-muthur` Step 4a gained a rule**: a path the source catalog marks
  `never` is not offered; its entry's instructions are the whole verdict, and
  nothing goes in the record. Needed because Step 3/4a never consulted
  `never.md`, so the entry alone would not have stopped the question.
- **`[attn adopters]`** on the commit/PR: existing adopters add the copy once.

## Errors and dead ends

None.

## State

- Branch `docs/adopter-license`, pushed; head before this relay `02743ab`.
- Draft PR https://github.com/vzakharov/muthur/pull/262, title
  `fix: [attn adopters] #261 LICENSE is never vendored, its notice is`.
- Squash proposal posted as a PR comment; tracked in
  `docs/remove-before-merging/squash-message.md`.
- `/polish` ran (commit `3510c7c`); `./scripts/vet.sh` green locally.
- Not finalized, not ready for review. No CI watch, no subscription.
- Estimate unchanged and complete for this session: 1.5 h senior prompter + 0.5
  h middle analyst. No remainder handed on.

## Pointers

- `.claude/skills/update-muthur/catalog/never.md` — the `LICENSE` entry.
- `.claude/skills/update-muthur/SKILL.md` § Step 4a — the `never` rule.
- `.claude/skills/detemplate/SKILL.md` Step 5.2.
- `ADOPTING.md` Step 4.
- `docs/issue/261/issue.md` — the issue export.
- Predecessor transcript:
  https://claude.ai/code/session_01DaohkEGD6ehkW7EJPLcbVB

## Next step

Wait for the operator — their answer to the open question (keep
`.claude/LICENSE.muthur` or switch to a root `NOTICE`), or `finalize`.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Now the `/go` tail: `/polish`, then `/pr`.

Пишу предложение squash-тела для PR #262.

Вова, привет. Сделал сразу, без плана: правка небольшая, и все затронутые файлы я назвал заранее. Если хочешь план, скажи `plan`, и я его напишу.

https://github.com/vzakharov/muthur/pull/262

**Решение:** адоптер не вендорит `LICENSE` как свой корневой файл. Но текст лицензии он копирует без изменений в `.claude/LICENSE.muthur`. MIT требует, чтобы уведомление было в каждой копии существенной части, а дословно скопированный скилл или скрипт ею и является. Поэтому требование адоптеров касается. Один файл покрывает всё, что адоптер взял из muthur. Свою корневую лицензию адоптер выбирает сам.

Что изменилось:
- **`catalog/never.md`**: новая запись `LICENSE` с disposition `never` и объяснением, куда идёт текст. Там же сказано, что при синке изменения `LICENSE` переносятся в эту копию.
- **`ADOPTING.md` Step 4**: одна фраза — корневой `LICENSE` не копировать, текст положить в `.claude/LICENSE.muthur`.
- **`/detemplate` Step 5.2**: в форке `LICENSE` переносится в `.claude/LICENSE.muthur`, а не удаляется вместе с остальными `never`-записями. Иначе форк потерял бы уведомление.
- **`/update-muthur` Step 4a**: путь с пометкой `never` в каталоге оператору больше не предлагается. Раньше `never.md` в этом шаге не читался, поэтому одна запись в `never.md` вопрос metka не закрыла бы.

Коммит и PR помечены `[attn adopters]`. Уже существующие адопторы, metka в том числе, на следующем синке один раз добавят `.claude/LICENSE.muthur`.

Вопрос к тебе: путь `.claude/LICENSE.muthur` выбрал я. Если вендоренные файлы адоптера лежат и вне `.claude/`, например в `scripts/`, корневой `NOTICE` может читаться понятнее. Это поправка на пару строк, не переделка.

`vet.sh` прошёл. `/polish` поправил одну фразу в `ADOPTING.md`. Предложение squash-тела висит комментарием в PR. В тексте я ссылаюсь на `#261`, хотя он закрыт как `not_planned`. MIT-часть — моё прочтение лицензии, а не юридическое заключение.
```
