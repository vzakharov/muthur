# Edit relay: Opus lists the edits, Haiku applies them

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
