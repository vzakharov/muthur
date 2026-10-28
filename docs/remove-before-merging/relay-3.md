# Relay 3: merge gate implemented, parked before finalize

## Standing constraints

None stated by the operator.

## The conversation

The session opened on `/relay take claude/merge-gate-hook-k2tzds` with the
caption «шаг 0 сделан (#237 влит и закрыт), дальше сам гейт по плану через go».
That is the predecessor's handoff line, not a typed operator message, and no
operator message followed it.

1. **Relay take (session's opening prompt).**

   **Agent:** attached (already on the branch), read `relay-2.md`, set the
   inherited estimate, flipped the plan from paused to in-progress, then built
   the gate, its tests and wiring, ran `/polish` in a subagent, pinned the
   shared marker with a test, completed the plan and refreshed the PR body.
   (verbatim in Last agent turn)

## Intent

A bare `/merge` lands a finalized PR with no model turn whenever every
mechanical condition of `/merge`'s gate holds; otherwise the prompt reaches the
agent as typed. It must hold for adopters too. Only a bare `/merge` triggers it.
(Carried from `relay-2.md`, where the operator set it.)

## Decisions

All of `relay-2.md` § "Decisions" stands. Added in this session, each forced by
the code:

- **The cold-cache guard runs as a subprocess, not an import**, the event marked
  `merge_gate_declined`. `scripts/lib/` and `.claude/costs/lib/` both carry a
  `lib.github`, and the gate imports `lib` as one namespace package across both,
  so `lib.github` is the scripts' one and no ledger module importing its own may
  be imported there.
- **The attestation marker moved to `.claude/costs/lib/attestation.py`**, so the
  gate reads it without `lib.finalized` (which imports the ledger's
  `lib.github`).
- **The after-merge note is told on every prompt until a response lands after
  it**, rather than skipping keepalive wakes: a prompt the cold-cache guard
  blocks must not use it up, and any answered prompt puts it in the
  conversation.
- **REST names stand in for GraphQL's**: `mergeable` true and `mergeable_state`
  `clean`.
- **Left as is (polish's second call):** `GitHub.previous` hard-codes
  `docs/pr/<n>/pr.md`, a one-line duplicate of `scripts/export-github-item.py`,
  which cannot be imported for the hyphen in its name.

## Errors and dead ends

- A test first reused one timestamp for every comment, so a human comment did
  not post-date the agent's and the awaiting check passed; fixed in the test.

## State

- **Branch:** `claude/merge-gate-hook-k2tzds`, head de4b431, pushed, clean.
- **PR:** https://github.com/vzakharov/muthur/pull/246, draft, `MERGEABLE` /
  `CLEAN`, body refreshed for what was built. Squash proposal comment unchanged
  (it already describes the result; the gate's own read-back parses it).
- **Plan:** `docs/plans/merge-gate-hook.completed.md`.
- **Not run:** `./scripts/vet.sh` (that is `/finalize`'s). Run by hand and
  green: `test_merge_gate.py`, `test_cold_cache.py`, `test_export_awaiting.py`,
  `check-skill-catalog.sh`, prettier on the touched Markdown.
- **Estimate:** this session 6 h senior developer ("seven GitHub-side checks, a
  merge with a head guard, and boundary-mocked tests for each decline; an
  auto-merge path tolerates no sloppy reading of API fields"). Nothing remains
  to hand on beyond `/finalize`.
- Nothing running: no subscription, no check-in, keepalive parked.

## Pointers

- `.claude/merge-gate/` — `hooks/merge_gate.py`, `hooks/record.py`,
  `test_merge_gate.py`, `CLAUDE.md` (the contract).
- `.claude/cold-cache/hooks/cold_cache.py` — the `/merge` deferral.
- `scripts/gh_export/awaiting.py` — `awaiting_rows()`.
- `.claude/skills/update-muthur/catalog/g11-merge-gate.md`.
- `relay-2.md` — the design conversation with the operator.
- This session's transcript:
  https://claude.ai/code/session_01DaohkCY3YE4xygob4Y3pBW

## Next step

Wait for the operator. The loop's next step is `/finalize` on PR #246, which the
operator has not asked for yet.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
The polish run raised one real risk: the `merge_gate_declined` marker string is written in both hooks and no test checks the two copies match. A one-sided rename would let a declined `/merge` past the price stop with the tests still green. Pinning that now.

Step 4: `/pr` refresh.

Вова, я продолжил работу сессии https://claude.ai/code/session_01DaohkFbMZ1baY15PNscdFf. Гейт готов. Теперь голый `/merge` сам мерджит финализированный PR без хода модели, а если хоть одна проверка не проходит, промпт молча уходит агенту. PR #246 остаётся draft, тело обновлено под то, что реально построено.

https://github.com/vzakharov/muthur/pull/246

**Что сделано:**
- **Хук `.claude/merge-gate/hooks/merge_gate.py`** проверяет семь условий из плана. Все факты он берёт с GitHub, а не из локального дерева. Если всё сходится, мерджит с `--match-head-commit` и блокирует промпт строкой `✅ Merged #<n> into <base> at <sha>`. Проверку чтения я прогнал вживую на #246, сам мердж был заглушён. Все запросы к GitHub работают, а мердж гейт не стал делать только потому, что PR в draft и без аттестации, как и должен.
- **Cold-cache guard пропускает голый `/merge` гейту.** Если гейт отказал, он сам запускает guard, и ценовой стоп появляется как обычно.
- **Тесты:** 26 штук в `test_merge_gate.py`. Шаблоны значений строк аттестации тест читает прямо из `attest.md`, так что код и шаблон не могут разойтись незаметно. В `test_cold_cache.py` добавлены случаи с `/merge`. Плюс `vet.sh`, запись G11 в каталоге и `CLAUDE.md` гейта.

**Три отступления от плана, все вынужденные** (записаны в плане):
1. В `scripts/lib/` и `.claude/costs/lib/` лежит по своему `lib.github`, а в одном процессе Python может жить только один из них. Поэтому guard запускается подпроцессом, а не импортом. По той же причине маркер аттестации переехал в `.claude/costs/lib/attestation.py`.
2. Заметка «PR уже смерджен» теперь показывается на каждом промпте, пока после неё не придёт ответ модели. Пропуск keepalive-будилок я выкинул. Иначе, если guard заблокирует следующий промпт, заметка сгорит впустую.
3. Вместо GraphQL-полей используются REST-аналоги: `mergeable` true и `mergeable_state` `clean`.

**Polish** сделал два своих коммита, тесты и прозу подтянул. Ещё он нашёл реальную дыру: строка-метка `merge_gate_declined` записана в обоих хуках, и ни один тест не сверял две копии. Если переименовать её только с одной стороны, отклонённый `/merge` на холодном кеше проскочил бы мимо ценового стопа, а тесты остались бы зелёными. Это я закрыл тестом (f45bb5c). Второй его пункт я оставил как есть: путь `docs/pr/<n>/pr.md` продублирован в одну строку, потому что экспортёр из-за дефиса в имени не импортируется.

Предложенный текст squash я не трогал: он и так точно описывает результат, гейт проверил, что он читается обратно.

Под конец пришло предупреждение о бюджете контекста (~234k). На паузу я не встал, потому что оставались только документация, polish и обновление PR, а это влезало в запас.

Дальше по циклу `finalize`. Если кто-то наберёт голый `/merge` уже после finalize и мердж пройдёт, гейт заодно проверит сам себя. Будет слегка рекурсивно, но честно.
```
