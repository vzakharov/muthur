# PR #159: feat: a Stop-hook keepalive for an idle session's prompt cache

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/159
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/cache-keepalive-he98hv
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-07T06:34:00Z
- **Updated:** 2026-10-07T06:44:24Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 1

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/keepalive/CLAUDE.md`:12 — unresolved — last: @vzakharov (human) 2026-10-07T06:43:17Z — "прямо очень короткая, не больше 5-7 слов" → [↓](#t01)

---

## Body

## Summary

- An idle web session loses its one-hour prompt cache, so the next prompt pays a full re-cache, roughly 40× what keeping it warm costs. `.claude/keepalive/hooks/keepalive.py` is a `Stop` hook with `asyncRewake` that wakes the session about 5 minutes before the cache expires. It re-arms itself after every turn, so the agent has nothing to do per reply. A later turn or prompt supersedes a sleeping hook by a token in `tmp/keepalive/`, not by killing it. Sessions on the 5-minute TTL are left alone.
- It wakes at most 5 times per idle spell. A prompt from the operator resets the count. Wakes 1–4 each get a one-line reply. Wake 5 writes the relay summary without spawning a successor and gives the operator the `/relay take <branch>` line to start a fresh session from.
- `/relay` gains a "Without a successor" section, which is what that last wake runs. `CACHE_KEEPALIVE=off` disables the hook.

## QA Checklist

- [ ] `vet` — `./scripts/vet.sh` passes, including the new `.claude/keepalive/test_keepalive.py`.
- [ ] `wake` — with `tmp/keepalive/period` set to 60, ending a turn brings a wake about a minute later with one short reply, and that wake's own Stop re-arms the hook.
- [ ] `warm` — the wake's request reads the context from cache rather than rewriting it (transcript usage).
- [ ] `reset` — an operator prompt resets the wake count.
- [ ] `last` — wake 5 commits `docs/remove-before-merging/relay-<N>.md`, prints the `/relay take` line and spawns no session.
- [ ] `off` — `CACHE_KEEPALIVE=off` arms nothing.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `vet` | yes | yes | |
| `wake` | partly | unit tests cover arming and replacement | the asyncRewake wake itself needs a live session |
| `warm` | no | no | read from the transcript |
| `reset` | yes | unit test | |
| `last` | partly | unit test covers the wake-5 message | the relay itself is agent behaviour |
| `off` | yes | unit test | |

https://claude.ai/code/session_014kq9BRXRCJpLo6GxbvAwcZ

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-07T06:34:12Z — "Proposed squash title/body: ``` feat: keep an idle session's…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-07T06:34:12Z

[https://github.com/vzakharov/muthur/pull/159#issuecomment-6032407792](https://github.com/vzakharov/muthur/pull/159#issuecomment-6032407792)

Proposed squash title/body:

```
feat: keep an idle session's prompt cache warm from a Stop hook (pr #159)
```

```
An idle web session loses its one-hour prompt cache, and the next
prompt re-caches the whole conversation, about 40 times what a cache
read before expiry costs. Nothing kept the cache warm without the
agent re-arming something on every reply.

A Stop hook with asyncRewake now sleeps in the background until about
five minutes before the cache expires, then wakes the session for a
one-line reply. Each turn's own Stop re-arms it, so the agent does
nothing per reply. A session on the five-minute TTL is left alone.

It wakes at most five times per idle spell, and an operator prompt
resets the count. The fifth wake runs /relay without a successor:
the summary is committed and the operator gets the /relay take line
to start a fresh session from, since a branch idle for about six
hours can wait, and the summary makes picking it up again cheap.
CACHE_KEEPALIVE=off turns it off.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/keepalive/CLAUDE.md`:12 — unresolved — last: @vzakharov (human) 2026-10-07T06:43:17Z — "прямо очень короткая, не больше 5-7 слов" → [↓](#t01)

<a id="t01"></a>

### `.claude/keepalive/CLAUDE.md`:12 — unresolved

```diff
@@ -0,0 +1,32 @@
… 8 lines elided …
+  (default 300) before the cache expires, and exits 2: the harness hands its
+  stderr to the model as a system reminder and the model answers it. The wake
+  turn's own `Stop` arms the next one.
+- **Every wake is one visible line.** The harness rejects a turn with no visible
```

**@vzakharov (human)** — 2026-10-07T06:43:17Z

прямо очень короткая, не больше 5-7 слов

---

## Timeline (status, references, and other events)

- **2026-10-07T06:44:15Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/159#pullrequestreview-5438592951.
