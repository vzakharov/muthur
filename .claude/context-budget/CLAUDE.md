# The context budget hook

`hooks/post-tool-context-budget.sh` tells the agent when its session's context
crosses the warning line and the pause line, so work is left resumable before a
compact or a dead session takes the choice away. The warning gives the work the
room up to the pause line, to finish in or to steer to a good stopping point and
pause there; the pause line is where that estimate missed, so it stops the work
where it stands, a last step aside. What the agent does on each notice is
`@.claude/skills/go/SKILL.md` § "Stopping partway releases the plan".

- **`PostToolUse`, not `UserPromptSubmit`.** The lines are crossed mid-turn, in
  the long autonomous stretches where no operator prompt arrives to fire on.
  `PostToolUse` fires after every tool call and its `additionalContext` reaches
  the model before its next step.
- **The reading is what the last request sent**: the last main-chain assistant
  record's
  `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`.
  `output_tokens` is left out — the next request carries it, and the next
  reading counts it then.
- **Both lines are priced by what `/relay` saves over the next 100k tokens of
  work** (the model's `SLICE`, shared with the cold-cache stop): the warning
  where that saving reaches `MUTHUR_CONTEXT_BUDGET_WARN_SAVING_USD` dollars
  (default 0.20), the pause where it reaches
  `MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD` (default 0.80). The model is
  `.claude/costs/lib/restart.py`, via `hooks/priced_line.py`, and the notice
  carries the dollars.
  - **The thresholds are dollars, not shares of what carrying on costs.** A
    handoff costs the same friction whatever the model charges — the summary's
    loss of detail, the operator's reading of one more — so what repays it is an
    absolute saving. A share would shrink with the model's price: on Haiku,
    whose cache reads cost a twentieth of Opus's, a handoff would pass for worth
    it at a fraction of a cent. The pricing says what a relay saves; whether it
    is worth a handoff is the threshold's call, which no measurement settles.
  - **The defaults are set on Opus and Sonnet.** Over the ledger's `/relay take`
    sessions a relay costs $0.4–1.8 up front and a slice $2–4. On a median
    session $0.20 puts the warning ~20k tokens past break-even, leaving ~75k of
    room before the pause at $0.80 — enough to finish a step and reach a
    stopping point.
  - **Each is capped at its fixed line, 300k and 400k**, so pricing only ever
    moves a line earlier: context quality and the hard window are not cost
    questions. The notice says which set the line it reports, since dollars
    beside a cap read as a case for relaying where carrying on is cheaper.
  - **The requests a slice takes** are this session's own since its last
    boundary, per token of growth; the `REQUESTS_PER_TOKEN` estimate stands in
    until it has grown `MIN_GROWTH`.
  - **The successor's reorientation** is `.claude/costs/lib/orientation.py`'s
    measure — the ledger's definition of acting — from the first source that has
    one: this session's own, when `/relay take` opened it; the mean over the
    ledger's rows opened that way; this session's own orientation; the
    `RAMP_UP*` estimate. The notice names which.
  - **The lines are cached** in `tmp/context-budget/<session_id>.line` and
    recomputed per 10k of growth, since a Python start-up per tool call is what
    this bash hook avoids.
  - **Without the ledger's lib, on an unpriced model, or under
    `MUTHUR_CONTEXT_BUDGET_LINES=fixed`**, the lines are those caps and the hook
    runs no Python.
- **The main chain only.** A tool call carrying `agent_id` is a subagent's and
  is skipped, as are `isSidechain` records and the `<synthetic>` placeholder
  Claude Code writes for a turn no model served — whose zeroed usage would read
  as a compact and re-arm the notices.
- **Each notice fires once per climb.** `tmp/context-budget/<session_id>` holds
  the highest level announced; a reading back under the warning line clears it,
  so a compact re-arms both. A notice that cannot be recorded is not sent, since
  it would otherwise repeat on every tool call.
- **The operator is resolved only when a notice is about to fire**, with
  `gh api user`, since it costs a network call and the ordinary tool call has no
  use for it — and not at all once `MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY` has
  settled how the pause ends. A `gh` that cannot answer, or a token that is not
  a `User`'s, has no operator file to read and leaves the default.
- **Anything unreadable is silence**, never an error: a missing notice costs a
  warning, a hook failing on every tool call costs the session.

`MUTHUR_CONTEXT_BUDGET_WARN` and `MUTHUR_CONTEXT_BUDGET_PAUSE` each fix their
line, in tokens, `MUTHUR_CONTEXT_BUDGET_WARN_SAVING_USD` and
`MUTHUR_CONTEXT_BUDGET_PAUSE_SAVING_USD` move the priced ones (the warning's
under the pause's), and `MUTHUR_CONTEXT_BUDGET_LINES=fixed` turns the pricing
off — set them in `.claude/settings.local.json`'s `env`, or on the web among the
cloud environment's variables, to tune without editing a tracked file.

## Manual relay

Either pause ends in `/relay`, run unasked and with no argument, and the relay's
report says the session relayed on its own. Either of two switches set to `true`
makes the pause end the turn offering the relay instead:

- **`MUTHUR_MANUAL_CONTEXT_BUDGET_RELAY`, for an environment**, set where the
  variables above are — on the web, the dialog that also holds the setup script.
  It is the switch for launches nobody reopens, whose successor would be a
  session nobody finds, and the only one for a session with no operator to
  resolve.
- **`manual-relay/<handle>`, for an operator**, the handle being the one
  `.claude/hooks/operator-voice.sh` resolves — the lowercased login of the
  session's `User`-type GitHub token.
  - **The relay's report asks for it, once.** While the operator's file holds
    neither a yes nor a no, the notice has the report offer it in plain words —
    "if you'd rather I ask before relaying, say so" — naming no file: the
    operator's part is the answer, never an edit. With no operator resolved
    there is nowhere to keep an answer, and nothing is offered.
  - **Only the operator's own words write it, a no included**, whenever they say
    it and in whichever session hears it, the relayed one or its successor:
    write `true` or `false`, commit it with their words quoted, and push,
    merging first if the other session pushed meanwhile. A later change of mind
    rewrites the file the same way.
  - **It applies wherever the tree carries it**: on this branch from the next
    notice, and on every branch once it reaches the default branch. Say so when
    you write it, since the operator's next session may start from a base that
    does not have it yet.

`yes`, `on` and `1` count as `true`; any other value leaves the default.
