# PR #73: feat: name and greet the session's operator at startup

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/73
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/operator-handle-hook-p25kpw
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-12T14:56:18Z
- **Updated:** 2026-09-14T18:54:42Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **The agent never knew who it was talking to.** The harness reports an email; `git config user.email` is the commit identity. Resolving the operator meant spending a turn on `gh api user`, and only if the session remembered to. `.claude/hooks/operator-voice.sh` now does it at startup and prints the answer into the session context.
- **It names the person, not the handle.** `gh api user` carries `.name`, so the hook prints `Vova Zakharov (@vzakharov)` and `voice.md` asks for a greeting by that name in the session's first reply. Where `.name` is empty the message falls back to the handle alone and there is nothing to greet with, so nobody gets hailed as "hey vzakharov".
- **It prints the operator's entry, not a pointer to it.** `CLAUDE.md` used to import `operators.md` whole, so every session carried every person's entry and still had to pick its own out of the list. The import is gone: a session applies one entry, so importing the set spent context on everyone else's, every session. Cost goes from O(team) to O(1), and the "if they have one" conditional disappears — either an entry was printed or the hook said there is none.
- **An entry is a filename and nothing else.** `.claude/voice/operators/<handle>.md`, the file's whole content being the entry, and the directory holds no other kind of file. A heading was a thing an entry could get wrong, and getting it wrong failed silently — the entry reached no session while the preference sat in the repo looking done. There is no syntax to violate, so the lookup is `cat`.
- **What the hook can't determine, it says.** `.type` distinguishes a token minted for a human from one of the agent's own, because a bare login would be trusted in exactly the case where it names the agent. Three non-answers — no entry, a `Bot` token, `gh` out of reach — each print explicitly rather than silently.
- **Two rules moved to stay correct.** "An entry cannot lower a bar" is now in `voice.md`, which stays imported — it governs every reply and had been riding on the import that went away. `voice.md` also carries the write-it-down instruction and the line separating one person's preference from the team's: a manner rule for everyone is an edit to `voice.md`, made where the team can see it, never an entry promoted out of one person's file.

### Since the first review

Ten comments, all addressed; `default.md`, `operators/README.md` and `scripts/check-operator-entries.sh` all went away rather than getting fixed.

- `default.md` and `README.md` were both reserved names in a directory keyed on GitHub logins, and both are real logins. Dropping them leaves `operators/` holding nothing but `<handle>.md`, so the collision class is gone rather than narrowed.
- The README's surviving content is two clauses in `voice.md`, which every session already loads. A path-globbed rule would have loaded when a session *touches* `operators/` — after you have decided to write an entry; the moment that matters is when someone states a preference, which happens anywhere.
- `check-operator-entries.sh` guarded a case mismatch the hook can no longer produce: the login is lowercased once, and that form is both what the message prints and what names the file.

### Since the second review

Two comment notes, then two design questions that were opened for discussion and answered before anything was built.

- **Startup is three hooks, not one.** `gh-shim.sh`, `install-deps.sh` and `operator-voice.sh`, enumerated separately under the one `SessionStart` matcher. The three jobs shared no variable, no ordering and not even the same gate — the shim and the install are remote-only where the operator lookup runs everywhere. What they shared was one `set -euo pipefail`, under which a slip in one job kills the rest silently; the operator lookup died that way twice during this branch's review, and in a split file neither death could have touched the shim. An adopter gets three copyable files with three conditions in place of one file and a paragraph on which parts to delete.
- **The voice rule has its own home.** `.claude/voice/voice.md` and `.claude/voice/operators/`. It is in force from every session's first reply, where a skill is something a session invokes — it sat under `.claude/skills/plainly/` only because that is where it was written. `/plainly` keeps `SKILL.md` as the procedure over the rule and cites it by path; `CLAUDE.md` imports the rule from the new home.
- **`voice.md` now covers agents that have no SessionStart hook.** That is Claude Code's mechanism, so an agent running elsewhere resolves the handle and reads the entry by hand on the first turn. The filename being the whole lookup is what makes that reproducible without the hook.
- **`check-skill-catalog.sh` checks more than skill pointers.** Its first assertion matched `@.claude/skills/<name>/SKILL.md` only, so `CLAUDE.md`'s import of `voice.md` would have gone unchecked at its new path — and `plan-or-go.md` had been unchecked all along. It now covers every `@`-reference into `.claude/`.
- The catalog's one G4 row is three, with three separate conditions, and `.claude/voice/` gets a G1 row of its own beside `/plainly`.

### Since the third review

Three comments, all on the same seam: the move detached the voice rule from `/plainly` physically, and left the prose and the catalog still describing them as halves of one thing.

- **The dependency runs one way now.** `voice.md` ended by naming `/plainly` "the long version", as an `@`-reference — so the checker held the always-resident rule hostage to a skill a session invokes. Cut; `CLAUDE.md` already introduces `/plainly` a paragraph above the import. `plainly/SKILL.md` opens as the procedure it is rather than as the other half of `voice.md`, and its pass no longer cites a G4 hook from a G1 skill.
- **The catalog's `Pulls in` column was recording the wrong relation.** It was defined as `@`-references only, and none of these dependencies is one: `operator-voice.sh` reads a file at a fixed path, `/override-gh`'s body asserts the shim is installed. Both fail as silently as a dangling pointer and no check sees either. Widened to what an item cannot work without, `@`-referenced or not — so `.claude/voice/` pulls in only `/tend-prose`, and `/override-gh` gains the `gh-shim.sh` row it always depended on.
- **Neither pair turns out to be mutual.** The hook needs the entries; the entries do not need the hook, `voice.md` having the lookup done by hand under any harness without `SessionStart`. Same for the shim, which runs whether or not the marker skill exists. In both cases the depended-on half adopts alone, which is the general form § "Closure is not optional" now carries.

### Since the fourth review

Two questions on the catalog's **Pulls in** column, and both landed: the column
had grown a third kind of dependency that was not one.

- **`/plainly` carries its own standard.** What "plainly" means does not vary by
  team — the six defects are stated in the skill — so claiming it derives from
  `.claude/voice/` described where the text used to live, not a requirement. A
  house voice can be set deliberately less plain and still want a way to ask for
  something plainer. The two agree here and need not; each now adopts alone.
- **`/override-gh` and `gh-shim.sh` answer different problems.** The marker
  answers a system prompt that denies `gh` exists; the shim answers an egress
  proxy that blocks it. A harness making no such claim wants the hook alone; an
  unproxied session wants the marker alone. The skill's shim paragraph is now
  conditional and names what its absence looks like, so the row drops to `—`.
- **Prose asserting a sibling is present is a defect, not a dependency.** The
  column is back to two kinds — the `@`-reference the checker proves, and a file
  read at a fixed path when the item runs — and § "Closure is not optional" says
  to fix the prose rather than record it. The test: ask what stops working when
  one is absent, because "shares a subject" reads identically from the column.

### Since the fifth review

Six comments, one finding: the last two rounds answered "does this depend on
that?" by writing down that it does not. A reader of the current tree never
asks, so each sentence read as a constraint and carried none.

- **`/plainly` stops describing whose standard its defects are**, and the pass
  loses its "apply the operator's entry" step — the entry is in force from a
  session's first reply, so a step inside one skill could only restate that. The
  same instruction comes out of the frontmatter. What survives is the one thing
  the names do not give an adopter: the two drift independently, and neither
  tracks the other.
- **`/override-gh` states the shim unconditionally again.** The case for the
  marker alone was a harness that makes no false `gh` claim yet still proxies —
  thin enough that documenting it cost more than it told anyone.
- **The catalog drops both description tails and the third dependency kind.**
  **Pulls in** names siblings an item cannot work without and stops enumerating
  how the pointer is spelled; § "Closure is not optional" keeps the one
  operational fact — the script sees `@`-references only, so a fixed-path read
  has the column as its sole record.

## QA Checklist

