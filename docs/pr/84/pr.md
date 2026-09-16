# PR #84: feat: route the opening prompt; stop reporting rules nobody invoked

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/84
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/untyped-flag-reports-ynjyku
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-16T21:59:31Z
- **Updated:** 2026-09-16T22:03:35Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **`/handle` reported on a flag nobody typed.** Its § "Argument shape" hung a reporting clause off the `and merge` bullet without scoping it to an invocation that carried the flag, and Step 5 then had every run pass `/finalize` "no `and merge`, per § Argument shape". Sessions relayed the rule instead of the run: operators who never wrote `and merge` were told why their merge was held. Both sites now fire on presence, and the section says so once.
- **The entry ladder now fires at the prompt it governs.** `.claude/hooks/prompt-route-notice.sh` puts CLAUDE.md's routing call in front of the session's opening prompt, where the call is actually made — a pointer, not a copy, since the rows are resident in context already. It skips a prompt the operator routed themselves with a leading `/`, and every prompt after the first.
- **`/plainly` names the class.** A seventh defect, `polar bear`, borrowed from `/tend-prose`'s negation lens: that lens sweeps prose the repo keeps, this row catches the same shape in a reply nobody will ever sweep.
- **`first_prompt` joins `need_command` in `.claude/hooks/lib.sh`.** Both once-per-session hooks tested the transcript the same way; the test tracks one external contract, so it lives in the file whose header already calls itself the home of the hooks' guards.

## QA Checklist

- [ ] `route-fires` — open a fresh session whose first prompt asks in prose for a change to this repo; confirm the routing notice is in the turn's context and the session enters `/task` instead of editing straight away.
- [ ] `route-quiet-later` — send a second prompt in that same session; no notice arrives, and the follow-up is handled directly.
- [ ] `route-quiet-slash` — open a session with `/handle <branch>` as the first prompt; no notice, the operator having routed it themselves.
- [ ] `export-still-fires` — open a session whose first prompt ends in `#<N>`; the issue export still runs, i.e. the hoisted `first_prompt` did not change that hook's behaviour.
- [ ] `handle-silent` — run `/handle <branch>` with no `and merge`; the report says nothing about a held merge.
- [ ] `handle-held` — run `/handle <branch> and merge`; the report does say the merge was held and names `/finalize <branch> and merge`.
- [ ] `catalog` — `./scripts/check-skill-catalog.sh` passes, the new hook having a row and the `@`-references resolving.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `route-fires` | unit | ❌ | Pipe a payload into the hook and assert `additionalContext` comes back; the agent's reaction to it stays manual |
| `route-quiet-later` | unit | ❌ | Same pipe with a transcript holding an `"type":"assistant"` record → exit 0, no output |
| `route-quiet-slash` | unit | ❌ | Same pipe with a prompt opening `/` → exit 0, no output |
| `export-still-fires` | unit | ❌ | Covered by the same `first_prompt` assertions; the export itself needs the network |
| `handle-silent` | manual-only | — | The finding is what an agent says in its report, which no assertion reaches |
| `handle-held` | manual-only | — | Same |
| `catalog` | unit | ✅ | `scripts/check-skill-catalog.sh`, already in `scripts/vet.sh` |

https://claude.ai/code/session_01T9pCz2N9nNkkMMc8Xufa1Y

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-16T22:00:03Z — "Proposed squash title/body: ``` feat: route the opening prom…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-16T22:00:03Z

[https://github.com/vzakharov/muthur/pull/84#issuecomment-5705183319](https://github.com/vzakharov/muthur/pull/84#issuecomment-5705183319)

Proposed squash title/body:

```
feat: route the opening prompt, and report the run not the rules (pr #84)
```

```
Two ends of the loop talked about rules instead of runs. `/handle` hung
its reporting clause on the `and merge` bullet without scoping it to an
invocation that carried the flag, so sessions explained to operators who
never typed it why their merge was held. And the entry ladder that
routes an opening prompt sat in CLAUDE.md, resident and routinely
skipped, so a change asked for in prose got made directly — no
plan-or-not call, no quality passes, no PR.

Every bullet in `/handle` § "Argument shape" now fires on presence, the
reporting included, and the section says so once. The one place a flag
nobody typed is still named is Step 5's note that land-prep was not
requested, and it names `/finalize` alone.

`.claude/hooks/prompt-route-notice.sh` puts the routing call in front of
the session's first prompt, pointing at the ladder rather than copying
its rows: CLAUDE.md is resident, so a copy would add nothing at the
decision point and would drift from its home. It stays quiet for a
prompt the operator routed with a leading `/`, and for every prompt
after the first — the test it now shares with the issue-export hook
through `first_prompt` in `.claude/hooks/lib.sh`.

`/plainly` gains a seventh defect, `polar bear`, borrowed from
`/tend-prose`'s negation lens: that lens sweeps prose the repo keeps,
this row catches the same shape in a reply nobody ever sweeps.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/plainly/SKILL.md`:1 — unresolved — last: @vzakharov (human) 2026-09-16T22:02:43Z — "думаю, пока не нужно менять этот скилл" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-09-16T22:03:00Z — "скорее fix" → [↓](#t02)
- **T03** `CLAUDE.md`:75 — unresolved — last: @vzakharov (human) 2026-09-16T22:03:32Z — "зачем говорить здесь об этом, если им сам хук это скажет?" → [↓](#t03)

<a id="t01"></a>

### `.claude/skills/plainly/SKILL.md`:1 — unresolved

**@vzakharov (human)** — 2026-09-16T22:02:43Z

думаю, пока не нужно менять этот скилл

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,38 @@
+Proposed squash title/body:
+
+```
+feat: route the opening prompt, and report the run not the rules (pr #84)
```

**@vzakharov (human)** — 2026-09-16T22:03:00Z

скорее fix

---

<a id="t03"></a>

### `CLAUDE.md`:75 — unresolved

```diff
@@ -72,7 +72,7 @@ So wiring `scripts/vet.sh` is what you do **when a stack lands**, alongside `.cl
… 1 line elided …
 
 - **The plan file's name gates implementation.** A plan is written as `docs/plans/<slug>.draft.do-not-implement.md` and stays that way until the operator gives an explicit go-ahead; only then is it `…
-- **A new session's opening prompt routes on one question: does it ask for a change to this codebase?** This ladder is the home of that rule; `/task`, `/plan` and `/go` point at it rather than restat…
+- **A new session's opening prompt routes on one question: does it ask for a change to this codebase?** This ladder is the home of that rule; `/task`, `/plan` and `/go` point at it rather than restating it, and `.claude/hooks/prompt-route-notice.sh` puts the call in front of the opening prompt itself.
```

**@vzakharov (human)** — 2026-09-16T22:03:32Z

зачем говорить здесь об этом, если им сам хук это скажет?

---

## Timeline (status, references, and other events)

- **2026-09-16T22:03:34Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/84#pullrequestreview-5228820281.
