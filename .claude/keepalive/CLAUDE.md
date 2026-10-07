# The cache keepalive

`hooks/keepalive.py` wakes an idle session shortly before its one-hour prompt
cache expires, because the next prompt after expiry re-caches the whole
conversation at about 40 times what a cache read costs.

- **A `Stop` hook with `asyncRewake`, so nothing re-arms it by hand.** It runs in
  the background after every turn, sleeps until `CACHE_KEEPALIVE_LEAD` seconds
  (default 300) before the cache expires, and exits 2: the harness hands its
  stderr to the model as a system reminder and the model answers it. The wake
  turn's own `Stop` arms the next one.
- **Every wake is one visible line.** The harness rejects a turn with no visible
  output and forces a second request, so the instruction asks for one line
  of at most seven words rather than silence.
- **One sleeper fires per idle spell step.** Each `Stop` and each operator
  prompt writes a fresh token to `tmp/keepalive/<session_id>.json`; a sleeper
  whose token was replaced exits 0 when it wakes. It is never killed, since an
  async hook dying by signal is the harness's to report.
- **`CACHE_KEEPALIVE_WAKES` (default 5) wakes per idle spell**, which an
  operator prompt resets. The last runs `/relay` without a successor
  (`@.claude/skills/relay/SKILL.md` § "Without a successor"): a branch idle for
  hours can wait, and the summary makes picking it up cheap. Nothing wakes the
  session after it.
- **Only a one-hour cache is kept**, read off the session's own cache writes by
  `.claude/costs/lib/restart.py`. A five-minute cache would take a wake every
  few minutes.
- **A container restart kills the sleeper**; the next turn's `Stop` arms again.
- **`tmp/keepalive/period`** holds a number of seconds that replaces the
  computed sleep, for a live check in minutes rather than an hour. Settings'
  `env` is read at session start, which is why this knob is a file.

`CACHE_KEEPALIVE=off` in `.claude/settings.local.json`'s `env` disables it.