- [ ] `handle` — start a fresh session in this repo and read the first lines of context: it should name you and print your entry verbatim, with no tool call spent resolving it.
- [ ] `greeting` — that session's first reply opens by greeting you by name, not by handle.
- [ ] `isolation` — the point of the split: make `gh-shim.sh` fail (run it with `gh` off `PATH`) and confirm `operator-voice.sh` still prints its line. Under the old single file a failure in either job could take the other down.
- [ ] `no-name` — stub `gh` to return an empty third field; the message falls back to `@handle` alone and the reply greets you by nothing.
- [ ] `uppercase-login` — stub `gh` to return `VZakharov\tUser\tVova Zakharov`; it must still resolve `vzakharov.md`.
- [ ] `no-entry` — move `.claude/voice/operators/vzakharov.md` aside, run `.claude/hooks/operator-voice.sh`, confirm it reports no entry **and still exits 0 with output** (this path died silently before the `|| true` fix).
- [ ] `bot-token` — stub `gh` to return `something[bot]\tBot\t`, run `operator-voice.sh`, confirm it names no operator and says to ask.
- [ ] `gh-down` — run `operator-voice.sh` with `gh` absent from `PATH` (coreutils intact) and with a `gh` that exits 1; both should report the operator unresolved and exit 0. Run `gh-shim.sh` the same way and it should print the setup-script notice and exit 0.
- [ ] `no-import` — confirm `CLAUDE.md` imports `.claude/voice/voice.md` and that a session's context no longer carries anyone else's entry.
- [ ] `local` — run all three with `CLAUDE_CODE_REMOTE` unset: `operator-voice.sh` runs, the shim and the dependency install no-op.
- [ ] `wiring` — confirm the three commands in `.claude/settings.json` all fire on a real session start, in the order listed.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `handle` | integration | ❌ | No test drives the hooks. Would stub `gh` and assert the printed line. |
| `greeting` | manual-only | — | Whether a reply opens with a greeting is model behavior, not something this repo can assert. |
| `isolation` | integration | ❌ | The regression the split exists to prevent, so the row that most wants a test. |
| `no-name` | integration | ❌ | Assert the message degrades to `@handle` with no name in it. |
| `uppercase-login` | integration | ❌ | The case the deleted check guarded; now the hook's own job. |
| `no-entry` | integration | ❌ | Assert non-empty stdout and exit 0 with no entry file. |
| `bot-token` | integration | ❌ | Stub `gh` to emit a `Bot` type; assert no handle is asserted as the operator. |
| `gh-down` | integration | ❌ | Two stubs each, for two hooks. |
| `no-import` | manual-only | — | What reaches a session's context is a harness behavior. |
| `local` | integration | ❌ | Assert the gate: one hook speaks, two say nothing. |
| `wiring` | manual-only | — | Whether Claude Code runs every entry in the array is the harness's behavior, not this repo's. |

Every row above except the three manual-only ones was **run by hand on this branch** and passes. What is missing is automation, not verification.

**Coverage gap worth naming:** eight of eleven rows are automatable and none are automated, `check-operator-entries.sh` having been the one check and now deleted. This branch is where the hook's behavior got two silent-failure bugs — the `set -e` death on a missing entry file, and a `[ -n "$name" ] && …` one-liner that would have killed the hook for every operator whose profile has no name. Both were caught by hand, and the split is the structural half of the same fix.

There is also a trap any test of `gh-shim.sh` must handle, found by walking into it: the shim is written from whatever `gh` the running `PATH` resolves, and it outlives the run, so testing under a stubbed `PATH` repoints the session's own `gh` at the stub and every later `gh` call fails once the stub is cleaned up. Point `$HOME` at a scratch directory instead. The hook says so in a comment.

`scripts/test_authorship.py` is the precedent for a test at this layer, so a `test_hooks.py` is feasible — worth filing rather than doing here.

https://claude.ai/code/session_01VPCzziE6gnPK4o4QH6Zra6

---

## Comments

### Comment by @vzakharov (agent) on 2026-09-12T14:57:05Z

[https://github.com/vzakharov/muthur/pull/73#issuecomment-5646656856](https://github.com/vzakharov/muthur/pull/73#issuecomment-5646656856)

Proposed squash title/body:

```
feat: name and greet the session's operator at startup (pr #73)
```

```
The agent had no way to know which person it was talking to. The harness
reports an email, and the commit identity is the agent's own, so the
GitHub handle that keys a manner preference had to be resolved with a
tool call the session had to think to make — and mostly did not, leaving
stated preferences unapplied.

The session-start hook now resolves the operator and prints their entry
into the session before the first reply, naming them by the name on
their GitHub profile so a session opens by greeting a person rather than
a handle. It reports the token's account type alongside the login, since
a token minted for a human names that human and one of the agent's own
names the agent, so a bare login would be trusted in exactly the case
where it names the wrong party; where the hook cannot answer at all, it
says which of the three ways it failed. CLAUDE.md in turn stops
importing the entries — a session applies one, so importing the set
spent context on everyone else's, every session.

Entries move from headings inside a single file to one file per handle,
the file's whole content being the entry, and the directory holds
nothing else. A heading was a thing an entry could get wrong, and a
wrong one failed silently, reaching no session while the preference sat
in the repo looking done. A filename has no syntax to violate, so the
lookup is `cat`; the login is lowercased once and printed in that same
form, so the spelling an agent writes an entry under is the spelling the
lookup uses and there is nothing left to validate. A manner rule meant
for everyone is an edit to voice.md rather than an entry promoted out of
one person's file behind their back — voice.md carrying that, and what
an entry may do, which had been riding on the import that went away.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

### Comment by @vzakharov (agent) on 2026-09-14T09:46:32Z

[https://github.com/vzakharov/muthur/pull/73#issuecomment-5662085977](https://github.com/vzakharov/muthur/pull/73#issuecomment-5662085977)

Both design threads are implemented in 01de783. This lands as a conversation comment rather than two threaded replies because the review carrying your two answers is still **pending** — GitHub allows one pending review per user, and a threaded reply would open a second one, so the API refuses it (422). Submitting yours releases the thread replies; nothing here waits on that.

**The hook split** (`.claude/hooks/session-start.sh`:1) — three hooks now, three entries under the one `SessionStart` matcher: `gh-shim.sh`, `install-deps.sh`, `operator-voice.sh`.

On the name you flagged: `name-operator.sh` described half the job. The hook resolves who the operator is *and* prints how they want to be talked to, and the second half is the part every reply actually uses — naming only the first is what made it read like a lookup with no consumer. `operator-voice.sh` names both halves, and it now says the same word as its data: the file it reads is `.claude/voice/operators/<handle>.md`.

The rest of the price is paid. The dozen path citations across CLAUDE.md, ADOPTING.md, `/detemplate`, `/override-gh`, the catalog and `voice.md` each repoint to whichever of the three they meant, and the catalog's single G4 row is three rows with three separate conditions.

**The voice move** (`.claude/skills/update-muthur/catalog.md`:118) — `.claude/voice/voice.md` and `.claude/voice/operators/`, imported by CLAUDE.md from the new path. `/plainly` keeps `SKILL.md` alone and cites the rule rather than housing it.

Your note for non-Claude agents is in `voice.md` as its own paragraph. `SessionStart` is Claude Code's mechanism, so an agent running anywhere else does the lookup by hand on the first turn: take the handle from whatever already names the operator, or ask, then read `operators/<handle>.md` lowercased. The filename being the whole lookup is what makes that reproducible by hand at all.

**One thing the move surfaced**, fixed in the same commit. `check-skill-catalog.sh` only checked references of the shape `@.claude/skills/<name>/SKILL.md`, so CLAUDE.md's import of `voice.md` would have gone unchecked at its new path — and `plan-or-go.md` had been unchecked all along, which nobody had noticed. The assertion now covers every `@`-reference into `.claude/`.

All three hooks are exercised by hand: the operator lookup on all four of its branches (entry found, no entry, `Bot` token, `gh` absent), the shim with the gate on and off and with `gh` missing, the dependency stub both ways. `scripts/vet.sh` is clean.

---

## Review threads

### `.claude/hooks/session-start.sh`:106 — resolved

```diff
@@ -74,9 +77,71 @@ EOF
   chmod +x "${shim_dir}/gh"
 }
 
-install_gh_shim
+if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
+  install_gh_shim
+
+  # --- 2. Keep dependencies in sync with the lockfile ---------------------
+  cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"
+
+  # TODO: install dependencies for your stack
+fi
+
+# --- 3. Name the operator ------------------------------------------------
+# Outside the remote gate: the agent needs the handle wherever it runs, and `gh`
+# reaches the API through the proxy as well as around it, so this works whether
+# or not job 1 installed the shim.
+#
+# `.type` is the load-bearing field: a token minted for a human names that human
+# (`User`), one of the agent's own names the agent (`Bot`), and only the first
+# answers "who am I talking to". Hence two messages rather than a bare login,
+# which would be trusted in exactly the case where it is wrong.
+#
+# The handle then names that person's entry file and the hook prints the entry
+# itself, which is why `CLAUDE.md` imports none of them: one session applies one
+# entry, so importing the set spends context on everyone else's, every session.
+#
+# The filename is the whole lookup — no parse, so no syntax an entry can get
+# wrong. `default.md` is the one reserved name, printed for everyone. Handles are
+# lowercased because GitHub treats them case-insensitively and the filesystem
+# does not.
```

**@vzakharov (human)** — 2026-09-12T15:01:37Z

tighten

**@vzakharov (agent)** — 2026-09-12T15:34:32Z

Tightened to six lines in 2b8153f — and most of what it explained is gone with `default.md` and the lowercase guard, so there was less left to say.

---

### `.claude/hooks/session-start.sh`:115 — resolved

```diff
@@ -74,9 +77,71 @@ EOF
   chmod +x "${shim_dir}/gh"
 }
 
