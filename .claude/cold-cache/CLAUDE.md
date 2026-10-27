# The cold-cache guard

`hooks/cold_cache.py` stops the first prompt after the session's prompt cache
expired and prices the ways on, because that prompt re-caches the whole
conversation and nothing else shows the price before it is paid. A blocked
prompt makes no API request, so the stop is free. It prices carrying on against
a fresh session with `.claude/costs/lib/restart.py`, the context budget hook's
model.

- **Two sources of "cold".** `SessionStart` on a resume carries
  `prompt_cache_likely_expired`, `context_tokens` and
  `estimated_cache_write_usd`; the hook keeps the last two in
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
  budget's question, which that hook asks once the session goes on. Only a fresh
  session skips the re-cache, so the guard prices it as the context budget
  prices a relay, by what it saves over the next 100k tokens of work: the
  reorientation against the re-cache up front, the smaller context on every
  request after. The stop gives each way's total over that slice, never its
  parts, since an up-front cost beside a per-request gain reads as a
  contradiction; where the reorientation is the dearer part, it adds the work
  under which continuing stays cheaper. `.claude/context-budget/CLAUDE.md`
  carries where a reorientation's price comes from; for a fresh successor the
  sources are the fresh sessions', not the relayed ones'.
- **Once per cold spell.** A block writes the last response's id and the stopped
  prompt to `tmp/cold-cache/<session_id>.blocked`, and a prompt against the same
  id passes. A bare `!` then stands for the stopped prompt: a hook cannot
  rewrite the prompt it is given, so it passes `!` with context telling the
  model to act on the stored one verbatim. A new response and a new gap re-arm
  it.
- **Images ride along by path.** The event carries the prompt's text and never
  its attachments, but Claude Code has saved each one in the `images/` beside
  `scratchpad_dir` before the hook runs, blocked prompt or not. A block copies
  those newer than the last response to `tmp/cold-cache/<session_id>.images/`,
  since a restart can reuse a number, and `!`'s context names the copies for the
  model to `Read`.
- **What always passes:** `/compact`, `/clear` and its aliases, `/relay`, and
  every built-in command that makes no model request — `PASSES`, taken from
  code.claude.com/docs/en/commands. Skills and the built-ins that prompt the
  model (`/go`, `/btw`, `/init`, `/plan`) are prompts like any other. Also
  passing: a session whose re-cache costs under `MUTHUR_COLD_CACHE_MIN_USD`
  (default `0.30`), where the stop costs more attention than it saves; and one
  whose fresh session saves nothing over the next 100k, or less than
  `MUTHUR_COLD_CACHE_MARGIN` (default `0.10`) of the re-cache, where the stop
  has no real choice to offer. An unpriced model is still stopped, with the
  token count and, where a resume carried one, Claude Code's own estimate.

`MUTHUR_COLD_CACHE_GUARD=off` in `.claude/settings.local.json`'s `env` disables
both halves.
