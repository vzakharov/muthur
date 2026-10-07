> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Cache keepalive: a Stop hook that keeps an idle session's prompt cache warm

## Goal

An idle web session loses its one-hour prompt cache, and the next prompt pays a
full re-cache (≈ $1.5–6 on a 150–330k context). A wake shortly before expiry is a
cache read, ~40× cheaper. The operator asked for (`relay-1.md` and this session):

- no per-reply ritual for the agent — a hook arms itself;
- at most **5 wakes** per idle spell; the cache then lives ~55 min more, ~5.5 h
  of idle in all;
- the **5th wake writes an "incomplete relay"**: the relay summary is committed
  and the operator gets the `/relay take <branch>` line to start a fresh session
  from, but no successor is spawned. A branch nobody touched for six hours can
  wait; the summary makes picking it up again cheap.

A visible one-line reply per wake stays: the harness rejects a silent turn
(`relay-1.md` § 4), and the only silent route found (a mod's `$.model.fork`) is
out of scope for now.

## Mechanism (verified in the CLI binary, 2.1.292)

A `Stop` hook with `asyncRewake: true` runs in the background and, on exit 2,
wakes the model with its stderr as a system reminder. So:

1. **Stop** → `keepalive.py` reads the transcript (`lib.restart.read_history`:
   last main-chain response time and the TTL its cache writes used). Not 1h TTL →
   exit 0: a 5-minute cache cannot be bridged at a sane rate.
2. It kills the previous sleeper of this session (pid in
   `tmp/keepalive/<session_id>.json`) — a killed sleeper exits by signal, not 2,
   so it wakes nothing — records its own pid, and sleeps until
   `last response + TTL − 5 min`.
3. On waking it re-checks it is still the recorded sleeper, bumps `wakes`, and
   exits 2 with the instruction. Wakes 1–4: reply with one short line in the
   conversation's language, no tools. Wake 5: the incomplete relay (below).
   `wakes` already at 5 → it arms nothing.
4. **UserPromptSubmit** (same script) resets `wakes` to 0: an operator prompt
   ends the idle spell.

The wake turn's own `Stop` re-arms step 1, so nobody re-arms anything by hand.

`timeout` is set explicitly on the hook entry (well above an hour), in case the
CLI enforces hook timeouts on async hooks too.

## The incomplete relay

`.claude/skills/relay/SKILL.md` gains a body section (no description change, so
no staging): "**Without a successor**" — Steps 1–2 as written, skip Step 3, and
the report gives the `/relay take <branch>` line in a fence for the operator to
start a new session with. The wake-5 reminder points at that section rather than
restating it.

## Controls

- `CACHE_KEEPALIVE=off` in `.claude/settings.local.json`'s `env` disables it, as
  `COLD_CACHE_GUARD=off` does the guard.
- `CACHE_KEEPALIVE_WAKES` (default 5) and `CACHE_KEEPALIVE_LEAD` (seconds before
  expiry, default 300).
- `tmp/keepalive/period` — a testing knob: when present, its number of seconds
  replaces the computed sleep, so a live check takes minutes, not an hour. Env
  from settings is read at session start, which is why the knob is a file.

## Accepted costs

- A container restart kills the sleeper; the next operator prompt (or the next
  Stop) re-arms. Whether the CLI reports a lost async hook the way it reports a
  lost background task is unknown — the live check notes it if seen.
- Each wake is one visible line in the feed and two requests' worth of cost
  only if the reply is empty, so the instruction asks for one line, not silence.

## Files

- `.claude/keepalive/hooks/keepalive.py` — the hook (stdlib, reuses `lib.restart`).
- `.claude/keepalive/test_keepalive.py` — unit tests: TTL gate, arm/kill/replace,
  wake counting and cap, reset on prompt, off switch, period knob.
- `.claude/keepalive/CLAUDE.md` — nested, the contract (like `cold-cache/`).
- `.claude/settings.json` — `Stop` entry with `asyncRewake: true` and `timeout`;
  `UserPromptSubmit` entry. Not in the staged set (no prompt-prefix text).
- `.claude/skills/relay/SKILL.md` — the "Without a successor" section.
- `scripts/vet.sh` — add `keepalive` to the test glob.

## Verification

- `./scripts/vet.sh`.
- Live: with `tmp/keepalive/period` at 60, end a turn, see a wake land with one
  line and the next Stop re-arm; check the cache read in the transcript; force
  wake 5 with a lowered state count and see the incomplete relay. Remove the knob.

## DRY notes

- Transcript reading, TTL detection and the last response's time are
  `.claude/costs/lib/restart.py`'s `read_history`/`epoch`, reached by path as
  `cold_cache.py` does — no second parser.
- State under `tmp/<feature>/<session_id>` follows `cold-cache` and
  `context-budget`; not extracted into a shared helper, since each is a few lines
  and their schemas differ.
- The relay procedure stays in `/relay`; the hook's wake-5 text only points at
  its new section.
