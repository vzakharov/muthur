> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Elephant and pizza — two ways to split work across sessions

Work too big for one session is split one of two ways, chosen once, at plan review:

- **Elephant** — eaten in chunks, one chunk per session, in one PR. The plan is coarse steps plus one detailed "Next chunk"; each session does that chunk, rewrites the plan and pauses; the operator reviews, compacts or opens a new session, and `/go`es again. The default.
- **Pizza** — the existing carve into issues: slices that each ship as their own PR.

The chunk-level "plan or not" call is `/task`'s two questions asked of the next chunk, answered in that one section of the megaplan — no second tier of plan files. The pause is the operator's look.

## Steps

1. **`plan/SKILL.md` § "Carving a task into issues" → § "Splitting work across sessions".** One entry: the work does not fit one session (otherwise take it whole, as now). Pizza when any of: (a) the slices are self-contained enough to land on the trunk separately; (b) there is a boundary worth locking in before a riskier stretch; (c) part of the task is needed by other, unrelated work — existing (found read-only with `/propose-issue` Steps 1–2) or likely (named for the operator to weigh). The existing "do not carve because…" list and "seams are real, not invented" guard those three reasons. Elephant otherwise. The plan names its shape with a recommendation, so the choice is the operator's at review (`/task` Step 3 already stops there). "Only the next slice is spelled out in full; the rest stays coarse" is stated here once for both shapes. Pizza → load `carving.md`; elephant → load `elephant.md`.
2. **New `plan/elephant.md`.** The megaplan's shape: coarse steps with ticks, and a `## Next chunk` section detailed to whatever the chunk needs — a line, or a page with its own DRY notes. That section is what marks a plan as an elephant for `/go`. The plan is the current contract at every moment: each pause rewrites it to what is true now — ticks, reworded steps, the next chunk — with no progress diary and no departures log; how it got there is git history and PR review. A chunk leaves `vet` green, lands whole, and is sized to finish, `/polish` included, before the context-budget warning line (`CONTEXT_BUDGET_WARN`), one chunk per session.
3. **`plan/carving.md`.** Its opening "Only the next slice has to be manageable" paragraph becomes a pointer to step 1's statement; the pizza name appears where the carve is introduced.
4. **`go/SKILL.md` Step 1.** Resuming an elephant, ask `/task`'s questions of `## Next chunk` before building it. A fork there with no recommendation → write the question into the section, pause again (step 5's planned end, with nothing built), and ask; don't barrel through.
5. **`go/SKILL.md` Step 2.** Step 2 of an elephant builds the next chunk only. One pause procedure, two triggers:
   - **Planned chunk end** — rewrite `## Next chunk` to the following chunk first, while the context is alive; tick and reword the steps; then Step 3 (`/polish`) and Step 4 (`/pr`), leaving the plan `*.paused.md`. Stop there even with budget left: the pause exists for the operator's review, not to save tokens.
   - **Budget pause mid-chunk** — the chunk's remainder becomes `## Next chunk`, `git mv` to `*.paused.md`, commit, push, handoff block. No `/polish`: the next planned end's polish floor is the last `polish:` commit, so it covers the interrupted half.
   The existing "Stopping partway releases the plan" paragraph becomes this procedure's non-elephant case.
6. **`go/SKILL.md` Step 3.** For an elephant it runs at every chunk end, and the flip is to `*.paused.md` while steps remain; `*.completed.md` only after the last chunk.
7. **`go/SKILL.md` § "Do NOT".** "Leave it as the approved snapshot" contradicts CLAUDE.md § "Writing things down" ("keep them current as the work deviates") and the elephant's rewrite-at-every-pause. Reword to: don't edit the plan per code change; it changes when what it states stops being true, and at a pause.
8. **`task/SKILL.md` Step 3.** "The scope is itself the question" names choosing between elephant and pizza beside the carve.
9. **`.claude/context-budget/hooks/post-tool-context-budget.sh`.** "Judge whether the work is nearly done" names the current chunk as the work when the plan is an elephant; finishing it reaches step 5's planned end, which stops. Add a test assertion in `test_context_budget.py` that both notices say so.
10. **`handle/SKILL.md`.** Verify only: its plan lane already hands a `*.paused.md` to `/go` Step 1, which is right for an elephant. No edit expected.
11. **`update-muthur/catalog.md`.** The `/plan` row names `elephant.md` beside `carving.md` and says the call is whether work is beyond one session and which shape it takes; the G3 note on stripping `carving.md` stays as is.

No skill `description:` changes, so nothing needs staging; CLAUDE.md already says the right thing about plans and stays untouched.

## DRY notes

- **"Only the next slice in full" — shared.** Both shapes plan that way, so it moves from `carving.md` into `plan/SKILL.md`'s section, and both files point at it.
- **The pause procedure — one procedure, two triggers**, in `go/SKILL.md` Step 2. The budget hook keeps pointing at that section rather than restating what a pause does; `elephant.md` states the chunk's shape and sizing, never the pause mechanics.
- **The chunk's budget reuses the hook's line** (`CONTEXT_BUDGET_WARN`) rather than a number of its own, so tuning the hook tunes the chunk.
- **`/task`'s questions are cited, not copied**, in `go` Step 1: `task/SKILL.md` stays their one home.
- **Not extracted:** `elephant.md` and `carving.md` stay separate files rather than one "splitting" procedure — they share one principle and nothing else, and a plan loads only the one its shape needs.
