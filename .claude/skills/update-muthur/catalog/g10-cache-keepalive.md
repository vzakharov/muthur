> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G10 — Cache keepalive

Where G9 stops the prompt that finds the cache cold, this wakes the idle session
before it goes cold. The cost lands on every idle turn, and whether the cache is
worth keeping warm is the operator's call — so the row is `opt-in: ask`.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `.claude/keepalive/` | Wake an idle session shortly before its one-hour prompt cache expires, so the next prompt does not re-cache the whole conversation at about 40 times a cache read. A `UserPromptSubmit` hook has the agent start a background watcher as each turn's last action — unless the branch alone lets a fresh session continue — and the watcher's exit is the wake. **The cost, which is why it is asked:** a background watcher on every idle turn, which is **the one exception to CLAUDE.md's ban on `run_in_background`**, so that line changes in your `CLAUDE.md` too; up to `CACHE_KEEPALIVE_WAKES` (5) wakes per idle spell, each a visible line in chat; and the last wake runs `/relay park`, which commits a summary file to the branch. Only a one-hour cache is kept, read off the session's own cache writes. Arrives with one `.claude/settings.json` `UserPromptSubmit` entry to merge and a `scripts/vet.sh` loop entry running `test_keepalive.py`; a no deletes the directory and both. | `python3` ≥3.9; a Bash tool with `run_in_background` | **`.claude/costs/lib/` and `prices.json` (G7)** — it imports `lib/restart.py`, which reads the ledger's pricing, so the dependency is hard rather than an optional input; `/relay` (G2), its `park` entry | adopt — **opt-in: ask** |

**It does not run without G7.** `keepalive.py` imports `.claude/costs/lib/restart.py`
at load, so a repo that declines the ledger has nothing for it to import: take
the directory only together with `.claude/costs/`, or answer no to both.