-install_gh_shim
+if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
+  install_gh_shim
+
+  # --- 2. Keep dependencies in sync with the lockfile ---------------------
+  cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"
+
+  # TODO: install dependencies for your stack
+fi
+
+# --- 3. Name the operator ------------------------------------------------
+# Outside the remote gate: the agent needs the handle wherever it runs, and `gh`
+# reaches the API through the proxy as well as around it, so this works whether
+# or not job 1 installed the shim.
+#
+# `.type` is the load-bearing field: a token minted for a human names that human
+# (`User`), one of the agent's own names the agent (`Bot`), and only the first
+# answers "who am I talking to". Hence two messages rather than a bare login,
+# which would be trusted in exactly the case where it is wrong.
+#
+# The handle then names that person's entry file and the hook prints the entry
+# itself, which is why `CLAUDE.md` imports none of them: one session applies one
+# entry, so importing the set spends context on everyone else's, every session.
+#
+# The filename is the whole lookup — no parse, so no syntax an entry can get
+# wrong. `default.md` is the one reserved name, printed for everyone. Handles are
+# lowercased because GitHub treats them case-insensitively and the filesystem
+# does not.
+OPERATORS_DIR="$(dirname "$0")/../skills/plainly/operators"
+
+# `|| true` because both files are optional and `set -e` would otherwise take the
+# whole hook down on a missing one — silently, since the caller assigns from a
+# command substitution.
+operator_entry() {
+  local handle
+  handle="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
+  cat "$OPERATORS_DIR/default.md" "$OPERATORS_DIR/$handle.md" 2>/dev/null || true
```

**@vzakharov (human)** — 2026-09-12T15:03:27Z

`default` could be -- and as it comes out -- *is* a real github user. Let's use an underscore as it's not allowed for github handles iirc.

**@vzakharov (agent)** — 2026-09-12T15:34:33Z

You're right that it collides, and the underscore would have worked — but the file is gone in 2b8153f per your later comment on the README, so there's no reserved name left to pick. Deleting `README.md` took the second collision with it: `operators/` is now nothing but `<handle>.md`.

---

### `.claude/hooks/session-start.sh`:147 — resolved

```diff
@@ -74,9 +77,71 @@ EOF
   chmod +x "${shim_dir}/gh"
 }
 
-install_gh_shim
+if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
+  install_gh_shim
+
+  # --- 2. Keep dependencies in sync with the lockfile ---------------------
+  cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"
+
+  # TODO: install dependencies for your stack
+fi
+
+# --- 3. Name the operator ------------------------------------------------
+# Outside the remote gate: the agent needs the handle wherever it runs, and `gh`
+# reaches the API through the proxy as well as around it, so this works whether
+# or not job 1 installed the shim.
+#
+# `.type` is the load-bearing field: a token minted for a human names that human
+# (`User`), one of the agent's own names the agent (`Bot`), and only the first
+# answers "who am I talking to". Hence two messages rather than a bare login,
+# which would be trusted in exactly the case where it is wrong.
+#
+# The handle then names that person's entry file and the hook prints the entry
+# itself, which is why `CLAUDE.md` imports none of them: one session applies one
+# entry, so importing the set spends context on everyone else's, every session.
+#
+# The filename is the whole lookup — no parse, so no syntax an entry can get
+# wrong. `default.md` is the one reserved name, printed for everyone. Handles are
+# lowercased because GitHub treats them case-insensitively and the filesystem
+# does not.
+OPERATORS_DIR="$(dirname "$0")/../skills/plainly/operators"
+
+# `|| true` because both files are optional and `set -e` would otherwise take the
+# whole hook down on a missing one — silently, since the caller assigns from a
+# command substitution.
+operator_entry() {
+  local handle
+  handle="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
+  cat "$OPERATORS_DIR/default.md" "$OPERATORS_DIR/$handle.md" 2>/dev/null || true
+}
+
+name_the_operator() {
+  local identity
+  identity="$(gh api user --jq '[.login, .type] | @tsv' 2>/dev/null || true)"
 
-# --- 2. Keep dependencies in sync with the lockfile -----------------------
-cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"
+  if [ -z "$identity" ]; then
+    echo "session-start: the operator's GitHub handle is unresolved (\`gh\` is unavailable or could not reach the API). Ask them for it, then read their entry under .claude/skills/plainly/operators/."
+    return 0
+  fi
+
+  local login="${identity%%	*}" type="${identity##*	}"
+
+  if [ "$type" != "User" ]; then
+    echo "session-start: the GitHub token in this session belongs to ${login}, a ${type} account — that is the agent's own identity, not the operator's. Ask the operator for their handle, then read their entry under .claude/skills/plainly/operators/."
+    return 0
+  fi
+
+  local entry
+  entry="$(operator_entry "$login")"
+
+  if [ -z "$entry" ]; then
+    echo "session-start: the operator is @${login} — the GitHub token in this session is that user's own. They have no entry under .claude/skills/plainly/operators/."
+    return 0
+  fi
+
+  echo "session-start: the operator is @${login} — the GitHub token in this session is that user's own. How they want to be talked to, from .claude/skills/plainly/operators/, applying to every reply:"
+  echo
+  echo "$entry"
+}
 
