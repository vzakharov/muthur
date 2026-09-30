# Auto-relay at the context budget's pause line

## The ask

> давай сделаем настройку авторелей на уровне репы: в таком случае релей по порогу бюджета контекста выполняется автоматически. при этом нужно чтобы за рулём был настоящий оператор […] Есть ли надёжный маркер "да, это точно оператор" -- неизвестно. Если нет, переместить настройку на уровень оператора. То есть типа при первом предложении релея агент говорит, если хочешь, в будущем я буду делать это сам, и если оператор отвечает "да, сделай", то он эту настройку включает (по аналогии с кастомными voice-ами для операторов)

## Is there a reliable "a human is driving" marker? No.

- Nothing documented distinguishes a web session someone is watching from a Claude Tag (Slack) one or any other launch: `CLAUDE_CODE_ENTRYPOINT` reads `remote` for every cloud session.
- The CLI sets `CLAUDE_CODE_SESSION_ATTENDED` and `CLAUDE_CODE_CHILD_SESSION` in the env of processes it spawns, but both are undocumented internals read off the minified binary, and `CHILD_SESSION=1` in a session the operator opened by hand shows their names don't mean what they seem to. Building a gate on them builds it on a guess.

So the setting is **per operator**, as the ask's fallback says. It is keyed on the same thing the voice entries are keyed on: the lowercased login of a **`User`-type** GitHub token. A session running on a bot's token (the case `operator-voice.sh` already names as "the agent's own identity") resolves no operator, so it never auto-relays. That is the closest thing to the marker the tree can check.

## Design

- **The setting**: `.claude/context-budget/auto-relay/<handle>`, one word, `on` or `off`. The filename is the whole lookup, as with the voice entries; it sits in `.claude/context-budget/` because that hook is its only reader, and not in `.claude/voice/operators/`, because `voice.md` scopes those entries to how an answer sounds and forbids them from changing what the agent does. No file means the operator hasn't been asked; anything but `on` or `off` reads as no file.
- **The hook** resolves the handle with `gh api user` only when a notice is about to fire (once per climb), never on the ordinary tool call. Unresolvable (`gh` missing, API down, non-`User` token) → today's notice, no opt-in offer, since there is nowhere to record an answer.
- **The two lines** (the operator's follow-up, in this session): the warning gives the work the room up to the pause line — finish in it if it fits, otherwise steer to the best stopping point reachable within it and pause there; the pause line is where that estimate missed, so it pauses where the work stands, with an escape only for a last step (~20k), not the warning's 100k. Either pause ends by the setting below.
- **Notice text by setting**:
  - *unset* — today's offer of `/relay`, plus: offer, once in the session, to relay on its own from now on; the operator's yes writes `on`, their no writes `off` (§ "Auto-relay" in `/relay`).
  - *`off`* — today's notices exactly.
  - *`on`* — the warning is today's plus a line that the pause will relay on its own; the pause is "pause per `/go` § Stopping partway, then run `/relay` without asking", instead of ending the turn on an offer. The "nearly done" judgement still comes first at both.
- **`/relay` § "Auto-relay"** (new) is the home of the procedure: what the setting is, why it is per operator, that only the operator's explicit answer writes it (their words quoted in the commit), that they can flip it any time by saying so, and that the file takes effect in any session whose tree carries it — this branch at once, every branch once it reaches `main`. An auto-relay is `/relay` with no argument, so the successor's Next step is the paused plan.
- **`/go` § "Stopping partway"**: its last paragraph ends the turn offering `/relay`; it gains "or, with auto-relay on, runs it".
- **`.claude/context-budget/CLAUDE.md`**: a bullet on the lookup's constraints (resolved only at notice time; unresolvable is off).
- **Catalog row** for `.claude/context-budget/` mentions the per-operator auto-relay and its directory.
- **Tests** in `test_context_budget.py`: a stub `gh` on `PATH` returning a `User`/`Bot` identity; cases for unset (offer made), `off` (no offer), `on` (pause says to run `/relay` without asking), a bot token (no offer), and a malformed file (reads as unset).

## DRY notes

- **Handle resolution is duplicated, deliberately small.** `operator-voice.sh` calls `gh api user` for login, type and name and builds three different messages from them; the budget hook needs only "the lowercased login if `User`, else nothing". Extracting a shared helper would mean `operator-voice.sh` sourcing `lib.sh`, which it does not today because it runs outside the payload-reading hook family; the shared part is one `jq` expression. The convention both follow (lowercased login names the file) is stated once, in each file's own comment on its lookup.
- **The notice text** reuses the hook's existing `relay`, `stopping` and `nearly_done` fragments; the three settings vary only the closing sentence of each notice.
- **The procedure** lives only in `/relay` § "Auto-relay"; the hook's notice, `/go` and the context-budget `CLAUDE.md` point at it.

## Checklist

- [x] Hook: handle resolution at notice time, setting read, three notice variants
- [x] Tests for the five cases above
- [x] `/relay` § "Auto-relay"
- [x] `/go` § "Stopping partway" pointer
- [x] `.claude/context-budget/CLAUDE.md` bullet, catalog row
