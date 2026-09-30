# Issue #127: Price dated model ids (claude-haiku-4-5-20251001) at their undated row

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/127
- **Author:** @vzakharov (human)
- **Created:** 2026-09-30T16:52:55Z
- **Updated:** 2026-09-30T16:52:55Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

A transcript that names a dated model id such as `claude-haiku-4-5-20251001` cannot be priced: `.claude/costs/prices.json` has only the undated `claude-haiku-4-5` row, so `lib/pricing.py` raises `UnpricedError` and `session_cost.py` writes **no row for that session at all**. The whole session's cost is lost, not just Haiku's share.

## Why it has not shown yet

Today Haiku reaches the ledger only through telemetry events: Claude Code's background calls, priced at the event's own price. They come to $0.024 of $154.68 across the ledger's 42 rows. The failure hits the first session where Haiku answers inside a transcript, for example as a subagent.

The context-budget and cold-cache hooks already catch the error and fall back to the next reorientation source, so they keep working. Only the ledger row is lost.

## Fix

Resolve a model id that ends in `-YYYYMMDD` to its undated row when the dated one is absent. Keep the loud `UnpricedError` for any model with no row either way, since `prices.json` is maintained by hand and a response counted as free is worse than no row.

## Acceptance

- A transcript whose responses name `claude-haiku-4-5-20251001` is priced at the `claude-haiku-4-5/standard` rates.
- A model with neither a dated nor an undated row still raises.
- A test in `.claude/costs/test_pricing.py` covers both.

---

