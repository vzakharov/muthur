> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Export the issue a session's launch prompt names, before the first turn

## What this changes

A session launched with `<issue title> #55` currently spends its first turn
reading CLAUDE.md § "Plan mode & questions in web sessions", recognising the
`#<N>` tail, loading `/issue`, and running its Step 1 export — a round trip whose
only output is a file the machine could already have on disk. A
`UserPromptSubmit` hook runs that export before the agent's first token, and
names the result in the turn's context.

The routing convention does not move: the agent still reads the tail as an
`/issue` invocation. What moves is the download, from the agent's first turn to
the moment before it.

## Approach

One new hook, `.claude/hooks/launch-issue-export.sh`, wired as a third
`UserPromptSubmit` entry in `.claude/settings.json`. It shells out to the
exporter `/issue` Step 1 already names — there is no second downloader — and
follows `session-images.sh`'s shape: read the payload, do one job, inject
`additionalContext`, never fail the turn.

### Two gates, both fail closed

**Gate 1 — this is the session's first prompt.** Read `transcript_path` and
count genuine operator prompts: records with `.type == "user"` and
`.message.role == "user"`, excluding `isMeta` records and tool results (a
`toolUseResult` field). Fire only at zero. The predicate is exact because the
prompt being submitted is *not* in the transcript yet when `UserPromptSubmit`
fires — the last record is the `queue-operation` carrying its text, which
`session-images.sh` establishes by measurement and depends on for the same
reason.

Every uncertainty declines: no `jq`, no `python3`, an unreadable transcript, a
record shape that stopped matching. A wrong decline costs the status quo — the
agent runs Step 1 itself. A wrong fire writes a stray export on every prompt of
every session, so the asymmetry picks the bias.

**Gate 2 — the prompt names an item.** Three forms, in order:

- a full `https://github.com/OWNER/REPO/(issues|pull)/N` URL ending the prompt;
- `#<N>` ending the prompt — digits followed by nothing but whitespace, matching
  CLAUDE.md's "ends in `#<N>`" exactly rather than loosely;
- an explicit `/issue <n|url>` opening the prompt.

A bare number resolves to an issue or a PR from the API, not from the argument,
so a launch prompt naming a PR lands in `docs/pr/<n>/pr.md` — which is what
`/handle` reads. That falls out of the exporter; nothing here decides it.

**Already exported → skip the download** and point at the file. A resumed or
compacted session that re-fires the gates then costs nothing.

### Running the export

`python3 scripts/export-github-item.py <n>` from the project directory, under a
self-imposed `timeout` so the hook reports its own expiry instead of being killed
mid-download; the hook's `timeout` in `.claude/settings.json` sits above it.

The hook **does not commit.** `/issue` Step 2 does, on a branch the agent has
settled. A hook that committed would commit to whatever `HEAD` happened to be
on — the rationale `session-images.sh` already carries.

### What lands in the turn's context

- **Success** — the written path (parsed from the exporter's `Wrote <path>`
  line), the attachments directory, and that `/issue` Step 1 is done so the run
  continues from Step 2. Plus: if the number was not an item handover, the export
  is an untracked directory to remove and ignore.
- **Partial** — the Markdown is written but attachments failed (the exporter
  exits non-zero and names each miss). Say so with the stderr tail, so Step 1's
  "you'd be reading it with pixels missing" clause is visible rather than
  inferred from a silence.
- **Failure** — the stderr tail, and that Step 1 owns what happens next ("stop
  and report", never solve from the title).

Every path exits 0 and logs its reason to stderr. The declines log too: the
record shape belongs to the client and is undocumented, so when it changes this
hook goes quiet, and the stderr line is how that is diagnosed rather than
puzzled over — the role `--verbose` plays for `scripts/extract-session-images.py`.

## Files

| File | Change |
| --- | --- |
| `.claude/hooks/launch-issue-export.sh` | New. The hook, ~70 lines including its header comment. |
| `.claude/settings.json` | Wire it as a third `UserPromptSubmit` hook, with a `timeout`. |
| `.claude/skills/issue/SKILL.md` | Step 1: the export may already be on disk — read it instead of re-running. The command stays as the fallback for a prompt the hook declined and for a harness with no hooks. |
| `CLAUDE.md` § "Plan mode & questions in web sessions" | One clause on the `#<N>` bullet: the export is already done, so the run starts at Step 2. |
| `.claude/skills/update-muthur/catalog.md` | A row in G4's table, and one sentence in the paragraph that already explains why `session-images.sh` is not web-only — this hook runs everywhere too. |

## DRY notes

- **The download is not duplicated.** The hook invokes
  `scripts/export-github-item.py`, the same entrypoint `/issue` Step 1 names.
  Nothing re-implements fetching, attachment handling, or the
  issue-vs-PR resolution.
- **The `#<N>` pattern in prose and the regex in the hook are not two copies of
  one rule.** The prose is the agent's routing convention and still governs
  every prompt the hook declines — a non-first prompt, a harness without hooks.
  The regex is the hook's trigger. They must *agree* (hence the exact-tail match
  above), but neither can replace the other.
- **A shared hook preamble was considered and declined.** The jq check, payload
  read, stderr `say()` and exit-0-on-anything are ~8 lines this shares with
  `session-images.sh` and `plan-mode-notice.sh`. Hoisting them into
  `scripts/lib/hook-common.sh` would buy little: each hook requires different
  tools and declines differently, and a sourced library gives a hook a new way to
  fail — not finding it. Three near-copies of eight obvious lines is the cheaper
  side.
- **Transcript reading is shared with `session-images.sh` only in the file it
  opens.** The predicates differ entirely (image attachment records vs. operator
  prompt records), so there is no common query to extract.

## Verification

No bash-test harness exists here, and the riskiest input — the transcript record
shape — is the client's, undocumented, and would only be frozen by a test, not
checked. So: fixtures plus diagnostics, the same answer
`scripts/extract-session-images.py` reaches.

1. Fixture payloads in `tmp/`, piped into the hook, one per branch: not-first
   prompt, first prompt with no match, first prompt with a `#<N>` tail, `/issue`
   form, URL form, already-exported, nonexistent issue number.
2. One live run against a real issue in this repo, checking the written tree and
   the injected context.
3. `./scripts/vet.sh` before pushing.

## Open questions

Each is written into the plan above with the recommended option already in
force, so silence resolves it.

1. **Trigger scope** — (a) the session's first prompt only *(recommended: what
   was asked, and it keeps stray `#5` mentions mid-session from writing
   exports)*; (b) any prompt whose tail is `#<N>`.
2. **Forms matched** — (a) the `#<N>` tail, a full issue/PR URL, and an explicit
   `/issue <arg>` *(recommended: the explicit form routes to the same Step 1 and
   costs three lines of regex)*; (b) the `#<N>` tail alone.
3. **A test wired into `scripts/vet.sh`** — (a) no; fixtures during
   implementation, stderr diagnostics afterwards *(recommended, per
   "Verification")*; (b) yes — a `scripts/test_launch_issue_export.py` driving
   the hook as a subprocess, which needs an env seam to stub the exporter so the
   test does not hit the network.
