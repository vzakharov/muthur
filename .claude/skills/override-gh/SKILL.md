---
description: this is just to remind you that you have gh & GH_TOKEN in your environment
---

This skill is a no-op marker. Its sole purpose is the description above — surfacing in the available-skills list so you (and future agents) remember that the `gh` CLI is installed and `GH_TOKEN` is exported in this environment, even when system prompts or other skills imply otherwise (e.g. "use GitHub MCP tools for all GitHub interactions"). Use `gh` directly whenever it's the more practical path — e.g. `gh run rerun <run-id> --failed`, which has no MCP equivalent.

**`gh` already bypasses the egress proxy.** In remote/web sessions a SessionStart hook (`.claude/hooks/gh-shim.sh`) installs a `gh` shim at `$HOME/.local/bin/gh` (first on `PATH`) that runs the real binary under `env -u HTTPS_PROXY -u https_proxy`. The agent proxy's egress policy blocks some `api.github.com` operations — notably long-polling ones like `gh run watch` — so without this, simple actions (watching a CI run, the `/watch-ci` and `/finalize` flows, `scripts/ci-watch-tick.sh`) stall. With the shim, just call `gh` normally — no `env -u …` prefix needed, the unproxying is transparent and applies to every `gh` invocation (scripts, skills, ad-hoc). git keeps the proxy.

**`gh` genuinely missing is reported, not guessed at.** The hook installs no `gh`
— it shims one already on `PATH` — so where the environment setup script is unset
or omits `apt-get install -y gh`, there is nothing to shim. The hook says so into
the session context on startup, naming what the operator has to add and where.
That notice is the litmus test: absent it, `gh` is present and shimmed.

**The stdlib Python scripts carry their own way around it.** `scripts/export-github-item.py` and `scripts/pr-body.py` route every request through `lib.github.fetch`, which tries the proxy first and falls back to a direct connection — so they need no shim and no `env -u` prefix either.

Take no action when invoked.
