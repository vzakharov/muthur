# Issue #105: Cost ledger's Stop hook still races the harness git check

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/105
- **Author:** @vzakharov (agent)
- **Created:** 2026-09-24T00:46:48Z
- **Updated:** 2026-09-24T00:46:48Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

The harness's `stop-hook-git-check.sh` keeps reporting "There are uncommitted changes in the repository" at the end of a turn, and the only uncommitted change is the cost row that `.claude/costs/hooks/stop-session-cost.sh` is writing at that moment. The agent then spends a turn on a problem that has already fixed itself: by the time it runs `git status` the ledger has committed and pushed the row, and the tree is clean. Seen several times in an adopting repo (Playgramai/playgramapp, synced to b8e79b6).

## Why the wait misses it

`run_ledger` looks for the check's process once, via `wait_out_harness_check`, and only then runs `session_cost.py`, which rewrites the tracked row file in place. On a long session that write is not instant — it prices the whole transcript plus every subagent file — so the tree is dirty for that whole stretch, not for a moment. If the check has not started yet when the one look happens, `pgrep` finds nothing, the hook goes ahead, and the check then starts in the middle of the write, sees a modified file and exits 2.

The fallback does not cover this case. The closing `outstanding` test runs after the push, when the tree is clean again, so the hook stays quiet. The agent sees only the harness's message, which reads as if its own work were uncommitted.

## Example

One turn from the adopting repo, as the log shows it:

```
3a04ee0 00:37:28  chore: session cost +10.95 USD, total 10.95 USD
c855999 00:44:13  chore: session cost +0.41 USD, total 11.36 USD   <- the check fired during this write
5a2aa08 00:44:30  chore: session cost +0.18 USD, total 11.54 USD   <- the extra turn it caused
```

The agent answered the check with "nothing to commit, working tree clean", and that extra turn produced a row of its own. It stops there only because of `stop_hook_active`.

## What would close it

- **Keep the worktree clean while the row is priced.** Write the row to a temp path, commit it with plumbing (`hash-object -w`, `update-index --cacheinfo`, `commit`), and only then put the file in place. The file would then differ from `HEAD` for milliseconds instead of for the whole pricing run.
- **Or wait for the check to finish rather than looking once**: poll for the check's process until the write starts, instead of a single look before it.
- **Either way, speak up when this turn's row was in flight.** If the hook wrote a row this turn, a check exiting 2 was probably counting it. The existing "a git check complaining above may be counting it" line is the right message; it just needs to fire in this case too, not only when something is still outstanding afterwards.

---

