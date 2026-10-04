# A human-hour estimate on every session's cost row

The cost ledger (`.claude/costs/`) knows what each session would have cost at API rates, and nothing about how much work that bought. A dollar figure alone cannot tell a hard week from a wasteful one. Pairing every row with an estimate of the work in **junior-hours** gives two numbers the ledger cannot produce today:

1. **API dollars per junior-hour** — what a unit of human work costs when an agent does it;
2. **its trend** — the same figure by week and by model, so "the model got nerfed" becomes a question the ledger answers: did the dollars per junior-hour go up for work of the same size?

The operator's ask, quoted: «За 1 человекочас должен приниматься час работы наиболее простой должности (типа джуна), соответственно 1 человекочас сениора должен стоить x сколько-то от джуна. должно быть также поле комментария -- почему такая оценка (комментарий по размеру не больше например одного твита). И количество, и комментарий должны иметь возможность меняться.»

## The unit

An estimate is **hours at a grade**, plus a comment of at most 280 characters saying why. `.claude/costs/grades.json` maps each grade to its multiplier against a junior hour:

| grade | × junior |
| --- | --- |
| `junior` | 1 |
| `middle` | 1.6 |
| `senior` | 2.5 |
| `staff` | 3.5 |

The grade is the one a team would hand **the whole task** to, and the hours are that person's. A row stores the raw hours and grade, never the junior-hours: `report.py` multiplies at read time, so retuning a multiplier re-rates the whole history at once and the trend stays comparable with itself.

**What the estimate measures is the task, not the session's struggle with it.** It goes up when the task turns out bigger — scope added, a difficulty no reasonable estimator would have foreseen — and never because the agent took wrong turns. A model that spends more on its own detours and books them as extra hours would hide exactly the regression the metric exists to show.

Every session gets one, a question-only session included: answering "what would it take to add X" is an hour of someone's research too.

## Where it lives

A row gains `estimates`: the list of revisions, oldest first, each `{at, hours, grade, comment}`. The last is the current estimate; the earlier ones are how it moved, which is what shows an estimate drifting from first guess to final.

- **`.claude/costs/estimate.py set <hours> <grade> <comment>`** appends a revision for the current session (`CLAUDE_CODE_SESSION_ID`) to `tmp/estimates/<session-id>.json`. Validation is at the boundary: hours ≥ 0, a grade `grades.json` names, a comment of 1–280 characters. `estimate.py show` prints the current one.
- **`session_cost.py` folds that file into the row** at every `Stop`, merged with the revisions the previous row already carries — a union keyed by `at`, sorted. The previous row is the carry-forward, the same way the unwritten-tail warnings are carried today, so a resumed session in a fresh container (empty `tmp/`) keeps its estimate.
- **`--session <id>` edits another session's committed row in place** — a relay successor correcting its predecessor, or the operator re-estimating after the fact. That is an ordinary change for the current session to commit. A row of a session still running would be rewritten at its next `Stop`, and the union keeps the edit, because it is merged rather than overwritten.

The Stop hook needs no change: the estimate rides in the row it already commits.

## When it is set and revised

A `UserPromptSubmit` hook, `.claude/costs/hooks/estimate-notice.sh`, prints one line on every prompt:

- **while the session has none** — the instruction: set one once the work's size is known, the unit, the comment limit, the command, and the "task, not struggle" rule;
- **once it has one** — the current estimate and comment, with "revise it if the scope changed".

The second form is what makes revision happen at all: scope creep arrives in an ordinary prompt, and nothing else would put the estimate back in front of the agent at that moment. Hook output is outside the staging set, so none of this touches `CLAUDE.md`.

**The relay moves the remainder.** `/relay` Step 1 revises this session's estimate down to the work actually done here, and Step 2's **State** section records both that figure and the remainder handed over, each with its grade. `/relay take` sets the successor's estimate to that remainder as its first act after reading the summary — so the two sessions add up to the job rather than each claiming the whole of it.