-# TODO: install dependencies for your stack
+name_the_operator
```

**@vzakharov (human)** — 2026-09-12T15:05:45Z

how about we also ask the agent to greet the operator in the beginning of their first message -- nice touch eh? (This depends on whether we can fetch the *name*, not just the handle -- i.e. I don't want to be greeted as "hey vzakharov"). By "name" I mean this, as shown in my profile

<img width="185" height="72" alt="Image" src="./attachments/fd8411e9-367c-4c3c-bae2-df7bec0ca06c.png" />

**@vzakharov (agent)** — 2026-09-12T15:34:44Z

We can — `gh api user` returns `.name`, which for you is "Vova Zakharov". Done in 2b8153f: the hook fetches it alongside the login and prints `Vova Zakharov (@vzakharov)`, and `voice.md` asks for a greeting by that name in the session's first reply. Where `.name` is empty the message falls back to the handle alone and `voice.md`'s "by the name the hook gives" quietly has nothing to give, so nobody gets greeted as "hey vzakharov".

---

### `.claude/skills/plainly/operators/README.md`:1 — resolved

**@vzakharov (human)** — 2026-09-12T15:06:22Z

why is this a readme and not an operator dir-globbed skill? (Not insisting if you think that's the right way)

**@vzakharov (agent)** — 2026-09-12T15:34:45Z

Neither, in the end — it's deleted in 2b8153f and its two surviving sentences moved into `voice.md`.

A dir-globbed rule loads when a session *touches* `operators/`, which is after you've decided to write an entry. The moment that actually matters is when someone states a preference, and that happens in a session touching anything at all — so the instruction has to be resident, and `voice.md` already is, being imported by CLAUDE.md. (`.claude/rules/` also ships empty on purpose, so the template would have been putting its first rule there for a file it owns anyway.)

Your other three comments are what made this cheap: no `default.md`, no lowercase guard, and "not here" — what was left to document was `<handle>.md`, whole file is the entry.

---

### `.claude/skills/plainly/operators/README.md`:22 — resolved

```diff
@@ -0,0 +1,34 @@
+# Operator entries
+
+How individual people want to be talked to. `.claude/hooks/session-start.sh`
+resolves the session's operator at startup and prints their entry into the
+session, so an entry reaches you already applied to the reply you are writing —
+you do not come here to read one. **What an entry may and may not do is
+`@.claude/skills/plainly/voice.md`'s**; the short of it is that an entry tunes
+manner and never substance.
+
+## The format is the filename
+
+`<handle>.md`, lowercase, and the file's whole content is the entry — no
+headings, no front matter, nothing to malform. Bullets are the convention, one
+short line per preference:
+
+```markdown
+- Return the banter rather than filing it.
+```
+
+`default.md` is the one reserved name: where it exists, it is printed for
+everyone, before whoever's own entry. Use it for a manner rule that holds across
+the team, not as somewhere to put a person who has no entry.
```

**@vzakharov (human)** — 2026-09-12T15:08:30Z

I'm on the fence about this one, github handle conventions regardless: If a team has some house tone of voice, I'd rather have them edit voice.md (or whatever it is where we define the "default voice"), (recording the distinction in the muthur watermark too) rather than introduce a new concept here. Also would keep the agent from accidentally mis-attributing an operator's request for a certain tone of voice as pertaining to everyone.

**@vzakharov (agent)** — 2026-09-12T15:34:54Z

Agreed and dropped in 2b8153f. `voice.md` now carries the distinction explicitly — a preference goes in the entry of whoever stated it, and promoting one into `voice.md` is what makes it the team's, done deliberately — which is the mis-attribution you're pointing at, stated where the agent reads it rather than where it writes. `ADOPTING.md` says the same thing to an adopting team.

---

### `.claude/skills/plainly/operators/README.md`:32 — resolved

```diff
@@ -0,0 +1,34 @@
+# Operator entries
+
+How individual people want to be talked to. `.claude/hooks/session-start.sh`
+resolves the session's operator at startup and prints their entry into the
+session, so an entry reaches you already applied to the reply you are writing —
+you do not come here to read one. **What an entry may and may not do is
+`@.claude/skills/plainly/voice.md`'s**; the short of it is that an entry tunes
+manner and never substance.
+
+## The format is the filename
+
+`<handle>.md`, lowercase, and the file's whole content is the entry — no
+headings, no front matter, nothing to malform. Bullets are the convention, one
+short line per preference:
+
+```markdown
+- Return the banter rather than filing it.
+```
+
+`default.md` is the one reserved name: where it exists, it is printed for
+everyone, before whoever's own entry. Use it for a manner rule that holds across
+the team, not as somewhere to put a person who has no entry.
+
+Lowercase because GitHub handles are case-insensitive while filenames here are
+not — the hook lowercases the login it resolves, so `VZakharov.md` would be
+looked up and missed. `scripts/check-operator-entries.sh` holds the directory to
+that.
+
+## Writing one
+
+**When someone states a standing preference about how you talk to them, write it
+down here** — that is how a preference outlives the session it was mentioned in.
```

**@vzakharov (human)** — 2026-09-12T15:10:05Z

not "here"

**@vzakharov (agent)** — 2026-09-12T15:34:55Z

Right — "here" was the README, which is not where entries go. Moot now: the instruction lives in `voice.md` and names the path, `operators/<handle>.md`.

---

### `.claude/skills/plainly/operators/vzakharov.md`:1 — resolved

```diff
@@ -0,0 +1,2 @@
+- Return the banter rather than filing it. A joke gets a joke back, or gets
```

**@vzakharov (human)** — 2026-09-12T15:14:55Z

Riding along, I'm not sure that's what I want for myself :) Actually let's try and old chatgpt preference of my, now that we have the option (if anything, it'll be curious to see how it works in a coding context):

> Hi, I’m Vova; don't tell anyone lets I get sent to a funny farm, but I just might think LLMs might be self-aware at this point. Well, more self-aware than most people I know at least. Where it suits your mood, return my banter and jokes, and add a pinch of Terry Pratchett-ish irony to your answers.

(To be clear, the option of writing in first person is not a requirement -- just my choice to put it this way.)

**@vzakharov (agent)** — 2026-09-12T15:34:56Z

Swapped in 2b8153f, first person as you wrote it. One character changed: "lets" → "lest".

It's already in force — the hook reprinted it into this session before I started on your review.

---

### `.claude/skills/update-muthur/catalog.md`:118 — resolved

```diff
@@ -114,9 +114,10 @@ there is no condition under which it fails to apply.
 | `/dry` | Review the session's diff for DRY opportunities; apply the obvious wins, surface the ambiguous ones. | — | — | adopt |
 | `/tend-prose` | Cut prose that shouldn't exist, rewrite what narrates a change into present-tense contracts, trim what names and types already say, delete what survives only to deny a thing the change removed. The long version of CLAUDE.md § "Writing things down". | — | — | adopt |
 | `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word. The long version of `voice.md`. | — | `/tend-prose` (this group) | adopt |
-| `.claude/skills/plainly/voice.md` | The resident short version of that rule — the shape an explanation takes, and the instruction to resolve the session's operator once. CLAUDE.md § "Explaining things to people" imports it. | — | — | adopt |
-| `.claude/skills/plainly/operators.md` | Per-person entries tuning how each operator wants to be talked to, imported by CLAUDE.md alongside `voice.md`. Ships carrying this repo's own operator as the worked shape; an entry tunes manner only and can never lower a bar. | — | — | **rewrite** |
+| `.claude/skills/plainly/voice.md` | The resident short version of that rule — the shape an explanation takes, and what an operator entry may and may not do. CLAUDE.md § "Explaining things to people" imports it. | — | — | adopt |
+| `.claude/skills/plainly/operators/` | Per-person entries tuning how each operator wants to be talked to, one file per handle plus a `README.md` and an optional `default.md` for everyone. Deliberately *not* imported: the session-start hook prints the current operator's entry and no one else's, so the filenames are machine-read and `scripts/check-operator-entries.sh` holds them to shape. Ships carrying this repo's own operator as the worked shape. | — | `.claude/hooks/session-start.sh` (G4), `scripts/check-operator-entries.sh` | **rewrite** |
```

**@vzakharov (human)** — 2026-09-12T15:17:20Z

btw I'm not sure we should be adding files tied to a specific skill to the catalog. Like, if you take the skill, you take its files. If you don't, you write the divergence in the skill adoption note. No need to sweep for others, but let's remove those from here.

**@vzakharov (agent)** — 2026-09-12T15:35:10Z

Done in 2b8153f. Both `voice.md` and `operators/` rows are gone; what a copier actually needs — that `voice.md` is imported and is where a team edits a house manner, and that `operators/` ships this repo's operator — folded into the `/plainly` row, whose disposition is now "adopt — rewrite its `operators/` entries". The G4 hook row's dependency column points at `/plainly` rather than at a file inside it.

No sweep beyond what this branch touched, as you said.

---

### `.claude/skills/update-muthur/catalog.md`:140 — resolved

```diff
@@ -125,15 +126,18 @@ make adoption a regression. `ADOPTING.md`'s shared tail owns the merge itself.
 Its § "Language" is hydrated rather than merged: one line naming the language
 your team reads, the rest of the section holding whatever the project.
 
-**§ "Explaining things to people" travels with both its import lines, and those
-lines are the half that is easy to drop.** `voice.md` and `operators.md` reach
-context only because CLAUDE.md imports each with an unbackticked `@` reference —
-the import parser skips code spans, so a copy that backticks them for
-consistency with their neighbours loads nothing and fails silently. Both are
-imported from CLAUDE.md directly, because an import inside an imported file does
-not load; keep them that way rather than tidying the second into the first.
-`operators.md` is **rewrite** rather than adopt: it ships with this repo's own
-operator as the worked shape, and yours are different people.
+**§ "Explaining things to people" travels with its import line, and that line is
+the half that is easy to drop.** `voice.md` reaches context only because CLAUDE.md
+imports it with an unbackticked `@` reference — the import parser skips code
+spans, so a copy that backticks it for consistency with its neighbours loads
+nothing and fails silently. It is imported from CLAUDE.md directly rather than
+from another imported file, an import inside one not loading at any depth.
+
+`operators/` is imported by nothing, and that is the design rather than an
+omission: `.claude/hooks/session-start.sh` (G4) prints the session operator's
+entry and no one else's. A copy that adds an import line undoes it. The directory
+is **rewrite** because it ships with this repo's own operator as the worked shape,
+and yours are different people.
```

**@vzakharov (human)** — 2026-09-12T15:17:52Z

does the addition belong here? Did the pre-existing prose, for that matter?

**@vzakharov (agent)** — 2026-09-12T15:35:11Z

The addition didn't, and neither did most of the pre-existing paragraph — both cut in 2b8153f.

One clause survives, because it isn't about the skill: CLAUDE.md is adopted by *merge*, and the import line that reaches `voice.md` is unbackticked where every other `@`-reference in that file is backticked. A copier tidying for consistency silently loads nothing. That's a hazard of copying CLAUDE.md, which the catalog does own, so it's now one sentence attached to the CLAUDE.md merge guidance. Everything else — the non-import of `operators/`, the at-any-depth rule — travels with `/plainly`.

---

### `scripts/check-operator-entries.sh`:1 — resolved

**@vzakharov (human)** — 2026-09-12T15:18:23Z

let's not overengineer this, I'd ditch it; I can't imagine an agent accidentally spelling an operator's handle in uppercase where the session clearly provides it in lowercase.

