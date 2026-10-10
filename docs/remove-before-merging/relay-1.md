# Relay 1 — design talk on #177 (stale session estimate)

## Standing constraints

None stated.

## The conversation

1. **Operator:** «The session estimate goes stale while the operator grows the task #177 — ещё вопрос, почему оценка меняется каким-то скриптом, а не просто Edit-ом? Как будто конфликтуем с собственными принципами. Там есть что-то такое, что обычный Edit не даст?»
   **Agent:** Routed as row 2 (a question, no change). Answered that `.claude/costs/estimate.py` is the write API of storage the Stop hook owns, not a file the agent authors: for the running session it writes the gitignored `tmp/estimates/<id>.json`, which `session_cost.py:114` folds into the row via `latest()`; the script sets `at` (a hand edit that forgets it silently loses to the older copy), validates role/grade/hours/reason length at write time, and replaces the estimate whole. Wrongly claimed a mid-turn `Edit` of the row would "race" the Stop hook.

2. **Operator:** «в клод коде же есть механизм что до любого Edit нужен Read, и оно не даёт Edit, если содержимое с тех пор поменялось?»
   **Agent:** Conceded: the hook runs only after the turn, so there is no race and the read-before-edit check would pass. An `Edit` of the row works from turn 2 on (the hook reads the previous row off disk, `session_cost.py:108`), at the cost of a commit per revision (the harness's `stop-hook-git-check.sh` blocks on the dirty file). What remains for the script: no row exists on turn 1, the `at` trap, and validation at write time rather than at report time.

3. **Operator:** «ладно, пусть будет как есть пока. а что по основному вопросу тикета (извини, сам ушёл -- вот тебе и догфуд?»
   **Agent:** Revised this session's estimate 0.6 → 1.8 senior-hours, the scope having grown. Proposed lever 2 of #177: a `Stop` hook that blocks once per turn when the turn had an operator prompt, HEAD moved, and the estimate was not set since that prompt (`estimate-notice.sh` recording HEAD at `UserPromptSubmit`), with lever 1's wording ("a request that adds a deliverable, even one asked as a question, is a size change") as its text; skip lever 3. Costs named: an extra round on every committing turn without a revision; growth without commits is not caught.

4. **Operator:** «что-то не нравится, wasteful. а что если добавить это шагом в polish?»
   **Agent:** Agreed polish is the better home: it already reads the branch diff since the last `polish:` floor, so no extra rounds, and every landed branch passes it at `/finalize`. Hole: post-`/go` follow-ups (the #177 case) skip polish until `/finalize`, possibly in another session whose estimate is not the stale one. Fix: map commits in scope to sessions via the `Claude-Session: <url>` trailer → the row's `url`, ask per session whether its estimate covers its commits, revise via `estimate.py set --session <id>`; "unchanged" stays the ordinary result so the step does not push hours up. Offered `/task #177` on «делай», and a comment on #177 recording polish over the Stop hook and why. **No answer yet.**

Then the cache keepalive's wakes ran out and this relay was written.

## Intent

Fix #177 (the estimate stays at its first figure while the operator grows the task) cheaply. The operator ruled out a per-turn `Stop`-hook nudge as wasteful, and left the script-vs-`Edit` question "как есть пока".

## Decisions

- **Polish step over a `Stop` hook** — the hook costs a model round on every committing turn; polish already reads the diff at milestones. Not yet confirmed by the operator as the go-ahead.
- **Keep `estimate.py`, not `Edit`** — "пусть будет как есть пока".
- **"Unchanged" is a legitimate result of any estimate check** — a check that nudges toward writing makes the agent book detours as hours, hiding the regression the figure measures (`.claude/costs/CLAUDE.md` § "Human-hour estimates").

## Errors and dead ends

- The "race between `Edit` and the Stop hook" claim was wrong (see message 2); the operator caught it.

## State

- Branch `claude/estimate-staleness-gr4c0w`, renamed from `claude/dazzling-ride-gr4c0w`. Deleting the old remote ref got a 403 from the git proxy, so it lingers; no PR is open on either name.
- No PR, no plan file, no CI or subscription. Only the cost-ledger commits and this summary are on the branch.
- Estimate: 1.5 h senior architect = 1.8 senior-hours, "judging where an estimate nudge should fire needs the harness's hook timing, the ledger's cost model, and how a nag would bias the very figure it measures — design work, no code". Covers the whole design talk; nothing handed on.

## Pointers

- `gh api repos/vzakharov/muthur/issues/177` — the issue and its three levers.
- `.claude/costs/estimate.py`, `.claude/costs/lib/rows.py` (pending path), `.claude/costs/session_cost.py:108-117` (fold-in), `.claude/costs/hooks/estimate-notice.sh`, `.claude/costs/CLAUDE.md` § "Human-hour estimates".
- `.claude/skills/polish/SKILL.md` — § "The floor" is what scopes the proposed step.
- Predecessor transcript: https://claude.ai/code/session_01ThPwHmD3Mcb3TEThoJ5MLa

## Next step

Wait for the operator. Pending: their answer to message 4's proposal — «делай» runs `/task #177` with the polish-step design, plus a comment on #177 recording why polish beat the `Stop` hook.
