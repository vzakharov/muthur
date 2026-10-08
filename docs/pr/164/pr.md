# PR #164: fix: keep the sync offer's lock re-check out of what the operator hears

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/164
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/silent-sync-lock-recheck-fahlt5
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-07T21:22:59Z
- **Updated:** 2026-10-08T05:05:34Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/skills/update-muthur/SKILL.md`:367 — unresolved — last: @vzakharov (human) 2026-10-08T05:04:51Z — "что это значит?" → [↓](#t01)

---

## Body

## Summary

- An agent holding an unanswered muthur-sync offer told the operator that the next session would "check whether another session took it before asking again". That is the agent's own plumbing: the operator only has to say yes or no, and the sentence hands them a mechanism with nothing to act on.
- The nudge's offer rules (`scripts/muthur-sync.sh`, which every session sees at start) and `update-muthur` § "Offered at session start" now say the lock re-check is never reported. A reply or handoff report carrying an unanswered offer calls it still open and stops there.
- The relay summary, written for the next session rather than the operator, still carries the offer and the re-check for that session to run.

## QA Checklist

- [ ] `nudge-text` — on a repo whose source is ahead of its watermark, `scripts/muthur-sync.sh nudge` prints the offer rules with the new "The check is yours alone" line, the lock name filled in.
- [ ] `handoff` — a session that ends with the offer unanswered (relay or plain end of turn) tells the operator at most that the sync offer is still open, without mentioning any re-check.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `nudge-text` | integration | ❌ | `test_muthur_sync.py` could assert the line in the nudge output |
| `handoff` | manual-only | — | Agent behaviour in prose; only observable in a real session |

https://claude.ai/code/session_01BESg9ry1HNZ62QpjyBchGH

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-07T21:23:13Z — "Proposed squash title/body: ``` fix: keep the sync offer's l…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-07T21:23:13Z

[https://github.com/vzakharov/muthur/pull/164#issuecomment-6047126640](https://github.com/vzakharov/muthur/pull/164#issuecomment-6047126640)

Proposed squash title/body:

```
fix: keep the sync offer's lock re-check out of operator replies (pr #164)
```

```
An agent holding an unanswered muthur-sync offer told the operator that
the next session would check whether another one had taken the sync
before asking again. The re-check is the agent's own plumbing; the
operator only has to say yes or no.

The nudge's offer rules and update-muthur's "Offered at session start"
now keep the re-check silent: a reply or handoff report carrying an
unanswered offer calls it still open and stops there.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/skills/update-muthur/SKILL.md`:367 — unresolved — last: @vzakharov (human) 2026-10-08T05:04:51Z — "что это значит?" → [↓](#t01)

<a id="t01"></a>

### `.claude/skills/update-muthur/SKILL.md`:367 — unresolved

```diff
@@ -360,6 +360,12 @@ claims nothing. Any output means the sync was claimed, or landed and left its
… 4 lines elided …
+is the offer, or who holds the lock; a reply or handoff report that carries an
+unanswered offer calls it still open and stops there. "A new session
+will check whether another one took it before asking again" puts the mechanism
+in a reader's head who only has to say yes or no.
```

**@vzakharov (human)** — 2026-10-08T05:04:51Z

что это значит?

---

## Timeline (status, references, and other events)

- **2026-10-08T05:05:34Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/164#pullrequestreview-5451704905.
