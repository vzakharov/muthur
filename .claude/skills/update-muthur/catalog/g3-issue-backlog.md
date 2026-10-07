> ⛔ **Part of [the catalog](../catalog.md), never vendored** — delete `catalog/` wherever `catalog.md` is deleted.

# G3 — Issue & backlog

Adopt on top of G2, and only if work is genuinely tracked as GitHub issues. If
you plan in Linear, Jira or a doc, decline the group and record why in
`watermark.json`'s `declined` map so re-sync stops offering it.

**A fork reverses the default.** The rule above weighs the group against a
process the repo already has; a whole-tree fork has none and inherits this
one's, so `/detemplate` keeps G3 unless the operator says otherwise — and files
the project's first issue on the way through.

| Item | What it does | Requires | Pulls in | Disposition |
| --- | --- | --- | --- | --- |
| `/take-issue` | Pull a GitHub issue onto the branch: export the thread and its attachments, commit them, hand the number back. Decides nothing — its callers are `/task`, `/plan` and `/go`, each running it first when the prompt carries a `#<N>`. Carries `video-frames.md`, which installs `ffmpeg` and extracts readable frames when an attachment turns out to be a video. | G2, `gh`, `scripts/export-github-item.py` | `/finalize`, `/plan` (G2) | adopt |
| `.claude/hooks/prompt-issue-export.sh` | Export the `#<N>` a session's first prompt *ends* in — skipping what is already on disk — so `/take-issue` Step 1 is done before the agent reads that prompt. A later `#<N>` is left to the agent, and any other prompt costs one `jq`. Commits nothing, and reports a failure rather than raising one. | `bash`, `jq`, `python3` ≥3.9, `scripts/export-github-item.py`, `.claude/settings.json` wiring (G4) | `.claude/hooks/lib.sh` (G4), `/take-issue` | adopt |
| `/issue` | Redirect for the name `/take-issue` was split out of: with a `#<N>` it runs `/plan` on the argument and names `/task` and `/go` as the same-shape alternatives; with none it names `/propose-issue` and stops. | G2 | `/plan` (G2), `/propose-issue` | conditional — see below |
| `/propose-issue` | File a unit of work as an issue, deduping against what's already open. Steps 1–2 are read-only and may run a turn earlier than Step 3, which is also where a `#<tbd>` on the branch gets its number. | G2, `gh`, `jq` | `/pr`, `/plan` (G2) | adopt |
| `/audit-github-backlog` | Sweep every open issue and PR against today's code and leave a reviewable close/refile/keep plan, prioritising `P0`–`P3` everything it keeps. Mutates nothing on GitHub. | G2, `gh` | `/go`, `/plan` (G2); `/propose-issue`; `/override-gh` (G4) | adopt |
| `scripts/export-github-item.py` | Download an issue — body, comments, timeline, attachments — into `docs/issue/<n>/`, or a PR (plus review threads, each one's resolved/unresolved state, and the lines its comment hangs off) into `docs/pr/<n>/`. Threads and comments are always indexed above their bodies. Stdlib-only. | `python3` ≥3.9, `$GH_TOKEN` or `gh auth token`, `scripts/lib/github.py` (G2), `scripts/gh_export/` | — | adopt |
| `scripts/gh_export/` | The exporter's pieces, one module per concern: argument parsing, the REST/GraphQL client, attachment download, the index-plus-bodies layout, and a renderer each for the header and comments, the review threads, and the timeline. | `python3` ≥3.9, `scripts/lib/github.py` (G2) | — | adopt |
