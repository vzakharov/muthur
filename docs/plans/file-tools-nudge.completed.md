# Turn away the first Bash read/edit of a file

## Why

CLAUDE.md § "Key principles" says to read and edit files with `Read`/`Edit`/`Write`
in every permission mode, and agents keep reaching for `sed`, `cat`, `head` and
heredocs anyway. Part of the cause sits outside the repo: the harness's auto-mode
prompt tells the agent that shell edits are fine, and that text arrives on every
turn, where the CLAUDE.md line is one bullet among twenty.

A reminder at the moment of the call beats a sentence in the prefix. The
operator's shape: the first such call fails with "did you forget the
instructions?", and a repeat goes through — the aim is to catch the accidental
habit, not to forbid a genuine mass substitution.

## Shape

A `PreToolUse` hook on `Bash`, `.claude/hooks/file-tools-nudge.py`.

- **Detection** — tokenise the command with `shlex` (punctuation mode, newline as
  a separator; heredoc bodies stripped first, since they carry unbalanced quotes),
  split it into simple commands on `; & | && || ( ) $( \n`, and flag:
  - **reads** → `Read`: `cat`, `head`, `tail`, `less`, `more`, `nl` with a file
    operand; `sed` with a file operand and no `-i`;
  - **edits** → `Edit`: `sed -i`, `perl -i`/`-pi`, `awk -i inplace`;
  - **writes** → `Write`: `cat`/`echo`/`printf` redirected into a file, `tee <file>`.

  A command after `xargs`, `sudo`, `env`, `command` or `find … -exec` counts as a
  command. `/dev/`, `/proc/`, `/sys/` and `-` are not files. A pipeline reading
  stdin (`git log | head -5`) is not flagged: no file operand.
- **Retry** — the unit is the identical command string, per session. The first
  time a flagged command is seen its hash goes into
  `tmp/file-tools-nudge/<session_id>` and the call is denied; the same command
  again is allowed. So every *new* shell read/edit gets one reminder, and a
  deliberate one costs a single retry.
- **Deny** — `permissionDecision: "deny"` with a reason naming what was detected,
  the tool to use instead, that CLAUDE.md wins over the harness's shell-edit
  text, and that re-running the identical command goes through.
- **Fails open.** Unparseable command, bad payload, unwritable state → allow and
  say so on stderr. A deny that cannot be recorded would deny forever.
- Subagents included: the principle binds them too.

Python rather than bash + `lib.sh`, because the detection is tokenising, which
`shlex` does and a regex over the raw string does not.

## Steps

- [ ] `.claude/hooks/file-tools-nudge.py` — detection, state, deny output.
- [ ] `.claude/settings.json` — `PreToolUse` entry, matcher `Bash`.
- [ ] `scripts/test_file_tools_nudge.py` — drives the hook as the harness does
      (payload on stdin): flagged and unflagged commands across the forms above,
      deny-then-allow on the same command, a different command denied afresh,
      separate sessions kept apart, bad payload exits 0 silent. Picked up by
      `check-muthur.sh` by its name.
- [ ] Catalog: a G1 row for the hook (it enforces a G1 principle; requires
      `python3` ≥3.9 and the `.claude/settings.json` wiring), and the
      `.claude/settings.json` row names the `PreToolUse` entry.
- [ ] `./scripts/vet.sh`.

## DRY notes

- No shared helper is reused: `.claude/hooks/lib.sh` is the bash hooks' payload
  and output layer, and this hook is Python. Porting `lib.sh`'s dozen lines of
  `jq` calls into a shared Python module for one consumer would be a module with
  one caller.
- The per-session state under `tmp/<feature>/<session_id>` mirrors
  `.claude/context-budget/`'s layout without sharing code — two hooks each
  writing one file is not an abstraction.
- The test follows `test_context_budget.py`'s harness-driving shape rather than
  importing the hook, so it tests the hook's contract, not its internals.

## Not in scope

- CLAUDE.md is not edited: the deny reason carries its own explanation, and an
  edit there would need staging for no behavioural gain.
- `grep`/`find` are not flagged: CLAUDE.md names only reading and editing.