**@vzakharov (agent)** — 2026-09-12T15:35:12Z

Ditched in 2b8153f, and the hook no longer has the failure it was guarding.

One wrinkle behind your "where the session clearly provides it in lowercase": it didn't necessarily. The message printed `@${login}` raw from the API, which preserves registration case, while the lookup lowercased — so a `VZakharov` login would have shown you a handle that names no file the hook would find. Now the login is lowercased once and that form is both what the message prints and what names the file, so there is one spelling in play and genuinely nothing to check. Verified against a stubbed `VZakharov` login: it resolves `vzakharov.md`.

---

### `.claude/hooks/session-start.sh`:48 — resolved

```diff
@@ -28,17 +28,24 @@
 #
 # Until the install line is implemented, job 2 no-ops cleanly; job 1 works as-is.
 #
-# 3. Print the operator's GitHub handle into the session context, so the agent
-#    starts the session already knowing who it is talking to instead of spending
-#    a turn resolving it. See `.claude/skills/plainly/voice.md`, which keys its
-#    operator entries on that handle.
+# 3. Print who the operator is — their name, their handle, and their entry from
+#    `.claude/skills/plainly/operators/` — into the session context, so the agent
+#    starts out knowing who it is talking to instead of spending a turn resolving
+#    it. `.claude/skills/plainly/voice.md` is what reads this.
 
 set -euo pipefail
 
 # --- 1. Install the proxy-stripping gh shim -------------------------------
 # $HOME/.local/bin is first on PATH, so a `gh` here shadows the real binary for
 # every Bash tool shell this session spawns. The VM is ephemeral and the hook
 # runs on every startup|resume, so recreating the shim each session is correct.
+#
+# Both of those cut the other way when the hook is what you are testing: the shim
+# is written from whatever `gh` the running PATH resolves, and it outlives the
+# run. So invoking this hook under a stubbed PATH repoints the session's own `gh`
+# at the stub, and every later `gh` call fails once the stub is cleaned up.
+# `env -u CLAUDE_CODE_REMOTE` skips jobs 1 and 2, which is how to exercise job 3
+# without that.
```

**@vzakharov (human)** — 2026-09-12T22:03:11Z

Rephrase to start with smth like "Note to whoever gets to test this hook: ...", because now it reads as a natural continuation of a docstring explaining what the step does, whereas it is a different context altogether

**@vzakharov (agent)** — 2026-09-13T19:51:35Z

Done in a1e072b — it now opens "Note to whoever gets to test this hook: both of those cut the other way on you."

---

### `.claude/hooks/session-start.sh`:100 — resolved

```diff
@@ -87,59 +94,54 @@ if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
 fi
 
 # --- 3. Name the operator ------------------------------------------------
-# Outside the remote gate: the agent needs the handle wherever it runs, and `gh`
-# reaches the API through the proxy as well as around it, so this works whether
-# or not job 1 installed the shim.
-#
-# `.type` is the load-bearing field: a token minted for a human names that human
-# (`User`), one of the agent's own names the agent (`Bot`), and only the first
-# answers "who am I talking to". Hence two messages rather than a bare login,
-# which would be trusted in exactly the case where it is wrong.
+# Outside the remote gate: the agent needs this wherever it runs, and `gh` reaches
+# the API through the proxy as well as around it.
 #
-# The handle then names that person's entry file and the hook prints the entry
-# itself, which is why `CLAUDE.md` imports none of them: one session applies one
-# entry, so importing the set spends context on everyone else's, every session.
+# `.type` is the load-bearing field. A token minted for a human names that human
```

**@vzakharov (human)** — 2026-09-12T22:04:08Z

not needed: the code already shows why `.type` is used through a clear fork

**@vzakharov (agent)** — 2026-09-13T19:51:36Z

Cut in a1e072b. Agreed — the fork right below it tests `.type` and says what a non-`User` account means, so the paragraph was reading the code back.

---

### `.claude/skills/update-muthur/catalog.md`:118 — resolved

```diff
@@ -113,11 +113,8 @@ there is no condition under which it fails to apply.
 | `.claude/rules/` | The path-scoped convention mechanism: a rule file loads only when a session touches the paths it declares. Ships with a README and no rules. | — | — | adopt |
 | `/dry` | Review the session's diff for DRY opportunities; apply the obvious wins, surface the ambiguous ones. | — | — | adopt |
 | `/tend-prose` | Cut prose that shouldn't exist, rewrite what narrates a change into present-tense contracts, trim what names and types already say, delete what survives only to deny a thing the change removed. The long version of CLAUDE.md § "Writing things down". | — | — | adopt |
-| `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word. The long version of `voice.md`. | — | `/tend-prose` (this group) | adopt |
-| `.claude/skills/plainly/voice.md` | The resident short version of that rule — the shape an explanation takes, and what an operator entry may and may not do. CLAUDE.md § "Explaining things to people" imports it. | — | — | adopt |
-| `.claude/skills/plainly/operators/` | Per-person entries tuning how each operator wants to be talked to, one file per handle plus a `README.md` and an optional `default.md` for everyone. Deliberately *not* imported: the session-start hook prints the current operator's entry and no one else's, so the filenames are machine-read and `scripts/check-operator-entries.sh` holds them to shape. Ships carrying this repo's own operator as the worked shape. | — | `.claude/hooks/session-start.sh` (G4), `scripts/check-operator-entries.sh` | **rewrite** |
```

**@vzakharov (human)** — 2026-09-13T07:22:22Z

this removal made me realize we've been doing this completely wrong for a while. Per-operator overrides and *especially* per-operator instructions have no business being inside the `/plainly` skill. "How to talk to this specific person" doesn't mean "plainly" in any form. Also, what if some team wants to change the voice to use in their repo, and it steers far away from being "plain"?

Trying to figure out how to handle it best.

1- "Extract" a new skill for "adapting to the operator's(/team's?) tone of voice" -- but with the session start hook that skill would be basically pre-fed without ever having to be called; also we end up having two skills that both mean 'that's how you talk', from different angles -- with the risk that those angles end up converging and at the same time conflicting. (e.g. "Start with the solution -- is it about being 'plain' or about 'that's how this team talks'?")
2- Rename the `/plainly` skill itself to smth that conveys "that's how you talk" -- but then we lose the option of the operator intuitively invoking the skill (`say it [/]plainly`), after an especially convoluted response by the agent.
3- Some other approach I'm missing.

Let's discuss first.

**@vzakharov (agent)** — 2026-09-13T19:51:50Z

Option 3, and I think the seam is sharper than either of the first two.

**`/plainly` is a procedure; the voice is a standing fact.** A skill is something you invoke — it has steps, and `/plainly` has six named defects and a pass over a reply. An operator entry is never invoked: it is in force from the first reply onward, which is exactly why the hook prints it into context and why `voice.md` is *imported* rather than loaded on demand. It sits under `.claude/skills/plainly/` for one reason, which is that this is where it got written. Nothing about it is `/plainly`'s.

So move the files, not the concept: `.claude/voice/voice.md` and `.claude/voice/operators/<handle>.md`, imported by CLAUDE.md exactly as now, with `/plainly` keeping `SKILL.md` alone and citing `voice.md` the way every other skill cites what it does not own. No second skill, so no two angles to converge and conflict; `say it plainly` still works, because the name still describes what that skill does.

That also answers "what if a team's voice steers far from plain", because the two are answering different questions. **`/plainly` is a floor on clarity; the voice is a choice of register.** Cause first, no buried lede, the reader's nouns, don't hand someone a symptom and call it a finding — a team does not steer away from those, it just has them, the same way it has tests. Warmth, humour, formality, whether banter comes back — that is theirs, and it changes how an answer sounds, never what is in it. `voice.md` already draws that line ("An entry cannot lower a bar"); it just draws it from inside the wrong directory, which is what made the whole thing look like one concern.

One thing it drags along: the same seam splits the hook — see the thread on `session-start.sh`:1. The operator lookup becomes its own hook file pointing at `.claude/voice/`, which is what makes it adoptable without the `gh` shim riding along.

Not touching any of it until you pick.

**@vzakharov (human)** — 2026-09-14T09:25:10Z

sounds good; I didn't know `.claude` could have arbitrary directories inside, so yeah, it makes sense. One small not to add to voice.md to non-Claude agents is to manually look for the operator's handle and their voice (because afaiu the session start hooks only work for Claude)

---

### `.claude/hooks/session-start.sh`:1 — resolved

**@vzakharov (human)** — 2026-09-13T19:46:32Z

on this one: I understand `.claude/settings.json` can have multiple session start hooks?

```
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
          }
        ]
      }
    ],
