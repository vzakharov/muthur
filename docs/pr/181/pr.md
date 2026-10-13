# PR #181: feat: count keepalive renewals, parking the session by default

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/181
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/keepalive-renewals-jgr7s4
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-10T13:11:08Z
- **Updated:** 2026-10-13T17:27:06Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/keepalive/CLAUDE.md`:24 — unresolved — last: @vzakharov (human) 2026-10-13T17:26:47Z — "давай сделаем префикс MUTHUR_ и заведём новую сессию с таско…" → [↓](#t01)

---

## Body

## Summary

- `CACHE_KEEPALIVE_WAKES` becomes `CACHE_KEEPALIVE_RENEWALS`: the number of wakes that only keep the prompt cache warm. The wake after the last renewal parks the session — `/relay` without a successor, no further watcher.
- Unset, the count is **0**, so an idle session's first wake (about 55 minutes in) parks it instead of renewing. A relay summary is the cheaper way back; an operator who prefers renewals sets the count.
- `.claude/keepalive/CLAUDE.md` states the cost that bounds the count. A renewal is two requests reading the whole cached conversation, so it costs 10% of a cold re-cache on the usual multipliers (read 0.1×, one-hour write 2× input), or 5% where the read rate is 1/40 of the write, as on the current Opus. More than 5 is not recommended: 5 unused renewals come to 25–50% of a cold re-cache, and 10–20 come to the whole of it. The re-cache ratio it cites is corrected from "about 40" to 20–40 by model.
- A negative count or lead is rejected like a malformed one, and the catalog row and `/relay` § "Without a successor" follow the new wording.

## QA Checklist

- [ ] `default-parks` — With no env set, let a session idle until the watcher wakes it: the wake runs `/relay` without a successor and starts no watcher.
- [ ] `renewals` — With `CACHE_KEEPALIVE_RENEWALS=2`, two wakes each reply with one short "кеш продлён, n/2" line and restart the watcher; the third parks the session.
- [ ] `reset` — An operator prompt between wakes resets the count to `renewal 1 of N`.
- [ ] `bad-value` — `CACHE_KEEPALIVE_RENEWALS=-1` or `five` arms nothing and says why on stderr.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `default-parks` | integration | ✅ | `test_by_default_the_first_wake_parks_the_session` |
| `renewals` | integration | ✅ | `test_a_renewal_asks_for_one_short_line_and_a_new_watcher`, `test_the_wake_after_the_last_renewal_parks_the_session` |
| `reset` | integration | ✅ | `test_it_starts_a_new_idle_spell` |
| `bad-value` | integration | ✅ | `test_a_malformed_setting_says_why` |

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-10T13:11:20Z — "Proposed squash title/body: ``` feat: count keepalive renewa…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-10T13:11:20Z

[https://github.com/vzakharov/muthur/pull/181#issuecomment-6097850980](https://github.com/vzakharov/muthur/pull/181#issuecomment-6097850980)

Proposed squash title/body:

```
feat: count keepalive renewals, parking the session by default (pr #181)
```

```
An idle session parked through a relay summary is often the cheaper
and more convenient way back than one kept warm wake after wake, and
operators differ on which they prefer — so the number of renewals is
a setting, and its default is none.

CACHE_KEEPALIVE_WAKES becomes CACHE_KEEPALIVE_RENEWALS: the wakes that
only keep the prompt cache warm. The wake after the last renewal parks
the session through /relay without a successor. Unset, the count is 0,
so the first wake parks. A negative count or lead is rejected like a
malformed one.

The keepalive's contract states the cost that bounds the count: a
renewal is two requests reading the whole cached conversation, 10% of
a cold re-cache on the usual multipliers and 5% where the read rate is
1/40 of a one-hour write. Five unused renewals cost 25-50% of the
re-cache they insure against, 10-20 the whole of it, so more than 5 is
not recommended. The cited re-cache ratio is 20-40 times a read, by
model.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/keepalive/CLAUDE.md`:24 — unresolved — last: @vzakharov (human) 2026-10-13T17:26:47Z — "давай сделаем префикс MUTHUR_ и заведём новую сессию с таско…" → [↓](#t01)

<a id="t01"></a>

### `.claude/keepalive/CLAUDE.md`:24 — unresolved

```diff
@@ -20,10 +21,16 @@ conversation at about 40 times what a cache read costs.
… 4 lines elided …
-  operator prompt resets. The last runs `/relay` without a successor
-  (`@.claude/skills/relay/SKILL.md` § "Without a successor"): a branch idle for
-  hours can wait, and the summary makes picking it up cheap. No watcher follows it.
+- **`CACHE_KEEPALIVE_RENEWALS` (default 0) renewals per idle spell**, which an
```

**@vzakharov (human)** — 2026-10-13T17:26:47Z

давай сделаем префикс MUTHUR_ и заведём новую сессию с таском сделать так для всех энвов которые у нас используются

---

## Timeline (status, references, and other events)

- **2026-10-13T17:27:06Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/181#pullrequestreview-5507440485.
