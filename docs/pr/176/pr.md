# PR #176: fix: extract images the operator sends mid-turn

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/176
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/mid-turn-session-images-l2b8m2
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-09T14:31:36Z
- **Updated:** 2026-10-09T17:36:38Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/remove-before-merging/squash-message.md`:9 — unresolved — last: @vzakharov (human) 2026-10-09T17:36:10Z — "дело не в том что оно умирало с машиной, а в том, что агент…" → [↓](#t01)

---

## Body

## Summary

- An image sent **while the agent is mid-turn** never reached `tmp/session-images/`. Claude Code doesn't record such a message as a `type: "user"` record: it folds it into the running turn as a `type: "attachment"` record whose `attachment.type` is `queued_command`, with the images under `attachment.prompt`. The extractor only read the first shape.
- The shape comes from the Claude Code client bundle (`getQueuedCommandAttachments` builds `prompt` as the text block followed by the image blocks). No transcript on this machine had a mid-turn image to sample.
- `scripts/extract-session-images.py` now accepts both shapes and keeps the human-origin filter on each. The existing SHA dedupe handles an image that shows up in both.
- New `scripts/test_extract_session_images.py` runs the script over synthetic transcripts of both shapes. The mid-turn case fails without the fix.

## QA Checklist

- [ ] `mid-turn` — in a session on this branch, send an image while the agent is working. Then send any ordinary prompt and confirm the image appears under `tmp/session-images/`, with a row in its `index.md`.
- [ ] `prompt` — attach an image to an ordinary prompt and confirm it still lands, exactly once, on the next prompt.
- [ ] `resend` — send the same image mid-turn and again with a prompt, and confirm only one file is written.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `mid-turn` | integration | ✅ | `test_mid_turn_image`, against a synthetic record. Only a live session can confirm that the real client writes this shape |
| `prompt` | integration | ✅ | `test_prompt_image` |
| `resend` | integration | ✅ | `test_same_image_twice_is_written_once` |

Fixes #175

https://claude.ai/code/session_01BwFufA1ZM3KaWe1yYwhn2o

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-09T14:31:48Z — "Proposed squash title/body: ``` fix: #175 extract images the…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-09T14:31:48Z

[https://github.com/vzakharov/muthur/pull/176#issuecomment-6082995580](https://github.com/vzakharov/muthur/pull/176#issuecomment-6082995580)

Proposed squash title/body:

```
fix: #175 extract images the operator sends mid-turn (pr #176)
```

```
An image the operator sent while a turn was running reached the agent's
context but never tmp/session-images/, so it died with the machine. The
client writes such a message not as a `user` record but as an
`attachment` record of type `queued_command`, with the image blocks
under `attachment.prompt`, and the extractor read only the first shape.

scripts/extract-session-images.py now reads an operator's message from
either record, with the human-origin filter on both; the SHA dedupe
already covers an image that appears in both. A new test runs the
script over synthetic transcripts of each shape.

Fixes #175

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:9 — unresolved — last: @vzakharov (human) 2026-10-09T17:36:10Z — "дело не в том что оно умирало с машиной, а в том, что агент…" → [↓](#t01)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:9 — unresolved

```diff
@@ -0,0 +1,26 @@
… 5 lines elided …
+
+```
+An image the operator sent while a turn was running reached the agent's
+context but never tmp/session-images/, so it died with the machine. The
```

**@vzakharov (human)** — 2026-10-09T17:36:10Z

дело не в том что оно умирало с машиной, а в том, что агент никак с ним потом не мог работать, кроме как просто "смотреть"

---

## Timeline (status, references, and other events)

- **2026-10-09T17:36:38Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/176#pullrequestreview-5473372427.
