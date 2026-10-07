# Issue #161: Catalog has no row for .claude/keepalive/

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/161
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-07T18:21:13Z
- **Updated:** 2026-10-07T18:21:13Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Problem

`.claude/keepalive/` (pr #159, 5b27aa8) has no row in `.claude/skills/update-muthur/catalog.md`. A downstream `/update-muthur` reads that catalog to offer a new path with its criteria attached (Step 4a), so the sync in vzakharov/life had to make up the criteria itself when it reached this commit.

It should be offered as opt-in, on the same grounds as `.claude/costs/`, `.claude/context-budget/` and `.claude/cold-cache/`:

- a `UserPromptSubmit` hook entry in `.claude/settings.json` to merge;
- a background watcher on every idle turn — the one exception to CLAUDE.md's `run_in_background` ban, so that line changes too;
- up to `CACHE_KEEPALIVE_WAKES` (5) wakes per idle spell, each a visible line in chat, the last one running `/relay` without a successor, which commits a summary file to the branch;
- a `scripts/vet.sh` opt-in loop entry for `test_keepalive.py`;
- it imports `.claude/costs/lib/restart.py`, so it depends on `.claude/costs/`.

## Fix

Add a `.claude/keepalive/` row to the catalog, `adopt — opt-in: ask`, naming the costs above and the dependency on `.claude/costs/`.

---

## Timeline (status, references, and other events)

- **2026-10-07T18:22:01Z** @vzakharov referenced this issue in a commit.
- **2026-10-07T18:22:42Z** @vzakharov cross-referenced this issue from [#166 chore: keepalive кэша, отчёт о стоимости по всем репо, перепроверка замка синка](https://github.com/vzakharov/life/pull/166).
