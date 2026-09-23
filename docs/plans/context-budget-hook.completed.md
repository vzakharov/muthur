# Context budget hook

## Task

A hook that watches how much context the session is carrying and tells the agent
twice:

- **At 200k tokens — a warning.** Get the work to a committed, pushed stopping
  point, tell the operator, and offer two ways on: `/compact` here, or a new
  session. The new-session offer is only real when a successor can resume: with a
  plan, that means it is paused with done and remaining work legible; with no
  plan, the offer is to write one retroactively ("done: …, left: …").
- **At 300k tokens — the pause.** Without asking: rewrite the plan's progress
  record and `git mv` it to `*.paused.md` — or create
  `docs/plans/<slug>.paused.md` when the work had no plan — commit, push, tell
  the operator, and end the turn with the `/go <branch>` handoff block.

**Either time, the agent's own judgment that the work is nearly done overrides
the stop.** The notice asks for the call to be made and stated in the report
("finishing — one commit left"), not skipped.

The hook is **opt-in and declinable**: no adoption route may wire it on without
the operator saying yes.

## Approach

### How the hook reads the number

- **Event: `PostToolUse`.** The threshold is crossed mid-turn, in the long
  autonomous stretches where there is no operator prompt for `UserPromptSubmit` to
  fire on. `PostToolUse` fires after every tool call and accepts
  `hookSpecificOutput.additionalContext`, which reaches the model before its next
  step.
- **The figure: the last main-chain assistant record's `usage`**, summed as
  `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`. That is
  what the last request sent, which is the context the session is carrying.
  Measured on this session: ~107k on the first few tool calls, so the baseline
  alone is half of the first threshold.
- **Read from the end.** `tac "$transcript" | grep -m1` for the last assistant
  record, then `jq` on that one line — a transcript runs to megabytes and the
  hook runs on every tool call.
- **Main chain only.** Records with `isSidechain: true` are skipped, and a
  payload that comes from inside a subagent is ignored outright: the notice is
  for the session that holds the plan, and a subagent pausing it would release a
  plan its parent is still working. *Verify during implementation* which payload
  field marks a subagent's tool call (`agent_id` is the expected one); if none
  does, the transcript-path check is the guard, since a subagent's records live in
  its own file.
- **Unreadable → silent.** No transcript, no `jq`, no usage record yet: exit 0
  with nothing, per the lib.sh contract. A missing notice costs a warning; a
  hook error on every tool call costs the session.

### Firing once per threshold

- State in `tmp/context-budget/<session_id>` — the highest level already
  announced (`warn` or `pause`). Gitignored `tmp/`, matching
  `tmp/session-images/`.
- A reading **below the warn threshold clears the state**, so a `/compact` (or
  auto-compact) re-arms both notices for the next climb.
- A reading that jumps straight past 300k fires only the pause notice.

### Thresholds

Constants at the top of the script, `WARN=200000` and `PAUSE=300000`, each
overridable by an env var (`CONTEXT_BUDGET_WARN`, `CONTEXT_BUDGET_PAUSE`) so an
operator tunes them in `.claude/settings.local.json` without editing a tracked
file. See question 3.

### Where the hook lives: `.claude/context-budget/`

One directory, like `.claude/costs/`, so the opt-in is one path in every place
that records it:

- `.claude/context-budget/hooks/post-tool-context-budget.sh` — the hook. Sources
  `.claude/hooks/lib.sh`.
- `.claude/context-budget/test_context_budget.py` — drives the hook as a
  subprocess over fixture transcripts: under warn → silent; crossing warn →
  warn notice once, silent on the next call; crossing pause → pause notice once;
  a reading back under warn re-arms; sidechain records ignored; missing
  transcript → silent, exit 0.
