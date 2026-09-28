> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Price `/relay` against carrying on, in both hooks

Follows `cold-cache-guard.completed.md` on the same branch. It answers the review on #109: T01–T04 and the operator's note that the budget notice was uninformative. T05 is #122.

## Why

- **Main offers one way on: `/relay`** (#113, #121). That leaves two options to price, carry on and relay, where the branch prices three. Comparing a new session against `/compact` told the operator nothing, because the new session won every time.
- **A payback count doesn't say how much is saved** (operator: «нужно мерить … НАСКОЛЬКО дешевле»). The measure below is dollars and a percentage over the work still to come.
- **Main's ledger already measures orientation** (`lib/orientation.py`, #112/#120). A successor started by `/relay take` *re-orients* from a summary, so its cost is a reorientation, not a fresh start. The branch has its own `ends_warm_up` definition of "started producing", which disagrees with main's definition of acting. Keep one.
- **The 300k pause stays fixed while the warning is priced**, and the operator wants the fixed 200k/300k lines kept behind a flag in case the pricing misreads (T03).
- The guard has two command rules to change. Every `/`-prompt passes today, including `/go`, `/handle` and `/finalize` (T02). And the operator wants a bare `!` to mean "send the stopped prompt again", in place of `!pass` (T01).

## The measure

**What relaying saves over the next slice of work**, where the slice is `finish` = 100k tokens of context growth. That is the size main's budget notice already uses for "nearly done". A session the notice asks to stop is, by that test, at least a slice from finishing, so the saving over one slice is a **floor** on what relaying saves.

Take C as the context now, W as the successor's context once reoriented, and K as the relay's up-front cost: the summary turn plus the successor's reorientation, priced as below. Take n as the requests the slice takes, which is the slice × this session's own requests per token of growth since its last boundary, and r as the cache-read rate. Then:

- saving = n·(C − W)·r − K
- relative saving = saving ÷ what carrying on costs over the slice

New context is written at the same rate under either option, so those writes cancel out of the saving but stay in the carry-on total.

**Worked example, on this session's own figures:** W ≈ 97k, reorientation ≈ $0.57, K ≈ $0.76, n ≈ 37 per 100k, r = $0.20/M. The saving crosses $0 at about **200k** and reaches about 20% at about **300k**. The fixed lines sit roughly where this pricing puts them. The notice now carries the dollars that justify them.

**Cheap cache reads keep the saving small.** A cache read costs 1/40 of a 1h write, so each request after a relay saves only about $0.006 at 126k. «Сразу дешевле» holds only well past 200k. The notice has to say so rather than imply a relay always pays.

## Steps

1. **Merge `main` into the branch.** Rebasing would need a force-push, and the house rules forbid one. Resolve the conflicts in `pricing.py` (main reworked it, and `restart.py` is re-pointed at its current API), `post-tool-context-budget.sh` (main's relay wording and `nearly_done()` stay the base), `settings.json`, `vet.sh` and `catalog.md`.
2. **`restart.py`: two options, one measure.**
   - Drop `/compact` and "new session" from `after_expiry` and `while_warm`, leaving carry on and relay.
   - A relay's up-front cost is the summary turn (a request at C, plus `SUMMARY_OUT` output) plus the successor's reorientation. On a cold cache the summary turn also pays the re-cache that carrying on pays.
   - Add `saving_over(slice)` for $ and %, and `line_for(threshold)` solving it for C.
   - Drop `payback`, `break_even_context` and `CONTEXT_BUDGET_REQUESTS`.
3. **Reorientation, from `lib/orientation.py`.** Delete `ends_warm_up` and `WRITE_TOOLS`, and read the orientation phase that main's `measure` computes. The successor's reorientation is priced from the first source available:
   1. this session's own orientation, when it began with `/relay take`, since it is the same kind of spend;
   2. the mean orientation of the ledger rows `.claude/costs/sessions/` records as relayed-into (#119 links the two; which field marks it is read off the rows when implementing);
   3. this session's own fresh orientation;
   4. the `RAMP_UP*` estimate.

   The notice names which source it used.
4. **Context budget lines.**
   - The warn line is where the saving over one slice reaches $0: a relay pays for itself before the work could be nearly done.
   - The pause line is where the saving reaches `CONTEXT_BUDGET_PAUSE_SAVING` (default 20%) of the slice.
   - Each line is capped at its fixed counterpart (200k/300k), so pricing can only move a line earlier. Context degradation and the hard window are not cost questions.
   - `CONTEXT_BUDGET_LINES=fixed` turns the pricing off: pure bash, no Python, main's behaviour. A hand-set `CONTEXT_BUDGET_WARN` or `CONTEXT_BUDGET_PAUSE` still fixes its own line.
   - The notice reads: "Relaying now costs ~$K up front and saves ~$X (~Y%) over the next 100k tokens of work, reorientation priced from <source>." The per-session line cache stays.
5. **The guard prices carry on against relay.**
   - Carry on is shown as the re-cache; relay adds its up-front cost and gives the same slice saving.
   - `/compact` still passes the guard (step 6) but is no longer priced.
6. **What passes the guard (T02).**
   - `/compact`, `/clear` (and `/reset` and `/new`), `/relay`, and every built-in command that makes no model request, as a constant listing the command names, sourced from https://code.claude.com/docs/en/commands. Re-read that page when implementing, since the list was taken from a model's summary of it.
   - Everything else starting with `/` is stopped like any prompt: skills (`/go`, `/handle`, `/finalize`) and model-driven built-ins (`/init`, `/plan`, `/code-review`, `/btw`).
   - Passing a command that never reaches `UserPromptSubmit` is a no-op, so the list can be exhaustive without first probing which commands arrive.
7. **Bare `!` (T01).**
   - A block also stores the stopped prompt's text in `tmp/cold-cache/<session>.blocked`.
   - A prompt that is exactly `!` passes with `additionalContext` telling the model to act on that stored prompt verbatim, because a hook cannot rewrite the prompt it is given.
   - `!pass` goes.
8. **Tests, docs, catalog.**
   - Pin the worked example's crossings and the four reorientation sources.
   - Add the command list's pass/stop cases, including `/go` stopped and `/context` passed.
   - Test `!` both with a stored prompt and with no block.
   - Test `CONTEXT_BUDGET_LINES=fixed`.
   - Update both `CLAUDE.md`s and the G8/G9 catalog rows, then run `./scripts/vet.sh`.

## DRY notes

- **"Acting" has one definition:** main's `lib/orientation.py`. The branch's `ends_warm_up` duplicates it with different rules (it counts a Bash `git commit`, and counts neither `AskUserQuestion` nor tmp exclusion), so it is deleted rather than reconciled.
- **Both hooks price with `restart.py`**, which means one `saving_over` and one relay cost. The guard's cold variant differs only in the summary turn's re-cache, which is an argument, not a second function.
- **The command list lives only in `cold_cache.py`.** No other hook needs it, and a shared module for one constant would be a home without a second caller.
- **The pause and warn lines share `line_for`**, with different thresholds. A second solver would drift.
- **`finish` (100k) is main's constant in bash.** The Python side reads it from the hook, which passes it as an argument, rather than restating the number.

## Open questions

1. **Slice size:**
   - a) 100k, main's `finish` *(recommended: it makes the saving a floor exactly when the notice fires)*.
   - b) Its own knob.
2. **Pause threshold:**
   - a) A 20% saving over the slice, capped at 300k *(recommended)*.
   - b) Keep 300k fixed and price only the warning.
3. **Should `/btw` pass?** It forks the conversation and reads the main context.
   - a) Stop it like any model request *(recommended)*.
   - b) Pass it.
