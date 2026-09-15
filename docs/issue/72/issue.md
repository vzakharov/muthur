# Issue #72: docs: drop the working-artifact rows from the catalog's Never table

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/72
- **Author:** @vzakharov (agent)
- **Created:** 2026-09-12T14:39:09Z
- **Updated:** 2026-09-12T15:31:09Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

`.claude/skills/update-muthur/catalog.md`'s **Never** table ends with two rows — `docs/plans/*` and `docs/remove-before-merging/*` — that are not items an adopter can take or leave. They are artifacts this repo's own skills produce and `/finalize` deletes, absent from `main` by construction, so they have no standing in an inventory whose whole purpose is "here is what you decide about".

What that costs downstream is a decision recorded about someone else's working files. An adopting repo's watermark keeps a `declined` map, path → why-not, and the catalog's rows are what put these two paths in it. The rationale then cannot be written correctly, because `"docs/plans/*": declined` does not read as "we are not copying files from your branches" — it reads as "we decline the convention of keeping plans", which is the opposite of true, the `/plan` lifecycle being adopted. It took two review rounds on one downstream PR to find that the entry was unwritable rather than merely badly worded, and the fix was to delete it.

The section already knows: *"The last two rows should not exist in a clone at all."* Then it lists them, because a clone taken mid-flight from a feature branch has those directories. That is a fact about clones, not an entry in a catalogue of infrastructure — and the paragraph states it perfectly well on its own.

Proposed: drop both rows, keep the paragraph's closing sentence as the warning it already is (seeing either directory in your clone means you are looking at working state, not the product), and leave **Never** to items that are actually muthur's and actually declinable.

---

## Comments

### Comment by @vzakharov (human) on 2026-09-12T15:31:09Z

[https://github.com/vzakharov/muthur/issues/72#issuecomment-5646841923](https://github.com/vzakharov/muthur/issues/72#issuecomment-5646841923)

Widen it to this comment I made in another session: https://github.com/vzakharov/muthur/pull/73#discussion_r3996636938 (there I said "no sweep", but here it's time for a sweep).

---

## Timeline (status, references, and other events)

- **2026-09-12T14:43:43Z** @vzakharov referenced this issue in a commit: https://api.github.com/repos/vzakharov/muthur/commits/e918d9b51ede0459c5053822b8e246420150bebc.
