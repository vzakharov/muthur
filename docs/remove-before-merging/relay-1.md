# Relay 1 — Opus quality gate (parked, keepalive's last wake)

## 1. Standing constraints

None stated by the operator.

## 2. The conversation

- **Operator (Russian, opening prompt):** a session on a weaker model (not Opus)
  should, after each cutoff of the loop (`/plan` where there is one, `/go`, any
  later `/go` and `/handle`, `/finalize`), create an Opus subagent asking "on
  your view, does what I did pass the quality check", with answers ordered best
  to worst: yes / no, make these changes (by substance, not verbatim) and show
  me again (unsure whether an already-reported subagent can be written to,
  otherwise a new one) / no, I fixed it, carry on / no, I fixed it but the work
  is too hard for you, relay to a new Opus session after the fixes / no, I
  cannot fix it (e.g. a limit of subagents as such), relay at once. The subagent
  may also edit `.claude/skills/go/delegation-model-capabilities.md`. "Dogfood
  it right here."
  - **Agent:** routed through `/task`, wrote and flipped a plan, implemented
    `go/review-gate.md` plus pointers, ran `/polish`, ran the gate on itself
    (verdict `fixed`, four fixes), opened PR 252 and posted the squash proposal.
    `(verbatim in Last agent turn)`

## 3. Intent

Make weak-model sessions get an Opus review at each loop cutoff, with the five
verdicts as described, and use this very branch as the first run of it.

## 4. Decisions

- **One file, no new skill.** A skill description loads on every turn of every
  session; the gate runs only on weak ones. Pointers in `/plan`, `/go`,
  `/finalize` carry the model condition so Opus sessions never load
  `review-gate.md`.
- **`/finalize` placement is before step 1**, right after `/polish`, not after
  the attestation: a fix after the vet run would make vet, base merge, squash
  body and attestation SHA stale.
- **`/handle` has no pointer**; its lanes end in `/go`, `/plan` or `/finalize`.
- **`revise` over `fixed`** by default: Opus fixes itself only what is cheaper
  to do than to describe, or where the session would repeat the mistake.
- **Three `revise` rounds** without a `pass` count as `relay`.
- **Relay model** is the id the reviewer names for itself (the session's system
  prompt names only its own model).
- **Model check** reads the system prompt's model name (what the pointers can
  see before the file loads); `MUTHUR_OPUS_GATE=off` skips the gate.

## 5. Errors and dead ends

- The first draft's `get_session`/`last_served_model` check sat inside
  `review-gate.md`, which a mis-served session never loads; the reviewer moved
  it to the system-prompt reading.
- `Agent` with `run_in_background: false` still launched async here; the session
  waited for the notification.
- Shell heredoc and `sed -i` were refused by the file-tools hook; `Write`/`Edit`
  used instead.

## 6. State

- Branch `claude/opus-quality-gate-tmds1o` (renamed from the auto-branch before
  the first commit), everything committed and pushed; PR 252 is an open draft
  against `main`, squash proposal comment posted and tracked in
  `docs/remove-before-merging/squash-message.md`.
- Plan: `docs/plans/opus-quality-gate.completed.md`.
- Not run: `./scripts/vet.sh` (that is `/finalize`'s); `/qa-checklist` was
  skipped, the PR body's checklist was written by hand.
- Estimate: 3 h senior prompter, the whole job; nothing left for a successor.

## 7. Pointers

- `.claude/skills/go/review-gate.md` — the procedure.
- `.claude/skills/go/delegation-model-capabilities.md`, `delegation.md`,
  `.claude/skills/relay/SKILL.md`,
  `.claude/skills/update-muthur/catalog/g2-pr-loop.md`.
- Gate fixes: commit 8ffd7b1. Session link:
  `https://claude.ai/code/session_01DaohkE7bS8WQiGsVZMXfjw`.

## 8. Next step

Wait for the operator. Likely: `/finalize` (vet, base merge, attestation).

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

```text
Вова, коротко: PR #252 открыт, сейчас публикую черновик squash-описания и уточняю заголовок.

Вова, гейт готов и запушен. PR: https://github.com/vzakharov/muthur/pull/252 (черновик). `./scripts/vet.sh` я не запускал, это работа `/finalize`. Проверки каталога скиллов и таблиц проходят.

Сначала про догфуд. Меня обслуживает Sonnet 5.5, поэтому на конце `/go` гейт сработал на этой же ветке. Ревьюер на Opus вернул `fixed`, один раунд, и сам закоммитил четыре правки (8ffd7b1). Самая показательная: проверка «какая модель сейчас обслуживает сессию» лежала внутри `review-gate.md`. Файл читает только сессия, которая уже знает, что она слабая, так что случай «сконфигурирован Opus, а отвечает Sonnet» эта проверка не ловила. Теперь модель берётся из системного промпта. Остальные три правки:
- убрано противоречие в брифе ревьюера: «не называй модель в коммитах и файлах» против «перепиши запись модели в `delegation-model-capabilities.md`»;
- relay на Opus теперь берёт id модели, который назвал сам ревьюер, потому что слабая сессия этот id не знает;
- диапазон ревью считается от головы, которую оставил последний `pass` или `fixed`.

Ревьюер же дописал в записи про `sonnet` в `delegation-model-capabilities.md`, чего слабая модель не заметила: ошибки согласованности внутри собственной процедуры.

Что получилось:
- **Файл процедуры.** `.claude/skills/go/review-gate.md` хранит всё: кто гейтится, где он срабатывает, бриф ревьюера и пять вердиктов (`pass`, `revise`, `fixed`, `fixed-relay`, `relay`). Каждый вердикт делает то, что ты описал.
- **Продолжить подагента можно.** На `revise` сессия правит и показывает ревьюеру ещё раз через `SendMessage` тому же агенту. Если продолжить нельзя, то свежему ревьюеру с прошлым вердиктом в брифе. После трёх `revise` без `pass` идёт `relay`.
- **Правки в capabilities.** Ревьюер правит `delegation-model-capabilities.md` по тем же правилам сжатия, что и `delegation.md`.
- **Где вызывается.** Строка-указатель с условием «модель ниже Opus» добавлена в `/plan`, `/go` и `/finalize`, а в `/relay` добавлен запуск преемника на модели ревьюера. Сессия на Opus сам файл не загружает.
- **Отключение.** `MUTHUR_OPUS_GATE=off`.

Два места, где я отошёл от твоей буквы, и оба в плане:
- **`/finalize`:** гейт стоит сразу после его проходов качества, до vet, а не в самом конце. Иначе правка после vet обесценила бы vet, merge базы и SHA в аттестации.
- **`/handle`:** своего указателя у него нет. Его линии ведут в `/go`, `/plan` или `/finalize`, а там гейт уже есть, поэтому двойного прогона не будет.

Нового скилла я не заводил: его description висел бы в каждой сессии ради работы, которую выполняют только слабые модели.

Две вещи, о которых стоит знать:
- **Фон вместо foreground.** Я запустил ревьюера с `run_in_background: false`, но он стартовал в фоне и вернулся через уведомление. Для процедуры это не важно, потому что сессия ждёт вердикта, но ожидание «foreground» из `review-gate.md` в этой среде не гарантировано.
- **Пропущено в PR.** Шаг `/qa-checklist` я не грузил: чеклист в теле PR написал сам, чтобы уложиться в бюджет контекста. Шаг `/plan-open` с отдельным PR под черновик плана тоже пропущен: план сразу ушёл в реализацию, и PR открылся один раз в конце.
```
