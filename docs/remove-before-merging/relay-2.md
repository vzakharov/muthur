# Relay 2 — the paragraph-cap checker needs no parser

## Standing constraints

None stated.

## The conversation

The session opened as `/relay take claude/markdown-paragraph-cap-7xl4uh` on a
`metkain/metka` container. The branch lives in `vzakharov/muthur`, so the attach
found nothing in `origin`. The session read `relay-1.md` through `gh api`, then
attached muthur with `add_repo` only for this park.

1. **Operator (mid-turn, answering relay-1's priced reply):** «скорее в плане
   реализации — я имел в виду, насколько неэлегантно будет выглядеть проверялка
   и не придётся ли ставить доп пакеты (например для ast парсинга)»

2. **Operator (mid-turn):** «тем более ты всегда себя недооцениваешь»

   **Agent:** no extra packages and no AST. Prettier has already normalised
   every tracked `.md`, so a stdlib line scan is enough. A 79-line prototype
   reproduced relay-1's counts exactly, and a spot-check found no false
   positives. Two small blemishes. Conceded the 3–4 h was human-hours. Asked for
   the threshold and full-vs-ratchet choice (verbatim in Last agent turn).

## Intent

Vova is weighing a rule: no paragraph or list item in tracked Markdown longer
than five prettier-wrapped lines, because long blocks are hard to read and run
together in diffs. They care about the implementation: how inelegant the checker
would be, and whether it drags in dependencies such as a Markdown AST parser.
The blast radius is explicitly not the question. They think the agent
underestimates itself.

## Decisions

None taken by the operator yet. Established facts the successor should not
re-derive:

- **No parser.** `scripts/check-markdown-wrap.sh` holds every tracked `.md` to
  prettier's output, so blocks are blank-line separated and list items start at
  a marker. A line scan is exact on that input. A real parser would come only
  through `npx`, like `scripts/prettier.sh`, because muthur deliberately has no
  `package.json` (adopters' own would collide). It would add a cold fetch and
  nothing else.
- **Blemish 1:** fence tracking would exist twice, in the awk in
  `scripts/check-markdown-tables.sh` and in the new Python. The proposed fix is
  one Python checker carrying both rules.
- **Blemish 2:** on an unformatted file the count is noise, but
  `check-markdown-wrap` already fails such a file.
- Counts on this branch: 432 blocks over 5 lines, 264 over 6, 107 over 8, in 74
  of 90 tracked `.md` files. Five lines is the most populated length (242
  blocks), so a cap of five instead of six nearly doubles the cleanup.
- Relay-1's options still stand: a full cleanup at 5, an honest threshold of
  6–7, or a ratchet over touched blocks, which relay-1 advised against as "fix
  it later".

## Errors and dead ends

- Attaching to the branch from a metka session failed, since the branch is not
  in metka. A successor should run in a session on `vzakharov/muthur`.

## State

- Branch `claude/markdown-paragraph-cap-7xl4uh` in `vzakharov/muthur`, base
  `6c8625d`. On top: relay-1's commit `8460a00`, and this park's commit, which
  adds this file and the prototype.
- No PR, no plan file, nothing running or scheduled.
- Estimate for this session: 1 h senior developer, judging whether a stdlib line
  scan can stand in for a Markdown parser. No remainder: implementation is not
  yet asked for.
- The muthur sync offer was made; do not make it again.

## Pointers

- `docs/remove-before-merging/check_paragraph_cap.py` — the prototype,
  `python3 -I <it> <cap> <files…>`. Run it on `git ls-files '*.md'` minus
  `.prettierignore`'d paths. Skips frontmatter, fences, headings, tables,
  blockquotes and HTML comments. A list item counts only its own lines.
- `scripts/check-markdown-tables.sh`, `scripts/test_markdown_tables.py`,
  `scripts/check-markdown-wrap.sh`, `scripts/prettier.sh` — what a real check
  joins or replaces.
- `docs/remove-before-merging/relay-1.md` — the pricing, with the per-file worst
  offenders and the `CLAUDE.md` char-cap constraint.
- Transcript: https://claude.ai/code/session_01DaohkFigbBUihN1tw7cQBV

## Next step

Wait for the operator. The pending question is theirs: the threshold (5, or 6–7)
and full cleanup versus ratchet. A go-ahead is a change, so `/task` with those
as inputs.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Вова, ветка не в metka, а в `vzakharov/muthur` — читаю её relay-сводку, чтобы ответить по реализации.

Вова, подхватил сессию https://claude.ai/code/session_01DaohkBhVnymkcskczYQ5j9. Одна оговорка: эта сессия открыта на `metka`, а ветка лежит в `vzakharov/muthur`. Поэтому я её не подключал, а только прочитал сводку и склонировал muthur в `tmp/` для замеров.

**Лишние пакеты не нужны, и проверялка получается короткой. Разбирать Markdown не надо, потому что это уже сделал prettier.** `check-markdown-wrap.sh` и так требует, чтобы каждый `.md` был отформатирован prettier. А в таком файле блоки всегда разделены пустой строкой, и каждый пункт списка начинается с маркера. Поэтому хватает построчного прохода на стандартной библиотеке Python. Ни AST, ни remark, ни pip.

Это не догадка, я проверил прототипом: `tmp/para-cap/check_paragraph_cap.py`, 79 строк. На дереве muthur он насчитал ровно то же, что прошлая сессия: 432 блока длиннее 5 строк, 264 длиннее 6, 107 длиннее 8, всего в 74 файлах. Три случайные находки я посмотрел глазами, все три настоящие простыни, ложных срабатываний среди них нет. Пропускает он frontmatter, code fence, заголовки, таблицы, цитаты и HTML-комментарии. У пункта списка считаются только его собственные строки, подпункты идут отдельными блоками.

Некрасивых мест два, оба мелкие:

- **Отслеживание code fence будет написано дважды**: в awk внутри `check-markdown-tables.sh` и в новом Python-файле. Это лечится, если перенести проверку таблиц в тот же Python-скрипт, тогда будет одна проверялка Markdown на два правила.
- **Проверка зависит от порядка.** На файле, который prettier ещё не отформатировал, она выдаст мусор. Но такой файл и так завалит `check-markdown-wrap`, так что ничего не проскочит.

Настоящий парсер подключить можно, но только через `npx`, как подключён prettier: `package.json` в muthur нет специально, чтобы не мешать тем, кто его подключает. На отформатированном тексте он ничего не добавит, а холодный запуск сделает медленнее.

Насчёт недооценки ты прав. Мои «3–4 часа» — это человеко-часы для журнала затрат, а сам прототип занял несколько минут. Если доводить его до тестов и подключать в `vet.sh`, это меньше часа работы агента. Дорогой остаётся только чистка старой прозы.

Если решишь делать, это будет правка в muthur, и начинать её лучше в сессии на этом репозитории. Мне нужны от тебя порог (5 или 6–7) и выбор между полной чисткой и проверкой только тронутых блоков.

И ещё: muthur ушёл на 23 коммита вперёд с последней синхронизации metka. Если хочешь, запущу отдельную сессию `/update-muthur`.
```
