# PR #222: feat: agents mark the end of their orientation themselves

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/222
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/orientation-mark-738nfp
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-25T11:35:56Z
- **Updated:** 2026-10-25T12:06:29Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 4

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/costs/sessions/2026-10/51146bb6-ee7b-5a47-bf48-c9df6ebb9594.json`:76 — unresolved — last: @vzakharov (human) 2026-10-25T12:03:14Z — "давай это тоже повыше перенесём, прямо под estimate" → [↓](#t01)
- **T02** `.claude/costs/hooks/orientation-notice.sh`:32 — unresolved — last: @vzakharov (human) 2026-10-25T12:04:14Z — "хочется покороче, но при этом стоит сказать что если ты сейч…" → [↓](#t02)
- **T03** `.claude/skills/update-muthur/catalog/g7-cost-ledger.md`:27 — unresolved — last: @vzakharov (human) 2026-10-25T12:06:01Z — "почему из четырёх сразу шесть стало? какую-то до этого не по…" → [↓](#t03)
- **T04** `.claude/settings.json`:87 — unresolved — last: @vzakharov (human) 2026-10-25T12:06:25Z — "я вот думаю не стоит ли их совместить -- по сути и то и то п…" → [↓](#t04)

---

## Body

## Summary

- **Orientation ended too late in the ledger.** It was measured up to the first write into the repo or the first reply to the operator, so a session that had its bearings and moved on to the work itself — tracing callers before changing anything — had that work booked as orientation.
- **The agent now marks the end itself** by running `python3 .claude/costs/oriented.py` bare. The Bash call in the transcript is the mark, so nothing else stores it; only a `python3` in command position counts, so a `grep`/`cat` of the script does not, and a subagent's mark is its own, not the session's. Whichever of the mark and the first action comes first ends the phase, so a forgotten mark falls back to the old measure. `endedBy` reads `oriented`, which the report's "orientation by what ended it" already breaks out.
- **`hooks/orientation-notice.sh` asks for the mark**, beside the estimate notice: on each prompt until the stretch since the latest compaction has one (silent after), and on the post-compaction `SessionStart`, where re-orientation starts without a prompt. The wording separates knowing what is what from having the whole ask settled, so the mark can come before an estimate can.

## QA Checklist

- [ ] `notice` — In a fresh session on this branch, the opening prompt's context carries the "Mark the end of your orientation…" line.
- [ ] `quiet` — After the agent runs `python3 .claude/costs/oriented.py`, the next prompt carries no orientation notice.
- [ ] `compact` — After a `/compact`, the notice is back, both at the compaction and on the next prompt until the agent marks again.
- [ ] `row` — The session's row on `cost-ledger` reads `"endedBy": "oriented"` with `endedAt` at the mark, and `report.py` lists `oriented` under "orientation by what ended it".
- [ ] `not-a-mark` — A `grep`/`cat` of `oriented.py`, or `oriented.py check <file>`, does not end orientation.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `notice` | integration | ✅ | `test_orientation_notice.py` — unmarked transcript gets the notice |
| `quiet` | integration | ✅ | `test_orientation_notice.py` — marked stretch adds nothing |
| `compact` | integration | ✅ | `test_orientation_notice.py` — boundary resets; `source: compact` asks without reading |
| `row` | unit | ✅ | `test_pricing.py` — mark ends orientation and a re-orientation; report breakdown keys on `endedBy` unchanged |
| `not-a-mark` | unit | ✅ | `test_pricing.py` — mentions, arguments and a subagent's mark are not the mark |

https://claude.ai/code/session_01XbFgG9uYDW5wcXMo6XaNXf

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-25T11:36:16Z — "Proposed squash body: ``` The ledger ended a session's orien…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-25T11:36:16Z

