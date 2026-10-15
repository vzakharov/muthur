# PR #199: feat: support sessions with several repositories attached

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/199
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/multi-repo-hooks-z0ln0c
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-15T05:23:18Z
- **Updated:** 2026-10-15T20:41:16Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 2

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/rules/multi-repo.md`:5 — unresolved — last: @vzakharov (human) 2026-10-15T20:40:05Z — "так, то есть пока агент не тронет что-то из этого, он не узн…" → [↓](#t01)
- **T02** `.claude/staged/CLAUDE.md.staged`:174 — unresolved — last: @vzakharov (human) 2026-10-15T20:40:46Z — "а, вот так? ну ок" → [↓](#t02)

---

## Body

## Summary

- **Cause:** a cloud session with several repositories attached starts in their parent (`/home/user`). Claude Code then loads no repo's hooks ([documented](https://code.claude.com/docs/en/settings#settings-in-cloud-sessions)) — no `gh` shim, operator greeting, `install-deps`, `.md` wrapping or cost rows — and the skills, which run `git`/`gh`/`scripts/…` relative to the shell, have no current repo. Where two repos carry a same-named skill, only the first source's copy is listed.
- **Hooks:** `scripts/multi-repo-hooks.py` builds the parent's `settings.json` from every attached repo's hooks (each with `CLAUDE_PROJECT_DIR=<repo>`), sorted into per-repo / once / skipped, and runs the `SessionStart` set right away. A user-level hook the environment setup script installs triggers it (block in `docs/adopting/web-remote.md`); the agent runs it itself where that hook is missing.
- **Skills:** `scripts/find-repo.py` resolves a branch, PR URL or `#N` to its repo, and one rule, `.claude/rules/multi-repo.md`, has every skill `cd` into that repo per Bash call and follow that repo's own copy of the skill — no per-skill edits. The rule's `paths:` name only its own scripts, so it never loads in a single-repo session; a pointer in the staged `CLAUDE.md` has a multi-repo session `Read` it on its first turn.
- **Upstream:** what no repo can fix — every attached repo's `CLAUDE.md` loading whole, once per repo — is filed as anthropics/claude-code#102311.
- `detect_origin_repo` reads `remote.origin.url` as configured, since `git remote get-url` applies `url.*.insteadOf` and would name a mirror instead of the GitHub repo.
- One open question in the plan, recommendation in force: what runs the generator — the setup-script hook plus the rule's fallback.

## QA Checklist

- [ ] `start-hook` — in a fresh multi-repo session with the setup-script block, the user-level `SessionStart` hook fires and the first turn carries the generator's output (operator entry, shim installed)
- [ ] `fallback` — in a multi-repo session without the block, the agent reads the rule and runs the generator itself, passing the first source as `--primary`
- [ ] `gh-graphql` — `gh pr list` succeeds in either case
- [ ] `deps` — every attached repo's dependencies are installed
- [ ] `format-md` — editing a `.md` in a non-primary repo wraps it with that repo's prettier
- [ ] `find-branch` — `/from-branch <branch of the second repo>` attaches in that repo without being told which
- [ ] `skill-copy` — `/finalize` on a `vovazakharov.com` branch, with muthur attached first, follows `vovazakharov.com`'s own `/finalize`
- [ ] `ambiguous-pr` — `/handle #N` where `#N` exists in two repos asks which one
- [ ] `single-repo` — a session with one repo behaves as before: no parent `settings.json`, `find-repo.py` prints the repo itself, the setup-script hook exits 0

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `start-hook` | manual-only | — | Needs a fresh cloud session; the one unverified assumption |
| `fallback` | manual-only | — | Needs a cloud session and `get_session` |
| `gh-graphql` | manual-only | — | Needs the live proxy |
| `deps` | integration | ✅ | `test_multi_repo_hooks.py`: `install-deps` runs once per repo, each with its own `CLAUDE_PROJECT_DIR` |
| `format-md` | unit | ✅ | `test_multi_repo_hooks.py`: one `format-md` entry per repo |
| `find-branch` | integration | ✅ | `test_find_repo.py`: fixture clones with local bare remotes |
| `skill-copy` | manual-only | — | Agent behavior under the rule |
| `ambiguous-pr` | integration | ✅ | `test_find_repo.py`: exit 2 naming both repos, for a branch and for `#N` |
| `single-repo` | unit | ✅ | Both test files; the hook's `exit 0` checked by hand |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01A1ZPEFseUYgmqt9Gdfbjx1
https://claude.ai/code/session_01URDtq8YsVkUmJ14j83XbmN

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-15T05:23:39Z — "Proposed squash body: ``` A cloud session with several repos…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-15T05:23:39Z

