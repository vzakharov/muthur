# Port the API-rate session cost ledger, opt-in for adopters

## Goal

Bring vzakharov/vovazakharov.com@d84f30a ("price each session at Claude API
rates", its PR #71) into muthur: every session is priced from its own transcript
at Claude API rates, and its row is committed to the branch by a `Stop` hook, so
the ledger reaches the trunk by the same merge as the work it paid for.

Two constraints from the operator:

- **Adopters opt in explicitly.** The adopter's agent asks the operator, never
  infers it — the ledger costs a commit and a push at the end of every turn, on
  every branch.
- **The catalog carries one row: `.claude/costs/`.** Not a row per script and
  hook.

The second shapes the layout: the whole feature lives under `.claude/costs/`, so
that one row is honest about what it covers.

## What the source commit is

| Piece | Source | Lines |
| --- | --- | --- |
| Rate table | `.claude/costs/prices.json` | 88 |
| Pricer (dedupe by `message.id`, `(model, speed)` rates, TTL-split cache writes, subagent files, unpriced pair throws) | `scripts/lib/session-cost.ts` | 366 |
| Session identity (opening prompt, PRs, URL, Claude Code's own total) | `scripts/lib/session-identity.ts` | 98 |
| Rollup by month/week/day/branch | `scripts/lib/cost-totals.ts` | 111 |
| CLI: write one row | `scripts/session-cost.ts` | 94 |
| CLI: report | `scripts/costs-report.ts` (`pnpm costs`) | 144 |
| Tests | `scripts/lib/*.test.ts` | 371 |
| `Stop` hook: price, commit, push, wait out the harness's git check | `.claude/hooks/stop-session-cost.sh` | 152 |
| `UserPromptSubmit` hook: ask the agent to name the session once | `.claude/hooks/prompt-session-name.sh` | 39 |
| Contract doc | `.claude/rules/costs.md` | 184 |
| Wiring | `.claude/settings.json` | +14 |

Nothing in the source has changed since that commit, so there is no later fix to
fold in.

## Approach

### 1. Port to stdlib Python, not TypeScript

The source runs under Node's type stripping with `zod`. Muthur has no stack —
`scripts/vet.sh` exits 0 for exactly that reason — and its tooling is bash plus
stdlib-only Python ≥3.9 (`scripts/export-github-item.py`,
`scripts/extract-session-images.py`, `scripts/pr-body.py`). Porting as TS would
give muthur a `package.json`, a lockfile and a Node pin, which makes it a repo
with a stack under `CLAUDE.md` § "Vetting", and would put Node + zod on the
requirement list of every adopter who says yes. Python is already on that list
for G2–G4.

"Validate at boundaries" still holds without zod: the transcript and the row are
parsed by small explicit functions that check each field's type and raise with
the record's line number, not read with `dict.get` and trusted. Rows are
dataclasses so the report reads them back through the same parse.

### 2. Layout: everything under `.claude/costs/`

```
.claude/costs/
  CLAUDE.md                 # the contract — what .claude/rules/costs.md is at the source
  prices.json               # copied verbatim
  sessions/<YYYY-MM>/<id>.json   # this repo's rows; never travels (§ 5)
  session_cost.py           # CLI: price one transcript, write its row  (session-cost.ts)
  report.py                 # CLI: totals by month/week/day/branch      (costs-report.ts)
  lib/pricing.py            # (lib/session-cost.ts)
  lib/identity.py           # (lib/session-identity.ts)
  lib/totals.py             # (lib/cost-totals.ts)
  test_pricing.py           # (lib/session-cost.test.ts), case for case
  test_totals.py            # (lib/cost-totals.test.ts), case for case
  hooks/stop-session-cost.sh
  hooks/prompt-session-name.sh
```

- **The contract doc is `.claude/costs/CLAUDE.md`, not a rule file.** Claude
  Code loads a nested `CLAUDE.md` the moment a session reads any file beneath
  it — checked in this repo, under `.claude/` specifically — so it keeps the
  rule's one advantage, reaching whoever edits the pricer or `prices.json`
  without their looking for it, while staying inside the directory. A rule would
  be a second path for the catalog row to name, and `.claude/rules/` ships empty
  on purpose, per its own README. Script and hook headers point at it, as the
  source's point at the rule.
- **Hooks sit under `.claude/costs/hooks/` and source `.claude/hooks/lib.sh`**
  (`read_payload`, `field`, `say`, `need_command`, `project_root`,
  `emit_context`). `lib.sh`'s header, which names only `UserPromptSubmit`
  hooks as its users, is widened to say the `Stop` hook sources it too.
- `node scripts/session-cost.ts` becomes `python3 .claude/costs/session_cost.py`
  everywhere, including the command `prompt-session-name.sh` hands the agent;
  `pnpm costs` becomes `python3 .claude/costs/report.py`.
- `write-atomic.ts` and `argv.ts` don't survive as modules: `argparse` replaces
  one, and the other is three lines (`tmp/` staging + `os.replace`) with one
  caller.
- The source's `TEMPORARY` wait log (appends to `tmp/harness-check-wait.log`
  whether the look ever caught the harness's check running) is **dropped**: muthur
  does not ship a temporary diagnostic. The contract doc says instead that whether the
  wait ever fires is unmeasured here.

### 3. Wire it on in muthur itself

`.claude/settings.json` gains the `Stop` entry and the `prompt-session-name.sh`
`UserPromptSubmit` entry, as at the source. Muthur's own sessions from then on
leave rows in `.claude/costs/sessions/`.

`scripts/vet.sh` gains one line running the tests when the directory exists:

```bash
costs="$(dirname "$0")/../.claude/costs"
[ ! -d "$costs" ] || python3 -m unittest discover -s "$costs" -p 'test_*.py' -q
```

It goes beside the three stack-agnostic lines, with a header paragraph like
theirs: an adopter who said yes keeps it through the vet rewrite, and one who
said no has no directory for it to find.

### 4. The catalog row, and the opt-in

A new group in `.claude/skills/update-muthur/catalog.md`, **G7 — Session cost
ledger**, with "Adopt when: **the operator says yes when asked** — never by
inference from the profile". One row:

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `.claude/costs/` | Price each session at Claude API rates from its transcript and commit its row to the branch at the end of every turn, so the ledger reaches the trunk with the work; `report.py` sums the rows by month, week, day and branch. **The cost, which is why it is asked:** a commit and a push per turn on every branch, extra CI runs where CI runs on push, and a `Stop` hook sharing the event with the harness's git check. Arrives with an empty `sessions/` and two `.claude/settings.json` entries to merge. | `bash`, `jq`, `git`, `python3` ≥3.9 | `.claude/hooks/lib.sh` (G4) | adopt — **opt-in: ask** |

The criteria live in that row and nowhere else; everything below points at it.

- **`ADOPTING.md` Step 2**, "What the repo cannot answer — ask": the cost ledger
  joins the list as the one question asked **whatever the profile says**, citing
  the row for what to tell the operator. Step 4's copy: on yes, copy
  `.claude/costs/` without `sessions/*` and merge the two settings entries; on no,
  record it in the watermark's `declined` so the sync never re-asks.
- **`/detemplate` Step 1** gets the same question in its numbered-prose list. A
  fork has the ledger wired on and carries muthur's own rows, so both answers
  change the tree: yes empties `sessions/`, no deletes `.claude/costs/`, its two
  settings entries and the vet line.
- **`/update-muthur` Step 4a** offers `.claude/costs/` the way it offers a new
  skill, even when a broader `adopted` entry (`.claude/`) already covers the path:
  an opt-in row is a question by its own path, never taken because a parent
  directory was.
- **`/spinoff` Step 2**: `.claude/costs/sessions/` never travels (it is the
  caller's ledger); the rest follows the caller's answer.

### 5. The source's rows never travel

`.claude/costs/sessions/` is the one path in the directory that is muthur's own
data. `/update-muthur` § "Two invariants" gets it as a third exclusion beside
the watermark: a sync that ported it would import this repo's spend into the
adopter's totals.

### 6. Where the ledger meets the loop

- **`/finalize` Step 7** names the branch head it verified, and the `Stop` hook
  commits a row after that turn ends. One sentence in Step 7: a later commit
  touching only `.claude/costs/sessions/` does not move the verified diff.
- **The last turn's row is lost on a merged PR** (`/finalize and merge` merges
  within the turn, the row lands after). That is the source's "last turn of a
  session" gap in a sharper form, and the contract doc's § "What the totals do not
  cover" says so.

### 7. A consequence at the source, noted not handled

vovazakharov.com adopted muthur, so its next `/update-muthur` will meet this
Python port beside its own TS one. Which it keeps is that repo's call, made in
that sync; nothing here changes it.

## Steps

1. Port `lib/pricing.py`, `lib/identity.py`, `lib/totals.py`, and the two test
   files case for case; get the tests green against the port.
2. Port `session_cost.py` and `report.py`; run `session_cost.py` against this
   session's own transcript (and its `subagents/`) and check the row against the
   `cost-state` total it records.
3. Port both hooks to `.claude/costs/hooks/`, calling `python3`; widen `lib.sh`'s
   header; wire `.claude/settings.json`.
4. Write `.claude/costs/CLAUDE.md` from the source's rule, rewritten for the
   Python paths and the dropped wait log.
5. Add the vet line and its header paragraph.
6. Catalog: G7 group and row, plus the groups table entry.
7. `ADOPTING.md` Step 2 and Step 4; `/detemplate` Step 1; `/update-muthur`
   § "Two invariants" and Step 4a; `/spinoff` Step 2; `/finalize` Step 7.
8. `./scripts/vet.sh` green, including `check-skill-catalog.sh`.

## DRY notes

- **Reused:** `.claude/hooks/lib.sh` for every hook primitive — nothing in the
  two hooks re-implements payload reading, diagnostics or the context JSON.
  `prices.json` copied verbatim.
- **Deliberately duplicated across repos:** the Python port duplicates the TS
  original at vovazakharov.com. One implementation in both would force a stack
  onto muthur (§ 1); the duplication is between repos, and the source's sync
  decides whether it persists.
- **Not extracted:** the transcript-reading here and in
  `scripts/extract-session-images.py` both walk the same JSONL, but for disjoint
  records (images in `user` content vs `usage` on responses). A shared reader
  would be a `for line in file: json.loads(line)` loop — nothing worth a module.
- **One home for the opt-in criteria:** the catalog row. `ADOPTING.md`,
  `/detemplate` and `/update-muthur` say "ask, citing the row" and don't restate
  the overhead.

## Open questions

Each has its recommendation already written into the plan above. The port's
language (stdlib Python, not TS) and muthur running the ledger itself are
settled.

2. **Home of the contract doc.**
   a. `.claude/rules/costs.md`, path-scoped as at the source, named in the row's "Pulls in";
   b. `.claude/costs/README.md`, reached only through the file headers' pointers;
   c. `.claude/costs/CLAUDE.md` *(recommended — auto-loads like the rule, stays inside the directory)*.
4. **The source's `TEMPORARY` wait log.**
   a. drop it *(recommended)*;
   b. port it as is, and remove later.
