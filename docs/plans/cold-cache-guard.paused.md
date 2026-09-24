# Cold-cache guard

## Goal

When the operator comes back to a session whose prompt cache has expired, stop
their first message before it reaches the model and show what each way on costs
— carry on, `/compact`, or a new session — so the choice is made knowing the
price. A blocked prompt makes no API request, so the stop itself is free.

## What the session established

- **A `UserPromptSubmit` block works in the web client.** `{"decision":"block","reason":…}`
  renders a card with the reason, a **View details** toggle and an **Edit prompt**
  button that gives the text back. The reason is plain text; no buttons, no prompt
  rewriting, no way for a hook to run `/compact`.
- **`SessionStart` fires with `source: "resume"` in the web client** when the
  process is relaunched, and carries `seconds_since_last_response`,
  `context_tokens`, `prompt_cache_likely_expired` and `estimated_cache_write_usd`
  (logged 2026-09-23 20:17:53: 23161 s, 149773 tokens, true, $1.1982). Hooks that
  fire on resume leave no record in the transcript.
- **The cache can expire without a relaunch** — the container lives, the process
  never restarts, no `SessionStart`. So the transcript's last response time is a
  required second source, not a fallback nicety.
- **The expiry is partial.** The first request after the 6.4 h gap read 40.8k
  from cache and wrote 118k: the system prompt and tool prefix shared by every
  session in the environment stayed warm. `estimated_cache_write_usd` assumes a
  full rewrite, so it overstates by that share.
- **The math** is the calculator's (https://claude.ai/artifact/A1zp44j8eAMMewDHFvrSsk),
  including its assumption that a cold `/compact` bills the history as input (×1)
  rather than as a cache write.

## Behaviour

**`SessionStart`** (every source): on `resume`/`fork` with
`prompt_cache_likely_expired: true`, write `tmp/cold-cache/<session_id>.json`
holding the four fields and the time it was written. Any other start removes that
file, so a stale flag never outlives the relaunch that made it.

**`UserPromptSubmit`**: pass silently unless all of these hold —

1. The prompt does not start with `/` (so `/compact`, `/clear` and every other
   command go through) and does not contain the stop word `!pass`.
2. The cache is cold: the flag file exists, **or** the last main-chain response in
   the transcript is older than the session's TTL. The TTL is read off that
   session's own cache writes — any 1-hour write means 3600 s, otherwise 300 s.
3. This cold spell has not been blocked already. A block records the last
   response's `message.id` in `tmp/cold-cache/<session_id>.blocked`; the next
   prompt sees the same id and passes. A new response and a new gap re-arm it.
4. Re-caching as is would cost at least `COLD_CACHE_MIN_USD` (default `0.30`), so
   a small session is never nagged.

The block reason, one paragraph:

> Prompt cache expired — 6.4 h since the last response, 150k tokens to re-cache.
> Carry on: ≈$1.07 up front. /compact: ≈$1.15 up front, then 1.6¢ less per API
> request, so it pays for itself after ~5 requests. New session: ≈$1.17, 0.7¢ less
> per request. This message was not sent: run /compact first, or click Edit prompt
> and send it again to carry on (a message containing !pass always goes through).

**The numbers.** Context from the flag's `context_tokens`, else the last
response's input + cache read + cache write. Rates from `.claude/costs/prices.json`
for the last response's `(model, speed)`. The warm shared prefix and the session's
starting context from the transcript's **first** main-chain response (its cache
read, and its input + read + write). The estimates the transcript cannot give —
summary length 8k, kept after compact 15k, new-session ramp-up 60k over 10
requests — are constants at the top of the module, named as estimates. An
unpriced model drops the dollar figures and keeps the time and token counts; it
never lets the prompt through unannounced.

**`COLD_CACHE_GUARD=off`** in `.claude/settings.local.json`'s `env` disables both
halves, for an operator who wants neither.

## Layout

Mirrors `.claude/context-budget/`:

- `.claude/cold-cache/CLAUDE.md` — the non-obvious contracts: why two sources, why
  the prefix discount, the once-per-spell key, the stop word, the constants.
- `.claude/cold-cache/hooks/cold_cache.py` — one entrypoint for both events,
  dispatching on `hook_event_name`. Python, not bash + jq, because the dollar
  model and the price table are Python already.
- `.claude/cold-cache/test_cold_cache.py` — drives the hook as the harness does,
  payload on stdin and a transcript on disk.
- `.claude/settings.json` — the probe's two entries become this hook's two.
- `scripts/vet.sh` — the test loop's glob gains `cold-cache`.
- `.claude/skills/update-muthur/catalog.md` — a G9 group and an inventory row,
  as G8 has; opt-in, since it blocks prompts.
- `.claude/hooks/cache-guard-probe.py` — deleted.

## Steps

1. Promote `_is_response_record` and `_parse_response` in
   `.claude/costs/lib/pricing.py` to public names and update their callers.
