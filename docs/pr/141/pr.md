# PR #141: feat: thread replies prompted in-session quote the session first

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/141
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/session-reply-context-euw38p
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-05T09:46:42Z
- **Updated:** 2026-10-05T09:49:21Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- When the operator raises in the session a point a PR thread already carries, the agent answers on that thread too — but the reply arrived without the question. Thread readers never see the session, so the comment answered something nobody on the thread had asked.
- CLAUDE.md § "GitHub comments" (via its staged copy, `.claude/staged/CLAUDE.md.staged`) now has such a reply open with the operator's in-session words — quoted when short, paraphrased in a line otherwise (`In the session: «…»`) — then the answer.
- The rule sits in CLAUDE.md rather than `/handle` because the operator talks in chat outside any skill run too; `/handle` Step 3 already points at this section for its reply rule.

## QA Checklist

- [ ] `quote-first` — In a session on a PR with an open review thread, raise that thread's point in chat; the agent's follow-up reply on the thread opens with `In the session: «…»` carrying your words, then its answer.
- [ ] `long-paraphrase` — Raise the point with a long, rambling message; the reply paraphrases it in one line rather than pasting it whole.
- [ ] `thread-only` — Answer a comment that came from the thread itself (not the session); the reply carries no `In the session` prefix.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `quote-first` | manual-only | — | Agent behaviour on a live PR; judging what counts as "a point the thread carries" needs a person |
| `long-paraphrase` | manual-only | — | Whether the paraphrase is faithful is a judgement call |
| `thread-only` | manual-only | — | Same live-PR setup as `quote-first` |

https://claude.ai/code/session_01FzrkSyKnGXXJbL8w85Efi6

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-05T09:46:50Z — "Proposed squash title/body: ``` feat: thread replies prompte…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-05T09:46:50Z

[https://github.com/vzakharov/muthur/pull/141#issuecomment-5992032191](https://github.com/vzakharov/muthur/pull/141#issuecomment-5992032191)

Proposed squash title/body:

```
feat: thread replies prompted in-session quote the session first (pr #141)
```

```
When the operator raises in the session a point a PR thread already
carries, the agent answers on that thread as well, but the reply
arrived without its question: the thread's readers never see the
session, so the comment answered something nobody there had asked.

CLAUDE.md § "GitHub comments" now has such a reply open with the
operator's in-session words, quoted when short and paraphrased in a
line otherwise, before the answer. The rule lives in CLAUDE.md rather
than in /handle because the operator talks in chat outside any skill
run too.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/sessions/2026-10/56d6c452-8041-5364-82ea-07f018ad8160.json`:88 — unresolved — last: @vzakharov (human) 2026-10-05T09:48:59Z — "давай введём отдельную позицию prompt engineer (можно просто…" → [↓](#t01)

<a id="t01"></a>

### `.claude/costs/sessions/2026-10/56d6c452-8041-5364-82ea-07f018ad8160.json`:88 — unresolved

```diff
@@ -0,0 +1,93 @@
… 84 lines elided …
+      {
+        "hours": 1.0,
+        "grade": "senior",
+        "role": "editor"
```

**@vzakharov (human)** — 2026-10-05T09:48:59Z

давай введём отдельную позицию prompt engineer (можно просто prompter) для правок, связанных с "общением" с ЛЛМкой. Это не совсем редактура (человек, который писал блоги, этого сделать не сможет), но и не совсем разработка.

---

## Timeline (status, references, and other events)

- **2026-10-05T09:49:21Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/141#pullrequestreview-5412695336.
