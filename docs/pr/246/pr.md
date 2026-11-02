# PR #246: feat: a bare /merge lands a finalized PR without waking the agent

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/246
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/merge-gate-hook-k2tzds
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-28T09:34:39Z
- **Updated:** 2026-11-02T02:52:08Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/merge-gate/hooks/merge_gate.py`:1 — unresolved — last: @vzakharov (human) 2026-11-02T02:48:54Z — "а наличие docs/remove-before-merging является препятствием с…" → [↓](#t01)
- **T02** `.claude/merge-gate/hooks/record.py`:5 — unresolved — last: @vzakharov (human) 2026-11-02T02:50:53Z — "хм, ну cannot drift кажется тут слишком сильное утверждение,…" → [↓](#t02)

---

## Body

## Summary

- **A bare `/merge` lands a finalized PR with no model turn.** `.claude/merge-gate/hooks/merge_gate.py`, on `UserPromptSubmit`, checks the branch's PR against every mechanical condition of `/merge`'s gate, all read from GitHub rather than the checkout: one open non-draft PR; a full attestation whose every line holds a value `attest.md`'s template allows; a head past the attested SHA only by ledger rows; a base that has not advanced; a clean merge state with every check green; nothing awaiting an answer; a squash record that reads back. It then squash-merges with `--match-head-commit` and blocks the prompt with `✅ Merged #<n> into <base> at <sha>`. A blocked prompt makes no API request.
- **When anything fails, the agent decides.** Any failed check or error passes the prompt through untouched, and the agent runs `/merge` with judgement as before. A `no vet` attestation always goes to the agent, and the `/test-on-gh is an unhydrated stub` line counts as green only while that skill on the PR head is still a stub, so an adopter who hydrated it gets a decline.
- **The gate owns the cold-cache decision for a bare `/merge`.** Hooks of one event run in parallel, so the guard lets a bare `/merge` through, and the gate runs the guard as a subprocess when it declines. A subprocess, because `scripts/lib/` and `.claude/costs/lib/` both carry a `lib.github`; the attestation marker moves to `.claude/costs/lib/attestation.py` for the same reason. After a merge, every prompt that reaches the model is told the PR landed until a response follows.
- **This PR also lands vzakharov/muthur#237**: the keepalive starts no watcher and parks nothing on a landed branch, so a session stops costing anything once its work is in. #237 is closed in favour of this PR.
- **Wiring:** `awaiting_rows()` comes out of the export's awaiting section so the gate counts rows; `scripts/vet.sh` runs the gate's tests; catalog entry G11 offers it to adopters as an ask.

## QA Checklist

- [ ] `merges` — on a finalized PR with green CI and nothing awaiting an answer, type `/merge`. The block message reads `✅ Merged #<n> …`, the PR shows merged with the proposed squash title and body, and the session spends no tokens.
- [ ] `declines` — on a PR whose base advanced after `/finalize`, type `/merge`. The agent wakes and runs `/merge` as usual.
- [ ] `args` — type `/merge no vet`. The gate does nothing and the agent handles it.
- [ ] `cold` — after the cache has expired on a finalized PR, type `/merge`. It merges with no price stop. On a PR the gate declines, the cold-cache stop appears, and `!` resends `/merge` to the agent.
- [ ] `note` — after a gate merge, send any prompt. The agent's reply shows it knows the PR landed.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `merges` | integration | ✅ | `test_merge_gate.py` `Merges`: the merge call's subject, body and head, and the block JSON |
| `declines` | integration | ✅ | `Declines`: one case per check, plus a refused merge and an error |
| `args` | unit | ✅ | `test_an_argument_is_left_to_the_agent` |
| `cold` | integration | ✅ | `ColdCache` here, and the deferral cases in `test_cold_cache.py`; the real price stop on a live session is manual |
| `note` | unit | ✅ | `AfterMerge`: told on each prompt until a response lands |

https://claude.ai/code/session_01DaohkCY3YE4xygob4Y3pBW

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-28T09:34:57Z — "Proposed squash title/body: ``` feat: a bare /merge lands a…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-28T09:34:57Z

[https://github.com/vzakharov/muthur/pull/246#issuecomment-6465524129](https://github.com/vzakharov/muthur/pull/246#issuecomment-6465524129)

Proposed squash title/body:

```
feat: a bare /merge lands a finalized PR without waking the agent (#246)
```

```
Landing a finalized PR took a model turn: the operator typed /merge,
and the agent re-read a cold conversation to run checks that were
already mechanical. A UserPromptSubmit hook now takes a bare /merge
first. When the PR passes every mechanical condition of the /merge
gate, the hook squash-merges it with the proposed title and body and
blocks the prompt with the merged SHA. No model request is made.

The conditions are read from GitHub, not from the checkout: a full,
all-green attestation; a head past it only by ledger rows; a base that
has not advanced; a clean merge state with every check passed; no
feedback awaiting an answer; and a squash record that reads back. The
merge pins the head commit it checked. Any failure or error passes the
prompt through untouched, and the agent's /merge runs with judgement
as before.

Hooks of one event run in parallel, so the cold-cache guard lets a
bare /merge through and the gate runs the guard's price stop itself
when it declines. After a merge, the next prompt tells the agent the
PR landed.

The keepalive starts no watcher and parks nothing on a branch whose PR
has landed, merged or closed, so a session stops costing anything once
its work is in. It asks GitHub only on turns no live watcher covers,
and once per commit after a landed answer.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/merge-gate/hooks/merge_gate.py`:1 — unresolved — last: @vzakharov (human) 2026-11-02T02:48:54Z — "а наличие docs/remove-before-merging является препятствием с…" → [↓](#t01)
- **T02** `.claude/merge-gate/hooks/record.py`:5 — unresolved — last: @vzakharov (human) 2026-11-02T02:50:53Z — "хм, ну cannot drift кажется тут слишком сильное утверждение,…" → [↓](#t02)

<a id="t01"></a>

### `.claude/merge-gate/hooks/merge_gate.py`:1 — unresolved

**@vzakharov (human)** — 2026-11-02T02:48:54Z

а наличие docs/remove-before-merging является препятствием с точки зрения "mechanical conditions"? (юс-кейс: пришёл, забыл сказать финалайз, сказал только /merge, они и мерджнул) или отсутствие аттестации все равно это поймает?

---

<a id="t02"></a>

### `.claude/merge-gate/hooks/record.py`:5 — unresolved

```diff
@@ -0,0 +1,104 @@
+"""What the merge gate reads off the PR's conversation comments: the attestation
+and the squash record. Each mirrors a prose home — the attestation template in
+`.claude/skills/finalize/attest.md`, the read-back in
+`.claude/skills/finalize/merge.md` § "Merging" — and `test_merge_gate.py` reads
+the template, so the patterns here cannot drift from it unnoticed.
```

**@vzakharov (human)** — 2026-11-02T02:50:53Z

хм, ну cannot drift кажется тут слишком сильное утверждение, учитывая что пишем и там и там? есть ли возможность сделать это полностью DRY? пока варианты, не правь

---

## Timeline (status, references, and other events)

- **2026-10-28T10:37:24Z** @vzakharov cross-referenced this pull request from [#237 feat: keepalive starts no watcher and parks nothing on a landed branch](https://github.com/vzakharov/muthur/pull/237).
- **2026-11-02T02:52:07Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/246#pullrequestreview-5731596539.
