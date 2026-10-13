# PR #182: feat: make auto-relay the default, with environment and operator opt-outs

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/182
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/auto-relay-default-8o7x6i
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-10T13:13:19Z
- **Updated:** 2026-10-13T17:23:59Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/context-budget/hooks/post-tool-context-budget.sh`:96 — unresolved — last: @vzakharov (human) 2026-10-13T17:19:21Z — "я не люблю default-on флаги, может MUTHUR_MANUAL_RELAY, вклю…" → [↓](#t01)
- **T02** `.claude/skills/relay/SKILL.md`:86 — unresolved — last: @vzakharov (human) 2026-10-13T17:23:34Z — "мне тут знаешь что не нравится? мы описываем механизм релея…" → [↓](#t02)

---

## Body

## Summary

- A context-budget pause now runs `/relay` on its own by default, instead of offering it and asking each operator once whether to opt in.
- Two switches turn it off, either one enough: `MUTHUR_AUTO_RELAY=off` among the environment's variables (on the web, the cloud environment's settings, next to the setup script), or `.claude/context-budget/auto-relay/<handle>` holding `off` for one operator. The environment's `on` does not override an operator's `off`; an unknown value reads as `off`.
- A session with no operator to resolve — a bot token, a `gh` that cannot answer — now relays too, so for launches nobody reopens the environment variable is the switch.
- `/relay` § "Auto-relay", `/go`'s pause paragraph, the budget hook's `CLAUDE.md` and the catalog row now describe the default and both switches.

## QA Checklist

- [ ] `default` — with no setting anywhere, cross the pause line: the session relays unasked and its report says how to turn that off.
- [ ] `operator-off` — with `auto-relay/<your handle>` holding `off`, the pause only offers `/relay`.
- [ ] `env-off` — with `MUTHUR_AUTO_RELAY=off` in the cloud environment's variables, a new session's pause only offers `/relay`, whatever the operator file says.
- [ ] `env-typo` — `MUTHUR_AUTO_RELAY=no` reads as `off` and the hook names the variable on stderr.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `default` | integration | ✅ | `test_an_operator_with_no_setting_relays_without_asking`, `test_an_unanswering_gh_leaves_the_default` |
| `operator-off` | integration | ✅ | `test_an_operators_off_keeps_the_offer` |
| `env-off` | integration | ✅ | `test_the_environments_off_outranks_the_operators_on`; that the cloud dialog's variables reach the hook is manual |
| `env-typo` | integration | ✅ | `test_an_unknown_environment_value_reads_as_off` |

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-10T13:13:39Z — "Proposed squash title/body: ``` feat: make auto-relay the de…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-10T13:13:39Z

[https://github.com/vzakharov/muthur/pull/182#issuecomment-6097869928](https://github.com/vzakharov/muthur/pull/182#issuecomment-6097869928)

Proposed squash title/body:

```
feat: make auto-relay the default, with env and operator opt-outs (pr #182)
```

```
A context-budget pause offered /relay and asked each operator once
whether to run it unasked from then on. Running it unasked is now the
default, so the question is gone and the relay's report says how to
turn it off instead.

Two switches turn it off, either one enough: MUTHUR_AUTO_RELAY=off
among the environment's variables (on the web, the cloud environment's
settings beside its setup script), or the operator's
.claude/context-budget/auto-relay/<handle> holding `off`. The
environment's `on` cannot override an operator's `off`, and a value
that is neither reads as `off`, since someone set it to reach for the
switch.

A session with no operator to resolve, a bot token or a gh that cannot
answer, now relays too; for launches nobody reopens, the environment
variable is the switch. /relay's Auto-relay section owns both switches.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/context-budget/hooks/post-tool-context-budget.sh`:96 — unresolved — last: @vzakharov (human) 2026-10-13T17:19:21Z — "я не люблю default-on флаги, может MUTHUR_MANUAL_RELAY, вклю…" → [↓](#t01)
- **T02** `.claude/skills/relay/SKILL.md`:86 — unresolved — last: @vzakharov (human) 2026-10-13T17:23:34Z — "мне тут знаешь что не нравится? мы описываем механизм релея…" → [↓](#t02)

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

---

<a id="t02"></a>

### `.claude/skills/relay/SKILL.md`:86 — unresolved

```diff
@@ -78,11 +78,12 @@ Reach for it only for a detail the summary dropped and no lower-numbered `relay-
 
 ## Auto-relay
 
-A pause the context budget calls for (`.claude/context-budget/`, at either of its lines) ends the turn offering a relay; an operator who has opted in has it run instead, unasked and with no argument. The setting is **per operator, not per repo**, because nothing documented tells a session someone is watching from one nobody will reopen — a Claude Tag launch, say — and a successor spawned from the second is a session nobody finds. The operator is the one `.claude/hooks/operator-voice.sh` resolves, the lowercased login of the session's `User`-type GitHub token; a session running on a bot's token resolves none, so it never auto-relays and is never asked.
+A pause the context budget calls for (`.claude/context-budget/`, at either of its lines) runs the relay unasked and with no argument, and its report says the session relayed on its own and how to turn that off. Two switches turn it off, either one enough on its own; the pause then ends the turn offering the relay instead.
 
-- **The file** is `.claude/context-budget/auto-relay/<handle>`, holding `on` or `off`. Anything else reads as never asked.
-- **Only the operator's own answer writes it.** The notice asks when there is no file; they may also say so at any other time, either way. Write the one word, commit it with their words quoted, and push. `off` is recorded too, so the question is not put again.
-- **It applies wherever the tree carries it**: on this branch from the next notice, and on every branch once it reaches the default branch. Say so when you write it, since the operator's next session may start from a base that does not have it yet.
+- **For an environment**: `MUTHUR_AUTO_RELAY=off` among its environment variables — on the web, in the cloud environment's settings, the dialog that also holds its setup script; locally, `.claude/settings.local.json`'s `env`. It is the switch for launches nobody reopens, whose successor would be a session nobody finds, and the only one for a session with no operator to resolve. A value other than `on` or `off` reads as `off`, and `on` cannot override an operator's `off`.
+- **For an operator**: `.claude/context-budget/auto-relay/<handle>` holding `off`, the handle being the one `.claude/hooks/operator-voice.sh` resolves — the lowercased login of the session's `User`-type GitHub token. Any other content leaves the default.
+  - **Only the operator's own words write it**, whenever they say it: write `off`, commit it with their words quoted, and push; asked to turn it back on, delete the file the same way.
+  - **It applies wherever the tree carries it**: on this branch from the next notice, and on every branch once it reaches the default branch. Say so when you write it, since the operator's next session may start from a base that does not have it yet.
```

**@vzakharov (human)** — 2026-10-13T17:23:34Z

мне тут знаешь что не нравится? мы описываем механизм релея в рамках context-budget в скилле релея, хотя по сути оно принадлежит теме про context budget. По-моему, релей должен просто знать "я вот такое, я создаю файл и передаю новой сессии", а вот уже контекстный хук (или что у нас там) должен говорить: при выполнении таких-то таких-то критериев ты делаешь релей, всё -- при этом вопрос нужно ли его вообще называть "авто", потому что это просто дефолтное поведение.

понимаешь о чём я, или я overthinking?

---

## Timeline (status, references, and other events)

- **2026-10-13T17:23:59Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/182#pullrequestreview-5507358321.
