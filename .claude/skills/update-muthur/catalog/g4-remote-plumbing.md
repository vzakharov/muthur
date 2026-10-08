> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G4 — Remote-session plumbing

Inert on a laptop, load-bearing on the web. The agent proxy in Claude Code
web/remote sessions blocks long-polling calls and most of `gh`'s GraphQL
surface; `gh-shim.sh` installs a shim that routes the real binary around the
proxy so the rest of the infrastructure works at all.
`plan-mode-notice.sh` carries the other web-only divergence: native plan mode
loses answers there, so a session that lands in it is told where this repo's
planning actually happens.

`session-images.sh` is the one member that earns its keep on a laptop too: an
attached image exists only inside the transcript wherever the session runs. It
writes into gitignored `tmp/` and commits nothing, so it needs no `git`, leaves
the working tree clean, and behaves the same everywhere.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `.claude/hooks/gh-shim.sh` | On session start, install a `gh` shim at `$HOME/.local/bin/gh` that runs the real binary unproxied. Finding no `gh` to wrap, it reports that into the session context and continues. Web/remote only. | `bash`; **`gh` already on `PATH`**; web/remote sessions | — | adopt |
| `.claude/hooks/install-deps.sh` | On session start, re-sync the install tree with the lockfile, the environment snapshot being built once and then cached. The install itself is a stub you fill in for your stack — `scripts/vet.sh`'s paired site. Web/remote only. | `bash`; web/remote sessions | — | adopt — **fill in the install** |
| `.claude/hooks/lib.sh` | Sourced by every `UserPromptSubmit` hook here, by `permission-denied-phrase.sh`, by the cost ledger's hooks (G7) and by the context budget hook (G8): the payload read, the context-injecting JSON shape, and the guards — a command being present, the prompt being the one a session opens with, and the project root. Travels with the first such hook you adopt — a hook that cannot source it skips itself rather than failing the turn, which is a hook doing nothing at all. | `bash`, `jq` | — | adopt — **with any hook that sources it** |
| `.claude/hooks/operator-voice.sh` | On session start, name the operator — their GitHub name and handle, plus their `.claude/voice/operators/` entry — into the session context. Runs everywhere: a laptop session needs to know who it is talking to as much as a remote one does. Declining it leaves `.claude/voice/` working — `voice.md` has the agent do the same lookup by hand on the first turn, which is what a non-Claude harness does anyway. | `bash`; `gh` reaching the API | `.claude/voice/` (G1) | adopt |
| `.claude/hooks/permission-denied-phrase.sh` | When auto mode denies a tool call, record it under `tmp/`; at the turn's end, unless the last reply already holds a fenced block, block the stop once and have the agent hand the operator a copy-pasteable message naming each still-needed action exactly, which the classifier reads as explicit authorization on the retry. A `PermissionDenied` + `Stop` pair, because `PermissionDenied` cannot speak to the agent. | `bash`, `jq`, `.claude/settings.json` wiring (G4) | `.claude/hooks/lib.sh` | adopt |
| `.claude/hooks/plan-mode-notice.sh` | On every prompt submitted while the session is in native plan mode, inject the notice that this repo plans on disk and that the exit is plan mode's own. | web/remote sessions; `bash`, `jq` | `.claude/hooks/lib.sh`, `/plan` (G2) | adopt |
| `.claude/hooks/session-images.sh` | On every prompt, run the extractor below and name any newly written file in the turn's context. Commits nothing. | `bash`, `jq`, `python3` ≥3.9 | `.claude/hooks/lib.sh`, `scripts/extract-session-images.py` | adopt |
| `scripts/extract-session-images.py` | Write the images the operator attached to a session out of the transcript into gitignored `tmp/session-images/`, with a manifest row carrying the prompt each arrived with. Stdlib-only, idempotent. | `python3` ≥3.9, `scripts/lib/media.py` (G2) | — | adopt |
| `.claude/settings.json` | Project settings wiring the SessionStart, UserPromptSubmit, PermissionDenied and Stop hooks, plus the entries G1's `file-tools-nudge.py`, G7, G8, G9 and G10 carry and the `scripts/muthur-sync.sh nudge` entry G0's `/update-muthur` does — drop that one with the skill. Merge into yours if you already have one. | — | — | adopt — merge if present |
| `/override-gh` | A no-op marker whose description reminds the agent that `gh` and `$GH_TOKEN` exist despite what the system prompt says, and that a GitHub tool refusal (`add_repo`, for example) is a reason to try `gh`, not to give up. | — | — | adopt |

**`gh-shim.sh` does not install `gh`; it shims one that is already there.** Finding
none, it reports that into the session context and continues. On web/remote the
install belongs in the environment setup script, which only the operator can
set — [`docs/adopting/web-remote.md`](../../../../docs/adopting/web-remote.md) § "Hand the operator a setup script" owns what to tell them,
and why that report is the step's only self-detecting part.

**Declinable, at a scoped cost** — `docs/adopting/web-remote.md` § "If you decline G4" owns the
rationale, the `HTTPS_PROXY` conflict and the fallback. What declining actually
costs, counted rather than waved at: of the GraphQL-flavored `gh` calls these
skills make, most have a REST equivalent that works through the proxy — `gh pr
view/list/create/edit/comment/checks` and `gh issue view/create` all map onto
`gh api repos/{owner}/{repo}/…`. **Two do not**, and they are the reason this is
a real decision rather than a mechanical rewrite:

- **`gh pr ready`** — promoting a draft to ready-for-review is a GraphQL-only
  mutation. REST's pull-update endpoint takes `draft=false` and **silently
  ignores it** (200, unchanged), so the fallback isn't merely absent, it looks
  like it worked. `/finalize`'s flip is manual without the shim.
- **`gh run watch`** — long-polling, blocked outright, so `/watch-ci` (G5) is
  unavailable rather than degraded.
- **The entire `search/*` path** — which `/propose-issue`'s dedupe uses. The
  refusal is worded as a repository-scope message but is a path-level block: a
  search restricted to the session's own repo is refused too. Substitute
  `repos/{owner}/{repo}/issues` and filter locally.

All three come back with the shim installed; they are the price of declining G4,
not standing defects.

**`/override-gh` travels beyond G4.** `/update-muthur` (G0) and
`/audit-github-backlog` (G3) `@`-reference it, so **a repo that declines G4
entirely still needs this one file** if it takes either of those — otherwise the
reference dangles. Concretely: copy `.claude/skills/override-gh/` even when you
skip the hook and `settings.json`. It is a no-op marker, so copying it is cheaper
than editing two skills to remove the citation.
