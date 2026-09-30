# The cold-cache guard

`hooks/cold_cache.py` stops the first prompt after the session's prompt cache
expired and prices the ways on, because that prompt re-caches the whole
conversation and nothing else shows the price before it is paid. A blocked
prompt makes no API request, so the stop is free. It prices carrying on against
a fresh session with `.claude/costs/lib/restart.py`, the context budget hook's
model.

- **Two sources of "cold".** `SessionStart` on a resume carries
  `prompt_cache_likely_expired`, `context_tokens` and
  `seconds_since_last_response`; the hook keeps them in
  `tmp/cold-cache/<session_id>.json` until a response lands after them. But the
  cache also expires while the process lives on and no `SessionStart` fires, so
  the transcript's last main-chain response time, against the TTL the session's
  own cache writes used, is the second source rather than a fallback.
- **The expiry is partial.** The system prompt and tool prefix every session in
  the environment shares stays warm, so the first request after a gap reads it
  from cache. The transcript's first response gives its size (its cache read),
  and Claude Code's `estimated_cache_write_usd`, which assumes a full rewrite,
  is shown only when the model has no row in `prices.json`.
- **The way on it prices is a fresh session, not `/relay`.** A relay's summary
  turn is a request at the whole context, so on a cold cache it pays the same
  re-cache carrying on does; the two cancel, and what is left is the context
  budget's question, which that hook asks once the session goes on. Only a
  fresh session skips the re-cache, so the guard prices it — the reorientation
  up front, the smaller context on every request after — and offers it only for
  work that is already all on the branch, a call the operator makes. The hook
  cannot see a decision made in chat after the last step that wrote one down —
  a plan, a PR body, a commit — so the offer names that condition too.
  `.claude/context-budget/CLAUDE.md` carries where a reorientation's price comes
  from; for a fresh successor the sources are the fresh sessions', not the
  relayed ones'.
- **Once per cold spell.** A block writes the last response's id and the
  stopped prompt to `tmp/cold-cache/<session_id>.blocked`, and a prompt against
  the same id passes. A bare `!` then stands for the stopped prompt: a hook
  cannot rewrite the prompt it is given, so it passes `!` with context telling
  the model to act on the stored one verbatim. A new response and a new gap
  re-arm it.
- **What always passes:** `/compact`, `/clear` and its aliases, `/relay`, and
  every built-in command that makes no model request — `PASSES`, taken from
  code.claude.com/docs/en/commands. Skills and the built-ins that prompt the
  model (`/go`, `/btw`, `/init`, `/plan`) are prompts like any other. Also
  passing: a session whose re-cache costs under `COLD_CACHE_MIN_USD` (default
  `0.30`), where the stop costs more attention than it saves. An unpriced model
  is still stopped, with the times and token counts and no dollars.

`COLD_CACHE_GUARD=off` in `.claude/settings.local.json`'s `env` disables both
halves.
