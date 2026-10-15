# Relay 3 — cost ledger on its own branch: steps 1–4 built, resume at step 5

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

   **Agent:** Picked up relay-2, whose Next step was the approved plan
   («погнали»). Flipped the plan to `in-progress` quoting «погнали», pushed an
   empty-tree orphan root to `cost-ledger` (the spike passed), and built plan
   steps 2–4. The context budget warning came at ~200k with steps 5–11 left,
   which would not fit in the next 100k, so the agent paused the plan and ran
   `/relay` unasked, as the budget notice directs. The operator has said nothing
   since the pickup.

## Intent

Count every session that spent money (abandoned branches, the merge turn, turns
after finalize, sessions on main), with cost visible in the PR diff while work
is in flight and **no rows on main at all** once this lands. Every adopter
migrates the same way.

## Decisions

The plan's § "Shape", § "Steps" and § "Decided" carry the settled design; its §
"Progress" carries what this session decided while building. The terms from
relay-2 still hold: **display copy**, **finalized**, **marker cache**
(`tmp/costs/finalized/<branch>`), **implicit unfinalize**, **revoke**. Coined
here: **`recency`**, the (`lastResponseAt`, `estimate.at`) pair that picks the
later of two copies of a row.

## Errors and dead ends

- The project's hooks refuse `cat`/`sed`/`head` file I/O in Bash; `BATCH_EDIT=1`
  in front lets a deliberate mechanical `sed` through. A line-number `sed` after
  an edit that shifted lines hit the wrong lines once; match by pattern.
- `last_line` of git's stderr gave "and the repository exists." — git spreads
  one refusal over several lines, hence the hook's `all_lines` for ledger
  errors.

## State

- **Branch:** `claude/cost-ledger-branch-pz4s1a`, never rename it (PR open).
- **PR:** https://github.com/vzakharov/muthur/pull/202, open draft, base `main`,
  title `feat: [attn adopters] keep the cost ledger on its own branch`. Its body
  and squash proposal predate the implementation; `/go`'s Step 4 refreshes them.
- **Last pushed commit:** 6eb7957 (plan paused). Code through 4281ba5.
- **Plan:** `docs/plans/cost-ledger-branch.paused.md`.
- **`cost-ledger` on origin:** root ec2bfe9, empty tree. `backfill` has not run;
  every hook run since 4281ba5 appends to it (this session's own Stop rows
  included).
- **Running:** nothing. No PR subscription, no check-ins, no keepalive.
- **Estimate:**
  - This session: 7 h senior developer ("the shared ledger plumbing, finalized
    detection and the dual-write Stop hook") + 0.25 h middle editor (the plan's
    progress record).
  - Remainder handed on, to set first:
    - 5 h senior developer, "the readers' union on two transports, the backfill
      run against every ref, and tests for the finalized cache, a racing writer
      and the trunk: git ref traps a middle would get wrong";
    - 1.25 h middle editor, "the ledger's CLAUDE.md, finalize's sweep and revoke
      mode, and the adopters' port note all change with the source of truth".

## Pointers

- `docs/plans/cost-ledger-branch.paused.md` — the spec, and § "Progress" for
  what is done and left (two additions: `estimate.py --session` on a ledger-only
  row, and a GitHub seam for the hook tests).
- New code: `.claude/costs/lib/ledger.py`, `.claude/costs/lib/finalized.py`,
  `.claude/costs/ledger.py`; changed: `.claude/costs/hooks/stop-session-cost.sh`
  (`run_ledger`, `commit_row`, the ledger verdict),
  `.claude/costs/test_stop_hook.py` (one test renamed).
- Still to change, per relay-2's list: `.claude/costs/session_cost.py`
  (`previous`), `report.py` (`this_repo`), `lib/github.py` (`REPO_FIELDS`,
  `discover`, `ledger_texts`, `remote_ledger`), `check_estimates.py`,
  `estimate.py`, `.claude/costs/CLAUDE.md`, `.claude/skills/finalize/SKILL.md`
  (sweep ~245, attestation marker ~271–343), `.claude/skills/check-merge/`,
  `.claude/skills/update-muthur/SKILL.md:145`, `scripts/muthur-sync.sh:176`,
  `scripts/check-repo-identity.sh:83`, `.claude/skills/detemplate/SKILL.md:108`.
- Earlier summaries: `docs/remove-before-merging/relay-1.md` (design, measured
  gap), `relay-2.md` (plan questions and answers).
- Predecessor transcripts:
  - this session: https://claude.ai/code/session_01EjjbAbLxx8qNg1XKJm3Et7
  - relay 2: https://claude.ai/code/session_01TNVxArQP8m5nFYcXyYdWDG
  - relay 1: https://claude.ai/code/session_01NgUZSXMZuxiwQHduuBy6yC

## Next step

The paused plan, under the go-ahead «погнали» already recorded in the
`in-progress` flip: `/go` from its Step 1 (flip `paused` → `in-progress`), then
steps 5–11 and the two additions in § "Progress", then `/polish` and `/pr`.