## The report

`report.py` gains a section, and `--json` the same data:

- **dollars per junior-hour by month and by ISO week**, over estimated rows only, each line with its sessions, junior-hours and spend;
- **the same by model** — a row's model is its costliest `byRate` key — so a change of model is not mistaken for a change in the model;
- **coverage**: how many rows carry no estimate, so a figure resting on a handful of sessions says so.

The section is a ratio of sums (total dollars over total junior-hours per bucket), not a mean of per-session ratios: one tiny session estimated at a few minutes would otherwise dominate the average.

## What this cannot tell apart

Stated in `.claude/costs/CLAUDE.md`'s new section, since getting it wrong misreads the trend:

- **The estimator is the model under measurement.** A model that changed may also estimate differently. The operator's corrections (`--session`) are the check, and the revisions list shows which figures a person touched.
- **Prompt and repo drift.** A heavier `CLAUDE.md` or a new mandatory pass raises the dollars per junior-hour with no change to the model.
- **Merged work only**, as the rest of the ledger: an abandoned branch's rows never reach the trunk.

## Steps

1. `grades.json`; `lib/estimate.py` — the revision dataclass, its parser through `lib/shape.py`'s readers, the merge, and the junior-hours conversion.
2. `lib/rows.py`: `estimates: List[Revision]` on `SessionCost`, defaulting empty, so existing rows parse unchanged.
3. `estimate.py` CLI (`set`, `show`, `--session`).
4. `session_cost.py`: read `tmp/estimates/<id>.json`, merge with the previous row's, write.
5. `hooks/estimate-notice.sh`, registered under `UserPromptSubmit` in `.claude/settings.json`.
6. `lib/totals.py` + `report.py`: the per-junior-hour section.
7. `/relay` body (Steps 1, 2 § State, `take`): the remainder hand-over. The `description:` is untouched, so no staging.
8. `.claude/costs/CLAUDE.md`: a § "Human-hour estimates" — the unit, "task not struggle", where it lives, what it cannot tell apart.
9. Tests beside the existing ones (`test_estimate.py`): validation, the merge and its carry-forward across a lost `tmp/`, `--session` on a committed row, the report's ratio-of-sums. `vet.sh` already globs `.claude/costs/test_*.py`.
10. Estimate this session itself, as the first row to carry one.

## DRY notes

- **Reused:** `lib/shape.py`'s `read_number` / `read_string` / `required` / `to_json` for the revision's parse and write; `lib/rows.py`'s `write_atomic`, `read_row` and `parse_session_cost` for `--session` edits; `session_cost.py`'s `previous()` for the carry-forward, which already exists for warnings; `hooks/lib.sh`'s `read_payload` / `need_command` / `emit_context` for the notice; `totals.py`'s month and ISO-week keying for the new section, rather than a second calendar.
- **Not shared, on purpose:** the per-junior-hour buckets are not `Bucket`s. `Bucket` sums spend; the new one is a ratio with a different denominator, and widening `Bucket` with an hours field would put a meaningless zero on every branch and operator line that never shows it.
- **No second copy of the rules.** The hook's text is the agent-facing home of the "when and how"; `.claude/costs/CLAUDE.md` carries the why and the limits, and points at the hook rather than restating it.

## Open questions (each with the plan already written to the recommendation)

1. **Multipliers** — (a, recommended) 1 / 1.6 / 2.5 / 3.5, a middle ground; (b) US salary ratios, ≈ 1 / 1.4 / 2 / 2.8; (c) RU/CIS market ratios, ≈ 1 / 2 / 3.5 / 4.5. Retroactive either way, so this is cheap to change later.
2. **The notice once an estimate exists** — (a, recommended) one line on every prompt with the current figure; (b) silent once set, relying on the agent to remember revisions.
3. **Grades per revision** — (a, recommended) one grade per revision, the one you'd hand the whole task to; (b) a breakdown (`2h senior + 4h junior`), more precise and more to argue about.
