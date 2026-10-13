> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G7 — Session cost ledger

Nothing in a repo says whether its operator wants to know what the work would
cost at API rates, and what the answer costs lands on every turn of every
session — so the row is `opt-in: ask`.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `.claude/costs/` | Price each session at Claude API rates from its transcript and commit its row to the branch at the end of every turn, so the ledger reaches the trunk with the work; each row also carries the agent's revisable estimate of the work in senior-hours, and `report.py` sums the rows by month, week, day and branch and prices a senior-hour of work, over this repo or, with `--all-my-repos`, every repo the `gh` user can see that carries a ledger. **The cost, which is why it is asked:** a commit and a push per turn on every branch, a line of estimate notice on every prompt, extra CI runs where CI runs on push, a hand-kept rate table that must gain a row before a new model's first session can be priced, a `Stop` hook sharing the event with the harness's git check, and a telemetry receiver listening on `127.0.0.1:4318` for the whole session, whose exporter variables go in the environment's settings by hand, since Claude Code ignores them in `.claude/settings.json` — `hooks/start-telemetry-receiver.sh` names them until they are set. Arrives with an empty `sessions/`, four `.claude/settings.json` hook entries to merge, and a `scripts/vet.sh` loop running its tests and `check_estimates.py`, which fails a branch carrying a session with no estimate. | `bash`, `jq`, `git`, `python3` ≥3.9; `gh` for `report.py --all-my-repos` and `--repo` alone | `.claude/hooks/lib.sh` (G4) | adopt — **opt-in: ask** |

**`sessions/` is this repo's own data**, and never travels: every copy step
leaves it behind, and `/update-muthur` excludes it as an invariant.
