# PR #200: feat: lead a cost row with its total

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/200
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/cost-row-total-first-yeq47x
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-15T05:24:41Z
- **Updated:** 2026-10-15T05:33:46Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/costs/lib/rows.py`:125 — unresolved — last: @vzakharov (human) 2026-10-15T05:33:35Z — "это очень редко a person к слову, давай подправим раз уж зал…" → [↓](#t01)

---

## Body

## Summary

- A session row in `.claude/costs/sessions/<YYYY-MM>/<id>.json` is now written with `total` as its first key, so opening a row shows what the session cost before anything else.
- `estimate`, the one field a person sets, moves to second place instead of first.
- Existing rows keep their key order until something rewrites them (the session's own `Stop` hook, an `estimate.py` edit, or a report reshaping an old row). Every reader parses keys by name, so the order is cosmetic.

## QA Checklist

- [ ] `new-row` — finish a turn in a session on this branch and open its row under `.claude/costs/sessions/`: the first key is `total`, the second `estimate`.
- [ ] `estimate-edit` — `python3 .claude/costs/estimate.py set --session <id> ...` on an older row rewrites it with `total` first, and the report still reads it.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `new-row` | unit | ✅ | `test_estimate.py` — `row_text` writes `total`, then `estimate`, and parses back to the same row |
| `estimate-edit` | integration | ✅ | `test_estimate.py` — rows rewritten through `row_text`, which carries the order |

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-15T05:24:53Z — "Proposed squash body: ``` A session's cost ledger row opened…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-15T05:24:53Z

[https://github.com/vzakharov/muthur/pull/200#issuecomment-6185097401](https://github.com/vzakharov/muthur/pull/200#issuecomment-6185097401)

Proposed squash body:

```
A session's cost ledger row opened on its estimate, so the figure a
person opens a row to see, what the session cost, sat below it.

Rows are now written with `total` as their first key and `estimate`
second. Every reader parses rows by key name, so existing rows stay
valid in their old order and take the new one when next rewritten.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/lib/rows.py`:125 — unresolved — last: @vzakharov (human) 2026-10-15T05:33:35Z — "это очень редко a person к слову, давай подправим раз уж зал…" → [↓](#t01)

<a id="t01"></a>

### `.claude/costs/lib/rows.py`:125 — unresolved

```diff
@@ -121,10 +121,10 @@ def json_text(value: Any) -> str:
… 3 lines elided …
-    """`estimate` leads the row, so a pull request's diff of it opens on the one
-    field a person sets."""
+    """A row opens on what the session cost, `total`, then on `estimate`, the
+    one field a person sets."""
```

**@vzakharov (human)** — 2026-10-15T05:33:35Z

это очень редко a person к слову, давай подправим раз уж залезли

---

## Timeline (status, references, and other events)

- **2026-10-15T05:33:46Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/200#pullrequestreview-5528591834.
