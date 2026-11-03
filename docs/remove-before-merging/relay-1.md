# Relay 1 — pricing a five-line cap on Markdown prose blocks

## Standing constraints

None stated.

## The conversation

1. **Operator:** «чего нам будет стоить добавить правило не более пяти строк
   прозы на абзац/элемент списка в md»

   (Routed as rung 2 of CLAUDE.md's ladder — a question, no change; nothing in
   the repo was edited.)

2. **Operator (mid-turn):** «стоить = скорее в плане реализации, а не
   бласт-радиуса»

3. **Operator (mid-turn):** «rationale = сложно читать, плюс при диффе всё
   слипается»

   **Agent:** priced the implementation, with the counts measured (verbatim in
   Last agent turn).

## Intent

Vova is weighing a convention: no paragraph or list item in tracked Markdown
longer than five (80-column, prettier-wrapped) lines. The reasons are
readability, and diffs where long blocks run together. They asked for the
implementation cost, explicitly not the blast radius.

## Decisions

None taken — the operator has not yet chosen to implement. The options put to
them:

- a full cleanup at 5 lines (432 blocks to split by hand);
- a softer threshold of 6–7 lines (264 blocks at 6, 107 at 8);
- a ratchet that checks only blocks the branch touched. The agent noted it reads
  as the "fix it later" CLAUDE.md § "Key principles" discourages, and leaned
  toward the first two.

Natural home for the rule text: `.claude/rules/markdown-wrap.md`. Natural shape
for the check: a `scripts/check-markdown-*.sh` modelled on
`scripts/check-markdown-tables.sh`, wired into `scripts/vet.sh`, skipping
`.prettierignore`d files (GitHub-bound text is unwrapped, so line count means
nothing there).

## Errors and dead ends

None.

## State

- Branch `claude/markdown-paragraph-cap-7xl4uh`, renamed locally from the
  harness's `claude/keen-noether-7xl4uh`, which was never pushed. The base is
  `6c8625d`, and this summary is the only commit on top.
- No PR, no plan file, nothing running or scheduled.
- Estimate: 1 h senior analyst, the whole of this session's task, so there is no
  remainder to hand on.

## Pointers

- The measuring script lived in this session's scratchpad and does not survive
  it: a line-based pass over `git ls-files '*.md'` that skips frontmatter,
  fences, headings, tables, blockquotes and HTML comments. It treats each list
  item and each paragraph as one block and counts its physical lines. Rewrite it
  under `tmp/` to re-measure.
- `scripts/check-markdown-tables.sh`, `scripts/test_markdown_tables.py` — the
  pattern a new check would copy.
- `scripts/check-claude-md-size.sh` — the char cap, at 28 532 of 30 000 when
  measured, which constrains rewording `CLAUDE.md`'s 20 over-long blocks.
- Transcript: https://claude.ai/code/session_01DaohkBhVnymkcskczYQ5j9

## Next step

Wait for the operator: the question was answered and nothing is pending. Should
Vova decide to proceed, that is a change, so the route is `/task`, with the
threshold and full-vs-ratchet choice as its inputs.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Вова, это вопрос без правки, так что я ничего не менял, только посчитал.

**Сам проверятель стоит недорого. Дорого обойдётся старая проза: 432 абзаца и пункта списка из 2312 уже длиннее пяти строк, и сидят они в 74 файлах из 89.** Механически их не поделишь, у каждого надо найти шов, по которому мысль режется на две.

Твой довод про дифф мне нравится, и вот почему. Перенос на 80 колонок уже даёт одну строку диффа на одну правку. Но слово, вставленное в начало абзаца, заставляет prettier переразложить весь хвост абзаца. Значит, длина абзаца и есть самый большой кусок диффа, который может дать правка в одно слово. Если ограничить абзац пятью строками, ограничится и этот кусок.

**Из чего складывается цена:**

1. **Проверятель, около 3–4 часов.** Скрипт `scripts/check-markdown-…` по образцу `check-markdown-tables.sh`, плюс тесты в духе `test_markdown_tables.py`. Ему придётся понимать пропуск code fence и frontmatter, вложенные списки (у пункта считается только его собственный текст, без подпунктов), таблицы, цитаты и HTML-комментарии. Ещё одна строка в `vet.sh` и абзац в его шапке. Файлы из `.prettierignore` надо пропускать: там тексты для GitHub без переноса строк, и абзац в них занимает одну физическую строку.
2. **Само правило, около часа.** Естественно ложится в `.claude/rules/markdown-wrap.md`, он и так про форму прозы и диффы. Нового файла не нужно.
3. **Чистка существующей прозы, главная статья: 20–35 часов редакторской работы**, если по 3–5 минут на абзац. Для агента это раздача по файлам субагентам, токенов уйдёт заметно. Сильнее всего задеты `.claude/costs/CLAUDE.md` (25), `plan/SKILL.md` (22), `squash-message/SKILL.md` (21) и корневой `CLAUDE.md` (20).
4. **`CLAUDE.md` правится через staged-копию, и там тесно.** Лимит считает символы (28 532 из 30 000), так что пустые строки почти ничего не стоят. Но при разрезании абзаца обычно нужна новая вводная фраза, а свободных символов около 1,5 тысячи на 20 абзацев. Скорее всего, по ходу придётся заодно ужимать текст.

**Как растёт чистка от порога:** при пяти строках править 432 абзаца, при шести 264, при восьми 107. Пять строк приходится ровно на самую населённую длину, 242 абзаца, так что «пять» против «шести» почти удваивает объём чистки.

**Можно не платить за чистку сразу.** Есть вариант с храповиком: проверять только абзацы, которые ветка тронула. Это плюс 1–2 часа к проверятелю, а старые простыни будут исправляться по мере того, как их кто-то правит. Но это и есть «починим потом», которое `CLAUDE.md` прямо не любит. Так что я бы выбирал из двух вариантов: полная чистка при пяти строках или честный порог в шесть-семь строк.

Мой подсчёт лежит в `/tmp/claude-0/-home-user-muthur/8dda4130-fa07-5812-88e0-cd3f549a44f0/scratchpad/measure.py`, если захочешь прогнать другие пороги.
```
