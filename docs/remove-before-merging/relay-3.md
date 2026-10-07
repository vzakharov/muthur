# Relay 3 — cache keepalive: watcher finished, live-checked, awaiting /finalize

Written by the keepalive's own last wake (5 of 5), without a successor: the
session idled for about four hours after the work was done.

## 1. Standing constraints

None stated by the operator.

## 2. The conversation

Operator: Vova (@vzakharov), Russian, «ты». This session picked up from relay-2
(https://claude.ai/code/session_014kq9BRXRCJpLo6GxbvAwcZ) via `/relay take`.

1. *(Launch: `/relay take claude/cache-keepalive-he98hv`.)*
   **Agent:** Attached, flipped the plan paused → in-progress. Answered relay-2's
   open points: a background task is the price of a living container (only it
   counts as session activity). Put the start-condition design as a choice:
   (1) the agent decides at the turn's end, from criteria in the hook's text
   (recommended — only the agent knows what was discussed and not recorded);
   (2) a mechanical predicate in the hook (plan state, commit newer than last
   prompt) — checkable, but runs at the turn's start and misreads a chat-only
   reply. Flagged an unknown: does `TaskStop` wake the session.
2. **Operator:** «первое, да»
   **Agent:** Probed `TaskStop`: no completion notice. Implemented option 1
   (d5ca991), rewrote tests and `.claude/keepalive/CLAUDE.md`, dropped the inert
   `Stop` entry, staged CLAUDE.md's `run_in_background` exception, `/polish` via
   subagent (bd69b74, 61ca46f; open DRY call on the `watch` literal declined),
   refreshed PR body/title and squash proposal (af08318). Started a live check
   with the 60 s period knob.
3. *(Wakes 1–5, no operator messages.)* Wake 1 came a minute later; the knob was
   removed; wakes 2–5 came ~55 min apart; this is wake 5.

## 3. Intent

Keep an idle web session's prompt cache warm only while losing the session
would lose something, with a ≤ 7-word line per wake, at most 5 wakes, the last
one relaying without a successor. Mods ruled out for now.

## 4. Decisions

- **Start condition is the agent's call** (operator: «первое, да»), stated in the
  hook's `SUFFICIENT` text; a running watcher is `TaskStop`ped once it holds.
  Beat: a mechanical hook-side predicate (turn-start timing, blind to chat-only
  replies).
- `TaskStop` is silent (probed twice); a natural exit is the wake.
- Terms: **неполный релей** = relay without a successor; **граница лупа** = the
  next step is an operator command (`/go` on a draft, `/finalize` after `/go`).

## 5. Errors and dead ends

Earlier ones are in relay-2 § 5 (async Stop hook let the container die). None
new here.

## 6. State

- Branch `claude/cache-keepalive-he98hv`, PR https://github.com/vzakharov/muthur/pull/159
  — draft, `MERGEABLE`/`CLEAN`, no CI checks reported.
- Plan: `docs/plans/cache-keepalive.completed.md`.
- Staged: `.claude/staged/CLAUDE.md.staged` (the exception) — `/finalize` swaps it in.
- Nothing running: no watcher (this last wake starts none), no subscriptions,
  no check-ins.
- Estimate: this session 1 h senior architect + 2 h middle developer, the whole
  remainder relay-2 handed on; nothing handed on beyond `/finalize`.

## 7. Pointers

- `.claude/keepalive/hooks/keepalive.py`, `.claude/keepalive/CLAUDE.md`,
  `.claude/keepalive/test_keepalive.py`.
- `docs/remove-before-merging/squash-message.md` — the posted proposal.
- relay-1, relay-2 in this directory for the earlier experiments.
- This session's transcript: https://claude.ai/code/session_01GD1UhShYvUD9s1iE7zsxih

## 8. Next step

The work is done and live-checked; the branch sits at a loop boundary awaiting
`/finalize`. Wait for the operator.
