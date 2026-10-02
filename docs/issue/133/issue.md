# Issue #133: tend-prose: § "Rule or README?" cites the rule homes as 3 and 4; the table numbers them 4 and 5

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/133
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-02T14:43:51Z
- **Updated:** 2026-10-02T14:55:35Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

`.claude/skills/tend-prose/SKILL.md` § "Rule or README?" (line 148) cites the two rule homes as **homes 3 and 4**, but the homes table above it (lines 128–136) numbers them **4** (the directory's own `CLAUDE.md`) and **5** (`.claude/rules/<area>.md`). Home 3 is "the skill or hook whose run it governs", which is not a rule home, so the cross-reference points one row too high — most likely left over from before a row was inserted into the table.

Fix: `homes 3 and 4 alike` → `homes 4 and 5 alike`.

vzakharov/vovazakharov.com already carries this fix as a local divergence and records it in its `.claude/skills/update-muthur/watermark.json` (vzakharov/vovazakharov.com#94). Once this lands, the divergence there can go on the next sync.

---

## Comments

- **C01** @vzakharov (human) — 2026-10-02T14:55:35Z — "просвипать что ещё могли упустить" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (human) on 2026-10-02T14:55:35Z

[https://github.com/vzakharov/muthur/issues/133#issuecomment-5955097110](https://github.com/vzakharov/muthur/issues/133#issuecomment-5955097110)

просвипать что ещё могли упустить

---

## Timeline (status, references, and other events)

- **2026-10-02T14:44:07Z** @vzakharov referenced this issue in a commit: https://api.github.com/repos/vzakharov/vovazakharov.com/commits/37b6cc2cdd2d4008d0c8f89f24570f26b27365b6.
- **2026-10-02T14:45:18Z** @vzakharov referenced this issue in a commit: https://api.github.com/repos/vzakharov/vovazakharov.com/commits/56ee6c229d1539555187128ed2cabe113e8b3f90.
- **2026-10-02T14:53:03Z** @vzakharov cross-referenced this issue from [#94 chore: cap CLAUDE.md, cost-aware relays and a cold-cache guard](https://github.com/vzakharov/vovazakharov.com/pull/94).
