# PR #249: feat: skip Haiku orientation mark; warn on relay at 5% saving

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/249
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/haiku-self-orientation-disable-extt4j
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-29T02:49:03Z
- **Updated:** 2026-10-29T02:57:17Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/context-budget/test_context_budget.py`:1 — unresolved — last: @vzakharov (human) 2026-10-29T02:55:37Z — "надо сплиттить" → [↓](#t01)

---

## Body

## Summary

- **A Haiku session is no longer asked for the orientation mark.** Asked, it runs `oriented.py` on its first response, before it has read anything, so the ledger records an orientation of $0. A `/relay take` session prices its own reorientation from that row, which put the context budget's warning line at break-even with the handoff itself, and the relay was offered right after the session started. `oriented.py exempt` reads the model from the transcript's latest `model` attachment or main-chain response (compactions and mid-session switches included), and `estimate-notice.sh` leaves the request out for any model in `UNMARKED_MODELS`.
- **The context budget's warning now waits for a saving worth a handoff.** It used to fire where a relay saves $0, which let it fire on savings of cents over a 100k slice that costs $2-4. It fires where a relay saves `MUTHUR_CONTEXT_BUDGET_WARN_SAVING` percent of what carrying on costs, default 5, beside the pause's 20.
- **Why 5%:** over the ledger's 30 `/relay take` sessions a relay's up-front cost is $0.4-1.8, and on the median session 5% puts the warning ~20k tokens past break-even (Sonnet 258k to 278k, Opus 268k to 291k) with ~75-85k tokens of room before the pause. 10% would leave ~50k, which is too little to reach a stopping point.

## QA Checklist

- [ ] `haiku-no-mark` — start a session on Haiku: the first prompt's context carries no "mark the end of your orientation" request, and neither does the context after a compaction.
- [ ] `other-models-asked` — start a session on Sonnet or Opus: the request is still there until `oriented.py` has been run.
- [ ] `warn-later` — on a session whose relay saves only cents at the old line, the warning arrives later and names "where relaying saves 5% of what carrying on costs".
- [ ] `warn-knob` — `MUTHUR_CONTEXT_BUDGET_WARN_SAVING=15` moves the warning out; a value not under `MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING` is refused on stderr.

| Item                 | Automatable | Covered? | Notes                                                                                 |
| -------------------- | ----------- | -------- | ------------------------------------------------------------------------------------- |
| `haiku-no-mark`      | integration | ✅       | `test_estimate_notice` — a Haiku attachment, after a compaction, on a `compact` start |
| `other-models-asked` | integration | ✅       | `test_estimate_notice` — latest model wins, a subagent's model is ignored             |
| `warn-later`         | integration | ✅       | `test_context_budget` — `ThePricedLines`                                              |
| `warn-knob`          | integration | ✅       | `test_context_budget` — a larger saving moves the line, a bad pair is refused         |

https://claude.ai/code/session_01DaohkEar2FEzE8ociMZkbf

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-29T02:49:20Z — "Proposed squash body: ``` A Haiku session that is asked to m…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-29T02:49:20Z

[https://github.com/vzakharov/muthur/pull/249#issuecomment-6486519704](https://github.com/vzakharov/muthur/pull/249#issuecomment-6486519704)

Proposed squash body:

```
A Haiku session that is asked to mark its orientation does so on its
first response, before reading anything. The ledger then records an
orientation of $0, a `/relay take` session prices its own
reorientation from that row, and the context budget's warning line
falls to break-even with the handoff itself, so a relay was offered
right after the session started.

The orientation notice now leaves the mark out for a model named in
`UNMARKED_MODELS` (Haiku), read from the transcript's latest `model`
attachment or main-chain response, so compactions and mid-session
switches are read alike. `oriented.py exempt` is the check the hook
runs.

The warning line, which sat where a relay saves $0, now sits where it
saves `MUTHUR_CONTEXT_BUDGET_WARN_SAVING` percent of what carrying on
costs (default 5, under the pause's 20). On the ledger's relayed
sessions a relay costs $0.4-1.8 up front and a 100k slice $2-4, so a
saving of cents was noise; 5% lands ~20k tokens past break-even and
keeps ~75k of room before the pause.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/context-budget/test_context_budget.py`:1 — unresolved — last: @vzakharov (human) 2026-10-29T02:55:37Z — "надо сплиттить" → [↓](#t01)

<a id="t01"></a>

### `.claude/context-budget/test_context_budget.py`:1 — unresolved

**@vzakharov (human)** — 2026-10-29T02:55:37Z

надо сплиттить

---

## Timeline (status, references, and other events)

- **2026-10-29T02:49:20Z** @vzakharov renamed from «feat: stop asking Haiku for the orientation mark; warn on a relay only at 5% saving» to «feat: skip Haiku orientation mark; warn on relay at 5% saving».
- **2026-10-29T02:57:17Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/249#pullrequestreview-5692314496.
