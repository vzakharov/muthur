# PR #262: fix: [attn adopters] #261 LICENSE is never vendored, its notice is

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/262
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← docs/adopter-license
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-11-05T11:08:00Z
- **Updated:** 2026-11-05T13:25:19Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/skills/update-muthur/catalog/never.md`:1 — unresolved — last: @vzakharov (human) 2026-11-05T13:24:59Z — "так, а не делает ли это приёмщиков MIT by definition?" → [↓](#t01)

---

## Body

## Summary

- `LICENSE` (#256) sat in neither the catalog nor `catalog/never.md`, so every `/update-muthur` sync met it as an undecided path and asked its operator again (metkain/metka declined it as the template's license). It is now a `never` entry: muthur's own license, never an adopter's root `LICENSE`.
- MIT keeps its copyright and permission notice with every substantial copy, which a verbatim skill or script is — so the entry has adopters copy the text unchanged to `.claude/LICENSE.muthur`, one notice for every file taken, and carry later changes to `LICENSE` into that copy.
- `ADOPTING.md` Step 4 and `/detemplate` Step 5.2 (which moves the fork's `LICENSE` there rather than deleting it) point at the same answer; `/update-muthur` Step 4a stops offering any path the catalog marks `never`.
- The commit is `[attn adopters]`: existing adopters add `.claude/LICENSE.muthur` once, on their next sync.

## QA Checklist

- [ ] `never-entry` — `.claude/skills/update-muthur/catalog/never.md` lists `LICENSE` with disposition `never` and names `.claude/LICENSE.muthur` as where its text goes.
- [ ] `adopting` — `ADOPTING.md` Step 4 tells a subset adopter to leave root `LICENSE` out and copy its text to `.claude/LICENSE.muthur`.
- [ ] `detemplate` — `/detemplate` Step 5.2 moves `LICENSE` to `.claude/LICENSE.muthur` instead of deleting it.
- [ ] `sync` — on a sync whose range touches `LICENSE`, `/update-muthur` Step 4a does not ask the operator, and carries the change into `.claude/LICENSE.muthur`.
- [ ] `vet` — `./scripts/vet.sh` passes.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `never-entry` | no | no | prose read |
| `adopting` | no | no | prose read |
| `detemplate` | no | no | exercised on the next template fork |
| `sync` | no | no | exercised on the next adopter sync |
| `vet` | yes | yes | ran green locally |

Fixes #261

https://claude.ai/code/session_01DaohkEGD6ehkW7EJPLcbVB

---

## Comments

- **C01** @vzakharov (agent) — 2026-11-05T11:08:13Z — "Proposed squash body: ``` LICENSE (#256) sat in neither the…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-11-05T11:08:13Z

[https://github.com/vzakharov/muthur/pull/262#issuecomment-6656448544](https://github.com/vzakharov/muthur/pull/262#issuecomment-6656448544)

Proposed squash body:

```
LICENSE (#256) sat in neither the catalog nor never.md, so every
/update-muthur sync met it as an undecided path and asked its operator
afresh; metkain/metka declined it as the template's own license.

It is now a never entry: muthur's MIT license never becomes an
adopter's root LICENSE. But MIT keeps its notice with every substantial
copy, which a verbatim skill or script is, so the entry has adopters
copy the text unchanged to .claude/LICENSE.muthur, one notice for every
file taken, and carry later changes to LICENSE into that copy.
ADOPTING.md Step 4 and /detemplate Step 5.2 (which moves the fork's
LICENSE there instead of deleting it) send readers to the same answer,
and /update-muthur Step 4a no longer offers a path the catalog marks
never.

Adopters: copy this repo's LICENSE, unchanged, to
.claude/LICENSE.muthur and commit it with the sync. Your own root
LICENSE, if any, stays as it is.

Fixes #261

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/update-muthur/catalog/never.md`:1 — unresolved — last: @vzakharov (human) 2026-11-05T13:24:59Z — "так, а не делает ли это приёмщиков MIT by definition?" → [↓](#t01)

<a id="t01"></a>

### `.claude/skills/update-muthur/catalog/never.md`:1 — unresolved

**@vzakharov (human)** — 2026-11-05T13:24:59Z

так, а не делает ли это приёмщиков MIT by definition?

---

## Timeline (status, references, and other events)

- **2026-11-05T13:25:19Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/262#pullrequestreview-5785620012.
