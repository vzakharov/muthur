# Edit relay: Opus lists the edits, Haiku applies them

## Status (paused for the context budget)

**Done:** everything under "What changes" below — `edit-relay.md` (3cdde0d), the
hook switch, tests, `/go` Step 2 and catalog (bd7d30c, applied by Haiku through
the relay itself: 16/16 items exact), polish (32f2aa2, 08f5664). PR #254 body
carries a dogfood section.

**Left — Vova's follow-ups in the session, all agreed:**

1. **Rename.** "Relay" collides with `/relay` (hand the session to a fresh one).
   Vova: build the name on «стенографировать». Recommended: mode **steno** —
   `MUTHUR_STENO`, `.claude/skills/go/steno.md`, the delegator dictates, Haiku
   takes it down. `grep -ril steno .claude scripts` is empty. Rename across hook
   (`RELAY_SWITCH`, `RELAY_FILE`, docstring), tests (`TheEditRelaySwitch`,
   `RELAY*`), `/go` Step 2, G2 catalog, PR title/body, squash proposal
   (`docs/remove-before-merging/squash-message.md`).
2. **Cost model in waves, not edits.** Vova's two points: fixing after Haiku,
   and things discovered only while editing. A relay run is a _wave_ — decide →
   Haiku applies → review diff and tests; whatever the review finds becomes the
   next wave, and each wave pays a near-fixed fee (Haiku start-up with CLAUDE.md
   and the skill listing, ≈$0.06 here, plus the delegator's review turn,
   ≈$0.05). Direct editing pays per turn `context × cache_read` (≈$0.025 at 125k
   on Opus 5.5) and absorbs discoveries inline. Break-even ≈ fixed / per-turn:
   ~8 turns at 50k context, ~4 at 125k, ~2–3 at 200k. Size of an edit barely
   matters — its text is paid as output once either way. `steno.md` gets a
   section on waves, and drops the paragraph that makes "parallel `Edit` calls
   in one turn" the typical alternative (it is the rare ideal; real direct work
   is sequential or per-file batches).
3. **Brief: "notice, don't touch".** Replace "fix nothing it notices" with
   "change nothing outside the list, and list in the report anything nearby that
   looks wrong". Evidence: Haiku left the stale "silent under
   `MUTHUR_DELEGATION=off`" two lines from its own catalog edit, by the brief;
   `/polish` caught it. Whether Haiku notices at all is untested (#253 says it
   does not look for the same defect elsewhere) — the next dogfood checks.
4. **Forecast before launching.**
   `.claude/costs/delegation.py --forecast --turns <n> --waves <w>`: reads the
   delegator's current context from the transcript (the script already does),
   prints "direct: $X, steno: ~$Y"; the per-wave fee comes from past rows (item
   5), with this run's figures as the seed. The procedure: forecast favours
   steno → dictate.
5. **Forecast-against-fact rows on the ledger branch** — Vova: "an auto-branch
   like cost-ledger, where the forecast is compared with the fact, so we can
   calibrate once there is enough data". Recommended: same `cost-ledger` branch,
   its own tree (e.g. `delegations/<YYYY-MM>/<branch>/<agent-id>.json` holding
   forecast inputs — turns, waves, context — the forecast, and `delegation.py`'s
   measured fact), written through `ledger.py`'s existing push-with-retry
   machinery rather than a second orphan branch; read `.claude/costs/CLAUDE.md`
   first, it owns filing and concurrency rules. A second branch is the
   alternative if rows must stay out of `report.py`'s totals. The forecast
   writes the row; the post-run weighing completes it.
6. **PR body:** the dogfood "a draw at best" was wrong — it assumed one parallel
   turn. Realistic direct work (5–8 turns at ~125k) puts steno at ~1.5–2×
   cheaper for one wave. Rewrite with the wave model.
7. **Haiku entry** in `delegation-model-capabilities.md`: still waits on #253.

An experimental `/go` Step 2 mode, off unless `MUTHUR_EDIT_RELAY=on`. The
delegating model reads, decides, and writes out every edit a stretch of work
needs — file, anchor text, replacement — as one list; a Haiku subagent applies
the list in the session's own tree and reports what did not apply. The delegator
reviews the diff and commits.

The bet, from the `haiku` evidence (applies named corrections exactly and only
those; misreads anything it must restate): Haiku is a reliable pair of hands
when nothing is left to interpret, so the delegator's per-edit turns — each a
re-read of its whole context — collapse into one turn writing the list plus one
reviewing the diff, and the reads Haiku needs to anchor each edit land in
Haiku's context at Haiku's rate.

## What changes

1. **`.claude/skills/go/edit-relay.md`** (new) — the procedure:
   - when a batch qualifies (every edit nameable exactly; nothing to decide;
     enough of them that the relay beats doing them — and when it does not,
     including that parallel `Edit` calls in one turn already save the turns);
   - the list's format: per item the file, the exact text to find (unique in the
     file), the exact replacement — or for a new file, its whole content; prose
     to insert is written out in full, never described;
   - launching: `Agent` with `model: "haiku"`, foreground, **no worktree** — it
     edits the session's tree while the delegator waits, so there is no merge;
     the brief forbids commits, interpretation and edits beyond the list, and
     asks for a per-item applied / not-applied report;
   - review: `git diff` whole against the list, fix or re-relay misses, commit
     under the delegator's name with the relay named in the body;
   - weighing: `.claude/costs/delegation.py <agent-id> --turns <n>` as
     `delegation.md` § "Weighing the cost", verdict into the `haiku` entry.
2. **`.claude/hooks/go-delegation.py`** — also deliver `edit-relay.md` when
   `MUTHUR_EDIT_RELAY` is `on` (exactly `on`; anything else, unset included,
   leaves it out). Delivery set: the two delegation files unless
   `MUTHUR_DELEGATION=off`, plus the relay file when it is on, plus the
   capabilities file whenever the relay is on (it names the `haiku` entry).
   Nothing to deliver → silent, as today.
3. **`scripts/test_go_delegation.py`** — cases: relay on delivers all three;
   relay unset / any other value leaves it out; relay on with delegation off
   delivers the relay and the capabilities only; a missing relay file fails open
   like the others.
4. **`.claude/skills/go/SKILL.md`** Step 2 — the delivery sentence names the
   relay file and its switch, and its no-hook fallback.
5. **`.claude/skills/update-muthur/catalog/g2-pr-loop.md`** — the G2 entry and
   the hook's entry mention the relay and its default-off switch.

**Dogfood:** items 3–5 (and the hook edit, if it is list-shaped once written
out) go through the relay once `edit-relay.md` exists; the report puts the
relay's cost beside doing the same edits directly, with the turn count assumed.

The `haiku` entry in `delegation-model-capabilities.md` is left alone here: PR
#253 rewrites it and has not merged; the dogfood verdict is reported on the PR
and folded in once #253 lands.

## DRY notes

- **The hook is extended, not duplicated.** A second hook would repeat
  `go-delegation.py`'s entry detection, once-per-session marker and fail-open
  handling for a third file. The relay is one more file on the same delivery,
  gated by its own switch — a conditional in `brief()`'s file list.
- **`edit-relay.md` points at `delegation.md`** for the weighing and the
  capabilities upkeep rather than restating them; it carries only what differs
  (no worktree, no merge, the list format, the brief's no-interpretation rule).
- **Tests reuse the suite's fixture and helpers**; `run_hook` takes a second env
  variable rather than a parallel helper.
