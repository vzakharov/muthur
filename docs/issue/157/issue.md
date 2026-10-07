# Issue #157: Re-check the sync lock right before offering /update-muthur

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/157
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-07T06:25:37Z
- **Updated:** 2026-10-07T06:25:37Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Problem

An offer to sync can still be made after another session has already claimed the sync, because nothing tells the agent to check the lock at the moment it speaks. The lock itself is not the problem: it is checked when the nudge runs and again when someone claims it. But an agent can spend hours between reading the nudge and making the offer, or repeating it, and a parallel session can claim the sync in that time.

Seen downstream (vzakharov/vovazakharov.com):

- 05:40: a session got the nudge and offered a ride-along of `4b5bbe6`. The operator did not answer.
- 06:06: a different session claimed `muthur-sync-lock-2fb5fa5c8774`.
- Later: the first session was relayed. Its summary listed the ride-along as an open offer, so the successor offered it to the operator again, even though another session had held the sync for hours.

The operator's call: leave `/relay take` alone. Instead, the place that tells the agent to make the offer should say to re-check the claim right before making it, because someone may have taken it in the meantime.

## Proposal

Add one rule in two places, `offer_rules()` in `scripts/muthur-sync.sh` and `/update-muthur` § "Offered at session start". The rule: before making the offer, and before repeating it, run `git ls-remote origin refs/heads/muthur-sync-lock-<lastSyncedSha:0:12>`. If the ref exists, drop the offer. The operator then hears either nothing or the holder's session link.

This sits alongside "nothing is cloned, read or claimed before the operator says yes". The check is one `ls-remote` and claims nothing. The point is to avoid offering something that is already taken.

## Also seen: the nudge skips sessions that don't start on the trunk

On a session that started on a non-default branch, the nudge printed `no trunk ref (origin/HEAD, origin/main or origin/master) to read the watermark from` and offered nothing. The reason: the container cloned only that branch, so it has no `origin/main`. `trunk_ref()` checks only refs that already exist on disk and never fetches. One possible fix: when none of those refs exist, ask the remote (`git ls-remote --symref origin HEAD`) and fetch the branch it names. Once fixed, those sessions would also see a held lock instead of offering nothing.

---

