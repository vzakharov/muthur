# PR #96: feat: opt-in context budget hook

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/96
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/context-budget-hook-tb5p5q
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-23T11:15:37Z
- **Updated:** 2026-09-23T12:03:12Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **A `PostToolUse` hook, `.claude/context-budget/hooks/post-tool-context-budget.sh`,** reads the context the session carries off the transcript's last main-chain `usage` record (`input + cache_read + cache_creation`) after every tool call. Past 200k tokens it injects a warning — reach a committed stopping point, tell the operator, offer `/compact` or a new session; past 300k, the pause itself. Either notice leads with the nearly-done override: finish and say so rather than stopping.
- **Once per climb:** the level announced is kept in `tmp/context-budget/<session_id>`; a reading back under 200k (a compact) re-arms both. Subagent tool calls (`agent_id`, per the hooks reference), sidechain records and `<synthetic>` responses are skipped; anything unreadable is silence. `CONTEXT_BUDGET_WARN` / `CONTEXT_BUDGET_PAUSE` override the lines. `emit_context` in `lib.sh` now reads `hookEventName` off the payload, so the new hook reuses it with no caller changes.
- **One pause procedure, two triggers:** `/go` § "Stopping partway releases the plan" takes the budget notice beside the operator's ask, writes `docs/plans/<slug>.paused.md` directly for planless work, and has an unasked pause reported and ended with the `/go <branch>` block.
- **Opt-in:** the catalog gains G8 (`adopt — opt-in: ask`), and what `opt-in: ask` means is stated once beside the dispositions. `ADOPTING.md`, `/detemplate` and `/update-muthur` ask every such row instead of naming the cost ledger. Wired on here in `.claude/settings.json`; `scripts/vet.sh` runs its tests beside the ledger's.
- **A one-turn session gets named too:** `.claude/costs/hooks/prompt-session-name.sh` asked for a name only once the session's cost row existed, and the row lands as a turn ends, so a session with a single turn — the `/plan` that opened this PR — was never asked. It now asks from the first prompt; the `--name` run writes the row itself.
- **CLAUDE.md's plan-file bullet cut to its tripwires:** a draft name means no source edits, in-progress belongs to another session, paused is where to resume; the rest points at `/plan` § "Plan file lifecycle".

## QA Checklist

- [ ] `under-warn` — in a fresh session (~100k baseline), run a few tool calls; no context-budget notice appears.
- [ ] `warn-once` — past 200k, the next tool call injects the warning; the agent reports and offers `/compact` or a new session, and the warning does not repeat on later calls.
- [ ] `pause` — past 300k, the agent pauses the plan (or writes `docs/plans/<slug>.paused.md` when there was none), pushes, tells the operator, and ends with a `/go <branch>` block.
- [ ] `nearly-done` — crossing either threshold with one small step left, the agent finishes and says why it did not stop.
- [ ] `rearm` — after `/compact`, climbing past 200k again fires the warning again.
- [ ] `subagent` — a subagent's tool calls never produce the notice.
- [ ] `opt-in` — `/detemplate` on a fork and `/update-muthur` on an adopter each ask about the hook before it is wired, and a no leaves no hook registered.
- [ ] `name-first-turn` — a session that ends after one turn leaves its cost row with a `name` set.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `under-warn` | unit | ✅ `test_says_nothing_under_the_warn_line` | |
| `warn-once` | unit | ✅ `test_warns_once_on_crossing_the_warn_line` | The agent's report is manual |
| `pause` | manual-only | ◐ `test_pauses_once_on_crossing_the_pause_line_after_the_warning` | The hook's half; the agent's response needs a live session |
| `nearly-done` | manual-only | — | Agent judgment |
| `rearm` | unit | ✅ `test_dropping_under_the_warn_line_rearms_both` | |
| `subagent` | unit | ✅ `test_ignores_a_subagents_tool_call`, `test_skips_a_sidechain_response` | |
| `opt-in` | manual-only | — | Skill procedure, read by an agent |
| `name-first-turn` | manual-only | — | The hook's output was checked by hand for all three row states; the agent acting on it needs a live session |

https://claude.ai/code/session_01NQLYa54isw3Ce5gq3NF5gh

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-23T11:15:53Z — "Proposed squash title/body: ``` feat: opt-in context budget…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-23T11:15:53Z

