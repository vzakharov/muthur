> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Sessions with several repositories attached

## Cause

When a cloud session has several repositories attached, Claude Code starts in
their common parent (`/home/user`), and two things the loop relies on stop
holding:

- **No repo's hooks load.** Claude Code reads project hooks only from the
  parent's `.claude/settings.json`, which does not exist. Each attached repo
  contributes its `CLAUDE.md`, rules and skills, but from its `settings.json`
  only `enabledPlugins` and `extraKnownMarketplaces` — documented in
  [settings § Settings in cloud sessions](https://code.claude.com/docs/en/settings#settings-in-cloud-sessions):
  _"a session with several repositories starts above the clones and reads only
  the `enabledPlugins` and `extraKnownMarketplaces` keys from each repository's
  `.claude/settings.json`, not permission rules, hooks, `env`, or other keys."_
- **There is no current repo.** The skills run bare `git …`, `gh pr view` and
  `scripts/…` relative to the shell's directory, which is `/home/user`, so every
  such call fails until the agent `cd`s. And where two repos carry a skill of
  the same name, only one copy is listed, so `/finalize` over `vovazakharov.com`
  may run muthur's text, which knows nothing of its deploy gate.

Observed in the session that wrote this plan (muthur + vovazakharov.com + life):
no `gh` shim (`gh pr list` through the proxy fails with
`HTTP 403: GitHub GraphQL is not available from Claude Code sessions`), no
operator entry, no `node_modules` in `vovazakharov.com`, no `.md` wrapping, no
cost rows, cold-cache, keepalive, `permission-denied-phrase`, `#N` export or
`muthur-sync` nudge — and every skill step needing a manual `cd`.

## Verified by hand in that session

- **A hook written into `/home/user/.claude/settings.json` mid-session fires on
  the next tool call** (the settings watcher), with
  `CLAUDE_PROJECT_DIR=/home/user`. A generated file in the parent therefore
  turns hooks on without a restart.
- **A `PreToolUse` hook in `~/.claude/settings.json` (user level) fires too**,
  although the docs say cloud sessions do not read that file. Whether a
  user-level `SessionStart` hook fires at a cloud session's start is **not yet
  verified** — it takes a fresh session.
- **The session's repos are an ordered list.** `get_session` returns
  `session_context.sources` in the order the UI shows ("vzakharov/muthur + …"),
  muthur first. **The first source's copy wins a skill-name collision** — here
  `/task` and `/pr` loaded from `/home/user/muthur/.claude/skills/…` — on one
  data point. The order is visible only through that MCP tool: no environment
  variable, file under `~/.claude` or `~/.ccr`, or transcript record carries it,
  so a hook or script cannot read it; the agent can.
- **The shell returns to `/home/user` between turns** — twice in that session —
  so a `cd` made in one turn does not survive to the next.
- The shim's unproxied path (`env -u HTTPS_PROXY gh …`) still works, although
  the proxy now answers GraphQL with new wording.
- Every hook locates its repo through `$CLAUDE_PROJECT_DIR` (falling back to the
  payload's `cwd`), so running a hook with `CLAUDE_PROJECT_DIR=<repo>` gives it
  the environment it has in a single-repo session.
- The repos are cloned before `SessionStart` fires — a single-repo session's
  hooks run from the clone (`$CLAUDE_PROJECT_DIR/.claude/hooks/…`).
- **What reaches a multi-repo session's first turn from the repos.** Every
  attached repo's `CLAUDE.md` was in the opening context, with its `@`-imports
  (`.claude/voice/voice.md`), because the platform sets
  `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`. Path-scoped `.claude/rules/`
  files from the repos arrived on a `Read` of a file they cover. An
  always-loaded rule (no `paths:`) from an attached repo is **not verified**:
  none of the three repos has one, and the docs list rules as loading under that
  same variable without saying more. The agent also knows it is in a multi-repo
  session from turn one: the environment block names a primary working directory
  that "is a git repository: false".

## Approach

### 1. `scripts/lib/` — the session's repos, in one place

A stdlib module both scripts below import: the session root
(`$CLAUDE_PROJECT_DIR` when set, else the parent of the repo the calling script
lives in), whether the session is multi-repo (the root is not itself a git work
tree), and the attached repos (child git work trees). The primary repo, when the
caller knows it, is passed in rather than guessed.

### 2. `scripts/multi-repo-hooks.py` — the hook generator

1. **Exits silently in a single-repo session**, where hooks already run.
2. **Collects the hooks** from `.claude/settings.json` of every attached repo.
   Each command becomes `CLAUDE_PROJECT_DIR=<repo> <command, path substituted>`,
   matchers and timeouts kept.
3. **Sorts them into per-repo, once, or skipped** (§ 3) and writes
   `<root>/.claude/settings.json` whole. The file is generated, outside every
   repo, and lives until the container is rebuilt. A file there the generator
   did not write (no marker key it recognizes) is refused with an explanation,
   never overwritten.
4. **Runs the collected `SessionStart` hooks now** (matcher `startup`) and
   prints their stdout: the start event has already passed, and the settings
   watcher only catches future events. The agent reads that output as context —
   the operator entry and the shim's notice included.

Takes `--primary <repo>` (§ 3). A rerun is idempotent: the file is regenerated,
the shim rewritten, `install-deps` re-syncs what is already in sync.

### 3. Which hook runs where

The rule is a short list in the generator, keyed by the command's repo-relative
path; anything not listed runs once.

- **Per repo** — hooks whose effect belongs to their own repo, or that filter on
  `CLAUDE_PROJECT_DIR` themselves so exactly one copy acts:
  - `install-deps.sh` — each repo's dependencies;
  - `muthur-sync.sh nudge` — each repo has its own watermark;
  - `format-md.sh`, `file-tools-nudge.py` — check that the path is inside their
    root;
  - the cost family (`stop-session-cost.sh`, `start-telemetry-receiver.sh`,
    `estimate-notice.sh`, `post-tool-context-budget.sh`) — a row lands in every
    repo and is committed only where the session commits work. The accepted
    cost: each repo's row carries the whole session's cost, so a sum across
    repos counts a shared session more than once.
- **Once** — session-wide, from the primary repo when `--primary` names it, else
  the alphabetically first repo carrying the hook: `gh-shim.sh`,
  `operator-voice.sh`, `cold_cache.py`, `keepalive.py`, `plan-mode-notice.sh`,
  `session-images.sh`, `prompt-route-notice.sh`, `permission-denied-phrase.sh`.
- **Skipped** — `prompt-issue-export.sh` and `prompt-handle-pr-export.sh`: a
  `#12` in the prompt does not say which repo the thread is in. `/take-issue`
  and `/handle` run the export themselves when the hook has not (both already
  carry that path), with the repo `find-repo.py` (§ 5) picks.

### 4. What runs the generator

Written with open question 1's option (a) in force:

- **The environment setup script**: merges into `~/.claude/settings.json` a
  user-level `SessionStart` hook that finds
  `"$CLAUDE_PROJECT_DIR"/*/scripts/multi-repo-hooks.py` and runs the first
  match. The code stays in the repos, versioned; the setup script carries only
  the lookup, because it runs once when the environment snapshot is built, when
  the set of repos is not yet known and they may not be on disk. A session
  attaching no muthur-based repo finds nothing and does nothing. Copies of the
  generator may differ in version across repos until each syncs; the lookup
  takes the first. The agent cannot edit the setup script, so the report hands
  the operator the block, and the worked example in
  `docs/adopting/web-remote.md` gains it.
- **The multi-repo rule** (§ 6) as the fallback: when `~/.local/bin/gh` is
  absent in a multi-repo session, the setup script's hook did not run, so the
  agent runs the generator itself as its first command — with
  `--primary <first source>`, read off `get_session`.

### 5. `scripts/find-repo.py <branch|#N|PR URL>` — the target repo

Prints the path of the one attached repo the argument names, or exits non-zero
listing the candidates:

- **A branch** — `git ls-remote --heads origin <branch>` in each repo. The
  random suffix makes a session branch unique across repos in practice; the one
  shared name is the current session's own auto-branch, which the harness
  creates in every attached repo.
- **A PR URL** — its `owner/repo` matched against each repo's `origin`, no
  network.
- **`#N`** — `gh api repos/<owner>/<repo>/pulls/N` (or `issues/N`) per repo; a
  number found in several is a genuine ambiguity, and the agent asks.
- **A single-repo session** prints its own repo, so skills call it without
  checking the mode.

A skill finds the script without a `cd`: the harness names the loaded skill's
base directory, three levels below the repo root that carries `scripts/`.

### 6. The multi-repo rule — one place, not every skill

The rule has to be in context from a multi-repo session's first turn, before any
skill or hook runs — so its home is whatever open question 3 settles, and
`CLAUDE.md` is the one home verified to arrive there. It holds when the
session's working directory is above the repos:

- **Every skill that acts on a branch, PR or issue first resolves its target
  repo** with `find-repo.py`, and remembers it for the rest of the task.
- **Every Bash call then starts with `cd <repo> &&`**, so every `git`, `gh`,
  `scripts/…` and relative path in a skill's text means that repo's — the shell
  returns to `/home/user` between turns, so one `cd` does not hold.
- **Scripts and `@.claude/skills/…` references resolve against the target
  repo**, never against the repo the loaded skill came from: `/finalize` loaded
  from muthur runs `life`'s `scripts/vet.sh`.
- **The loaded copy of a skill is only the entry point.** Once the target is
  known, if the skill's base directory lies outside it, read
  `<repo>/.claude/skills/<name>/SKILL.md` and follow that copy instead. Steps
  taken before the switch are safe, since resolving the target is the same in
  every synced copy.
- **The fallback for the generator** (§ 4), and **attaching the repo you work in
  first** as the operator's habit, since the first source's copy wins a skill
  collision.

### 7. Docs, inventory, tests

- `docs/adopting/web-remote.md`: the block in the setup-script example, and a
  multi-repo paragraph under "Known gaps".
- Entries for both scripts and the rule in
  `.claude/skills/update-muthur/catalog/g4-remote-plumbing.md`, beside the shim.
- Tests beside the scripts, run by `vet.sh`:
  - `scripts/test_multi_repo_hooks.py` — path substitution, the
    per-repo/once/skipped sort, `--primary`, the silent exit in a single-repo
    session, the refusal to overwrite a foreign file;
  - `scripts/test_find_repo.py` — branch, URL and `#N` resolution against
    fixture repos with local bare remotes, the ambiguous and not-found exits.

## Out of scope — proposed as separate issues

- **`/relay` in a multi-repo session** starts its successor with a single
  `source_url`, so the successor is a single-repo session that has lost the
  others.

## Open questions

1. **What runs the generator?**
   - a) **Both: the setup script plus the multi-repo rule's fallback**
     (recommended) — automatic once the operator adds the block, manual until
     then.
   - b) The rule's fallback only — needs nothing from the operator, but rests on
     the agent noticing, and does not rerun by itself after a container rebuild.
   - c) The setup script only — reliable, but without it a multi-repo session
     silently stays hookless.