[https://github.com/vzakharov/muthur/pull/199#issuecomment-6185082086](https://github.com/vzakharov/muthur/pull/199#issuecomment-6185082086)

Proposed squash body:

```
A cloud session with several repositories attached starts in their
parent directory. Claude Code then loads none of the repos' hooks, and
the skills, which run git, gh and scripts relative to the shell, have
no current repo; where two repos carry a same-named skill, only the
first source's copy is listed.

scripts/multi-repo-hooks.py writes the parent's .claude/settings.json
from every attached repo's hooks, each run with CLAUDE_PROJECT_DIR set
to its own repo: per repo where the hook acts on its repo, once for
session-wide ones, skipped for the #N export hooks. It runs the
SessionStart set at once, since the settings watcher only catches later
events. A user-level hook from the environment setup script triggers
it, and the agent runs it itself where that hook is missing.

scripts/find-repo.py resolves a branch, PR URL or #N to the one repo
carrying it. .claude/rules/multi-repo.md has every skill resolve its
target that way, cd into it on each Bash call, and follow that repo's
own copy of the skill, so no skill text changes. The rule is scoped to
its own scripts and loaded through a CLAUDE.md pointer, so it costs a
single-repo session nothing. What no repo can work around — each
attached repo's CLAUDE.md loading in full — is
anthropics/claude-code#102311.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/rules/multi-repo.md`:5 — unresolved — last: @vzakharov (human) 2026-10-15T20:40:05Z — "так, то есть пока агент не тронет что-то из этого, он не узн…" → [↓](#t01)
- **T02** `.claude/staged/CLAUDE.md.staged`:174 — unresolved — last: @vzakharov (human) 2026-10-15T20:40:46Z — "а, вот так? ну ок" → [↓](#t02)

<a id="t01"></a>

### `.claude/rules/multi-repo.md`:5 — unresolved

```diff
@@ -0,0 +1,61 @@
+---
+description: Working in a session with several repositories attached — wire the hooks, resolve the target repo, and run that repo's own copy of each skill
+paths:
+  - scripts/find-repo.py
+  - scripts/multi-repo-hooks.py
```

**@vzakharov (human)** — 2026-10-15T20:40:05Z

так, то есть пока агент не тронет что-то из этого, он не узнает про эти правила? или так и задумано?

---

<a id="t02"></a>

### `.claude/staged/CLAUDE.md.staged`:174 — unresolved

```diff
@@ -165,6 +165,14 @@ there. What `vet.sh` must exit, and why, is `.claude/rules/stack.md`.
… 2 lines elided …
 
+## Sessions with several repositories
+
+**When the primary working directory is not a git repository** — a cloud session
+with several repositories attached, starting in their parent — `Read`
+`.claude/rules/multi-repo.md` in any attached repository that carries it, before
+anything else, once per session: no hook runs and no skill knows its repository
+until it has.
```

**@vzakharov (human)** — 2026-10-15T20:40:46Z

а, вот так? ну ок

---

## Timeline (status, references, and other events)

- **2026-10-15T06:03:15Z** @vzakharov renamed from «feat: run repo hooks in sessions with several repositories attached» to «feat: support sessions with several repositories attached».
- **2026-10-15T07:18:54Z** @vzakharov cross-referenced this pull request from [#102311 [FEATURE] Multi-repo cloud sessions load each repository's CLAUDE.md in full, multiplying standing context](https://github.com/anthropics/claude-code/issues/102311).
- **2026-10-15T20:41:16Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/199#pullrequestreview-5539605489.
