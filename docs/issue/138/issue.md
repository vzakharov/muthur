# Issue #138: Estimate comment should justify the team, not summarise the work

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/138
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-04T20:11:34Z
- **Updated:** 2026-10-04T20:11:34Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

The human-hour estimate's comment (`.claude/costs/estimate.py set "<comment>" --part …`, prompted by `.claude/costs/hooks/estimate-notice.sh`) is asked to say "why the task is this size". In practice agents fill it with a summary of what the session did, which the cost row and the commits already carry.

What a reader of the row needs from the comment is the case for the team: why these roles, at these grades, for these hours — e.g. "a middle developer, since the code change is a routine component slot; a senior copywriter, since the prose needs judgement of voice". A summary of the work does not let anyone check the estimate; a justification of each part does.

Proposed change: reword the notice hook, `estimate.py`'s help and the `.claude/costs/CLAUDE.md` section so the comment justifies each `--part` (role, grade and hours) rather than describing the work, and say so wherever a revision is asked for too.

Raised in review on vzakharov/vovazakharov.com#95 by @vzakharov: https://github.com/vzakharov/vovazakharov.com/pull/95

---

