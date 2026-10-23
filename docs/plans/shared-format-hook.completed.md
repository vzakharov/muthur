# A shared format-on-edit hook, driven by a per-repo list

## The task

A PostToolUse hook that formats the file an agent just edited, plus the vet-side
check of the same rule, generic over the formatter and the paths. Muthur today
has this only for Markdown (`format-md.sh` + `check-markdown-wrap.sh`); life
grew a prettier-and-`apps/`-specific copy for code. The generic version replaces
both, and life's copy becomes one entry in a list.

## Decisions

- **The per-repo part is data: `.claude/format.json`** (the operator's option
  1). A top-level array of entries, each
  `{"name", "files": [glob…], "format": [argv…], "check": [argv…]}`. Data rather
  than a project script (option 2), because what an adopter writes is one entry
  rather than a shell dispatcher, and `/update-muthur` merges an array of
  entries more cleanly than a hand-edited script; an entry's command can still
  be any script, so option 2's generality survives inside option 1. Not prettier
  generalised (option 3): it ties every adopter to prettier.
- **Markdown moves in.** Muthur's list ships one entry, the Markdown wrap; the
  stub for code is the absence of a code entry. Keeping `format-md.sh` beside a
  generic hook would leave two hooks doing the same thing in two copies.
- **One script, two modes: `scripts/format.py hook` and
  `scripts/format.py check`**, so the hook and the vet run cannot disagree on
  which file an entry covers. Python rather than bash: the config is parsed and
  validated at the boundary, and the glob matcher is one function both modes
  call.
- **Globs are `fnmatch` patterns against the repo-relative path**, `*` crossing
  `/` — the same reading as git's default pathspec and bash `case`, which the
  two existing scripts used.
- **The hook formats exactly what the check would check:** a file inside the
  project that git does not ignore. That subsumes life's `node_modules`
  exclusion and the out-of-project rule `format-md.sh` carried.
- **Every matching entry runs, in list order** (an `eslint --fix` entry and a
  prettier entry on the same `.ts` both apply).
- **Failure is loud.** A formatter failure in the hook exits 2 with
  `<name> could not format <path>:` and its output; a malformed
  `.claude/format.json` exits 2 in the hook and 1 in the check. No config file
  is a quiet 0 in both.
- **The check reads a staged always-loaded file through its copy** (one
  `scripts/staged.sh list`, when that script exists), as
  `check-markdown-wrap.sh` did; any other file is checked as itself.

## Steps

1. `scripts/format.py` — load + validate config, matcher, `hook` and `check`.
2. `.claude/format.json` with the Markdown entry (`scripts/prettier.sh --write`
   / `--check`, `--log-level warn`), patterns `*.md`, `*.md.staged`.
3. Delete `.claude/hooks/format-md.sh` and `scripts/check-markdown-wrap.sh`;
   rewire `.claude/settings.json` (PostToolUse `scripts/format.py hook`) and
   `scripts/vet.sh` (line + header note).
4. `scripts/test_markdown_wrap.py` → `scripts/test_format.py`: the Markdown
   cases kept, plus generic ones against a fake formatter entry (no npx).
5. Repoint every mention: `scripts/multi-repo-hooks.py` `PER_REPO` and its test,
   `.claude/hooks/lib.sh` header, `.claude/rules/markdown-wrap.md`, the
   update-muthur catalog (G1 entries, G4's `lib.sh` and `settings.json` entries,
   G2's mention).
6. Vet, then `[attn adopters]` in the commit subject: an adopter's
   `settings.json` still wires `format-md.sh`.

What life adds after `/update-muthur`, replacing its two scripts:

```json
{
  "name": "code format",
  "files": ["apps/*.vue", "apps/*.ts", "apps/*.mjs"],
  "format": ["scripts/prettier.sh", "--write", "--log-level", "warn"],
  "check": ["scripts/prettier.sh", "--check", "--log-level", "warn"]
}
```

## DRY notes

- **Shared:** the matcher and the config loader, one copy in `format.py` that
  both modes call — the point of putting the hook and the check in one file.
  `scripts/prettier.sh` stays the only prettier invocation; `staged.sh list` is
  reused rather than reimplemented.
- **Removed duplication:** `format-md.sh` and life's `format-code.sh` were the
  same hook with different `case` lines; both collapse into entries.
- **Not reused:** `.claude/hooks/lib.sh` is bash; the Python hook needs only
  `json.load(stdin)` and `CLAUDE_PROJECT_DIR`, so a shared helper would buy
  nothing. `scripts/check-stop-words.py --hook` (life) is the precedent for one
  script serving both a hook and vet.
