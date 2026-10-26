# PR #230: fix: price Claude Haiku 5.5, long prompts included

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/230
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← feat/external-docs-and-haiku-price
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-26T17:57:43Z
- **Updated:** 2026-10-26T20:31:40Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/costs/lib/pricing.py`:1 — unresolved — last: @vzakharov (human) 2026-10-26T20:30:43Z — "распухло, давай сплиттить" → [↓](#t01)

---

## Body

## Summary

- **`prices.json` gains `claude-haiku-5-5/standard`** (from the claude-api skill's model table, cached 2026-10-06). Without it, the Stop hook's pricing raises on any session that spawned a Haiku 5.5 subagent.
- **A rate row may carry a long-prompt card, `above`.** It holds a `prompt_tokens` threshold and a second set of rates. A response whose prompt (input plus cache reads and writes) runs past the threshold is billed whole at the second set, output included. Haiku 5.5 uses it: $0.10 / $0.50 up to 100K tokens, $0.50 / $2.50 above. The rate is picked per response, both in the transcript pricer and in the cold-cache restart estimate (`lib/restart.py`).
- **Open question, recorded in the row's `confidence` note:** the docs say only "prompt". Whether cache reads count toward the 100K threshold, as the code assumes, needs a real bill to settle.

## QA Checklist

- [ ] `haiku-priced` — spawn an Agent with `model: haiku`, then end the turn. The Stop hook writes the cost row without an unpriced-model block.
- [ ] `long-tier` — `python3 .claude/costs/test_pricing.py`. It covers a prompt at the threshold, a prompt one token past it via a cache read, each response priced on its own prompt, and an `above` with no threshold refused.
- [ ] `old-rows` — every other row in `prices.json` has no `above`, so `test_restart.py`, `test_stop_hook.py` and the cold-cache tests should still pass unchanged.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `haiku-priced` | Partly | No | Needs a live Haiku subagent |
| `long-tier` | Yes | Yes | `test_pricing.py` |
| `old-rows` | Yes | Yes | Whole costs and cold-cache suites pass |

https://claude.ai/code/session_01PMrbaxMhMeLJWu9sCmkxag

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-26T17:57:59Z — "Proposed squash body: ``` An unpriced (model, speed) pair ma…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-26T17:57:59Z

[https://github.com/vzakharov/muthur/pull/230#issuecomment-6423497652](https://github.com/vzakharov/muthur/pull/230#issuecomment-6423497652)

Proposed squash body:

```
An unpriced (model, speed) pair makes the Stop hook's pricing raise, so
no session that spawned a Claude Haiku 5.5 subagent could be priced.
Haiku 5.5 also bills by prompt length, which a one-card rate row could
not express.

A rate row may now carry `above`: a `prompt_tokens` threshold and a
second set of rates. A response whose prompt (input plus cache reads
and writes) runs past it is billed whole at the second set, output
included. The pick is per response, in the transcript pricer and the
cold-cache restart estimate alike.

`prices.json` gains `claude-haiku-5-5/standard`: 0.10 / 0.50 per MTok
up to 100K tokens and 0.50 / 2.50 above, with the usual cache
multipliers, from the claude-api skill's model table cached
2026-10-06. Its confidence note flags the open question: the docs say
only "prompt", so whether cache reads count toward the threshold waits
on a bill.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/lib/pricing.py`:1 — unresolved — last: @vzakharov (human) 2026-10-26T20:30:43Z — "распухло, давай сплиттить" → [↓](#t01)

<a id="t01"></a>

### `.claude/costs/lib/pricing.py`:1 — unresolved

**@vzakharov (human)** — 2026-10-26T20:30:43Z

распухло, давай сплиттить

---

## Timeline (status, references, and other events)

- **2026-10-26T17:58:35Z** @vzakharov renamed from «feat: mark documents someone else wrote, and price Haiku 5.5» to «chore: price Claude Haiku 5.5».
- **2026-10-26T17:58:43Z** @vzakharov renamed from «chore: price Claude Haiku 5.5» to «fix: price Claude Haiku 5.5».
- **2026-10-26T18:06:24Z** @vzakharov renamed from «fix: price Claude Haiku 5.5» to «fix: price Claude Haiku 5.5, long prompts included».
- **2026-10-26T20:31:40Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/230#pullrequestreview-5658554447.
