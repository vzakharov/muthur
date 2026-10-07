> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G8 — Context budget

Whether a session should stop itself partway is the operator's call about how
they want to work, and the hook's notices reach every long session — so the row
is `opt-in: ask`.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `.claude/context-budget/` | After every tool call, read the context the session carries off its transcript, and past the warning line tell the agent to finish if it fits in the room left before the pause line, or else to steer to the best stopping point it can reach by then and pause there; past the pause line, to pause where the work stands, a last step aside. Either pause releases the plan — writing one when the work had none — and ends the turn offering `/relay`, or runs it unasked for an operator whose `auto-relay/<handle>` says `on`, a per-operator setting the first offer asks about. With G7's lib and price table, the lines sit where a relay starts saving over the next 100k tokens of work and where it saves 20% of it, capped at 200k and 300k, and the notice gives the dollars; without them, or under `CONTEXT_BUDGET_LINES=fixed`, they are 200k and 300k. **The cost, which is why it is asked:** a `PostToolUse` hook on every tool call, and a session that can end its own turn with the work paused, or hand itself to a new one. Arrives with one `.claude/settings.json` entry to merge and a `scripts/vet.sh` loop running its tests; a no deletes the directory and both. | `bash`, `jq`; `gh` for auto-relay, without which it is never offered; `python3` ≥3.9 for its tests and the priced lines | `.claude/hooks/lib.sh` (G4), `/go` and `/relay` (G2); `.claude/costs/lib/` and `prices.json` (G7) for the priced lines | adopt — **opt-in: ask** |