2. Write the cost model as pure functions (`once` and `per_request` for each
   option, the pay-back in requests) with unit tests pinning the calculator's
   defaults: 174k context, 41k shared, 82k start → $1.07 / $1.15 / $1.17, pay-back
   5 requests.
3. Write the two event handlers and the block text; tests for each rule in
   § "Behaviour": warm passes, cold-by-flag blocks, cold-by-transcript blocks,
   second prompt passes, `/`-prompt and `!pass` pass, below threshold passes,
   unpriced model blocks without dollars, sidechain and `<synthetic>` records
   ignored, `COLD_CACHE_GUARD=off` passes.
4. Wire `settings.json`, `vet.sh`, the catalog; delete the probe.
5. Write `.claude/cold-cache/CLAUDE.md`.
6. Run `./scripts/vet.sh`.

## Priced context budget

The operator asked for this too: `.claude/context-budget/` warns at a fixed 200k
and pauses at 300k. It should warn at the point where carrying on starts costing
more than starting over, computed from the session's own numbers, using the same
cost model as the guard.

- **Starting over is costed from this session's own warm-up**, since a new
  session on the same task reads roughly what this one read before it started
  working. Warm-up = the context at the first write-shaped tool call (`Edit`,
  `Write`, `NotebookEdit`, or a Bash `git commit`), minus the starting context.
  This is a heuristic: the operator flagged the warm-up/work boundary as the
  open part, and the first write is the cheapest honest reading of "stopped
  looking, started producing". Fall back to `RAMP_UP` when no write has happened.
- **The hook cannot know how much work is left; the agent can.** So the notice
  gives the break-even count rather than a verdict: "a new session pays for
  itself after N more requests, /compact after M". The agent compares that with
  what the plan says is left, and states both numbers when it offers the choice.
  With a warm cache: new session once ≈ start write + warm-up write + warm-up
  reads; per request, `(start + warm-up) × read` against `context × read`.
  `/compact` once ≈ `context × read + summary × output + (start + kept) × write`.
- **When it fires:** once N drops below `CONTEXT_BUDGET_REQUESTS` (default 100
  — about two heavy operator messages' worth of work). The fixed pause at 300k
  stays as the backstop against a context-quality cliff that no price captures.
- **Shared code:** the cost model moves out of `cold_cache.py` into
  `.claude/costs/lib/` (e.g. `restart.py`), imported by both hooks. The
  context-budget hook becomes Python for its reading, or calls a Python helper
  from its bash; decide by which keeps the per-tool-call cost lowest — a Python
  start-up on every tool call is ~30 ms.

## Progress

Paused at ~282k context, on the operator's call: the remaining work is over 40
requests, which is past where a new session pays for itself.

Done:
- Plan published as draft PR #109; squash proposal posted and tracked in
  `docs/remove-before-merging/squash-message.md`.
- Step 1: `is_response_record` / `parse_response` public in
  `.claude/costs/lib/pricing.py`; ledger tests pass.
- Step 2 and most of step 3 in code: `.claude/cold-cache/hooks/cold_cache.py`
  (cost model, both event handlers, block text). Checked by hand against the
  calculator's defaults: $1.07 / $1.15 / $1.17, pay-back ~5 requests. Not run
  as a hook yet, not wired, no tests.

Left:
- Step 3's tests (`.claude/cold-cache/test_cold_cache.py`), including the
  pure-model pins above.
- Step 4: wire `settings.json` (replace the probe's two entries), add
  `cold-cache` to `scripts/vet.sh`'s test glob, catalog G9 group + row, delete
  `.claude/hooks/cache-guard-probe.py`.
- Step 5: `.claude/cold-cache/CLAUDE.md`.
- § "Priced context budget" above.
- Step 6 vet, then `/go` Step 3's `/polish`, `/pr` refresh.

## Open questions

1. **On by default in this repo?** Recommendation: yes — here the loop is the
   product, and this session is the evidence it is wanted. Adopters get it opt-in
   through the catalog.
2. **Threshold $0.30?** Recommendation: yes, and tunable through
   `COLD_CACHE_MIN_USD`. Below it the block costs the operator more attention than
   it saves money.

## DRY notes

- **Reused:** `.claude/costs/prices.json` and `lib/pricing.py`'s `parse_prices`,
  `rate_key` and response parsing (`Response`, its `Tally`). The rates live in
  one table; a second copy in the hook would drift on the next price change.
  Promoting the two private parsers to public is the cost of sharing them.
- **Not shared with `.claude/context-budget/`:** that hook reads the last
  response's context in bash + jq on every tool call, where a Python start-up per
  call is the cost it avoids. This hook runs once per prompt and needs the price
  table, so it reads the same numbers through the ledger's parser instead. Two
  readers of one quantity is the lesser evil against porting either hook to the
  other's language.
- **Not shared with the calculator page:** the page is a published artifact in
  JavaScript, outside the repo. The Python model is the source of truth; the page
  is an illustration of it.
- **`.claude/hooks/lib.sh`** is not used: it is a bash library, and this hook's
  guards (payload read, project root, missing transcript) are three lines of
  Python.
