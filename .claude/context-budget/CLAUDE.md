# The context budget hook

`hooks/post-tool-context-budget.sh` tells the agent when its session's context
crosses the warning line and 300k tokens (the pause), so work is left resumable
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
- **The warning line is priced**: the context past which a new session pays for
  itself within `CONTEXT_BUDGET_REQUESTS` (default 100) requests, against
  carrying on — computed by `hooks/priced_line.py` with the cold-cache guard's
  model (`.claude/costs/lib/restart.py`, whose home document is
  `.claude/cold-cache/CLAUDE.md`), a new session being costed from this one's
  own warm-up. The hook cannot know how much work is left, so the notice gives
  the break-even counts and the agent weighs them against the plan. The line is
  cached in `tmp/context-budget/<session_id>.line`, since a Python start-up on
  every tool call is the cost this bash hook exists to avoid; it is recomputed
  only while the warm-up is still an estimate. Without the ledger's lib, on an
  unpriced model, or with `CONTEXT_BUDGET_WARN` set, the line is a fixed 200k.
  The pause stays fixed: it guards a context-quality cliff no price captures.
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

`CONTEXT_BUDGET_WARN` and `CONTEXT_BUDGET_PAUSE` fix the two lines, in tokens,
and `CONTEXT_BUDGET_REQUESTS` moves the priced one — set them in `.claude/settings.local.json`'s `env` to tune without
editing a tracked file.
