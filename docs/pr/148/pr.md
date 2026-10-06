# PR #148: fix: open the PR export on a verdict of what awaits an answer

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/148
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/pr-export-awaiting-answer
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-06T08:50:59Z
- **Updated:** 2026-10-06T09:12:35Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: none

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (the export committed at a2b210b). Resolved threads never count; an `(agent)` tail is a reply already given._

---

## Body

## Summary

- On #147, a `/handle and finalize` run read its PR export through `sed -n 1,60p`. That window held only the PR body and the agent's own sticky comments, so the run finalized over a review with two unanswered inline threads. The `## Review threads` index sat at line ~101, below every comment body.
- The export now runs `/handle` Step 2's two tests itself. Right under its header, above the PR body, it opens on `## Awaiting an answer: <count>`, with one linked row for each unresolved thread whose newest post is a human's, and for each human review or comment posted after the head commit. When the count is zero the section prints `none`, so the verdict never disappears silently. If the timeline has no head-commit date, every human post counts. A thread's newest post is the one that went out last: a comment counts from its review's submission time, since its own `created_at` is when it was drafted into a pending review.
- `.claude/hooks/prompt-handle-pr-export.sh` puts that section into the turn's context word for word. `/handle` Step 2 now treats its count as the review lane's verdict, and the `and merge` stand-down in `/finalize` reads it off a fresh export. Review bodies get `R<nn>` anchors so the section can link to them.
- Two other fixes were considered and not taken. Exporting less, by dropping the agent's sticky comment bodies, still leaves the order to chance on a PR with long human comments. Diffing against the last committed export shows what changed, not what is still unanswered: a thread left open across two exports produces no diff at all.

## QA Checklist

- [ ] `live-export` — `python3 scripts/export-github-item.py 147`: line ~16 reads `## Awaiting an answer: none` (both threads are resolved now, with agent tails) and names head `83a2868`.
- [ ] `human-tail` — on a scratch PR, leave an inline comment and do not reply: a re-export lists it as `T01 … (human)` under `## Awaiting an answer: 1`, and its link jumps to the thread body.
- [ ] `hook` — on that branch, send `/handle`: the injected context carries the verdict section verbatim.
- [ ] `unit` — `./scripts/vet.sh` passes, including `scripts/test_export_awaiting.py`.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `live-export` | integration | ❌ | Needs GitHub API access; run by hand in this session |
| `human-tail` | manual-only | — | Needs a real review thread on a PR |
| `hook` | integration | ❌ | Needs a session prompt to fire the hook |
| `unit` | unit | ✅ | `test_export_awaiting.py` covers tail, recency, numbering and the missing-date fallback |

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-06T08:51:14Z — "Proposed squash title/body: ``` fix: open the PR export on a…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-06T08:51:14Z

[https://github.com/vzakharov/muthur/pull/148#issuecomment-6012774038](https://github.com/vzakharov/muthur/pull/148#issuecomment-6012774038)

Proposed squash title/body:

```
fix: open the PR export on a verdict of what awaits an answer (pr #148)
```

```
A /handle run could finalize over unanswered review threads: the PR
export put its thread index below the PR body and every comment body,
so a reader that took only the first screen saw no feedback to answer.

The export now runs /handle Step 2's tail and recency tests itself and
opens, under the header, on `## Awaiting an answer: <count>` - one
linked row per unresolved thread whose newest post is a human's, and
per human review or comment posted after the head commit. A zero
prints as `none`, and with no head-commit date every human post
counts. A thread's newest post is the one that went out last: a
comment counts from its review's submission, not its created_at,
which predates it for anything drafted in a pending review.

The /handle hook carries that section into the turn's context
verbatim; /handle treats its count as the review lane's verdict, and
/finalize's `and merge` stand-down reads it off a fresh export.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/hooks/prompt-handle-pr-export.sh`:129 — unresolved — last: @vzakharov (agent) 2026-10-06T09:05:41Z — "Работает, с одной оговоркой. Экспорт с этой ветки открылся н…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (agent) 2026-10-06T09:05:43Z — "Yes — the change repairs a defect (a `/handle` run finalized…" → [↓](#t02)

<a id="t01"></a>

### `.claude/hooks/prompt-handle-pr-export.sh`:129 — unresolved

```diff
@@ -120,9 +120,17 @@ if [ -f "$export_path" ]; then
     context+=$'arrived on the PR since. That is the answer to "has anything changed?" — do not '
     context+=$'reach it any other way.'
   fi
+  # The verdict rides in verbatim: it is the review lane's whole input, and one
+  # read off the file depends on the reader opening it at the top.
+  awaiting="$(awk '/^## Awaiting an answer/ { on = 1 } on && /^---$/ { exit } on' "$export_path")"
+  if [ -n "$awaiting" ]; then
+    context+=$'\n\nThe export\'s verdict on unanswered feedback, as it opens the file:\n\n'
+    context+="$awaiting"
+  fi
```

**@vzakharov (human)** — 2026-10-06T09:02:10Z

ну давай задогфудим. работает? :)

**@vzakharov (agent)** — 2026-10-06T09:05:41Z

Работает, с одной оговоркой. Экспорт с этой ветки открылся на `## Awaiting an answer: 2`, и в нём оба треда, этот и «fix?» (закоммичено в d2f32f1). Хук, запущенный вручную на этой ветке с промптом `/handle`, кладёт эту секцию в контекст дословно.

Оговорка: в этой сессии хук сработал до attach, на авто-ветке от `main`, то есть со старым экспортёром — и настоящий контекст хода вердикта не содержал. Это бутстрап, а не баг: хук берёт скрипт с той ветки, где стоит HEAD, так что после мержа свежая сессия получит вердикт с первого промпта.

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,28 @@
+Proposed squash title/body:
+
+```
+feat: open the PR export on a verdict of what awaits an answer (pr #148)
```

**@vzakharov (human)** — 2026-10-06T09:02:43Z

fix?

**@vzakharov (agent)** — 2026-10-06T09:05:43Z

Yes — the change repairs a defect (a `/handle` run finalized over unanswered threads), so it's `fix:`. Squash proposal in aa16730; the comment above and the PR title now match.

---

## Timeline (status, references, and other events)

- **2026-10-06T09:03:12Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/148#pullrequestreview-5426103397.
- **2026-10-06T09:05:27Z** @vzakharov renamed from «feat: open the PR export on a verdict of what awaits an answer» to «fix: open the PR export on a verdict of what awaits an answer».
