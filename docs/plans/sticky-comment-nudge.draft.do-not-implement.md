> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# Steer hand-rolled sticky-comment writes to `scripts/pr-comment.sh`

## The incident

In `vzakharov/vovazakharov.com` PR #248, a session picked up through
`/relay take` had the Next step "refresh the squash proposal to mention the
footer". It edited the working file, then built the find-and-PATCH itself:
`cd … && id=$(gh api …/issues/<n>/comments …) && gh api -X PATCH …/issues/comments/$id -F body=@…`.
Auto mode denied it (External System Writes), and the agent handed the operator
a phrase authorizing that PATCH — instead of running
`scripts/pr-comment.sh squash <n> <file>`, which does exactly this and is the
one command the allow rules cover.

The cause is reachability: the script is named only in `/squash-message` Step 4
and `/finalize`'s attest/revoke/merge files. A session that touches the sticky
comment from anywhere else — a relay's Next step, an operator's ask, memory —
never meets it, and nothing on the hand-rolled path points back.

## The fix: catch the call, not the reader

Three layers, strongest first. Only the first would have stopped the incident on
its own; the other two cost a sentence each and cover what the first cannot see.

### 1. `PreToolUse` hook: `.claude/hooks/sticky-comment-nudge.py`

Denies a hand-rolled write of a sticky comment, once, with a reason naming the
command to run instead. A `PreToolUse` hook runs before auto mode's classifier,
so the agent is redirected before any denial exists and no phrase is ever asked
for.

**What it catches** — a write whose body leads with one of the script's markers
(`Proposed squash`, `<!-- finalize-attestation`):

- **`Bash`**: a simple command running `gh` (through the same wrapper unwrapping
  the file-tools nudge does), anywhere in a chain or `$(…)`, that is either
  - `gh api <path>` with `<path>` matching `issues/<n>/comments` or
    `issues/comments/<anything>` and a write — `-X`/`--method` `POST`/`PATCH`,
    or a `body` field (`-f`/`-F`/`--field`/`--raw-field`), since `gh api` posts
    whenever a field is given; or
  - `gh pr comment` (any of `--body`/`-b`, `--body-file`/`-F`, `--edit-last`).
- **The body** is read from where the command names it: inline `body=<text>` /
  `--body <text>`, or a file — `body=@<path>`, `--body-file <path>` — whose
  leading bytes are checked, resolved against the payload's `cwd`. A body the
  hook cannot resolve (`body=@$f`, stdin) is let through: the hook stays narrow
  and never nudges a comment it cannot prove is a sticky one.
- **`mcp__github__add_issue_comment` / `mcp__github__update_issue_comment`**
  whose `body` leads with a marker — the same write through the other door the
  classifier also gates.

**What it says** — the kind, and the exact line to run:
`scripts/pr-comment.sh <kind> <n> <file>`, "from the repository root, spelled
exactly so, nothing chained in front", plus `--update-only` for a refresh that
must not create one. When the body was inline, it says to write it to the
working file `/squash-message` keeps first. The PR number is filled in when the
path carries it (`issues/<n>/comments`), left as `<n>` when the path had only a
comment id.

**Deny once, then let through**, on the file-tools nudge's own mechanic (the
command's digest in the session's state file): a second identical attempt is the
agent saying it means it — debugging a failing script, say — and the classifier
still stands behind it. A `DELETE`, or a read, is never touched: the script does
neither.

**Fails open** like its sibling: unreadable payload, untokenisable command,
unreadable file, unrecordable state → allowed, with a line on stderr.

