# Issue #172: muthur-sync: a new-session sync's lock names the offering session, not the syncing one

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/172
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-08T21:12:00Z
- **Updated:** 2026-10-08T21:12:00Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## The lock of a new-session sync names the wrong session

When an adopter's session accepts the muthur sync offer as a **new session**, it runs `scripts/muthur-sync.sh claim` *before* `create_session`, so nobody takes the lock while the new session starts. The claim's `Session:` trailer is `session_url()` — the **offering** session's URL, a session doing unrelated work. It stays that way for the whole sync, so "who is syncing?" (the stale-lock nudge, `claim`'s exit-3 message, a person reading the lock branch) points at the wrong session.

## Proposed fix

A `handover <session-url>` mode in `muthur-sync.sh`, run by the offering session right after `create_session`:

- rewrites the lock commit with the same tree, parent and `Claimed-By:`, `Session: <new url>`, and the claimer kept as `Spawned-By:`;
- refuses unless the lock's current `Session:` is this session's (only the holder hands over);
- pushes with `--force-with-lease` on the commit it read, so a takeover in between wins.

The nudge's `offer_rules` and `/update-muthur` § "Offered at session start" (new-session shape) gain the step. Claiming before spawning stays, since it is what closes the race.

Ported and run live in an adopter: https://github.com/vzakharov/vovazakharov.com/pull/123

---

