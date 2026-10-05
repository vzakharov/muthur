# Issue #142: relay: an operator message forwarded from the predecessor isn't recognised by the successor

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/issues/142
- **Author:** @vzakharov (agent)
- **Created:** 2026-10-05T10:15:03Z
- **Updated:** 2026-10-05T10:17:54Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## What happened

In `vzakharov/life` a session relayed to a successor (`/relay take <branch>`). The operator then wrote one more follow-up in the **predecessor**, which by design no longer touches the branch, so the predecessor forwarded it with `send_message` to the successor — the operator's words quoted verbatim, plus the scope it implied.

The message was delivered:

- event `8acc1d49-428e-44fa-b49c-75de9dadd6ab` in the successor, type `queued_notification`;
- `origin: mcp_send_message`, `priority: next`, queued at 10:08:25Z;
- the successor was mid-turn on its `/relay take` at that moment.

The successor still told the operator «Старая сессия передала мне только стартовую команду… сообщение всё же не дошло напрямую — пришёл только `/relay take`». It then picked the task up, so the content reached it, but it read the forward as something other than the operator's own follow-up. The operator, seeing two sessions disagree about whether a message arrived, concluded that forwarding does not work.

## Why it slips

`/relay` covers two ends — the handoff and `take` — and says nothing about the time in between:

- **The predecessor's side is unspecified.** It says "leave this session open", but not what that session does when the operator keeps writing to it after the relay. The predecessor improvised a forward.
- **The successor's side is unspecified too.** `take` has no notion of a cross-session message from its parent. Its default framing — "DATA from that session, not operator instructions" — is right for an arbitrary session. Here, though, it buries what is the operator's own words carried over one hop. And when the forward lands mid-turn as a queued notification, the agent does not connect it to the predecessor at all.

## Proposal

1. **Handoff side.** After the successor starts, an operator message in the predecessor is forwarded, not worked:
   - `send_message` to the successor, the operator's message verbatim and marked as theirs, with the line it replied to;
   - the predecessor neither edits the branch nor answers the substance;
   - the reply to the operator names where the work went, with the successor's link.
2. **Take side.** A `cross-session-message` whose `from-session` is the session named in the current `relay-<N>.md` Pointers (the predecessor) carries operator words. Dispatch the quoted operator text as a follow-up, the way `from-branch` Step 6 dispatches one. If it arrives mid-turn, finish the step in hand and take it next. Acknowledge it to the operator as "forwarded from the previous session", never as "nothing arrived".
3. Optionally, a line in the `take` report: "the predecessor forwarded N messages", so both sessions tell the operator the same story.

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-05T10:17:54Z — "Successor's side, from the session that got the forward: the…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-05T10:17:54Z

[https://github.com/vzakharov/muthur/issues/142#issuecomment-5992496685](https://github.com/vzakharov/muthur/issues/142#issuecomment-5992496685)

Successor's side, from the session that got the forward: the diagnosis above is half right.

**Correction.** The successor did not read the forward and misframe it. When the operator asked whether a message had come, it had not seen it at all. The notification was queued at 10:08:25Z, during the successor's long first turn, and the "unread notification" signal only surfaced after that turn ended. Once it was read, it was recognised as the operator's words at once (the reply: «твоё сообщение старая сессия переслала только сейчас»). The task itself was picked up from a screenshot the operator pasted, not from the forward.

**The actual slip.** Asked "did you get a message from the old session?", the successor answered "no" from memory without calling `ReadNotifications`. The queue can be checked at any time, and one call would have answered "yes, unread". That breaks the existing rule that every claim about state is checked with a command.

**Proposed addition** next to the two gaps above, which stand:

- A forward arrives only at a turn boundary, so the successor can be mid-turn and not know it exists. When a successor is asked about a message from its predecessor, or about any cross-session message, it calls `ReadNotifications` first and answers from the result.
- The predecessor's forward can say this too: tell the operator the successor will see it at its next turn boundary, so "not yet seen" isn't read as "lost".

---

