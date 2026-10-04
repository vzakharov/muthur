# A human-hour estimate on every session's cost row

The cost ledger (`.claude/costs/`) knows what each session would have cost at API rates, and nothing about how much work that bought. A dollar figure alone cannot tell a hard week from a wasteful one. Pairing every row with an estimate of the work in **junior-hours** gives two numbers the ledger cannot produce today:

1. **API dollars per junior-hour** — what a unit of human work costs when an agent does it;
2. **its trend** — the same figure by week and by model, so "the model got nerfed" becomes a question the ledger answers: did the dollars per junior-hour go up for work of the same size?

The operator's ask, quoted: «За 1 человекочас должен приниматься час работы наиболее простой должности (типа джуна), соответственно 1 человекочас сениора должен стоить x сколько-то от джуна. должно быть также поле комментария -- почему такая оценка (комментарий по размеру не больше например одного твита). И количество, и комментарий должны иметь возможность меняться.»

## The unit

An estimate is **a list of parts**, each the hours one **role** at one **grade** would spend on the task — "3 h senior developer + 2 h middle copywriter" — plus one comment of at most 280 characters saying why the task is that size. The parts add up to the session's figure. `.claude/costs/rates.json` holds two multiplier tables, and a part is worth hours × role × grade junior-hours:

| role | × | | grade | × |
| --- | --- | --- | --- | --- |
| `copywriter` | 1 | | `junior` | 1 |
| `editor` | 1.1 | | `middle` | 1.6 |
| `qa` | 1.2 | | `senior` | 2.5 |
| `designer` | 1.3 | | `staff` | 3.5 |
| `analyst` | 1.4 | | | |
| `developer` | 1.5 | | | |
| `architect` | 1.8 | | | |

A junior-hour is an hour of the role rated 1 at the lowest grade — the simplest position, per the ask. A role or grade the table does not name is refused, so adding one is an edit to the table, never a free-form string. A row stores the raw parts, never the junior-hours: `report.py` multiplies at read time, so retuning a multiplier re-rates the whole history at once and the trend stays comparable with itself.

**What the estimate measures is the task, not the session's struggle with it.** It goes up when the task turns out bigger — scope added, a difficulty no reasonable estimator would have foreseen — and never because the agent took wrong turns. A model that spends more on its own detours and books them as extra hours would hide exactly the regression the metric exists to show.

Every session gets one, a question-only session included: answering "what would it take to add X" is an hour of someone's research too.

## Where it lives

A row gains `estimate`: `{at, parts: [{hours, grade, role}], comment}`, or null. There is no revision list: a revision replaces the estimate whole, and the row's history in git is how it moved. The comment is held to `/tend-prose`'s rules like any other durable prose — it says why the task is this size as it stands, never how the figure got there.

- **`.claude/costs/estimate.py set <comment> --part <hours> <grade> <role> [--part …]`** writes the current session's (`CLAUDE_CODE_SESSION_ID`) estimate to `tmp/estimates/<session-id>.json`. Validation is at the boundary: at least one part, hours ≥ 0, a role and grade `rates.json` names, a comment of 1–280 characters. `estimate.py show` prints the current one.
- **`session_cost.py` folds that file into the row** at every `Stop`, against the estimate the previous row already carries: the one with the later `at` wins. The previous row is the carry-forward, the same way the unwritten-tail warnings are carried, so a resumed session in a fresh container (empty `tmp/`) keeps its estimate.
- **`--session <id>` edits another session's committed row in place** — a relay successor correcting its predecessor, or the operator re-estimating after the fact. That is an ordinary change for the current session to commit. A row of a session still running keeps the edit through its next `Stop`, since the edit is later than the pending file; the session's own next `set` is later still, and overrides it.

The Stop hook needs no change: the estimate rides in the row it already commits.

## When it is set and revised

A `UserPromptSubmit` hook, `.claude/costs/hooks/estimate-notice.sh`, prints one line on every prompt:

- **while the session has none** — the instruction: set one once the work's size is known, the unit, the comment limit, the command, and the "task, not struggle" rule;
- **once it has one** — the current estimate and comment, with "revise it if the scope changed".

The second form is what makes revision happen at all: scope creep arrives in an ordinary prompt, and nothing else would put the estimate back in front of the agent at that moment. Hook output is outside the staging set, so none of this touches `CLAUDE.md`.

**The relay moves the remainder.** `/relay` Step 1 revises this session's estimate down to the work actually done here, and Step 2's **State** section records both that figure and the remainder handed over, each as its parts. `/relay take` sets the successor's estimate to that remainder as its first act after reading the summary — so the two sessions add up to the job rather than each claiming the whole of it.

