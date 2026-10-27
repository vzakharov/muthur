# PR #232: fix: the keepalive always parks, even when the branch holds all the work

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/232
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/keepalive-always-parks-9khkys
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-27T02:32:39Z
- **Updated:** 2026-10-27T03:29:01Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/keepalive/CLAUDE.md`:20 — unresolved — last: @vzakharov (human) 2026-10-27T03:12:59Z — "не уверен но возможно медведь? возможны и аргументы против,…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:1 — unresolved — last: @vzakharov (human) 2026-10-27T03:14:12Z — "думаю это таки не фикс; прямо "поломано" не было" → [↓](#t02)

---

## Body

## Summary

- **The keepalive watcher now starts after every turn**, unless the operator asks to stop it. It used to be skipped whenever the branch and its PR's threads let a fresh session continue, so such a session simply went cold and left nothing behind.
- **Why it matters:** the watcher's last wake parks, and a park keeps the session's last reply verbatim and hands the operator a ready `/relay take` line to paste. That last reply often raises points easier to answer directly than to dig back out of files, and pasting one line beats going to the PR, leaving a review and typing `/handle` by hand.
- **A parked summary is rewritten, never deleted**, when its operator comes back and nothing is left pending — for the same reason. A summary gone from disk now only means `/finalize` swept it.

## QA Checklist

- [ ] `boundary-watcher` — In a session whose branch is at a loop boundary (e.g. a paused plan, everything pushed), end a turn: the hook's context asks for the watcher with no "unless the branch suffices" escape, and the agent starts it.
- [ ] `boundary-park` — Leave that session idle until the watcher fires: the wake runs `/relay park`, commits `docs/remove-before-merging/relay-<N>.md` with the last reply verbatim, and ends with a fenced `/relay take <branch> — …` line.
- [ ] `stop-word` — Say "stop" in a session: the hook tells the agent to skip or `TaskStop` the watcher, and no park follows.
- [ ] `return-rewrite` — Come back to a parked session and finish what it listed as pending: the summary file is rewritten in place, not `git rm`'d.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `boundary-watcher` | Yes | Yes | `test_the_agent_is_told_to_start_the_watcher_unless_told_to_stop` checks the hook text |
| `boundary-park` | No | No | needs a real idle hour (or `tmp/keepalive/period`) and the agent following `/relay park` |
| `stop-word` | Partly | Partly | `test_a_running_watcher_is_left_to_the_agent_to_stop` checks the text; the agent's compliance is manual |
| `return-rewrite` | No | No | agent behaviour under `relay/SKILL.md` § "When the summary goes stale" |

https://claude.ai/code/session_01DaohkD2amc2dynSfpzvst3

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-27T02:32:52Z — "Proposed squash body: ``` A session whose branch and PR alre…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-27T02:32:52Z

[https://github.com/vzakharov/muthur/pull/232#issuecomment-6432299751](https://github.com/vzakharov/muthur/pull/232#issuecomment-6432299751)

Proposed squash body:

```
A session whose branch and PR already held all its work skipped the
cache keepalive's watcher, so it went cold with nothing left behind.
Its last reply often raises points the operator would rather answer
directly than dig back out of files, and a park would have kept that
reply verbatim with a ready `/relay take` line to paste, in place of a
trip to the PR and a hand-typed `/handle`.

The keepalive's UserPromptSubmit hook now asks for the watcher after
every turn, skipping it only when the operator asks to stop the
keepalive, so its last wake always parks.

For the same reason, a parked session its operator comes back to
rewrites its summary rather than deleting it once nothing is pending;
a summary missing from disk now only means `/finalize` swept it.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/keepalive/CLAUDE.md`:20 — unresolved — last: @vzakharov (human) 2026-10-27T03:12:59Z — "не уверен но возможно медведь? возможны и аргументы против,…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:1 — unresolved — last: @vzakharov (human) 2026-10-27T03:14:12Z — "думаю это таки не фикс; прямо "поломано" не было" → [↓](#t02)

<a id="t01"></a>

### `.claude/keepalive/CLAUDE.md`:20 — unresolved

```diff
@@ -11,14 +11,12 @@ is below the usual tenth of input (`.claude/costs/prices.json`).
… 8 lines elided …
-  a review lane whose open items all sit as replies or questions on the PR is at
-  a boundary, the operator answering there rather than in chat. Only the agent
-  knows what the conversation holds that the branch and PR do not. `TaskStop`
+- **It runs after every turn, a branch that holds all the work included, because
+  its last wake parks**: the summary keeps the session's last reply verbatim,
+  which the operator answers more easily than they dig the same points out of
+  files, and hands them a `/relay take` line to paste. A session left to go cold
+  leaves neither. The `UserPromptSubmit` hook asks the agent to start it as a
+  turn's last action unless the operator asks to stop the keepalive. `TaskStop`
   ends a task without a completion notice, so stopping one wakes nothing.
```

**@vzakharov (human)** — 2026-10-27T03:12:59Z

не уверен но возможно медведь? возможны и аргументы против, зависит от того, возникло бы у агента желание усомниться в парковке, если бы в бранче всё уже было -- а это знать лучше тебе (хотя чтобы знать тебе тоже нужно "не думать о белом медведе". загагулинка-с)

ну и в принципе глянь ещё раз внимательно не осталось ли больше медведей (полиш был но всё же) -- учитывая что суть пиара "убрать что-то", к этому нужно быть особенно внимательным. (Попутно, в самом скилле tend-prose в разделе про медведей тоже дописать это примечание.)

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:1 — unresolved

**@vzakharov (human)** — 2026-10-27T03:14:12Z

думаю это таки не фикс; прямо "поломано" не было

---

## Timeline (status, references, and other events)

- **2026-10-27T03:14:15Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/232#pullrequestreview-5661802098.
