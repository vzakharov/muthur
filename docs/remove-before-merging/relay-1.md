# Relay 1 — worktree hook dispatcher (parked)

## Standing constraints

From the scheduled prompt, verbatim:

> Keep the PR, commits and any issue free of private data: no names of people,
> companies, clients or downstream projects, no local paths, emails or session
> ids — describe the incident generically as above.

> Limits to state in the PR rather than solve: hook configuration is snapshotted
> at session start, so a running session keeps its old hooks; and in a worktree
> session the dispatcher itself is read from `$CLAUDE_PROJECT_DIR`, so it takes
> effect once it is on the main checkout's branch.

## The conversation

1. **Scheduled prompt (no live operator).** Fix, in muthur, the split between
   where hooks run (`CLAUDE_PROJECT_DIR` = main checkout) and where the agent's
   scripts run (the worktree) in a git-worktree session: add
   `.claude/hooks/dispatch.sh <repo-relative hook> [args…]` (payload `.cwd` →
   `git rev-parse --show-toplevel`; same `--git-common-dir` and hook executable
   there → run from that checkout with `CLAUDE_PROJECT_DIR` set to it; else from
   the anchor; `exec` so exit/stdout pass through; fallbacks: non-git cwd, other
   repo, branch predating the hook), route every `.claude/settings.json` command
   through it, make `scripts/multi-repo-hooks.py` `hook_key` read past the
   dispatcher, add tests, docs and sync-catalog wiring, consider
   `[attn adopters]`. Done = a PR through `/task` → `/go` → `/pr`, tests and vet
   green.
   - Agent: routed as rung 1 → `/task`; chose outcome 2 (no plan — the prompt is
     the spec). Implemented on `claude/worktree-hook-dispatch`, `/polish` ran
     via subagent, `./scripts/vet.sh` exit 0. `gh pr create` was **denied by the
     auto-mode classifier** ("Unsanctioned Communication"); the agent did not
     route around it, sent a push notification, and handed the operator a fenced
     phrase to send back. (verbatim in Last agent turn)

2. Keepalive's last wake → this `/relay park`.

## Intent

A merged-ready draft PR in muthur fixing the hook/script checkout split, with
the adopters' ask and the two limits stated in the PR, free of private data.

## Decisions

- **No plan file** — the scheduled prompt names every file and behavior; a plan
  would restate it.
- **Dispatcher anchors on `git rev-parse --show-toplevel` of
  `CLAUDE_PROJECT_DIR`** for the same-checkout comparison, so a subdirectory cwd
  of the anchor stays on the anchor.