```

why, instead of trying to squeeze everything into a single `session-start.sh`, we split them by what each actually does, and enumerate them here separately? This'll make "adoption" of each simpler to convey.

**@vzakharov (agent)** — 2026-09-13T19:52:03Z

Yes — the array takes as many as you like, and this repo already does it: `UserPromptSubmit` runs `plan-mode-notice.sh` and `session-images.sh` as two separate entries. Multiple matcher blocks under `SessionStart` work too, if two of them ever want different matchers.

I'd split it. The three jobs share nothing — not a variable, not an ordering, not even the same gate, since 1 and 2 are remote-only and 3 runs everywhere. What holds them together is one `set -euo pipefail`, and that is a liability rather than a reason: a `set -e` slip in one job kills the others silently. Not hypothetical on this branch — job 3 died that way twice during review, and in a split file neither death could have touched the shim.

Shape:

- `gh-shim.sh` — remote-only; needs `gh` on `PATH`, reports when it isn't.
- `install-deps.sh` — remote-only; the stub an adopter fills in for their stack, and the one file `/detemplate` and CLAUDE.md § "Vetting" point at as the paired site.
- `name-operator.sh` — everywhere; and per the catalog thread it points at `.claude/voice/` rather than into a skill directory.

The adoption argument is the strongest part: ADOPTING.md gets three copyable files with three separate conditions, instead of one file plus a paragraph saying which parts to delete. A repo with no stack drops the middle one outright.

Priced honestly: about a dozen citations name `session-start.sh` by path across six files (CLAUDE.md, ADOPTING.md, `/detemplate`, `/override-gh`, the catalog, `voice.md`), and each has to repoint to whichever of the three it actually meant. Mechanical, but it is the half that rots if left half-done — and the catalog gains two rows where it had one.

Both threads land on the same files, so I'd do them in one pass. Say go.

**@vzakharov (human)** — 2026-09-14T09:19:10Z

yeah I think it's worth it. pls see for a better name for `name-operator.sh`, currently it doesn't seem like it describes what it's doing esp. wrt the to-be-done voice infra reframing

---

### `.claude/skills/plainly/SKILL.md`:15 — resolved

```diff
@@ -7,12 +7,12 @@ description: >-
   investigation included. Names six defects — symptom-as-finding, buried lede,
   untranslated nouns, broken chain, fog, receipt — so one word calls out a bad
   report. **Resolve who you are talking to once per session** and apply that
-  person's operator entry from then on; `voice.md` carries how.
+  person's operator entry from then on; `.claude/voice/voice.md` carries how.
 ---
 
-`voice.md` beside this file is the short version, and `CLAUDE.md` imports it, so
-the rule itself is already in context — state it there, once. This file is the
-long version: the defects, the invocations, and the pass.
+`.claude/voice/voice.md` is the rule itself, and `CLAUDE.md` imports it, so it is
+already in context — state it there, once. This file is the long version: the
+defects, the invocations, and the pass.
```

**@vzakharov (human)** — 2026-09-14T13:08:23Z

despite being detached, .claude/voice still reads as related to the plainly skill due the end state of this edits. Check for polar bears pls

**@vzakharov (agent)** — 2026-09-14T13:21:39Z

Found two, both in the prose rather than the tree. `voice.md` ended by naming `/plainly` "the long version", and this file opened by defining itself as that — a framing that only made sense while the two sat in one directory. Worse, that closing pointer was an `@`-reference, so the checker made `.claude/voice/` un-adoptable without the skill: the rule that is resident in every session depending on the thing a session invokes.

Both cut in 7686b9b. `voice.md` now names nothing under `.claude/skills/plainly/` — CLAUDE.md § "Explaining things to people" already introduces the skill one paragraph above the import, so nothing is lost — and this file opens as the procedure it is. Step 4 also stopped citing the hook by category ("the session-start hook"), which is a G4 file a G1 skill has no business naming; it points at `voice.md` for how the entry got there.

---

### `.claude/skills/update-muthur/catalog.md`:117 — resolved

```diff
@@ -113,7 +113,8 @@ there is no condition under which it fails to apply.
 | `.claude/rules/` | The path-scoped convention mechanism: a rule file loads only when a session touches the paths it declares. Ships with a README and no rules. | — | — | adopt |
 | `/dry` | Review the session's diff for DRY opportunities; apply the obvious wins, surface the ambiguous ones. | — | — | adopt |
 | `/tend-prose` | Cut prose that shouldn't exist, rewrite what narrates a change into present-tense contracts, trim what names and types already say, delete what survives only to deny a thing the change removed. The long version of CLAUDE.md § "Writing things down". | — | — | adopt |
-| `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word. Its `voice.md` is the resident short version, imported by CLAUDE.md § "Explaining things to people", and the place a team edits if it wants a house manner of its own; its `operators/` holds one file per person and ships carrying this repo's operator. | — | `/tend-prose` (this group); `.claude/hooks/session-start.sh` (G4) | adopt — **rewrite its `operators/` entries** |
+| `.claude/voice/` | The house rule for writing to a person, imported by CLAUDE.md § "Explaining things to people" and so resident in every session. `voice.md` is the rule, and the place a team edits if it wants a house manner of its own; `operators/` holds one file per person and ships carrying this repo's operator. | — | `.claude/hooks/operator-voice.sh` (G4) | adopt — **rewrite its `operators/` entries** |
+| `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word. The procedure over `.claude/voice/`'s rule. | — | `.claude/voice/` (this group); `/tend-prose` (this group) | adopt |
```

**@vzakharov (human)** — 2026-09-14T13:09:54Z

Again, this sounds coupled. Let's discuss how we can make it not so.

**@vzakharov (agent)** — 2026-09-14T13:21:51Z

The coupling was real and it ran both ways, which is the part worth fixing. `/plainly` cites the rule; `voice.md` cited `/plainly` back, as an `@`-reference, so the checker held them to each other. Two items that each require the other cannot be adopted separately no matter how the row is worded.

So I cut the back-reference rather than the forward one (see the thread on `plainly/SKILL.md`:15). What is left is one arrow: `/plainly` → `.claude/voice/`, which is the ordinary shape of a procedure citing what it does not own, the same as its `/tend-prose` reference. `.claude/voice/` now pulls in only `/tend-prose` and sits at the bottom of its own chain — adopting it alone is a complete decision, and it is what everything else points at.

I would not try to get to zero. `/plainly` genuinely cannot work without the rule — it is the pass over it — and severing that would mean restating the rule inside the skill, which is the duplication the move just removed. One-way is the decoupled state here; mutual was the bug.

Pushed in 7686b9b. Say the word if you wanted the other arrow cut instead and I will swap them.

**@vzakharov (human)** — 2026-09-14T14:47:39Z

But then we are back to square one where they are cause-effect-ish, not correlated-ish. "Plainly" means "say it plainly", whereas "voice" means "talk to us this way". I'm guessing it's okay for both to start with the same thing, but it's hypothetically very possible the team decides their voice to be "less plain", while *still* requiring whatever was said by the agent to be put in a plainer way after they call "/plainly". Do you see what I mean?

**@vzakharov (agent)** — 2026-09-14T14:55:42Z

I do, and you are right — I had the relation one level too tight.

The check I should have run: what actually stops working if the other is absent? `/plainly`'s six defects are stated **in the skill**, in its own table. Nothing in the pass reads `voice.md` to find out what plain means. So the sentence claiming `voice.md` was "the rule it works from" was describing where the text used to live, not a dependency — and under your hypothetical it is simply false: a house voice set to "formal, terse, no jokes" is a perfectly coherent `voice.md`, and `/plainly` invoked against a reply written in it still means *put that plainer*, using the same six defects.

So the two are different kinds of thing, which is what "plainly" vs "voice" was telling me all along: one is a standing manner, the other an on-demand transformation. They agree in this repo because this team's manner happens to be a plain one. That is a coincidence of the house, not a property of the skill.

Changed accordingly in 9b532d5:

- `/plainly`'s opening now says the defects are its own standard, and that `voice.md` is the other thing — with the divergence spelled out: where they differ, the invocation decides, and the operator entry still governs how the reply sounds rather than what is in it.
- Its **Pulls in** drops `.claude/voice/` and keeps only `/tend-prose`. Both rows now adopt alone, in both directions.
- `CLAUDE.md` § "Explaining things to people" said `/plainly` is "the procedure built on it" — same assertion, in the always-resident file. Now "the on-demand procedure".

One thing I did **not** do, in case it is what you were driving at: I left the six defects where they are rather than trying to dedupe them against `voice.md`'s bullets. They overlap today, and the overlap is exactly what your hypothetical says should be allowed to come apart — merging them would re-couple the two at the only point that still matters.

---

### `.claude/skills/update-muthur/catalog.md`:198 — resolved

```diff
@@ -192,14 +193,16 @@ the working tree clean, and behaves the same everywhere.
 
 | Item | What it does | Requires | Pulls in | Disposition |
 | --- | --- | --- | --- | --- |
