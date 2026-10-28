# Relay 1 — keepalive skips a landed branch (parked)

## Standing constraints

None stated by the operator.

## The conversation

1. Operator (`/task`):

   > Сделать исключение в cache keepalive (`.claude/keepalive/`): не запускать
   > watcher и не парковать сессию (`/relay park`), когда PR ветки уже смерджен
   > или закрыт — сводка на такой ветке никому не нужна, а коммит в неё — это
   > работа поверх смердженной истории. Хорошо бы программно, прямо в хуке
   > `.claude/keepalive/hooks/keepalive.py`: смердженность ветки определяется,
   > например, через `gh pr view --json state` для текущей ветки (или PR, у
   > которого она head) — выбери способ, который надёжен в облачных сессиях и не
   > тормозит каждый ход заметно; при недоступности `gh` хук должен вести себя
   > как сейчас (fail open). Тот же тест — и в последнем пробуждении watcher-а,
   > которое просит парковку. Поправь `.claude/keepalive/CLAUDE.md` и `/relay`
   > там, где они говорят, что watcher запускается после каждого хода. Контекст:
   > в downstream-репо vzakharov/life сессия после мерджа своего PR получила от
   > хука просьбу запарковаться и отказалась вручную; оператор просит сделать
   > этот отказ правилом.

   Agent: routed as planless (`/go` § "Planless entry"); implemented, vetted,
   polished, opened draft PR #237 with the squash proposal posted.

2. Operator (mid-turn): «кстати,а хуки идут параллельно или по очереди?»

   Agent: answered in the final report — matching hooks for one event run in
   parallel, the turn waits for the slowest, their `additionalContext` merges in
   no guaranteed order; nine `UserPromptSubmit` hooks here, one with a 90 s
   timeout, so the new ~0.4 s `gh` call mostly hides behind them. (verbatim in
   Last agent turn)

## Intent

Make the hand-refusal to park on a merged branch a rule in the hook, fail-open
when `gh` is unavailable, cheap per turn.

## Decisions

- **Check only on turns with no live watcher** (beat: every turn) — a running
  watcher's turns need no answer; its wake asks then.
- **Landed = PR `MERGED`/`CLOSED` and HEAD equal to or an ancestor of the PR's
  `headRefOid`** (beat: state alone) — a branch restarted with commits past its
  merged PR is live work.
- **Cache a landed answer against HEAD in the state file** (beat: no cache) — a
  landed session would otherwise call GitHub on every turn; open answers aren't
  cached because the watcher then runs and no further checks happen.
- **A wake on a landed branch answers with one line** (renewal and last wake
  alike) — the harness needs visible output; no park, no new watcher.
- Fail open on any git/gh failure or a 5 s timeout (`PROBE_TIMEOUT`).

## Errors and dead ends

None.

## State

- Branch `claude/keepalive-skips-landed-pr`, head pushed (this relay commit on
  top of `9c755cd`).
- PR https://github.com/vzakharov/muthur/pull/237 — draft, open, no CI checks
  reported.
- No plan file (planless). No PR subscription, no scheduled check-in, no
  watcher.
- Estimate unchanged: 3 h senior developer + 0.5 h middle copywriter — the work
  is done in this session; nothing remains handed on beyond `/finalize`.

## Pointers

- `.claude/keepalive/hooks/keepalive.py` — `landed()`, `context()`,
  `on_prompt()`.
- `.claude/keepalive/test_keepalive.py` — `WhenTheBranchsPrHasLanded`.
- `.claude/keepalive/CLAUDE.md`, `.claude/skills/relay/SKILL.md` § park,
  `.claude/skills/update-muthur/catalog/g10-cache-keepalive.md` — the exception
  stated.
- `docs/remove-before-merging/squash-message.md` — squash proposal.
- Transcript: https://claude.ai/code/session_01DaohkFA7GcyVRfJ49bpGCB

## Next step

Wait for the operator — the PR is ready for `/finalize` when they want it.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages,
usually unneeded but harmless; the reply proper is usually its last
paragraphs.

```text
Тесты зелёные (18). Теперь документация.

Код закоммичен и запушен, vet зелёный. Дальше по `/go` идут `/polish` и `/pr`.

Полировка прошла, коммит 42f4ba5. Теперь `/pr`.

PR #237 открыт. Дописываю к нему предложение для squash-коммита.

Готово: на ветке, чей PR смерджен или закрыт, keepalive больше не запускает watcher и не просит парковку. Отказ, который сессия в vzakharov/life сделала руками, теперь делает сам хук.

https://github.com/vzakharov/muthur/pull/237

- **Когда проверяет.** `keepalive.py` зовёт `gh pr view --json state,headRefOid` только на ходах без живого watcher-а. Пока watcher работает, хук в сеть не ходит.
- **Что считается «приземлившейся» веткой.** PR в состоянии `MERGED`/`CLOSED`, и HEAD совпадает с головой PR или стоит позади неё. Если на ветке есть коммиты поверх PR, она считается живой: это новая работа на той же ветке.
- **Пробуждение.** Если watcher был запущен ещё до мерджа, его пробуждение (и продление, и последнее) не паркует сессию и не запускает новый watcher. Агент отвечает одной строкой, что keepalive остановился, потому что PR приземлился.
- **Скорость.** Один вызов `gh` занимает около 0,4 с. Ответ «приземлилась» запоминается по SHA HEAD в state-файле, так что на такой ветке GitHub спрашивается один раз на коммит, а не на каждом ходу.
- **Fail open.** Если `git` или `gh` недоступны, падают или не отвечают за 5 с, хук ведёт себя как раньше.

Исключение дописано в `.claude/keepalive/CLAUDE.md`, в `/relay park` и в запись каталога G10. Тесты keepalive проходят (18, из них 5 новых, с подменённым `gh` в PATH), `vet.sh` зелёный. Предложение для squash-коммита висит комментарием в PR.

**Про хуки:** насколько я помню документацию Claude Code, все хуки, подходящие под событие, запускаются параллельно, а не по очереди. Ход ждёт самого медленного из них, их `additionalContext` склеиваются, и порядок не гарантирован. На `UserPromptSubmit` у нас висит девять хуков, среди них экспорт issue/PR с таймаутом 90 с. Поэтому новые 0,4 с на `gh` в основном прячутся за остальными, а не добавляются к ним.

Watcher запущен, этот PR пока открыт, так что новое правило к нему не относится. Если `gh` его однажды не найдёт, он хотя бы не обидится.
```