[https://github.com/vzakharov/muthur/pull/96#issuecomment-5793840367](https://github.com/vzakharov/muthur/pull/96#issuecomment-5793840367)

Proposed squash title/body:

```
feat: opt-in context budget hook (pr #96)
```

```
A session that runs long enough compacts or dies mid-task, and the
successor inherits whatever state the work was left in. The agent
cannot see its own context size, so nothing prompted it to leave a
resumable state before that happened.

A PostToolUse hook in .claude/context-budget/ reads the context the
session carries off the transcript's last main-chain usage record. At
200k tokens it warns: reach a committed stopping point, tell the
operator, offer /compact or a new session. At 300k it pauses the plan
outright - writing a paused one for work that had none - and ends the
turn with a /go handoff. Either time, the agent's judgment that the
work is nearly done overrides the stop, and is stated. Each notice
fires once per climb; a compact re-arms it. The pause is /go's one
"Stopping partway" procedure, which an operator's ask also runs.

The hook is declinable and never wired on unasked: the catalog carries
it as G8, opt-in: ask, and ADOPTING.md, /detemplate and /update-muthur
now ask every opt-in row rather than the cost ledger by name.

The cost ledger's naming hook now asks for a session's name from its
first prompt. It used to wait for the session's cost row, which lands
only as a turn ends, so a one-turn session - a /plan ending on its
handoff block - was never asked.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

_1 resolved thread omitted; re-run with `--include-resolved` to export it._

- **T01** `CLAUDE.md`:75 — unresolved — last: @vzakharov (human) 2026-09-23T12:03:12Z — "давай заведём issue сделать такое со всеми другими частями C…" → [↓](#t01)

<a id="t01"></a>

### `CLAUDE.md`:75 — unresolved

```diff
@@ -72,7 +72,7 @@ So wiring `scripts/vet.sh` is what you do **when a stack lands**, alongside `.cl
… 1 line elided …
 Claude Code's **web/remote** sessions have a bug in the plan-mode approval UI and the `AskUserQuestion` tool: after a session sits idle, the backend re-wakes it and re-emits the pending plan/question…
 
-- **The plan file's name gates implementation.** A plan is written as `docs/plans/<slug>.draft.do-not-implement.md` and stays that way until the operator gives an explicit go-ahead; only then is it `…
+- **The plan file's name gates implementation.** A plan is written as `docs/plans/<slug>.draft.do-not-implement.md` and stays that way until the operator gives an explicit go-ahead; only then is it `git mv`'d to `<slug>.in-progress.md` (quoting the go-ahead in the commit) — and to `<slug>.completed.md` when done. The `do-not-implement` token is a deliberate tripwire: if you're about to edit source while the plan still carries it, you have not been cleared. `<slug>.in-progress.md` is the mirrored tripwire: it says a session holds this plan **right now**, so the state a later session resumes from is `<slug>.paused.md` — written by a session told to stop partway, or out of context budget, recording where it got to. `/plan` writes and flips-on-approval, `/go` flips draft→in-progress→(paused→in-progress→)completed, `/finalize` sweeps the whole tree at squash so no plan reaches the trunk. Every state still matches `docs/plans/*.md`, so directory-glob consumers are unaffected. Because implementation normally starts in a **new** session, a `/plan` turn ends by handing over a copyable `/go <branch>` command rather than asking whether to proceed — the block's exact format lives in the skill.
```

**@vzakharov (human)** — 2026-09-23T11:52:40Z

это было уже и так слишком долго, а стало вообще неприемлемо. сократи пополам, оставив только то, что нужно знать ВСЕГДА, а не только когда собственно сталкиваешься с этим процессом

**@vzakharov (agent)** — 2026-09-23T11:56:57Z

Сократил втрое, а не вдвое. В пункте остались только три правила, которые нужны на каждом ходу: пока план называется `draft.do-not-implement`, код не трогаем; `in-progress` значит, что план держит другая сессия; продолжать надо с `paused`. Кто и когда переименовывает файлы, как `/finalize` их убирает и как устроен хендофф, теперь не расписано, вместо этого ссылка на `/plan` § "Plan file lifecycle": там всё это и так уже есть. fe2be2e

**@vzakharov (human)** — 2026-09-23T12:03:12Z

давай заведём issue сделать такое со всеми другими частями CLAUDE.md (и записать в сам файл такой подход) -- кажется, его неприлично раздуло.

---

## Timeline (status, references, and other events)

- **2026-09-23T11:52:48Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/96#pullrequestreview-5290516535.
