# PR #182: feat: relay at a context-budget pause by default, with a manual switch

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/182
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/auto-relay-default-8o7x6i
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-10T13:13:19Z
- **Updated:** 2026-10-13T17:58:32Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (the export committed at a40da5d). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/context-budget/hooks/post-tool-context-budget.sh`:96 — unresolved — last: @vzakharov (human) 2026-10-13T17:58:31Z — "даже MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY, длинновато но не пе…" → [↓](#t01)

---

## Body

## Summary

- A context-budget pause now runs `/relay` on its own by default, instead of offering it and asking each operator once whether to opt in.
- Either of two switches set to `true` (or `yes`, `on`, `1`) makes the pause offer the relay instead: `MUTHUR_MANUAL_RELAY` among the environment's variables (on the web, the cloud environment's settings, next to the setup script), or `.claude/context-budget/manual-relay/<handle>` for one operator. Any other value leaves the default; one that is not a no either is named on stderr, so a typo does not pass silently.
- A session with no operator to resolve — a bot token, a `gh` that cannot answer — relays too, so for launches nobody reopens the environment variable is the switch.
- The rule for when a pause relays lives with the context budget, in `.claude/context-budget/CLAUDE.md` § "Manual relay", which the notice points at; `/relay` only describes what a relay is, and `/go`'s pause paragraph ends the turn as the notice says.

## QA Checklist

- [ ] `default` — with no setting anywhere, cross the pause line: the session relays unasked and its report says how to have the pause ask first.
- [ ] `operator-manual` — with `manual-relay/<your handle>` holding `true`, the pause only offers `/relay`.
- [ ] `env-manual` — with `MUTHUR_MANUAL_RELAY=true` in the cloud environment's variables, a new session's pause only offers `/relay`, whatever the operator file says.
- [ ] `env-typo` — `MUTHUR_MANUAL_RELAY=ture` leaves the relay automatic and the hook names the variable on stderr.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `default` | integration | ✅ | `test_an_operator_with_no_setting_relays_without_asking`, `test_an_unanswering_gh_leaves_the_default` |
| `operator-manual` | integration | ✅ | `test_an_operators_true_keeps_the_offer`, `test_an_operators_yes_is_a_true` |
| `env-manual` | integration | ✅ | `test_the_environments_true_keeps_the_offer_whatever_the_operator_says`; that the cloud dialog's variables reach the hook is manual |
| `env-typo` | integration | ✅ | `test_an_unknown_environment_value_is_named_and_leaves_the_default` |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01TMUnDUc4KfS2oRHWMpEfxZ
https://claude.ai/code/session_01FMTfCEbXR9pmGuyMwKtuap

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-10T13:13:39Z — "Proposed squash title/body: ``` feat: relay at a context-bud…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-10T13:13:39Z

[https://github.com/vzakharov/muthur/pull/182#issuecomment-6097869928](https://github.com/vzakharov/muthur/pull/182#issuecomment-6097869928)

Proposed squash title/body:

```
feat: relay at a context-budget pause by default, with a manual switch (pr #182)
```

```
A context-budget pause offered /relay and asked each operator once
whether to run it unasked from then on. Running it unasked is now the
default, so the question is gone and the relay's report says how to
have the pause ask first instead.

Either of two switches set to `true` (or yes, on, 1) makes the pause
offer the relay instead: MUTHUR_MANUAL_RELAY among the environment's
variables (on the web, the cloud environment's settings beside its
setup script), or the operator's
.claude/context-budget/manual-relay/<handle>. Any other value leaves
the default, and one that is not a no either is named on stderr.

A session with no operator to resolve, a bot token or a gh that cannot
answer, relays too; for launches nobody reopens, the environment
variable is the switch. When a pause relays is the context budget's
rule, kept in its CLAUDE.md beside the hook; /relay describes only what
a relay is.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

_1 resolved thread omitted; re-run with `--include-resolved` to export it._

- **T01** `.claude/context-budget/hooks/post-tool-context-budget.sh`:96 — unresolved — last: @vzakharov (human) 2026-10-13T17:58:31Z — "даже MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY, длинновато но не пе…" → [↓](#t01)

<a id="t01"></a>

### `.claude/context-budget/hooks/post-tool-context-budget.sh`:96 — unresolved

```diff
@@ -90,18 +90,26 @@ mkdir -p "$state_dir" && printf '%s\n' "$level" >"$state_file" || {
… 15 lines elided …
+# Auto-relay is on unless the environment or the operator turns it off. A value
+# that is neither was set by someone, so it reads as the switch they reached for.
+auto_relay=on
+case "${MUTHUR_AUTO_RELAY:-on}" in
```

**@vzakharov (human)** — 2026-10-13T17:19:21Z

я не люблю default-on флаги, может MUTHUR_MANUAL_RELAY, включается только если `true`? (взять ли `on` и `yes` -- на твоё усмотрение)

**@vzakharov (agent)** — 2026-10-13T17:54:43Z

Согласен, сделал в 6e291b0: теперь `MUTHUR_MANUAL_RELAY`, по умолчанию выключен. Включают его `true`, а также `yes`, `on` и `1` — регистр не важен. Любое другое значение оставляет дефолт; если это не «нет» (`false`/`no`/`off`/`0`), хук пишет имя переменной в stderr, чтобы опечатка вроде `ture` не прошла молча. Файл оператора переехал по той же логике в `manual-relay/<handle>` и тоже включается `true`. Твой `auto-relay/vzakharov` с `on` удалил — теперь это и так дефолт.

**@vzakharov (human)** — 2026-10-13T17:58:31Z

даже MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY, длинновато но не перепутаешь

---

## Timeline (status, references, and other events)

- **2026-10-13T17:23:59Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/182#pullrequestreview-5507358321.
- **2026-10-13T17:55:40Z** @vzakharov renamed from «feat: make auto-relay the default, with environment and operator opt-outs» to «feat: relay at a context-budget pause by default, with a manual switch».
