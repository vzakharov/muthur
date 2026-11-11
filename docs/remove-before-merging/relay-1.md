# Relay 1 — parked

## Standing constraints

None stated.

## The conversation

1. **Operator** (via `/task`):

   > fix: add a colocated `CLAUDE.md` to `.claude/voice/` saying what the
   > directory is not for.
   >
   > Why: in a downstream repo (vovazakharov.com), an agent took the operator's
   > «можно я не буду каждый раз напоминать?» (about republishing review boards
   > after each merge) and wrote it as an entry in
   > `.claude/voice/operators/<handle>.md`. The operator, Vova, rejected that:
   > «voice -- не место для этого». The voice files govern _how_ the agent talks
   > to a person (manner, language, register), and `voice.md` already says an
   > entry "changes how an answer sounds, never what is in it, what gets
   > reported, or which checks run". That sentence did not stop the agent,
   > because it was reading the directory to write a preference, not re-reading
   > `voice.md`'s fine print.
   >
   > What the operator asked for, in his words: «привязать к voice-у collocated
   > CLAUDE.md который говорит что он не для этого; что для любых repo-wide
   > инструкций нужно использовать другие места».
   >
   > So the new `.claude/voice/CLAUDE.md` (it loads when a session reads a file
   > in that directory, which is exactly when an agent is about to add an entry)
   > should say, briefly:
   >
   > - this directory holds how to talk to a person — manner only;
   > - a workflow rule, a "do X after Y", or anything else that changes what the
   >   agent does or which steps run never goes here, even when one operator
   >   asked for it;
   > - where such a thing goes instead: the skill that owns the step, a
   >   `.claude/rules/` file, a colocated `CLAUDE.md`, or root `CLAUDE.md` per
   >   its own "About this file" test.
   >
   > Keep it short, follow the repo's tend-prose rules, and dedupe against
   > `voice.md` (one home per constraint: if `voice.md`'s "An entry cannot lower
   > a bar" paragraph now overlaps, make one of them the pointer). Commit type
   > `fix:`. Open a PR when done.

   **Agent:** went planless; staged `voice.md`, wrote `.claude/voice/CLAUDE.md`,
   narrowed two `voice.md` sentences, vetted, polished, opened draft PR #271
   with the squash proposal. Put one decision to the operator: kept the
   four-item "where it goes" list rather than replacing it with a pointer to
   `tend-prose` § "Lens 1" (verbatim in Last agent turn).

## Intent

Stop agents from writing workflow wishes into `.claude/voice/operators/`
entries; point them at the right home at the moment they are about to write.

## Decisions

- **Planless** — two files, scope fully given by the prompt.
- **Narrowed the always-loaded `voice.md` line** "A stated preference is written
  down" to "about how to talk to them": that sentence is what invited the
  misplaced write, so fixing only the colocated file would leave the trigger.
- **One home**: `voice.md`'s "cannot lower a bar" paragraph keeps the
  sounds-vs-substance rule (it matters on every reply); its last sentence now
  points to `.claude/voice/CLAUDE.md` for where a substance change goes.
- **Kept the home list in the new file** over a pointer to `tend-prose` § "Lens
  1" (polish subagent's DRY call): the guidance must be at hand at write time.
  Open to operator reversal.

## Errors and dead ends

None.

## State

- Branch `fix/voice-dir-scope`, head `01a9dd8`, pushed, clean.
- PR https://github.com/vzakharov/muthur/pull/271 — open, draft.
- `voice.md` staged at `.claude/staged/.claude/voice/voice.md.staged` (staging
  commit `1e867b0`); `/finalize` swaps it in.
- Squash proposal comment posted; tracked at
  `docs/remove-before-merging/squash-message.md`.
- No plan file, no PR subscription, no review board.
- Estimate: 0.75 h senior prompter ("deciding which home owns the constraint and
  wording a scope fence an agent heeds at write time takes judgement of how
  agents read the loop") + 0.25 h senior editor ("dedupe against voice.md needs
  a one-home edit across two files"); no remainder handed on.

### Watches

None.

## Pointers

- `.claude/voice/CLAUDE.md` — the new file.
- `.claude/staged/.claude/voice/voice.md.staged` — the edited `voice.md`.
- Transcript: https://claude.ai/code/session_01DaohkEv6tytZdnPLY5TzST

## Next step

Wait for the operator — review of PR #271 and the kept-list call; `/finalize`
when they ask.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Полировка прошла и срезала одну повторяющую фразу. Открываю PR.

Step 6: squash proposal.

Готово: черновой PR открыт — https://github.com/vzakharov/muthur/pull/271

Делал без плана: правка в два файла, вся помещается в голове. Скажи `plan`, и я напишу план задним числом.

**Что изменилось:**
- **Новый `.claude/voice/CLAUDE.md`.** Подгружается, когда агент читает файл в этой папке, то есть ровно перед тем, как дописать запись оператора. В нём сказано: папка только про то, как разговаривать с человеком. Всё, что меняет поведение агента, сюда не идёт, даже если об этом попросил один оператор. Это «сделай X после Y», добавить или пропустить проверку, умолчание скилла. Такое кладётся туда, где живёт сам шаг: в скилл, которому шаг принадлежит, в `.claude/rules/`, в `CLAUDE.md` нужной папки или в корневой `CLAUDE.md`, если пройдёт его собственный тест.
- **`voice.md`, через staged-копию:** `/finalize` подставит её на место оригинала. Поправил две фразы:
  - «A stated preference is written down» сузил до предпочтений о том, как говорить с оператором. Именно эта фраза грузится на каждом ходу и приглашала записывать в `voice/` любые пожелания.
  - Последняя фраза абзаца «An entry cannot lower a bar» теперь отсылает к новому файлу: там написано, куда идёт пожелание по существу. У каждого правила остался один дом.
- **Проверки:** `vet.sh` прошёл. Полировка срезала в новом файле одну фразу, повторявшую первую.

**Что я решил за тебя:** полировка заметила, что список «куда класть» частично повторяет § "Lens 1" из `tend-prose`. Предложила заменить его ссылкой. Я оставил список: файл нужен ровно затем, чтобы ответ был под рукой в момент записи. Отсылка заставила бы в этот самый момент грузить ещё один скилл. Если считаешь, что одна правда должна жить в одном месте даже ценой лишнего прыжка, скажи, и я заменю список ссылкой.

Предложенный текст для сквоша висит комментарием на PR, заголовок — `fix: say what .claude/voice/ is not for, where a write would land`. Агент из vovazakharov.com, надеюсь, теперь поймёт, что папка `voice` — это голос, а не записная книжка для поручений.
```
