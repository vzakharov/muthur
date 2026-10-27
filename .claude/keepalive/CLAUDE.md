# The cache keepalive

`hooks/keepalive.py` wakes an idle session shortly before its one-hour prompt
cache expires, because the next prompt after expiry re-caches the whole
conversation at 20 times what a cache read costs — 40 on a model whose read rate
is below the usual tenth of input (`.claude/costs/prices.json`).

- **The watcher is a background Bash task, the one exception to CLAUDE.md's ban
  on `run_in_background`.** The platform reclaims an idle container within
  minutes unless a background task is running; an async hook does not count.
  `keepalive.py watch` polls the transcript and exits
  `MUTHUR_CACHE_KEEPALIVE_LEAD` seconds (default 300) before the cache expires,
  and the task's completion notice is the wake.
- **It runs after every turn, because its last wake parks**: the summary keeps
  the session's last reply verbatim, which the operator answers more easily than
  they dig the same points out of files, and hands them a `/relay take` line to
  paste. The `UserPromptSubmit` hook asks the agent to start it as a turn's last
  action unless the operator asks to stop the keepalive. `TaskStop` ends a task
  without a completion notice, so stopping one wakes nothing.
- **Every wake is one visible line.** The harness rejects a turn with no visible
  output and forces a second request, so the instruction asks for one line
  rather than silence — and spends it on the two answers that end the spell, in
  plain words an operator types without knowing the loop: one parks the session
  (`/relay park`), one just stops. The hook maps both back.
- **`MUTHUR_CACHE_KEEPALIVE_RENEWALS` (default 0) renewals per idle spell**,
  which an operator prompt resets. The wake after the last one runs
  `/relay park` (`@.claude/skills/relay/SKILL.md`), and no watcher follows it —
  so by default the first wake parks. A renewal competes with that summary,
  which makes picking the work up cheap.
- **More than 5 renewals is not recommended.** A renewal is two requests (the
  Bash call starting the next watcher, then the line), each reading the whole
  cached conversation, so it costs 2 ÷ 20 = 10% of a cold re-cache, or 5% where
  the ratio is 40. Renewals the operator never comes back for are spent
  outright: 5 come to 25–50% of a cold re-cache, and 10–20 to all of it.
- **Only a one-hour cache is kept**, read off the session's own cache writes by
  `.claude/costs/lib/restart.py`. A five-minute cache would take a wake every
  few minutes.
- **`tmp/keepalive/period`** holds a number of seconds that replaces the
  computed deadline, for a live check in minutes rather than an hour. Settings'
  `env` is read at session start, which is why this knob is a file.

`MUTHUR_CACHE_KEEPALIVE=off` in `.claude/settings.local.json`'s `env` disables
it.
