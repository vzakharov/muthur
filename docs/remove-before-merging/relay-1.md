# Relay summary 1 — parked

## Standing constraints

None stated.

## The conversation

1. **Operator:** «некоторые адоптерские вотермарки разрослись до неприличных
   размеров (см. например
   https://github.com/metkain/metka/blob/76371efbb1e4a153a6a020f8a2d5effe05cc4d02/.claude/skills/update-muthur/watermark.json),
   нужно придумать как их можно разбивать (и как мерить, учитывая что json не
   переносится по строкам)»

   **Agent:** Treated this as a question (rung 2) and answered it. Metka's
   watermark is 48 KB: 484 physical lines, 924 at 80 columns. `adopted` makes up
   36 KB, and about 40% of its note paragraphs are sync history. Proposed three
   layers: (1) a rule that notes are rewritten, not appended to; (2) moving the
   prose out of JSON into Markdown; (3) not sharding the JSON. Also proposed
   measuring as Σ ceil(len/80).

2. **Operator:** «> Правило переписывать, а не дописывать — ага. > Вынести прозу
   из JSON в Markdown — ага. > watermark.json становится чистым индексом … — а
   нужно вообще adopted/declined в вотермарке? > Заметки и причины отказа
   переезжают в watermark.md — а watermark.md вообще удачное название? оно
   исторически сложилось потому что мы храним sha последнего синка, но кажется
   что "что приняли что отклонили" немного про другое.»

   **Agent:** Proposed deriving "taken as is" from the files on disk (file here
   and unmentioned means verbatim). Re-expressions and declines go into the
   record. The JSON keeps only `repo`, the SHA, the date and `lineage`. Proposed
   the name `divergence.md`.

3. **Operator:** «> Поэтому на переходный период читатели должны понимать оба
   формата — какой переходный период? это же всё делается одним пиаром»

   **Agent:** Agreed, there is no transition period. The new format is the old
   one minus two fields. Each adopter converts in the one sync PR that ports the
   change. The conversion is done by hand, not by a converter script, because it
   takes judgment.

4. **Operator:** «> Нужны ли adopted/declined в вотермарке / Нет. Список adopted
   почти целиком повторяет то, что и так лежит на диске — я не это спрашивал, я
   спрашивал нужны ли они именно в джсоне. что нужны в принципе с описанием что
   принято, что изменено -- нужны, потому что иначе при продвижении muthur-а не
   понять, что нужно менять. или нет?»

   **Agent:** The record is needed, but not in JSON. The only script that reads
   it is `muthur-sync.sh:74`, which just prints the keys, and nothing reads
   `declined`. Re-expressions and declines are required. A verbatim take is
   shown by the tree itself.

5. **Operator:** «может тогда и пусть в свободной форме пишет, а не прямо
   попунктно, логика такая: каждый агент лучше знает своему репу, и ему лучше
   знать, как лучше описать то, чем то что здесь отличается от того что в маме?»

   **Agent:** Agreed: free form, which also lets a cross-cutting difference be
   stated once. Three hard rules: paths named literally in backticks; a decline
   reads as a decline; current state, not history. Measurement is lines at 80
   columns.

6. **Operator:** «давай делать»

   **Agent:** Routed through `/task` and wrote the plan. Renamed the branch to
   `claude/watermark-divergence-1dwzoj`. Opened draft PR
   https://github.com/vzakharov/muthur/pull/229 with a squash proposal.

7. **Operator** (mid-turn): «можно уже выполнять сразу»

   **Agent:** Flipped the plan to in-progress, quoting both go-ahead messages,
   and implemented it in four commits. Ran `/polish` through a subagent. Fixed
   the hydration wording, completed the plan, refreshed the PR body and the
   squash proposal. Reported the result and one `/dry` question: share the UTF-8
   char-count trick across the three scripts that use it, or keep each script
   self-contained? (recommended: self-contained, as built). (verbatim in Last
   agent turn)

## Intent

Keep adopter watermarks from growing without bound. The operator wants a record
of how an adopter differs from muthur, written freely by that adopter's agent.
They do not want a JSON index of everything taken. They ruled out a transition
period with dual-format readers.

## Decisions

- **`watermark.json` = position only** (`repo`, `lastSyncedSha`, `lastSyncedAt`,
  `lineage`). Rejected alternative: keeping `adopted`/`declined` as a bare path
  index. No script needs them, and the tree already shows what was taken
  verbatim.
- **`divergence.md`** (in `.claude/skills/update-muthur/`) is the free-form
  record of re-expressions, declines and cross-cutting differences. The name
  beat `watermark.md` and `deviations.md`. The template ships none.
- **Three rules**: paths named literally (so Step 3 can `grep -F` for them); a
  decline reads as one, with a present-tense condition or "never"; current
  difference, not sync history.
- **Cap: 450 lines counted at 80 columns** (Σ ceil(chars/80), counting
  characters, not bytes). The cap covers the whole record, which is a single
  file, because every sync reads all of it. Splitting into `divergence/*.md` was
  rejected (plan's open question, option a in force): parts spread the cost
  without cutting it.
- **No transition period and no converter script**: the commit is
  `[attn adopters]`, and each adopter converts by hand in their next sync.
- **`/dry` call left open**: the `LC_ALL=C tr -d '\200-\277'` trick now appears
  in `check-claude-md-size.sh`, `check-squash-message.sh` and
  `check-divergence.sh`. Recommendation: keep each script self-contained, as
  built. Not yet answered by the operator.

## Errors and dead ends

- The first answer said "adopted/declined are not needed", which the operator
  took to mean "no record at all". Clarified in turn 4: the record is needed,
  just not in JSON.
- The first answer proposed dual-format readers for a transition period. The
  operator pointed out it's one PR, and the agent agreed.
- The `polish` subagent noted that the plan said "POSIX sh" while the script is
  bash. The plan text was corrected.

## State

- Branch `claude/watermark-divergence-1dwzoj`, everything pushed, head `ed4ed0a`
  before this summary's commit.
- Draft PR https://github.com/vzakharov/muthur/pull/229, title
  `feat: [attn adopters] a capped divergence.md replaces adopted/declined`, with
  a squash proposal comment and its working file at
  `docs/remove-before-merging/squash-message.md`.
- Plan: `docs/plans/watermark-divergence.completed.md`.
- `/go` is done. The next loop step is `/finalize`, which has not been run (no
  vet run on the branch yet).
- The old remote ref `claude/bold-noether-1dwzoj` couldn't be deleted (proxy
  403). It carries no PR.
- Estimate: 2 h senior architect + 4 h senior developer. All of it is this
  session's work, and nothing is handed on.
- Nothing running: no PR subscription, no check-in, no keepalive.

## Pointers

- `.claude/skills/update-muthur/SKILL.md` § "The watermark", § "The divergence
  record", Steps 1, 3, 4, 4a, 7 — the new contract.
- `scripts/check-divergence.sh`, `scripts/test_check_divergence.py`,
  `scripts/vet.sh` (wiring), `scripts/muthur-sync.sh` (nudge),
  `scripts/test_muthur_sync.py`.
- `docs/adopting/sync.md`, `/detemplate` Step 5.6, `/spinoff` Step 3 — writers
  of the record.
- Metka's watermark, re-fetchable:
  `gh api 'repos/metkain/metka/contents/.claude/skills/update-muthur/watermark.json?ref=76371efbb1e4a153a6a020f8a2d5effe05cc4d02' --jq .content | base64 -d`
- This session: https://claude.ai/code/session_01Eeow5zrMDxzvWKcnWiw5GK

## Next step

Wait for the operator. Pending: their answer to the `/dry` question (share the
UTF-8 char-count trick or keep the scripts self-contained; self-contained stands
if unanswered), and then `/finalize` when they ask for it.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages,
usually unneeded but harmless; the reply proper is usually its last
paragraphs.

```text
`/polish` прошёл, план помечен выполненным. Последнее — обновить тело PR и squash-предложение под реальный дифф.

Вова, всё сделано и запушено в черновой PR https://github.com/vzakharov/muthur/pull/229. Дальше на очереди только `/finalize`.

**Что изменилось:**
- **`watermark.json`** теперь хранит только позицию синка: `repo`, `lastSyncedSha`, `lastSyncedAt`, `lineage`. `nudge` больше не печатает «You adopted».
- **Расхождения с источником** пишутся в свободной форме в `divergence.md`. Обязательных правил три: путь называется буквально, отказ читается как отказ, описывается текущее состояние, а не история. Синк читает файл целиком; потолок — 450 строк при переносе на 80 колонок.
- **`scripts/check-divergence.sh`** подключён в `vet.sh` и падает в двух случаях: в вотермарке остались `adopted`/`declined` или запись вылезла за потолок. Ширина считается в символах, а не в байтах, поэтому кириллица не раздувает счёт втрое. Новые тесты и тесты синка проходят.
- **`/update-muthur`:** шаг 3 больше не фильтрует лог по `adopted`. Он раскладывает весь лог на три группы: есть у нас и записи нет / есть запись / нет ни файла, ни записи. Шаг 7 переписывает задетые места записи, а не дописывает к ним.
- **`/detemplate` и `/spinoff`** сразу записывают отказ от всего, что они не взяли. Без этого первый синк предложил бы всё выброшенное заново.
- **Заголовок PR** — `feat: [attn adopters] a capped divergence.md replaces adopted/declined`. В абзаце `Adopters:` написано, как адоптеру перевести свой вотермарк вручную, прямо в синке, который принесёт эту правку.

**Один вопрос от `/dry`:** приём «считать символы UTF-8 через `LC_ALL=C tr -d '\200-\277'`» теперь повторяется в трёх скриптах — `check-claude-md-size.sh`, `check-squash-message.sh` и новом. Вынести его в общий подключаемый файл, или каждый скрипт остаётся самодостаточным? Я за самодостаточность, и так всё и сделано. Общий файл адоптерам пришлось бы тащить рядом с каждым скриптом, а сам приём — одна строка.

**По ходу:**
- На середине пришло предупреждение о бюджете контекста. Я не остановился, потому что оставшаяся работа (`/polish` и обновление PR) явно помещалась в запас.
- Ветку я переименовал в `claude/watermark-divergence-1dwzoj`. Старую `claude/bold-noether-1dwzoj` удалить не получилось: прокси ответил 403. PR на ней нет, так что она просто висит, никому не мешая.
```
