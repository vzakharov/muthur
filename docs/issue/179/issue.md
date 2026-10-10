# Issue #179: Vet: fail when a branch's cost row has no human-hour estimate

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/179
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-10T13:00:22Z
- **Updated:** 2026-10-10T13:00:22Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## What happened

An unattended routine in vovazakharov.com (`/file-basilisk-case`, PR vzakharov/vovazakharov.com#130) ran to its end and committed its cost row with `"estimate": null`. Nobody noticed until the operator looked at the row. The estimate was backfilled afterwards with `estimate.py set --session`.

The notice did go out. Going by the session's events, `.claude/costs/hooks/estimate-notice.sh` ran twice, once on the routine's prompt and once on a task notification. Both times it exited 0 and returned the full "no human-hour estimate yet" text as `additionalContext`. The agent never called `estimate.py`. It worked through the skill's steps, and the skill has no estimate step. "Once the size of the work is known" has no deadline, and nothing comes back to it later.

## What the operator wants

**A vet check that fails when a cost row on the branch has no estimate.** The operator ruled out a `Stop`-hook block, because the size of the work is often not settled when a turn ends. Vet runs at `/finalize`, where the work is done and the size is known, so the gate belongs there.

Sketch:

- Check the rows under `.claude/costs/sessions/` that the branch adds or changes against its merge base. Rows already on the trunk are left alone, because many predate estimates.
- The running session (`CLAUDE_CODE_SESSION_ID`) passes when its pending `tmp/estimates/<id>.json` exists, even if the row on disk does not carry it yet. That uses the same `latest(row, pending)` rule `estimate.py show` applies. A running session with no row yet and no pending estimate fails.
- The failure names each session id and the exact command that fixes it: `estimate.py set --part … [--session <id>]`.
- It reads only the ledger, so it can join the fan-out next to the ledger's tests.

## Related

#177 is the same failure from the other side: there the estimate went stale after the task grew. A vet gate would not catch a stale figure, only a missing one.

---

