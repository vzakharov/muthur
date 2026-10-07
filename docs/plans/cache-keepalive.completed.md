# Cache keepalive: a Stop hook that keeps an idle session's prompt cache warm

## Paused: redesign from an async Stop hook to a background watcher

**Why.** The Stop/`asyncRewake` design below shipped (7b8d1cd…5895be2) and woke
the session once in a live check, but overnight the container was reclaimed
7.5 min after the last turn (06:45:14 → SIGTERM 06:52:57, `/tmp/claude-code-*.diag.log`:
`session_activity_at_shutdown refcount 0`, `bg_tasks: {}`). An async hook does
not count as session activity; a background Bash task does (relay-1: two
55-min idles survived with one). The cold-cache guard caught the morning prompt.

**Done (uncommitted design, now committed as WIP).** `keepalive.py` rewritten:
- `keepalive.py watch <session_id> <transcript>` — the watcher, run as a
  background Bash task (`run_in_background`, `timeout: 7200000`, description
  starting `Cache keepalive`). Polls the transcript (mtime-cached) every 30 s,
  exits 0 at `last response + TTL − lead`, recording `wakes+1`, `fired: true`,
  `pid: None`. Self-exits at `LIFETIME` 7000 s (under the 2 h Bash cap). Skips
  firing when the cache already expired. `tmp/keepalive/period` knob kept.
- `UserPromptSubmit` hook: resets `wakes` unless the prompt carries `MARK`
  (a task notification and the restart notice carry the task description), and
  when no watcher is alive (`/proc/<pid>/cmdline`) adds context: start the
  watcher; or wake k: start it and reply ≤ 7 words; or last wake: relay without
  a successor, don't restart. The hook was already live in this session and
  emitted the "start the watcher" context correctly.
- Verified: a background task's completion notice carries only the exit code
  and the description, never stdout; `UserPromptSubmit` hooks fire on task
  notifications too.

**Done after the pause (relay-2's successor).**
1. The operator's condition (verbatim below) is the agent's call, not a
   mechanical predicate — operator picked it («первое, да») over a hook-side
   check of plan state and commit times, which runs at the turn's start and
   cannot see a reply that went only to chat. The hook asks the agent to start
   the watcher as the turn's last action unless the branch alone lets a fresh
   session continue, and to `TaskStop` a running one once that holds. Probed:
   `TaskStop` ends a task with no completion notice, so stopping wakes nothing.
2. `settings.json`'s `Stop` entry dropped; tests rewritten; `.claude/keepalive/CLAUDE.md`
   rewritten; CLAUDE.md's `run_in_background` exception staged.

3. PR body, title and squash proposal refreshed; `/polish` run (bd69b74, 61ca46f).
4. Live check: with the period knob at 60 s the first wake came a minute later;
   with the knob removed, wakes 2–5 came about 55 min apart (09:51, 10:46,
   11:41, 12:37 UTC), the container alive through four hours of idle, and the
   fifth relayed without a successor (relay-3).

**Left.** Nothing in the plan; the branch waits on `/finalize`.

Operator, on the condition: «давай так, запускать фоновую задачу только тогда,
когда сессия не в "готовом к запуску с новой сессии" состоянии, т.е. не на
границе лупа (типа /plan → /go, /go → finalize) и не с .paused. планом. Грубо
говоря, запускаем тогда, когда всей имеющейся в репе информации НЕ достаточно
для продолжения с новой сессии (пример: обсуждали, нигде не зафиксировали)»

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
