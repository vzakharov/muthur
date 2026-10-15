# Relay 4 — cost ledger on its own branch: steps 1–8 built, resume at step 9

## Standing constraints

- «ветка всё-таки пусть называется cost-ledger, без muthur-; если у адоптера она
  уже будет, сам решит при адоптинге как переименовать.» The ledger branch is
  `cost-ledger`, nothing else.
- The silent fallback on a failed GitHub query (treat as not finalized) is
  approved for that one call site only («1a»). No other silent fallback is.

## The conversation

The operator (Vova, `@vzakharov`) writes in Russian; replies in Russian, «ты».

1. **Operator:** `/relay take claude/cost-ledger-branch-pz4s1a` (bare: no
   further message)

   **Agent:** Picked up relay-3, whose Next step was the paused plan under
   «погнали». Flipped it to `in-progress`, built steps 5–7 (step 8 needed
   nothing), and paused at the context budget warning (~206k), since steps 9–11
   would not fit in the next 100k. Along the way, `test_estimate.py`'s
   `--session` test, run in the real checkout, pushed a fixture row to the real
   `cost-ledger`; the agent pushed a commit removing it (0de5f18 on
   `cost-ledger`, no force) and moved those tests into a clone. The operator has
   said nothing since the pickup.

## Intent

Count every session that spent money (abandoned branches, the merge turn, turns
after finalize, sessions on main), with cost visible in the PR diff while work
is in flight and **no rows on main at all** once this lands. Every adopter
migrates the same way.

## Decisions

The plan's § "Shape", § "Steps" and § "Decided" carry the settled design; its §
"Progress" carries what each session decided while building. Terms from earlier
relays still hold: **display copy**, **finalized**, **marker cache**
(`tmp/costs/finalized/<branch>`), **implicit unfinalize**, **revoke**,
**`recency`**. New here: **sides**, the two places a repository's rows can be
(`refs/heads/cost-ledger` and `HEAD`), `lib/github.py`'s `SIDES`.

- `check_estimates.py` fetches the ledger (a failed fetch fails the check, no
  fallback) rather than reading a possibly stale local ref.
- `/check-merge` was left alone: it never reads the attestation marker.

## Errors and dead ends

- Any test that runs a command which pushes must run in `test_stop_hook.Clone`,
  never the real checkout — that is how the fixture row reached the real ledger.
- The project's hooks refuse `cat`/`sed`/`head` file reads in Bash; use `Read`,
  and `BATCH_EDIT=1` in front of a deliberate scripted edit.

## State

- **Branch:** `claude/cost-ledger-branch-pz4s1a`, never rename it (PR open).
- **PR:** https://github.com/vzakharov/muthur/pull/202, open draft, base `main`.
  Its body and squash proposal predate the implementation; `/go`'s Step 4
  refreshes them.
- **Plan:** `docs/plans/cost-ledger-branch.paused.md`.
- **Staged:** `.claude/skills/finalize/SKILL.md` →
  `.claude/staged/.claude/skills/finalize/SKILL.md.staged` (step 7's edits).
- **`cost-ledger` on origin:** root ec2bfe9; `backfill` has not run. Tip was
  0de5f18 at the cleanup; Stop rows land on it after every turn.
- **Running:** nothing. No PR subscription, no check-ins, no keepalive.
- **Estimate:**
  - This session: 2.5 h senior developer ("the readers' union on two transports
    and the ledger-side estimate edit: git ref and GraphQL traps a middle would
    get wrong") + 0.5 h middle editor ("finalize's sweep, SHA marker and revoke
    mode change with the source of truth").
  - Remainder handed on, to set first:
    - 2.5 h senior developer, "the backfill run against every ref, and tests for
      the finalized cache, a racing writer and the trunk, with a GitHub seam in
      the hook: git ref traps a middle would get wrong";
    - 0.75 h middle editor, "the ledger's CLAUDE.md, update-muthur's carve-out
      and the adopters' port note all change with the source of truth".

## Pointers

- `docs/plans/cost-ledger-branch.paused.md` — the spec; § "Progress" says what
  is done and left.
- This session's code: `.claude/costs/lib/ledger.py` (`path_of`, `copies`),
  `session_cost.py` (`previous`), `estimate.py` (`edit`), `check_estimates.py`
  (`ledger_rows`), `report.py` (`ledger_rows`, `this_repo`), `lib/github.py`
  (`SIDES`, `Candidate.sides`, `remote_ledger`), `test_estimate.py`
  (`TheCommand` in a `Clone`), `test_github.py` (`TheTwoSides`).
- Still to change for step 11: `.claude/costs/CLAUDE.md`,
  `.claude/skills/update-muthur/SKILL.md:145`, `scripts/muthur-sync.sh:176`,
  `scripts/check-repo-identity.sh:83`, `.claude/skills/detemplate/SKILL.md:108`
  (line numbers from relay-2; check them).
- Earlier summaries: `relay-1.md` (design), `relay-2.md` (plan Q&A),
  `relay-3.md` (steps 1–4).
- Predecessor transcripts:
  - this session: https://claude.ai/code/session_016EVcpgqoYET5tQWnhgeQpM
  - relay 3: https://claude.ai/code/session_01EjjbAbLxx8qNg1XKJm3Et7
  - relay 2: https://claude.ai/code/session_01TNVxArQP8m5nFYcXyYdWDG
  - relay 1: https://claude.ai/code/session_01NgUZSXMZuxiwQHduuBy6yC

## Next step

The paused plan, under the go-ahead «погнали» already recorded: `/go` from its
Step 1 (flip `paused` → `in-progress`), then steps 9–11 and the hook-test seam
in § "Progress", then `/polish` and `/pr`. Step 9's backfill pushes to
`cost-ledger` on origin, which the approved plan covers.