Wired in `.claude/settings.json` `PreToolUse` (the `Bash` group, and a new
matcher for the two MCP tools), in `scripts/multi-repo-hooks.py`'s list, and in
the update-muthur catalog (`g2-pr-loop.md`, beside the script's entry).

### 2. CLAUDE.md § "Key principles", the auto-mode-denial bullet

One clause, through a staged copy (`scripts/staged.sh`), since CLAUDE.md loads
on every turn: before writing the operator a phrase, check
`.claude/settings.json` `permissions.allow` for a narrow script that does the
denied action, and run that instead. The allow list is the registry, so the
clause covers scripts added later without naming any. This is the layer for a
hand-rolled write the hook did not recognize — a body it could not resolve, a
new sticky kind.

`.claude/hooks/permission-denied-phrase.sh`'s Stop reason gets the same sentence
ahead of its phrase instructions, for a reply that forgot both.

### 3. `/relay` Step 2, item 8 — the Next step names its skill

One sentence: a Next step whose action a skill owns names that skill — "refresh
the squash proposal" is `/squash-message update-only`, a re-attestation is
`/finalize`. The successor's `/relay take` dispatches the Next step as a task,
so a named skill is loaded instead of reconstructed. Not specific to the sticky
comments: any skill-owned artifact (a plan's lifecycle, the PR body) has the
same seam.

## What this declines

- **Widening `/squash-message`'s description** so it triggers on "refresh the
  squash proposal": the description is always loaded, and the incident's agent
  had the words and still did not load the skill — the call site is the reliable
  place.
- **Denying every `gh api` comment write**: comments that are not sticky ones
  (review replies, ordinary PR comments) have no script, and a nudge naming none
  is noise.

## Tests

`scripts/test_sticky_comment_nudge.py`, beside
`scripts/test_file_tools_nudge.py` (picked up by `check-muthur.sh` with the
other `scripts/test_*.py`):

- the incident's command verbatim (chained, `$id`, `-F body=@file` with a squash
  file) → denied, reason names `scripts/pr-comment.sh squash`;
- the same command a second time → allowed;
- `gh pr comment <n> --body-file <attestation file>` → denied, `attestation`;
- `-f body='Proposed squash…'` inline → denied;
- a POST of a body without a marker, a GET listing, a `DELETE` → allowed;
- `body=@$f` → allowed;
- `scripts/pr-comment.sh squash 248 f.md` itself → allowed;
- the MCP `update_issue_comment` with a marker body → denied; without → allowed.

`./scripts/vet.sh` at `/finalize`.

## DRY notes

- **Shared, extracted**: the shell parsing in `file-tools-nudge.py` —
  `strip_heredocs`, `tokens`, `simple_commands`, `program`, `WRAPPERS`, `unwrap`
  — moves to `.claude/hooks/shell_words.py` and both hooks import it. The
  hyphenated hook file cannot be imported, and a second copy of a heredoc-aware
  tokeniser is exactly the drift CLAUDE.md warns about.
- **Shared, extracted**: the deny-once record (digest of the command, looked up
  then appended to the session's state file, fail-open on `OSError`) moves into
  `session_state.py` as one function; both hooks call it.
- **Duplicated, guarded**: the markers. Parsing them out of
  `scripts/pr-comment.sh`'s `case` arms at hook time would make a shell script a
  data file; instead they are a constant in the hook with a comment naming the
  script as the home, and a test asserts each marker in the hook appears in the
  script's `case`, so a new kind or a changed marker fails vet instead of
  drifting.
- **Not shared**: the MCP branch's detection is a field read on `tool_input`,
  which shares nothing with the shell path but the marker check.

## Open questions

1. **Layer 2 in CLAUDE.md, or only in the Stop hook?** Recommended: both. The
   Stop hook alone would not have fired in the incident — the reply already held
   its fenced phrase, which the hook takes as compliance — and the clause costs
   one line on every turn. Against: today the allow list holds one script, which
   layer 1 already guards.
2. **Deny once, or always?** Recommended: once, as above. "Always" would make
   the script the only path even when it is the thing failing.

## Commits

1. `refactor:` extract `shell_words.py` and the deny-once record from the
   file-tools nudge (its tests unchanged and green).
2. `feat:` the sticky-comment nudge hook, its wiring, catalog entry and tests.
3. `feat:` the CLAUDE.md clause (staged) and the Stop-hook sentence.
4. `feat:` `/relay`'s Next step names the skill that owns it.
