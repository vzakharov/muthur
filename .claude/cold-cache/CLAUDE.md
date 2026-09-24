# The cold-cache guard

`hooks/cold_cache.py` stops the first prompt after the session's prompt cache
expired and prices the ways on, because that prompt re-caches the whole
conversation and nothing else shows the price before it is paid. A blocked
prompt makes no API request, so the stop is free. The model it prices with is
`.claude/costs/lib/restart.py`, shared with the context budget hook.

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
- **A new session costs what this one's warm-up cost**: every response up to the
  first write-shaped tool call (`Edit`, `Write`, `NotebookEdit`, a Bash `git
  commit`) or the first reply that ends a turn, priced as billed. That boundary
  is a heuristic for "stopped looking, started producing". Before it is reached,
  the `RAMP_UP*` constants estimate it, as `SUMMARY_OUT` and
  `KEPT_AFTER_COMPACT` estimate what the transcript cannot say about `/compact`.
  A cold `/compact` bills the history as input rather than as a cache write.
- **Once per cold spell.** A block writes the last response's id to
  `tmp/cold-cache/<session_id>.blocked`, and a prompt against the same id
  passes — so resending the refused prompt (Edit prompt, send) carries on. A new
  response and a new gap re-arm it.
- **What always passes:** a prompt starting with `/`, so `/compact` and every
  other command can run; a prompt containing `!pass`; a session whose re-cache
  costs under `COLD_CACHE_MIN_USD` (default `0.30`), where the stop costs more
  attention than it saves. An unpriced model is still stopped, with the times and
  token counts and no dollars.

`COLD_CACHE_GUARD=off` in `.claude/settings.local.json`'s `env` disables both
halves.
