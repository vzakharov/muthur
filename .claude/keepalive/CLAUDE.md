# The cache keepalive

`hooks/keepalive.py` wakes an idle session shortly before its one-hour prompt
cache expires, because the next prompt after expiry re-caches the whole
conversation at about 40 times what a cache read costs.

- **The watcher is a background Bash task, the one exception to CLAUDE.md's
  ban on `run_in_background`.** The platform reclaims an idle container within
  minutes unless a background task is running; an async hook does not count.
  `keepalive.py watch` polls the transcript and exits `CACHE_KEEPALIVE_LEAD`
  seconds (default 300) before the cache expires, and the task's completion
  notice is the wake.
- **It runs only while losing the session would lose something.** The
  `UserPromptSubmit` hook asks the agent to start it as a turn's last action,
  unless the branch alone lets a fresh session continue — the work at a loop
  boundary, nothing said since that the repo lacks — and to `TaskStop` a running
  one once that holds. Only the agent knows what the conversation holds that
  the branch does not. `TaskStop` ends a task without a completion notice, so
  stopping one wakes nothing.
- **Every wake is one visible line.** The harness rejects a turn with no visible
  output and forces a second request, so the instruction asks for one line
  of at most seven words rather than silence.
- **`CACHE_KEEPALIVE_WAKES` (default 5) wakes per idle spell**, which an
  operator prompt resets. The last runs `/relay` without a successor
  (`@.claude/skills/relay/SKILL.md` § "Without a successor"): a branch idle for
  hours can wait, and the summary makes picking it up cheap. No watcher follows it.
- **Only a one-hour cache is kept**, read off the session's own cache writes by
  `.claude/costs/lib/restart.py`. A five-minute cache would take a wake every
  few minutes.
- **`tmp/keepalive/period`** holds a number of seconds that replaces the
  computed deadline, for a live check in minutes rather than an hour. Settings'
  `env` is read at session start, which is why this knob is a file.

`CACHE_KEEPALIVE=off` in `.claude/settings.local.json`'s `env` disables it.