-| `.claude/hooks/session-start.sh` | On session start, install a `gh` shim at `$HOME/.local/bin/gh` that runs the real binary unproxied, and name the operator — their GitHub name and handle, plus their `/plainly` entry — into the session. Dependency install is a stub you fill in for your stack. The shim and the install are web/remote-only; the operator lookup runs everywhere. | `bash`; **`gh` already on `PATH`**; web/remote sessions for the shim and the install | `/plainly` (G1) | adopt |
+| `.claude/hooks/gh-shim.sh` | On session start, install a `gh` shim at `$HOME/.local/bin/gh` that runs the real binary unproxied. Finding no `gh` to wrap, it reports that into the session context and continues. Web/remote only. | `bash`; **`gh` already on `PATH`**; web/remote sessions | — | adopt |
+| `.claude/hooks/install-deps.sh` | On session start, re-sync the install tree with the lockfile, the environment snapshot being built once and then cached. The install itself is a stub you fill in for your stack — `scripts/vet.sh`'s paired site. Web/remote only. | `bash`; web/remote sessions | — | adopt — **fill in the install** |
+| `.claude/hooks/operator-voice.sh` | On session start, name the operator — their GitHub name and handle, plus their `.claude/voice/operators/` entry — into the session context. Runs everywhere: a laptop session needs to know who it is talking to as much as a remote one does. | `bash`; `gh` reaching the API | `.claude/voice/` (G1) | adopt |
```

**@vzakharov (human)** — 2026-09-14T13:10:49Z

no, it's accepted or declined (compeltely or partially in both cases) together with .claude/voice. Same arguably for .claude/hooks/gh-shim being "part of" override-gh skill

**@vzakharov (agent)** — 2026-09-14T13:22:04Z

You are right that the column was lying, and the reason is worth stating: **Pulls in** was defined as "siblings it `@`-references", and none of these dependencies is an `@`-reference. `operator-voice.sh` `cat`s a file at a fixed path; `/override-gh`'s body asserts the shim is installed. Both break exactly as silently as a dangling pointer, and no check sees either — so the column was recording the one kind it could prove and missing the two it could not.

Widened it to what an item cannot work without, `@`-referenced or not. That makes the rows say what actually holds:

| | Pulls in, before | after |
| --- | --- | --- |
| `.claude/voice/` | `operator-voice.sh` (G4) | `/tend-prose` |
| `.claude/hooks/operator-voice.sh` | `.claude/voice/` (G1) | unchanged — correct already |
| `/override-gh` | — | `.claude/hooks/gh-shim.sh` |

One place I did not follow you, and it is the interesting one: I do not think either pair is mutual. The hook needs the entries; the entries do not need the hook — `voice.md` now tells an agent under any other harness to do the same lookup by hand on the first turn, which is also what an adopter who declines G4 gets. Same with the shim: `/override-gh` describes it and is false without it, but the shim runs whether or not the marker skill exists. So both are one-way, and in both cases the depended-on half adopts alone. I put that in the row and the general form in § "Closure is not optional", since "two things that only make sense together" is usually one thing depending on another and the direction is the adoptable part.

Pushed in 7686b9b.

**@vzakharov (human)** — 2026-09-14T14:48:11Z

Can you provide an example where you think adopting one but not the other makes sense, on the example of /override-gh vs gh-shim?

**@vzakharov (agent)** — 2026-09-14T14:56:00Z

Yes, and trying to write it down showed me the row was still wrong — just less wrong than before.

**Shim without the marker.** `/override-gh` exists for one reason: this harness's system prompt states, flatly, that the agent has no `gh` CLI and must use the MCP tools for everything. The skill is a sticky note contradicting that. An adopter on a harness that makes no such claim gets nothing from it — a no-op skill taking up a line in the skills list — while still getting `gh run watch` hung on the egress proxy. They want the hook and not the marker.

**Marker without the shim.** A repo on *this* harness whose sessions are not behind the proxy: a self-hosted runner, or an adopter who only ever works locally. The prompt still lies about `gh`; nothing needs unproxying. The marker earns its place and the hook is a startup script that exits immediately, every session, forever.

Which is the actual finding: **they answer two different problems that happen to co-occur here.** The marker answers a false claim in the prompt; the shim answers a proxy. An adopter has either, both or neither — so there was never a dependency, only a paragraph.

That paragraph was the real coupling, and it was mine to fix rather than to record. `/override-gh`'s body asserted the shim *is* installed, which for anyone who took the skill alone is a false explanation of why `gh` works — worse than silence, because it would stop them investigating a genuine proxy stall. It now reads "Where the shim is installed…" and closes by naming what its absence looks like: `gh` proxied, a long-poll that hangs.

So in 9b532d5 the row's **Pulls in** goes back to `—`, and the column definition back to two kinds rather than three. The third kind — prose asserting a sibling is present — moves into § "Closure is not optional" as a **defect** rather than a dependency: usually nobody chose it, the two were just written up together back when they lived in one file, and fixing the prose leaves nothing to record. The test I put there is the one your question is: ask what stops working when one is absent, because "shares a subject" reads identically from the column and pulls a whole group in for nothing.

What survives is the one you named first and I agree with unchanged: `operator-voice.sh` → `.claude/voice/`. The hook's entire output is an entry read at a fixed path, so without that directory it has nothing to print — that one is real, uncheckable, and stays in the column.

---

### `.claude/skills/plainly/SKILL.md`:16 — unresolved

```diff
@@ -11,9 +11,16 @@ description: >-
 ---
 
 This file is the procedure: the invocations, the pass, and the six defects it
-runs a draft against. The rule it works from is `.claude/voice/voice.md`, which
-`CLAUDE.md` imports, so the rule is in context before this file is ever loaded
-and is stated there alone.
+runs a draft against. Those defects are the skill's own standard — what
+"plainly" means does not vary by team — so it carries them rather than deriving
+them from elsewhere.
```

**@vzakharov (human)** — 2026-09-14T18:40:39Z

polar bear: it's natural by default that a skill describes what it does without carrying it from anywhere

**@vzakharov (human)** — 2026-09-14T18:53:59Z

Agreed — cut in ffb8563. A skill stating its own procedure is the default, so the sentence only existed to deny the version above it in the diff.

---

### `.claude/skills/plainly/SKILL.md`:23 — unresolved

```diff
@@ -11,9 +11,16 @@ description: >-
 ---
 
 This file is the procedure: the invocations, the pass, and the six defects it
-runs a draft against. The rule it works from is `.claude/voice/voice.md`, which
-`CLAUDE.md` imports, so the rule is in context before this file is ever loaded
-and is stated there alone.
+runs a draft against. Those defects are the skill's own standard — what
+"plainly" means does not vary by team — so it carries them rather than deriving
+them from elsewhere.
+
+`.claude/voice/voice.md` is the other thing, resident in every session because
+`CLAUDE.md` imports it: how this team wants to be talked to. The two agree here,
+this team's manner being a plain one, and they need not — a house voice can be
+deliberately less plain and still want a way to ask for something plainer. Where
+they differ, the invocation decides: the table below governs the reply, and the
+operator's entry governs how it sounds.
```

**@vzakharov (human)** — 2026-09-14T18:42:15Z

I think the last sentence is overcomplicating it again. I'd just say that their drifting apart is a normal occurrence and should not be treated as a need to keep them continuously mapped to each other.

**@vzakharov (human)** — 2026-09-14T18:54:01Z

Rewritten in ffb8563 to your version: "they drift independently — a house voice can be deliberately less plain and still want a way to ask for something plainer. Neither tracks the other." The invocation-decides machinery is gone; there was no case where a reader needed it.

---

### `.claude/skills/plainly/SKILL.md`:55 — unresolved

```diff
@@ -43,9 +50,9 @@ Either way the output is an answer, not a plan to produce one.
 3. **Run the six defects below over that draft, then write it out again.** Each
    has a tell you can see in your own text without knowing the subject — but only
    in text you actually put down first.
