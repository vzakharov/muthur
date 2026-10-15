> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Hooks in sessions with several repositories

## Cause

When a cloud session has several repositories attached, Claude Code starts in
their common parent (`/home/user`) and reads project hooks only from that
directory's `.claude/settings.json` — which does not exist. Each attached repo
contributes its `CLAUDE.md`, rules and skills, but from its `settings.json` only
`enabledPlugins` and `extraKnownMarketplaces`. This is documented
([settings § Settings in cloud sessions](https://code.claude.com/docs/en/settings#settings-in-cloud-sessions)):
_"a session with several repositories starts above the clones and reads only the
`enabledPlugins` and `extraKnownMarketplaces` keys from each repository's
`.claude/settings.json`, not permission rules, hooks, `env`, or other keys."_

So **none** of muthur's ~20 hooks run in such a session. Observed in the session
that wrote this plan (muthur + vovazakharov.com + life):

- no `~/.local/bin/gh` — the shim was never installed, and `gh pr list` through
  the proxy fails with
  `HTTP 403: GitHub GraphQL is not available from Claude Code sessions`;
- `operator-voice.sh` printed no operator entry, so no greeting by name;
- `install-deps.sh` never ran — `vovazakharov.com` has no `node_modules`;
- `format-md.sh` does not wrap edited `.md`, so vet fails on wrapping later;
- no cost rows, cold-cache, keepalive, `permission-denied-phrase`, `#N` export
  or `muthur-sync` nudge.

## Verified by hand in that session

- **A hook written into `/home/user/.claude/settings.json` mid-session fires on
  the next tool call** (the settings watcher), with
  `CLAUDE_PROJECT_DIR=/home/user`. A generated file in the parent therefore
  turns hooks on without a restart.
- **A hook in `~/.claude/settings.json` (user level) fires too**, although the
  docs say cloud sessions do not read that file. The environment setup script
  already writes `autoMode` there, and the classifier sees it.
- The shim's unproxied path (`env -u HTTPS_PROXY gh …`) still works, although
  the proxy now answers GraphQL with new wording.
- Every hook locates its repo through `$CLAUDE_PROJECT_DIR` (falling back to the
  payload's `cwd`), so running a hook with `CLAUDE_PROJECT_DIR=<repo>` gives it
  the environment it has in a single-repo session.

## Approach

### 1. `scripts/multi-repo-hooks.py` — the generator

Stdlib Python, like muthur's other scripts. Runs from any attached repo:

1. **Detects the mode.** The session root is `$CLAUDE_PROJECT_DIR` when set,
   else the parent of the repo the script lives in. A root that is itself a git
   work tree is a single-repo session: exit silently, hooks already run there.
2. **Collects the hooks** from `.claude/settings.json` of every child git repo.
   Each command becomes `CLAUDE_PROJECT_DIR=<repo> <command, path substituted>`,
   matchers and timeouts kept.
3. **Sorts them into per-repo, once, or skipped** (§ 2) and writes
   `<root>/.claude/settings.json` whole. The file is generated, outside every
   repo, and lives until the container is rebuilt. A file there the generator
   did not write (no marker key it recognizes) is refused with an explanation,
   never overwritten.
4. **Runs the collected `SessionStart` hooks now** (matcher `startup`) and
   prints their stdout: the start event has already passed, and the settings
   watcher only catches future events. The agent reads that output as context —
   the operator entry and the shim's notice included.

A rerun is idempotent: the file is regenerated, the shim rewritten,
`install-deps` re-syncs what is already in sync.

### 2. Which hook runs where

The rule is a short list in the generator, keyed by the command's repo-relative
path; anything not listed runs once.

- **Per repo** — hooks whose effect belongs to their own repo, or that filter on
  `CLAUDE_PROJECT_DIR` themselves so exactly one copy acts:
  - `install-deps.sh` — each repo's dependencies;
  - `muthur-sync.sh nudge` — each repo has its own watermark;
  - `format-md.sh`, `file-tools-nudge.py` — check that the path is inside their
    root;
  - the cost family (`stop-session-cost.sh`, `start-telemetry-receiver.sh`,
    `estimate-notice.sh`, `post-tool-context-budget.sh`) — a cost row lands in
    every repo, and is committed only where the session commits work. The
    accepted cost: each repo's row carries the whole session's cost, so a sum
    across repos counts a shared session more than once.
- **Once** — session-wide, from the alphabetically first repo carrying the hook
  (the copies are synced from muthur, so which copy runs does not matter):
  `gh-shim.sh`, `operator-voice.sh`, `cold_cache.py`, `keepalive.py`,
  `plan-mode-notice.sh`, `session-images.sh`, `prompt-route-notice.sh`,
  `permission-denied-phrase.sh`.
- **Skipped** — `prompt-issue-export.sh` and `prompt-handle-pr-export.sh`: a
  `#12` in the prompt does not say which repo the thread is in, and running it
  in each would export three different threads. `/take-issue` stays the
  mandatory path (CLAUDE.md already has `/task`, `/plan` and `/go` run it); the
  hook is only an accelerator.

### 3. What runs the generator

- **The environment setup script** (automatic, survives a container rebuild):
  merges into `~/.claude/settings.json` a user-level `SessionStart` hook that
  finds `"$CLAUDE_PROJECT_DIR"/*/scripts/multi-repo-hooks.py` and runs the first
  match. In a single-repo session the generator exits at step 1. The agent
  cannot edit that script, so the report hands the operator the block, and the
  worked example in `docs/adopting/web-remote.md` gains it.
- **A line in `CLAUDE.md`** (the fallback for environments without the block):
  when the session's working directory is above this repo and `~/.local/bin/gh`
  is absent, this repo's hooks are not loaded — run
  `<repo>/scripts/multi-repo-hooks.py` as the first command. `CLAUDE.md` loads
  from every attached repo, so the line is in force exactly where the hooks are
  not. The edit goes through `scripts/staged.sh stage`.

### 4. Docs and inventory

- `docs/adopting/web-remote.md`: the block in the setup-script example, and a
  multi-repo paragraph under "Known gaps".
- An entry for the script in
  `.claude/skills/update-muthur/catalog/g4-remote-plumbing.md`, beside the shim.
- `scripts/test_multi_repo_hooks.py`: path substitution, the
  per-repo/once/skipped sort, the silent exit in a single-repo session, the
  refusal to overwrite a foreign file. `vet.sh` runs it with the others.

## Out of scope — proposed as separate issues

- **Same-named skills collapse into one.** In a multi-repo session the skill
  listing has one entry per name across all repos: muthur's `/finalize` may run
  over `life`, and muthur's `/release`/`/hotfix` stubs show up although
  vovazakharov.com declined them. Claude Code does not document which copy wins.
- **`/take-issue`, `/pr`, `/finalize` in a multi-repo session** treat the repo
  holding `cwd` as the current one. That works as long as the agent `cd`s, but
  nothing says so.

## Open questions

1. **What runs the generator?**
   - a) **Both: the setup script plus the CLAUDE.md line** (recommended) —
     automatic once the operator adds the block, a manual fallback until then.
   - b) The CLAUDE.md line only — needs nothing from the operator, but rests on
     the agent noticing it, and does not rerun by itself after a container
     rebuild.
   - c) The setup script only — reliable, but without it a multi-repo session
     silently stays hookless.
2. **Cost rows in a multi-repo session:**
   - a) **A row in every repo, committed only where work was** (recommended) —
     no new logic; the price is double counting in a cross-repo sum.
   - b) One repo only — needs a way to decide which is "primary", a notion
     hosted multi-repo sessions do not have.

The plan is written with the recommendations in force.

## DRY notes

- **Each repo's `settings.json` stays the one source of hooks.** The generator
  re-lists nothing: it reads what is there and substitutes the path. A new hook
  in muthur reaches multi-repo sessions on its own, as "once" by default.
- **The per-repo/skipped list is the only new knowledge**, and it lives in the
  generator. Marking hooks in `settings.json` itself would sit closer to them,
  but Claude Code validates that file, and an extra key in a hook entry risks
  breaking single-repo sessions for the sake of multi-repo ones.
- **The hooks do not change.** They all honor `CLAUDE_PROJECT_DIR` already, so a
  multi-repo mode inside each hook would duplicate one check across twenty
  files.
- `gh-shim.sh` keeps finding the real `gh` and reporting its absence; the
  generator only runs it.
