# The context budget hook

`hooks/post-tool-context-budget.sh` tells the agent when its session's context
crosses the warning line and the pause line, so work is left resumable
before a compact or a dead session takes the choice away. What the agent does on
each notice is `@.claude/skills/go/SKILL.md` § "Stopping partway releases the
plan".

- **`PostToolUse`, not `UserPromptSubmit`.** The lines are crossed mid-turn, in
  the long autonomous stretches where no operator prompt arrives to fire on.
  `PostToolUse` fires after every tool call and its `additionalContext` reaches
  the model before its next step.
- **The reading is what the last request sent**: the last main-chain assistant
  record's `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`.
  `output_tokens` is left out — the next request carries it, and the next
  reading counts it then.
- **Both lines are priced by what `/relay` saves over the next 100k tokens of
  work** (`finish`, the slice "nearly done" is measured in, so the saving is a
  floor whenever a notice fires): the warning where that saving reaches $0, the
  pause where it reaches `CONTEXT_BUDGET_PAUSE_SAVING` percent (default 20) of
  what carrying on costs. The model is `.claude/costs/lib/restart.py`, via
  `hooks/priced_line.py`, and the notice carries the dollars.
  - **Each is capped at its fixed line, 200k and 300k**, so pricing only ever
    moves a line earlier: context quality and the hard window are not cost
    questions.
  - **The requests a slice takes** are this session's own since its last
    boundary, per token of growth; the `REQUESTS_PER_TOKEN` estimate stands in
    until it has grown `MIN_GROWTH`.
  - **The successor's reorientation** is `.claude/costs/lib/orientation.py`'s
    measure — the ledger's definition of acting — from the first source that
    has one: this session's own, when `/relay take` opened it; the mean over the
    ledger's rows opened that way; this session's own orientation; the
    `RAMP_UP*` estimate. The notice names which.
  - **The lines are cached** in `tmp/context-budget/<session_id>.line` and
    recomputed per 10k of growth, since a Python start-up per tool call is what
    this bash hook avoids.
  - **Without the ledger's lib, on an unpriced model, or under
    `CONTEXT_BUDGET_LINES=fixed`**, the lines are 200k and 300k and the hook
    runs no Python.
- **The main chain only.** A tool call carrying `agent_id` is a subagent's and
  is skipped, as are `isSidechain` records and the `<synthetic>` placeholder
  Claude Code writes for a turn no model served — whose zeroed usage would read
  as a compact and re-arm the notices.
- **Each notice fires once per climb.** `tmp/context-budget/<session_id>` holds
  the highest level announced; a reading back under the warning line clears it,
  so a compact re-arms both. A notice that cannot be recorded is not sent, since
  it would otherwise repeat on every tool call.
- **Anything unreadable is silence**, never an error: a missing notice costs a
  warning, a hook failing on every tool call costs the session.

`CONTEXT_BUDGET_WARN` and `CONTEXT_BUDGET_PAUSE` each fix their line, in
tokens, `CONTEXT_BUDGET_PAUSE_SAVING` moves the priced pause, and
`CONTEXT_BUDGET_LINES=fixed` turns the pricing off — set them in
`.claude/settings.local.json`'s `env` to tune without editing a tracked file.