[https://github.com/vzakharov/muthur/pull/222#issuecomment-6397132012](https://github.com/vzakharov/muthur/pull/222#issuecomment-6397132012)

Proposed squash body:

```
The ledger ended a session's orientation at its first write into the
repository or first reply to the operator, so a session that already
had its bearings and had moved on to the work itself, such as tracing
callers before changing anything, had that work booked as orientation.

The agent now marks the end itself by running
`python3 .claude/costs/oriented.py` bare. The Bash call in the
transcript is the mark, so nothing else stores it. Only a `python3` in
command position counts, and a subagent's mark is its own. Whichever of
the mark and the first action comes first ends the phase, so a
forgotten mark falls back to the old measure. `endedBy: oriented` shows
in the report's breakdown by what ended it.

A new notice hook beside the estimate notice asks for the mark on every
prompt until the stretch since the latest compaction has one, and right
after a compaction, where re-orientation starts without a prompt. It
tells knowing what is what apart from having the whole ask settled, so
the mark can come before an estimate does.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/sessions/2026-10/51146bb6-ee7b-5a47-bf48-c9df6ebb9594.json`:76 — unresolved — last: @vzakharov (human) 2026-10-25T12:03:14Z — "давай это тоже повыше перенесём, прямо под estimate" → [↓](#t01)
- **T02** `.claude/costs/hooks/orientation-notice.sh`:32 — unresolved — last: @vzakharov (human) 2026-10-25T12:04:14Z — "хочется покороче, но при этом стоит сказать что если ты сейч…" → [↓](#t02)
- **T03** `.claude/skills/update-muthur/catalog/g7-cost-ledger.md`:27 — unresolved — last: @vzakharov (human) 2026-10-25T12:06:01Z — "почему из четырёх сразу шесть стало? какую-то до этого не по…" → [↓](#t03)
- **T04** `.claude/settings.json`:87 — unresolved — last: @vzakharov (human) 2026-10-25T12:06:25Z — "я вот думаю не стоит ли их совместить -- по сути и то и то п…" → [↓](#t04)

<a id="t01"></a>

### `.claude/costs/sessions/2026-10/51146bb6-ee7b-5a47-bf48-c9df6ebb9594.json`:76 — unresolved

```diff
@@ -0,0 +1,94 @@
… 72 lines elided …
+    }
+  },
+  "warnings": [],
+  "orientation": {
```

**@vzakharov (human)** — 2026-10-25T12:03:14Z

давай это тоже повыше перенесём, прямо под estimate

---

<a id="t02"></a>

### `.claude/costs/hooks/orientation-notice.sh`:32 — unresolved

```diff
@@ -0,0 +1,32 @@
… 28 lines elided …
+
+# One line: the agent reads it unwrapped, and a hard break inside the command
+# would split it.
+emit_context "Mark the end of your orientation by running \`python3 $script\`, bare, the moment you know what the repository is and what the request is about — before the first step that carries the request out, even one that only reads, such as tracing the callers of the code you are about to change. Details of the ask still open are no reason to wait: orientation is knowing what is what, not having the whole answer, so the mark often comes before an estimate can. The ledger times the session's orientation by it, and without one a write to the repository or a reply to the operator ends it instead, later than it ended. Once per session, and once more after each compaction.$unread"
```

**@vzakharov (human)** — 2026-10-25T12:04:14Z

хочется покороче, но при этом стоит сказать что если ты сейчас собираешься Edit или отвечать юзеру, то можно не запускать.

---

<a id="t03"></a>

### `.claude/skills/update-muthur/catalog/g7-cost-ledger.md`:27 — unresolved

```diff
@@ -16,14 +16,15 @@ session — so the entry is `opt-in: ask`.
… 9 lines elided …
   receiver listening on `127.0.0.1:4318` for the whole session, whose exporter
   variables go in the environment's settings by hand, since Claude Code ignores
   them in `.claude/settings.json` — `hooks/start-telemetry-receiver.sh` names
   them until they are set. Arrives with no rows — the first session's row roots
-  the repo's `cost-ledger` — four `.claude/settings.json` hook entries to merge,
+  the repo's `cost-ledger` — six `.claude/settings.json` hook entries to merge,
```

**@vzakharov (human)** — 2026-10-25T12:06:01Z

почему из четырёх сразу шесть стало? какую-то до этого не посчитали?

---

<a id="t04"></a>

### `.claude/settings.json`:87 — unresolved

```diff
@@ -73,6 +82,10 @@
             "type": "command",
             "command": "$CLAUDE_PROJECT_DIR/.claude/costs/hooks/estimate-notice.sh"
           },
+          {
+            "type": "command",
+            "command": "$CLAUDE_PROJECT_DIR/.claude/costs/hooks/orientation-notice.sh"
```

**@vzakharov (human)** — 2026-10-25T12:06:25Z

я вот думаю не стоит ли их совместить -- по сути и то и то про косты-оценки, а плодить лишние хуки не хочется

---

## Timeline (status, references, and other events)

- **2026-10-25T12:06:28Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/222#pullrequestreview-5643125358.