- **Catalog**: a new G4 entry for `dispatch.sh` (disposition "adopt — with
  `settings.json`"), and the `settings.json` entry gained "Pulls in:
  `.claude/hooks/dispatch.sh`" plus the instruction to spell local hooks through
  it. No separate pairing mechanism exists in `scripts/muthur-sync.sh`.
- **Title** carries `[attn adopters]`, and the PR body an `Adopters:` paragraph
  (re-spell local hooks through the dispatcher, take `dispatch.sh` in the same
  port).

## Errors and dead ends

- `gh pr create --draft …` denied by auto mode. `permissions.allow` holds only
  `scripts/pr-comment.sh`, no PR-opening script. Not retried through the GitHub
  MCP tool, to avoid working around the denial.

## State

- Branch `claude/worktree-hook-dispatch`, pushed; head `d6c73d2` (`polish:` on
  top of `3b91d5a fix: run hooks from the worktree the session works in`), base
  `main` at `f7dff8e`.
- **No PR yet.** No squash proposal posted. No plan file. No CI, subscription or
  check-in running. No artifact watches.
- Estimate for this session: 3.75 h senior developer ("a bash dispatcher whose
  fallbacks (non-git, other repo, stale branch) each have to stay exact, plus
  the multi-repo generator's classification") + 1 h middle qa ("worktree
  fixtures in a temp repo cover the routing matrix and exit passthrough").
  Remainder handed on: 0.25 h senior developer — opening the PR and composing
  its squash record.

### Watches

(none)

## Pointers

- `.claude/hooks/dispatch.sh`, `scripts/test_dispatch.py` — the dispatcher and
  its 9 tests.
- `scripts/multi-repo-hooks.py` (`DISPATCHER`, `hook_key`),
  `scripts/test_multi_repo_hooks.py`
  (`test_dispatched_hooks_are_classified_by_the_hook_they_front`).
- `.claude/skills/update-muthur/catalog/g4-remote-plumbing.md` — the two
  entries.
- Predecessor transcript:
  https://claude.ai/code/session_01RAikutHxsrZ71oQYawowXs
- The drafted PR body lived only in this container's scratchpad, so it is
  reproduced here (title:
  `fix: [attn adopters] run hooks from the worktree the session works in`):

```markdown
## Summary

- **The defect.** In a desktop session working in a git worktree (e.g. `<repo>/.claude/worktrees/<name>`), Claude Code hands hooks `CLAUDE_PROJECT_DIR` = the main checkout, while the session's shell — and every script the agent runs — works in the worktree. Every hook was spelled `$CLAUDE_PROJECT_DIR/<path>`, so hooks ran the main branch's code and kept per-session state under the main checkout's `tmp/`. Observed: a session joined to a mail channel never got its wake, because the keepalive watcher looked for the join record in the main checkout's `tmp/` while the join had written it in the worktree's; and the "no human-hour estimate yet" notice kept firing after an estimate was set from the worktree.
- **`.claude/hooks/dispatch.sh <hook> [args…]`** fronts every registered hook. It reads the payload once, takes `.cwd` (via `jq`), and when that lies in another worktree of the same repository (same `git rev-parse --git-common-dir`) that carries the hook as an executable, `exec`s that copy with `CLAUDE_PROJECT_DIR` pointed at the worktree. A cwd outside git (multi-repo parent), in another repository, on a branch predating the hook, a payload with no cwd, or no `jq` — all run the hook from `CLAUDE_PROJECT_DIR` as an undispatched registration would. Exit code, stdout, args and payload pass through.
- **`.claude/settings.json`**: every command is now `$CLAUDE_PROJECT_DIR/.claude/hooks/dispatch.sh <old path> [args]`. **`scripts/multi-repo-hooks.py`**'s `hook_key` reads past the dispatcher token to the hook it fronts, so PER_REPO / SKIPPED classification and the once-only dedupe still hold; `localize` is unchanged.
- **Sync catalog (G4)** gains a `dispatch.sh` entry adopted *with* `settings.json`, and the `settings.json` entry pulls it in and tells adopters to spell their own hooks through it — one without the other breaks every hook.

**Adopters:** a `settings.json` carrying local hooks must re-spell each of them as `$CLAUDE_PROJECT_DIR/.claude/hooks/dispatch.sh <path> [args]` when taking this, and take `.claude/hooks/dispatch.sh` in the same port.

### Limits, stated rather than solved

- Hook configuration is snapshotted at session start, so a running session keeps its old (undispatched) hooks until it restarts.
- In a worktree session the dispatcher itself is read from `$CLAUDE_PROJECT_DIR` (the main checkout), so the fix takes effect for worktree sessions once it is on the main checkout's branch.

## QA Checklist

- [ ] `tests` — `python3 scripts/test_dispatch.py` and `python3 scripts/test_multi_repo_hooks.py` pass (both run in `./scripts/vet.sh`).
- [ ] `worktree-session` — open a desktop session in a worktree of this repo (main checkout on a branch carrying this change); set an estimate with `.claude/costs/estimate.py set …` from the worktree; the next prompt no longer shows the "no human-hour estimate yet" notice.
- [ ] `plain-session` — in an ordinary (non-worktree) session, hooks still fire as before: the operator greeting at start, the file-tools nudge on a `cat`.
- [ ] `multi-repo` — in a cloud session with two repos attached, `scripts/multi-repo-hooks.py` writes a parent `settings.json` whose commands go through each repo's dispatcher, with `format-md.sh` per repo and the issue-export hooks skipped.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `tests` | yes | yes | unit tests in vet |
| `worktree-session` | partly | routing covered by `test_dispatch.py` | the end-to-end needs a desktop worktree session |
| `plain-session` | partly | same-checkout case in `test_dispatch.py` | live hook firing needs a real session |
| `multi-repo` | yes | `test_dispatched_hooks_are_classified_by_the_hook_they_front` | |

https://claude.ai/code/<successor session id>
```

## Next step

Open the draft PR — `/pr` (Steps 4–6: create with the title and body above, the
session link swapped for the successor's own, then `/squash-message`). It needs
the operator's go-ahead past the auto-mode denial; the phrase handed to them:
"Open a draft PR in vzakharov/muthur from claude/worktree-hook-dispatch into
main titled "fix: [attn adopters] run hooks from the worktree the session works
in", with the body from the scratchpad pr-body.md". Until they send it (or an
equivalent), wait for the operator.

## Last agent turn

The agent's last turn before the relay, verbatim, appended by
`scripts/relay-last-reply.py`. It includes the turn's interim messages, usually
unneeded but harmless; the reply proper is usually its last paragraphs.

````text
Это рунг 1 — просьба об изменении кода, так что маршрут ведёт в `/task`.

One mechanical substitution over 35 identical command prefixes — the shell is the better tool here; retrying.

Now `hook_key`:

Tests pass. Now checking what else parses `settings.json` commands:

Коммичу диспетчер, переписанные хуки, тесты и запись в каталоге, потом запускаю `/polish`.

Полировка готова. Дальше `vet.sh`, потом PR.

Vet зелёный (exit 0, `test_dispatch.py` подхватывается через glob в `check-muthur.sh`). Теперь `/pr`.

Вова, the fix is built, tested and pushed, but there's no PR yet: auto mode blocked `gh pr create` as unsanctioned communication. Nothing in `permissions.allow` covers opening a PR, so I stopped instead of trying the same thing another way.

**What's on `claude/worktree-hook-dispatch`** (2 commits, vet green):
- **`.claude/hooks/dispatch.sh`**: reads the payload once and takes its `cwd`. When that `cwd` is in another worktree of the same repository and that worktree has the hook, it runs the worktree's copy with `CLAUDE_PROJECT_DIR` pointed at the worktree. In every other case the hook runs from the anchor as before: `cwd` outside git, in another repository, on an older branch without the hook, no `cwd` in the payload, or no `jq`. The hook is `exec`'d, so exit code, stdout, args and payload pass straight through.
- **`.claude/settings.json`**: all 33 hook commands now go through the dispatcher.
- **`scripts/multi-repo-hooks.py`**: `hook_key` now looks past the dispatcher to the hook it fronts, so per-repo, skipped and run-once hooks are sorted as before.
- **Tests**: `scripts/test_dispatch.py` has 9 cases in a temp repo with `git worktree add`, covering the cases in your list plus an older worktree without the hook, a payload with no `cwd`, and `CLAUDE_PROJECT_DIR` unset. `test_multi_repo_hooks.py` has a new case for dispatched hooks.
- **Sync catalog (G4)**: `dispatch.sh` is listed to be taken together with `settings.json`, and the `settings.json` entry tells adopters to route their own hooks through it.

I kept the title tag `[attn adopters]`, because an adopter with local hooks has to re-spell them through the dispatcher. The PR body covers the defect, the ask to adopters and the two limits: hooks load at session start, and a worktree session reads the dispatcher from the main checkout. It's ready at `/tmp/claude-0/-home-user-muthur/7b42cb14-c9a7-5e86-b225-efaae315d251/scratchpad/pr-body.md`.

To finish, send this back and I'll open the PR and post the squash proposal:

```
Open a draft PR in vzakharov/muthur from claude/worktree-hook-dispatch into main titled "fix: [attn adopters] run hooks from the worktree the session works in", with the body from the scratchpad pr-body.md
```
````