- `.claude/context-budget/CLAUDE.md` — only the non-obvious contracts: why
  `PostToolUse`, what the figure sums and why, the re-arm rule. (Loaded when the
  directory's files are touched, as `.claude/costs/CLAUDE.md` is.)

### What the notices say

The hook's text is short and points at one home for the procedure, the way
`plan-mode-notice.sh` points at `native-plan-mode.md`:

- **Warn:** the reading, then: judge whether the work is nearly done; if it is,
  finish and say so. Otherwise reach a clean commit, push, and tell the operator
  — offering `/compact` or a new session, and for the latter either pausing the
  plan or (no plan) writing one retroactively. Do not pause unasked at this
  level.
- **Pause:** the reading, then: same nearly-done override; otherwise pause now
  per § "Stopping partway releases the plan", tell the operator it was done and
  why, end the turn with the handoff block.

### The procedure's home: `/go` § "Stopping partway releases the plan"

Extend that section (`.claude/skills/go/SKILL.md:82`) rather than writing a new
page:

- Its trigger widens from "the operator asks you to stop" to also "the context
  budget notice's pause level".
- **Planless work gets a plan at pause time**: `docs/plans/<slug>.paused.md`
  written directly — the task as asked, what is done (with commits), what is left,
  and decisions a successor would otherwise re-litigate. No draft stage: the work
  is already underway on the operator's go-ahead, and `*.paused.md` is exactly the
  state `/go` Step 1 resumes from.
- CLAUDE.md § "Plan mode & questions in web sessions" names `*.paused.md` as
  "written by a session told to stop partway" — widen to "told to stop partway, or
  out of context budget".

### Opt-in: a catalog row asked like G7

- **`.claude/skills/update-muthur/catalog.md` gains § "G8 — Context budget"**:
  one row, `.claude/context-budget/`, disposition `adopt — **opt-in: ask**`,
  stating what it costs (a `PostToolUse` hook on every tool call; a notice that
  can end a turn with the plan paused) and what a yes and a no each change in the
  tree.
- **The three sites that ask G7 ask every `opt-in: ask` row instead**, so a third
  such row later needs no edit to them:
  - `ADOPTING.md` Step 2 ("One question is asked whatever the profile says") and
    the copy step beside it (line ~220);
  - `/detemplate` Step 1 — a fork carries it wired on, so a no deletes
    `.claude/context-budget/`, its `.claude/settings.json` entry and its vet loop;
  - `/update-muthur` § "An opt-in row is offered by its own path" (line ~267).
  Each records the answer in the watermark's `adopted` / `declined`, so it is
  asked once.
- **In this repo it is wired on**: `.claude/settings.json` gains a `PostToolUse`
  entry. The operator asking for it here is the yes. See question 2.
- `scripts/vet.sh` gains a loop over `.claude/context-budget/test_*.py`, keyed on
  the directory exactly as the costs loop is, and its header comment names it.

## Files

- new: `.claude/context-budget/hooks/post-tool-context-budget.sh`
- new: `.claude/context-budget/test_context_budget.py`
- new: `.claude/context-budget/CLAUDE.md`
- `.claude/hooks/lib.sh` — `emit_context` takes the event name
- `.claude/settings.json` — `PostToolUse` entry
- `.claude/skills/go/SKILL.md` — § "Stopping partway releases the plan"
- `CLAUDE.md` — the `*.paused.md` sentence
- `.claude/skills/update-muthur/catalog.md` — § "G8", plus the `lib.sh` and
  `settings.json` rows naming the new consumer
- `.claude/skills/update-muthur/SKILL.md`, `.claude/skills/detemplate/SKILL.md`,
  `ADOPTING.md` — ask every `opt-in: ask` row
- `scripts/vet.sh` — the test loop

## Steps

1. Spike in `tmp/`: confirm `PostToolUse` `additionalContext` reaches the model,
   and which payload field marks a subagent's call.
2. Generalise `emit_context` to take the event name; update its callers.
3. Write the hook and its test; wire `settings.json` and `vet.sh`.
4. Widen `/go` § "Stopping partway" and the CLAUDE.md sentence.
5. Add catalog § "G8"; generalise the three asking sites.
6. `./scripts/vet.sh`, then `/polish`.

## DRY notes

- **Shared:** `lib.sh` — payload read, `field`, `need_command`, `project_root`,
  and `emit_context` once it takes the event name. `emit_context`'s hardcoded
  `UserPromptSubmit` is the one thing standing between the new hook and reuse;
  parameterising it beats a second emitter.
- **Shared:** the pause procedure. The notice points at `/go` § "Stopping
  partway" instead of restating it, so operator-asked and budget-triggered pauses
  are one procedure with two triggers.
- **Shared:** the opt-in ask. The three sites stop naming G7 and read the
  catalog's `opt-in: ask` disposition, so the catalog row is the single place a
  row's cost and tree consequences are stated.
- **Not extracted:** the transcript read. `.claude/costs/lib/pricing.py` parses
  whole transcripts in Python, deduplicating by `message.id` to price every
  response; this hook needs the *last* record only, in bash, on every tool call.
  Sharing the parser would put a Python start-up and a full-file parse on each
  tool call to reuse logic this hook does not need.
- **Not extracted:** the directory layout mirrors `.claude/costs/` (hooks/,
  tests, CLAUDE.md) by convention only — two instances is not a pattern worth a
  framework.

## Open questions

1. **Opt-in shape.**
   a. *(recommended, in force above)* The G7 pattern: registration in
      `settings.json` is the switch; the catalog marks the row `opt-in: ask`;
      adoption, detemplate and sync each ask and record the answer. A fork
      carries it on until `/detemplate` asks — the same exposure the cost ledger
      already has.
   b. A runtime switch: the hook is registered everywhere but no-ops until an
      opt-in file exists (e.g. `.claude/context-budget/enabled`). Closes the fork
      window only if the file is also deleted by detemplate, so it adds a second
      switch without removing the first.
2. **On in this repo?**
   a. *(recommended, in force)* Yes — your asking for it is the consent here.
   b. Ship it wired off here too; muthur only carries it for adopters.
3. **Thresholds.**
   a. *(recommended, in force)* Constants with env overrides.
   b. Constants only; tuning is an edit to the script.
