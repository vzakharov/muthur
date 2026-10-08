# PR #171: feat: warn on a large PR review up front, route it through subagents

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/171
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/large-review-warning-ov483m
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-08T19:32:51Z
- **Updated:** 2026-10-08T20:05:16Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:23 — unresolved — last: @vzakharov (human) 2026-10-08T20:04:06Z — "надо как-то по-умному сделать, чтобы субагенты вернули доста…" → [↓](#t01)
- **T02** `scripts/gh_export/awaiting.py`:52 — unresolved — last: @vzakharov (human) 2026-10-08T20:04:23Z — "хм.. что такое "ряд" здесь? 20 рядов не звучит как что-то ог…" → [↓](#t02)

---

## Body

## Summary

- A `/handle` on a PR with a large review used to read the whole export before editing anything (vzakharov/vovazakharov.com#115: 3,164 lines, 104 awaiting rows, the 200k warning line crossed before a single edit). The export knew its size before anyone read it; now it says so.
- The `## Awaiting an answer` verdict opens on a **Large review** warning (lines, ~tokens, awaiting count, and what to do instead) when more than 20 rows await, or one read of the file would take more than a fifth of the context budget's warning line (`$CONTEXT_BUDGET_WARN`, default 200k). A large export with nothing awaiting stays quiet. The warning sits above the section's `---`, so `prompt-handle-pr-export.sh` lifts it into the turn with the verdict, unchanged.
- `/handle` Step 2 gains the rule for a flagged export: read only the verdict, batch its rows by file or by kind, and give each batch to a parallel subagent that returns a digest per row and edits nothing. The main session keeps the edits, commits and replies.
- Left out: the issue's optional one-file-per-thread split. The rows already carry anchors into the one file, which is all a subagent needs to open only its slice.

## QA Checklist

- [ ] `small` — export a PR with a handful of awaiting rows: the verdict carries no warning.
- [ ] `rows` — on a PR with more than 20 awaiting rows, the verdict opens on `> **Large review: … , N awaiting.**`.
- [ ] `size` — `CONTEXT_BUDGET_WARN=1000 python3 scripts/export-github-item.py <n>` on a PR with at least one awaiting row: the warning appears; on a PR with none awaiting, it does not.
- [ ] `bad-env` — `CONTEXT_BUDGET_WARN=abc python3 scripts/export-github-item.py <n>` exits non-zero with `CONTEXT_BUDGET_WARN must be a whole count of tokens`.
- [ ] `hook` — `/handle <branch>` on a large-review PR: the hook's context shows the warning inside the verdict, before the turn.
- [ ] `subagents` — on that `/handle`, the session reads only the verdict and dispatches batches to subagents rather than paging `pr.md`.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `small` | unit | ✅ | `test_export_awaiting.py` — `test_a_small_review_carries_no_warning` |
| `rows` | unit | ✅ | `test_rows_past_the_threshold_warn` (20 quiet, 21 warns) |
| `size` | unit | ✅ | `test_a_large_file_warns_whatever_the_row_count`, `…_with_nothing_awaiting_carries_no_warning`, `test_the_size_threshold_follows_the_warning_line` |
| `bad-env` | unit | ✅ | `test_a_malformed_override_stops_the_export`, `test_the_warning_line_reads_the_budgets_override` |
| `hook` | unit | ✅ | `test_the_warning_rides_inside_what_the_hook_lifts` — the warning sits above the first `---` |
| `subagents` | manual-only | — | Agent behaviour under a skill rule; only observable in a live session |

Closes #170

https://claude.ai/code/session_016xxZEpQABszUQ2yHhVUbUc

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-08T19:33:04Z — "Proposed squash title/body: ``` feat: #170 warn on a large P…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-08T19:33:04Z

[https://github.com/vzakharov/muthur/pull/171#issuecomment-6067542273](https://github.com/vzakharov/muthur/pull/171#issuecomment-6067542273)

Proposed squash title/body:

```
feat: #170 warn on a large PR review up front (pr #171)
```

```
A /handle on a PR with a large review spent its whole context reading
the export before editing a file, and nothing warned it: the export
knew its own size before anyone read a line.

The export's "Awaiting an answer" verdict now opens on a Large review
warning, giving lines, ~tokens and the awaiting count, when more than
20 rows await or one read of the file would take more than a fifth of
the context budget's warning line ($CONTEXT_BUDGET_WARN, default 200k
tokens). An export with nothing awaiting stays quiet. The warning sits
inside what the /handle hook lifts into the turn's context, so the
agent meets it before reading anything.

/handle Step 2 says what a flagged export gets: the session reads the
verdict only, batches its rows, and hands each batch to a parallel
subagent that returns a digest per row and edits nothing, keeping the
edits, commits and replies for itself.

Closes #170

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:23 — unresolved — last: @vzakharov (human) 2026-10-08T20:04:06Z — "надо как-то по-умному сделать, чтобы субагенты вернули доста…" → [↓](#t01)
- **T02** `scripts/gh_export/awaiting.py`:52 — unresolved — last: @vzakharov (human) 2026-10-08T20:04:23Z — "хм.. что такое "ряд" здесь? 20 рядов не звучит как что-то ог…" → [↓](#t02)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:23 — unresolved

```diff
@@ -0,0 +1,32 @@
… 16 lines elided …
+inside what the /handle hook lifts into the turn's context, so the
+agent meets it before reading anything.
+
+/handle Step 2 says what a flagged export gets: the session reads the
+verdict only, batches its rows, and hands each batch to a parallel
+subagent that returns a digest per row and edits nothing, keeping the
+edits, commits and replies for itself.
```

**@vzakharov (human)** — 2026-10-08T20:04:06Z

надо как-то по-умному сделать, чтобы субагенты вернули достаточно информации, чтобы ведущий агент по ним смог решить как и что распределять (уже между другими подагентами), так как, разумеется, группировка по числам (для первых подагентов) не будет группировкой по темам (для тех кто собственно будет исполнять)

---

<a id="t02"></a>

### `scripts/gh_export/awaiting.py`:52 — unresolved

```diff
@@ -42,6 +46,22 @@
… 3 lines elided …
+# Either alone makes a review large: more rows than one session works through
+# beside their edits, or one read of the export taking more than this share of
+# the context budget's warning line.
+LARGE_ROW_COUNT = 20
```

**@vzakharov (human)** — 2026-10-08T20:04:23Z

хм.. что такое "ряд" здесь? 20 рядов не звучит как что-то огромное

---

## Timeline (status, references, and other events)

- **2026-10-08T20:05:16Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/171#pullrequestreview-5462213351.
