> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G9 — Cold-cache guard

A hook that refuses a prompt changes how every returning session starts, and
whether the price is worth a stop is the operator's call — so the row is
`opt-in: ask`.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `.claude/cold-cache/` | Stop the first prompt after the session's prompt cache expired, before it reaches the model, and price the two ways on: carry on, which pays the re-cache, or a fresh session, for work that is already all on the branch. Resending any prompt goes through, a bare `!` resends the stopped one, and `/compact`, `/clear`, `/relay` and the built-ins that make no model request always pass. **The cost, which is why it is asked:** one refused prompt per return to a session worth more than `COLD_CACHE_MIN_USD` to re-cache. Arrives with two `.claude/settings.json` entries to merge and a `scripts/vet.sh` loop running its tests. | `python3` ≥3.9 | `.claude/costs/lib/` and `prices.json` (G7) | adopt — **opt-in: ask** |
