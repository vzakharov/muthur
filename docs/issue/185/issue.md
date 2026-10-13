# Issue #185: Let an adopting repository add its own fixed-grade estimate roles

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/185
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-12T22:32:16Z
- **Updated:** 2026-10-12T22:32:16Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

An adopting repository needs estimate roles of its own that the shared `rates.json` does not carry. In vovazakharov.com that role is `artist`: some sessions do creative work — a persona's reflections on songs, say — that neither `copywriter` nor `editor` captures. Today the only way in is editing `rates.json`, which collides with every sync of it.

Two requirements, from the operator's review of a first attempt:

1. **Such a role is fixed-grade, not gradeless.** `artist` is always senior. Its hours land in the existing `senior` column of the report's "hours by role and grade" table (junior / middle / senior / total) — no new column, no ungraded path through the estimate, the CLI or the report.
2. **The estimate notice has to make the role visible enough that an estimator actually books the matching work under it.** In the one session that had `artist` available, the reflections were still booked as `copywriter`. Listing the role among the others was not enough.

How to implement it is muthur's call. For context only, the attempt that prompted this review: a `.claude/costs/rates.repo.json` beside `rates.json`, in its shape, that may only add (an entry `rates.json` already rates at another multiplier raises, so history is never re-rated silently), loaded by `estimate.py`, `report.py` and `check_estimates.py`, and read off each repository by `--all-my-repos` too, since a row there may name a role only its own repository rates. It also added an `ungraded` table — the part requirement 1 rules out.

---

## Timeline (status, references, and other events)

- **2026-10-12T22:32:33Z** @vzakharov referenced this issue in a commit: https://api.github.com/repos/vzakharov/vovazakharov.com/commits/9f414a55c89635ad41ac2f939c632f27f999abed.
