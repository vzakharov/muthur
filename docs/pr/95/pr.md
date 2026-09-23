# PR #95: feat: per-turn spend in cost-row subjects, warn on unwritten tail

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/95
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/cost-row-end-turn-x2sn2u
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-23T11:11:34Z
- **Updated:** 2026-09-23T11:59:16Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **The cost-row commit subject says what the turn cost.** The Stop hook now commits `chore: session cost row +0.10 USD, total 0.64 USD` instead of a bare `chore: session cost row`. The delta is measured from the row as last committed, so a hand run of `session_cost.py` between turns does not eat into it. The `chore: session cost row` prefix `/finalize` matches on is unchanged.
- **The "last turn is lost" claim is measured rather than stated.** `.claude/costs/CLAUDE.md` said the transcript lags the live conversation, so a session's last turn goes unpriced. That began as a "may lag" hypothesis in vzakharov/vovazakharov.com's plan and was never measured. In this session every Stop hook run priced its own turn's `end_turn`, five of five. The hook now passes `--at-stop`, and a transcript whose last main-chain response (subagents and `<synthetic>` records aside) stopped on anything but `end_turn` gets a warning naming the response and its `stop_reason`. Later rewrites carry the warning forward the way they carry the name, since a caught-up transcript can't recompute it.
- **The bullet that made the claim, and the transcript watcher it weighed, leave `.claude/costs/CLAUDE.md`.** The warning is what will say whether there is anything there.

## QA Checklist

- [ ] `subject` — end a turn; `git log -1 --format=%s` reads `chore: session cost row +X USD, total Y USD`, and Y minus the previous row commit's total is X.
- [ ] `first-row` — in a fresh session, the first row commit reads `+Y USD, total Y USD`.
- [ ] `hand-run` — run `session_cost.py --transcript … --name '…'` mid-turn, end the turn; the delta in the next subject covers the whole turn, not only what came after the hand run.
- [ ] `clean-tail` — after an ordinary turn, the row's `warnings` holds no "not yet written when the Stop hook read the transcript" entry.
- [ ] `short-tail` — run `session_cost.py --at-stop` on a transcript cut after a `tool_use` response; the row warns, naming that message id and `tool_use`.
- [ ] `carry` — re-run on the full transcript; the warning from `short-tail` is still in the row, once.
- [ ] `no-flag` — the same cut transcript without `--at-stop` produces no tail warning.
- [ ] `doc` — `.claude/costs/CLAUDE.md` § "What the totals do not cover" no longer lists the last turn of a session.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `subject` | integration | ❌ | Drive `stop-session-cost.sh` against a temp repo with a committed row and a rewritten one; assert the subject |
| `first-row` | integration | ❌ | Same harness, no committed row |
| `hand-run` | integration | ❌ | Same harness: dirty the row between two commits, assert the delta spans both |
| `clean-tail` | unit | ✅ | `test_passes_a_transcript_ending_on_end_turn` |
| `short-tail` | unit | ✅ | `test_warns_when_the_turn_s_last_response_is_not_yet_written` |
| `carry` | integration | ❌ | Run `session_cost.py` twice over a temp `COSTS` dir; checked by hand on a scratch copy this session |
| `no-flag` | unit | ✅ | `test_says_nothing_outside_the_stop_hook` |
| `doc` | manual-only | — | Prose removal |

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-23T11:11:53Z — "Proposed squash title/body: ``` feat: per-turn spend in cost…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-23T11:11:53Z

[https://github.com/vzakharov/muthur/pull/95#issuecomment-5793789474](https://github.com/vzakharov/muthur/pull/95#issuecomment-5793789474)

Proposed squash title/body:

```
feat: per-turn spend in cost-row subjects, warn on unwritten tail (pr #95)
```

```
The ledger's contract said the transcript lags the live conversation,
so a session's last turn goes unpriced. That began as a "may lag"
hypothesis in the source repo's plan and was never measured: in the
session that wrote this, every Stop hook run priced its own turn's
end_turn, five of five.

So the Stop hook measures it. With --at-stop, which the hook passes,
session_cost.py warns in the row when the transcript's last main-chain
response stopped on anything but end_turn, naming the response and its
stop_reason. A caught-up transcript cannot recompute that warning, so
each rewrite carries it forward as it carries the name, and a row ends
up listing every turn the hook read short. The last-turn bullet and the
transcript watcher it weighed leave .claude/costs/CLAUDE.md.

The cost-row commit subject also says what the turn cost -- "chore:
session cost row +0.10 USD, total 0.64 USD" -- measured from the row as
last committed, so a hand run between turns does not eat into it.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/costs/hooks/stop-session-cost.sh`:114 — unresolved — last: @vzakharov (human) 2026-09-23T11:57:33Z — "давай уберём слово "row", не очень понятно к чему оно тут. е…" → [↓](#t01)

<a id="t01"></a>

### `.claude/costs/hooks/stop-session-cost.sh`:114 — unresolved

```diff
@@ -100,14 +100,23 @@ run_ledger() {
… 12 lines elided …
+    jq -r '.total.costUsd // 0' 2>/dev/null)"
+  now="$(jq -r '.total.costUsd' "$row")"
+  subject="$(awk -v was="${was:-0}" -v now="$now" \
+    'BEGIN { printf "chore: session cost row +%.2f USD, total %.2f USD", now - was, now }')"
```

**@vzakharov (human)** — 2026-09-23T11:57:33Z

давай уберём слово "row", не очень понятно к чему оно тут. ещё реши сам cost или costs правильнее

---

## Timeline (status, references, and other events)

- **2026-09-23T11:59:16Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/95#pullrequestreview-5290624435.