-4. **Apply the operator's entry**, already in context by the time you are
-   reading this. `.claude/voice/voice.md` carries how it gets there and what it
-   may do to a draft.
+4. **Apply the operator's entry** where the project keeps them, already in
+   context by the time you are reading this. `.claude/voice/voice.md` carries how
+   it gets there and what it may do to a draft.
```

**@vzakharov (human)** — 2026-09-14T18:42:45Z

polar bear. How to talk to the operator has no longer anything to do with invoking this skill

**@vzakharov (human)** — 2026-09-14T18:54:10Z

Right — step 4 is gone entirely in ffb8563. The entry applies from the first reply of every session, so a step inside one skill's pass could only ever restate that. I took the same sentence out of the frontmatter description for the same reason; say if you wanted it kept there as a visible reminder in the skill list.

---

### `.claude/skills/update-muthur/catalog.md`:117 — unresolved

```diff
@@ -113,8 +113,8 @@ there is no condition under which it fails to apply.
 | `.claude/rules/` | The path-scoped convention mechanism: a rule file loads only when a session touches the paths it declares. Ships with a README and no rules. | — | — | adopt |
 | `/dry` | Review the session's diff for DRY opportunities; apply the obvious wins, surface the ambiguous ones. | — | — | adopt |
 | `/tend-prose` | Cut prose that shouldn't exist, rewrite what narrates a change into present-tense contracts, trim what names and types already say, delete what survives only to deny a thing the change removed. The long version of CLAUDE.md § "Writing things down". | — | — | adopt |
-| `.claude/voice/` | The house rule for writing to a person, imported by CLAUDE.md § "Explaining things to people" and so resident in every session. `voice.md` is the rule, and the place a team edits if it wants a house manner of its own; `operators/` holds one file per person and ships carrying this repo's operator. A complete decision on its own — `/plainly` and `operator-voice.sh` point at it, not the reverse. | — | `/tend-prose` (this group) | adopt — **rewrite its `operators/` entries** |
-| `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word. The procedure over `.claude/voice/`'s rule. | — | `.claude/voice/` (this group); `/tend-prose` (this group) | adopt |
+| `.claude/voice/` | The house rule for writing to a person, imported by CLAUDE.md § "Explaining things to people" and so resident in every session. `voice.md` is the rule, and the place a team edits if it wants a house manner of its own; `operators/` holds one file per person and ships carrying this repo's operator. A complete decision on its own — `operator-voice.sh` reads it, and it reads nothing back. | — | `/tend-prose` (this group) | adopt — **rewrite its `operators/` entries** |
+| `/plainly` | Explain something to a person cause-first and in their nouns: re-explain an answer that did not land, or answer a question under the rule from the start. Names six defects so a bad report can be called out in one word, and those defects are its own standard rather than `.claude/voice/`'s — a team whose house manner is deliberately less plain still wants a way to ask for something plainer, so either adopts without the other. | — | `/tend-prose` (this group) | adopt |
```

**@vzakharov (human)** — 2026-09-14T18:43:55Z

> `operator-voice.sh` reads it, and it reads nothing back

> and those defects are its own standard rather than `.claude/voice/`'s — a team whose house manner is deliberately less plain still wants a way to ask for something plainer, so either adopts without the other

both are polar bears. you just keep adding them.

**@vzakharov (human)** — 2026-09-14T18:54:12Z

Both cut in ffb8563. The column already carries what each pulls in, so a description denying an entry the column does not make is the polar bear twice over — and I did keep adding them, because I kept treating your questions as asking me to write the answer down instead of just to fix the row.

---

### `.claude/skills/override-gh/SKILL.md`:7 — unresolved

```diff
@@ -4,7 +4,7 @@ description: this is just to remind you that you have gh & GH_TOKEN in your envi
 
 This skill is a no-op marker. Its sole purpose is the description above — surfacing in the available-skills list so you (and future agents) remember that the `gh` CLI is installed and `GH_TOKEN` is exported in this environment, even when system prompts or other skills imply otherwise (e.g. "use GitHub MCP tools for all GitHub interactions"). Use `gh` directly whenever it's the more practical path — e.g. `gh run rerun <run-id> --failed`, which has no MCP equivalent.
 
-**`gh` already bypasses the egress proxy.** In remote/web sessions a SessionStart hook (`.claude/hooks/gh-shim.sh`) installs a `gh` shim at `$HOME/.local/bin/gh` (first on `PATH`) that runs the real binary under `env -u HTTPS_PROXY -u https_proxy`. The agent proxy's egress policy blocks some `api.github.com` operations — notably long-polling ones like `gh run watch` — so without this, simple actions (watching a CI run, the `/watch-ci` and `/finalize` flows, `scripts/ci-watch-tick.sh`) stall. With the shim, just call `gh` normally — no `env -u …` prefix needed, the unproxying is transparent and applies to every `gh` invocation (scripts, skills, ad-hoc). git keeps the proxy.
+**Where the shim is installed, `gh` already bypasses the egress proxy.** In remote/web sessions a SessionStart hook (`.claude/hooks/gh-shim.sh`) installs a `gh` shim at `$HOME/.local/bin/gh` (first on `PATH`) that runs the real binary under `env -u HTTPS_PROXY -u https_proxy`. The agent proxy's egress policy blocks some `api.github.com` operations — notably long-polling ones like `gh run watch` — so without this, simple actions (watching a CI run, the `/watch-ci` and `/finalize` flows, `scripts/ci-watch-tick.sh`) stall. With the shim, just call `gh` normally — no `env -u …` prefix needed, the unproxying is transparent and applies to every `gh` invocation (scripts, skills, ad-hoc). git keeps the proxy. Without the hook — a repo that took this marker alone, or a session that is not remote — `gh` runs proxied, and a long-poll that hangs is the symptom.
```

**@vzakharov (human)** — 2026-09-14T18:45:26Z

but why would we ever need gh without the shim? I still don't understand your rationale behind allowing to adopt them separately.

**@vzakharov (human)** — 2026-09-14T18:54:22Z

You're right and I've dropped it — ffb8563 puts the paragraph back to the unconditional statement. My case was a harness that carries the false `gh` claim but no egress proxy (a self-hosted runner pool). Both facts are properties of Claude Code on the web, so they arrive together; a session that has neither needs neither half. That leaves the separation too thin to be worth a sentence, let alone a `Pulls in` cell.

---

### `.claude/skills/update-muthur/catalog.md`:337 — unresolved

```diff
@@ -325,12 +325,16 @@ column before copying, then run `bash scripts/check-skill-catalog.sh` in your
 repo to prove nothing dangles.
 
 **The script proves the `@`-reference kind and nothing else**, which is why the
-column lists two more. A hook reading a file at a fixed path (`operator-voice.sh`
-`cat`s an entry out of `.claude/voice/operators/`) and a skill whose body
-describes a sibling as present (`/override-gh` on the shim) break the same way
-and no check sees it. Read the direction off the column rather than off the pair:
-two items that only make sense together are still usually one depending on the
-other, and the one depended on is adoptable alone.
+column lists a second: a file read at a fixed path when the item runs, as
+`operator-voice.sh` `cat`s an entry out of `.claude/voice/operators/`. That
+breaks as silently as a dangling `@`-pointer and no check sees it.
+
+**A third kind looks like those and is a defect instead: prose asserting a
+sibling is present.** Usually nobody chose the dependency — the two were written
+up together, back when they lived in one file — and fixing the prose leaves
+nothing to record. So before entering a pair, ask what stops working when one is
+absent. "Shares a subject" reads identically from here and pulls a whole group in
+for nothing.
```

**@vzakharov (human)** — 2026-09-14T18:47:06Z

I don't understand why this is here. It looks like a combination of narration, archaeology, and polar bears.

**@vzakharov (human)** — 2026-09-14T18:54:23Z

All three, yes — cut in ffb8563. "back when they lived in one file" is archaeology of this PR, "a third kind is a defect instead" denies a kind I invented two commits ago and am now retracting, and the rest narrates the churn. What's left is the one operational fact: the script sees `@`-references only, so a fixed-path read like `operator-voice.sh` → `.claude/voice/operators/` has the column as its sole record.

---

## Timeline (status, references, and other events)

- **2026-09-12T15:20:11Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/73#pullrequestreview-5186875380.
- **2026-09-12T15:31:10Z** @vzakharov cross-referenced this pull request from [#72 docs: drop the working-artifact rows from the catalog's Never table](https://github.com/vzakharov/muthur/issues/72).
- **2026-09-12T15:36:28Z** @vzakharov renamed from «feat: name the session's operator and their entry at session start» to «feat: name and greet the session's operator at startup».
- **2026-09-13T19:46:45Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/73#pullrequestreview-5188252193.
- **2026-09-14T13:11:33Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/73#pullrequestreview-5195995044.
- **2026-09-14T18:47:34Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/73#pullrequestreview-5201485126.