## The report

`report.py` gains a section, and `--json` the same data:

- **dollars per junior-hour by month, ISO week and day** — at 10–15 sessions a day, a day is enough to read — over estimated rows only, each line with its sessions, junior-hours and spend;
- **the same by model** — a row's model is its costliest `byRate` key — so a change of model is not mistaken for a change in the model;
- **coverage**: how many rows carry no estimate, so a figure resting on a handful of sessions says so.

The section is a ratio of sums (total dollars over total junior-hours per bucket), not a mean of per-session ratios: one tiny session estimated at a few minutes would otherwise dominate the average.

## What this cannot tell apart

Stated in `.claude/costs/CLAUDE.md`'s new section, since getting it wrong misreads the trend:

- **The estimator is the model under measurement.** A model that changed may also estimate differently. The operator's corrections (`--session`) are the check, and the row's git history shows which figures a person touched.
- **Prompt and repo drift.** A heavier `CLAUDE.md` or a new mandatory pass raises the dollars per junior-hour with no change to the model.
- **Merged work only**, as the rest of the ledger: an abandoned branch's rows never reach the trunk.

## Steps

1. `rates.json`; `lib/estimate.py` — the estimate and part dataclasses, the parser through `lib/shape.py`'s readers, the later-wins pick, and the junior-hours conversion.
2. `lib/rows.py`: `estimate: Optional[Estimate]` on `SessionCost`, defaulting null, so existing rows parse unchanged.
3. `estimate.py` CLI (`set` with repeated `--part`, `show`, `--session`).
4. `session_cost.py`: read `tmp/estimates/<id>.json`, keep whichever of it and the previous row's is later, write.
5. `hooks/estimate-notice.sh`, registered under `UserPromptSubmit` in `.claude/settings.json`.
6. `lib/totals.py` + `report.py`: the per-junior-hour section.
7. `/relay` body (Steps 1, 2 § State, `take`): the remainder hand-over. The `description:` is untouched, so no staging.
8. `.claude/costs/CLAUDE.md`: a § "Human-hour estimates" — the unit, "task not struggle", where it lives, what it cannot tell apart.
9. Tests beside the existing ones (`test_estimate.py`): validation, the later-wins pick, a multi-part `set`, `--session` on a committed row, the report's ratio-of-sums and its day buckets. `vet.sh` already globs `.claude/costs/test_*.py`.
10. Estimate this session itself, as the first row to carry one.

## DRY notes

- **Reused:** `lib/shape.py`'s `read_number` / `read_string` / `read_object` / `required` / `to_json` for the estimate's parse and write; `lib/rows.py`'s `write_atomic`, `read_row` and `parse_session_cost` for `--session` edits; `session_cost.py`'s `previous()` for the carry-forward, which already exists for warnings; `hooks/lib.sh`'s `read_payload` / `need_command` / `emit_context` for the notice; `totals.py`'s month, ISO-week and day keying for the new section, rather than a second calendar. Roles and grades share one multiplier check in `lib/estimate.py` rather than two copies.
- **Not shared, on purpose:** the per-junior-hour buckets are not `Bucket`s. `Bucket` sums spend; the new one is a ratio with a different denominator, and widening `Bucket` with an hours field would put a meaningless zero on every branch and operator line that never shows it.
- **No second copy of the rules.** The hook's text is the agent-facing home of the "when and how"; `.claude/costs/CLAUDE.md` carries the why and the limits, and points at the hook rather than restating it.

## Open questions (each with the plan already written to the recommendation)

1. **Grade multipliers** — (a, recommended) 1 / 1.6 / 2.5 / 3.5, a middle ground; (b) US salary ratios, ≈ 1 / 1.4 / 2 / 2.8; (c) RU/CIS market ratios, ≈ 1 / 2 / 3.5 / 4.5. Retroactive either way, so this is cheap to change later.
2. **The notice once an estimate exists** — (a, recommended) one line on every prompt with the current figure; (b) silent once set, relying on the agent to remember revisions.
3. **How roles combine with grades** — (a, recommended) two independent tables, a part worth role × grade, so a new role is one line; (b) one rate per role-and-grade pair, more exact and a table that grows as roles × grades.
4. **Role multipliers** — the table above is a first guess at market ratios with the cheapest role at 1; retroactive like the grades.
5. **A part's own label** — (a, recommended) none: one comment for the whole estimate, and a part is told apart by its role and grade; (b) a short `for` per part ("for the migration"), clearer on what changed and a second string to keep durable.