2. _(answered: a row in every repo — § 3.)_
3. **Where the multi-repo rule lives** — waits on question 1, since the rule
   carries the generator's fallback and so must be in context on turn one:
   - a) **`.claude/rules/multi-repo.md` (no `paths:`) plus a pointer line in
     `CLAUDE.md`** (recommended, if a first multi-repo session shows the rule
     file in its opening context) — the same always-loaded cost, a shorter
     `CLAUDE.md`.
   - b) The whole rule in `CLAUDE.md` — the one home verified to load from every
     attached repo on turn one; the fallback if (a)'s check fails.
4. _(answered: one PR.)_

The plan is written with the recommendations in force; questions 1 and 3 stay
open until answered.

Resolved: cost rows go to every repo rather than a primary one, which the
setup-script path could not have read anyway; hooks and skills ship in one PR,
since they share `scripts/lib/` and are dogfooded in the same session.

## DRY notes

- **Each repo's `settings.json` stays the one source of hooks.** The generator
  re-lists nothing: it reads what is there and substitutes the path. A new hook
  in muthur reaches multi-repo sessions on its own, as "once" by default.
- **The per-repo/skipped list is the only new knowledge about hooks**, and it
  lives in the generator. Marking hooks in `settings.json` itself would sit
  closer to them, but Claude Code validates that file, and an extra key in a
  hook entry risks breaking single-repo sessions for the sake of multi-repo
  ones.
- **"Which repos are in this session" lives once, in `scripts/lib/`**, imported
  by both scripts: a generator and a resolver disagreeing about the attached
  repos would wire hooks into one set and run skills against another.
- **No hook and no skill changes.** The hooks already honor
  `CLAUDE_PROJECT_DIR`; the skills get one rule rather than a `git -C` threaded
  through twenty files, which would duplicate the same concern everywhere and
  rot on the next synced edit.
- `gh-shim.sh` keeps finding the real `gh` and reporting its absence; the
  generator only runs it.
