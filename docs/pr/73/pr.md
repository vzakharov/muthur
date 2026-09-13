# PR #73: feat: name and greet the session's operator at startup

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/73
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/operator-handle-hook-p25kpw
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-12T14:56:18Z
- **Updated:** 2026-09-13T19:46:45Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **The agent never knew who it was talking to.** The harness reports an email; `git config user.email` is the commit identity. Resolving the operator meant spending a turn on `gh api user`, and only if the session remembered to. Job 3 of `.claude/hooks/session-start.sh` now does it at startup and prints the answer into the session context.
- **It names the person, not the handle.** `gh api user` carries `.name`, so the hook prints `Vova Zakharov (@vzakharov)` and `voice.md` asks for a greeting by that name in the session's first reply. Where `.name` is empty the message falls back to the handle alone and there is nothing to greet with, so nobody gets hailed as "hey vzakharov".
- **It prints the operator's entry, not a pointer to it.** `CLAUDE.md` used to import `operators.md` whole, so every session carried every person's entry and still had to pick its own out of the list. The import is gone: a session applies one entry, so importing the set spent context on everyone else's, every session. Cost goes from O(team) to O(1), and the "if they have one" conditional disappears — either an entry was printed or the hook said there is none.
- **An entry is a filename and nothing else.** `.claude/skills/plainly/operators/<handle>.md`, the file's whole content being the entry, and the directory holds no other kind of file. A heading was a thing an entry could get wrong, and getting it wrong failed silently — the entry reached no session while the preference sat in the repo looking done. There is no syntax to violate, so the lookup is `cat`.
- **What the hook can't determine, it says.** `.type` distinguishes a token minted for a human from one of the agent's own, because a bare login would be trusted in exactly the case where it names the agent. Three non-answers — no entry, a `Bot` token, `gh` out of reach — each print explicitly rather than silently.
- **Two rules moved to stay correct.** "An entry cannot lower a bar" is now in `voice.md`, which stays imported — it governs every reply and had been riding on the import that went away. `voice.md` also carries the write-it-down instruction and the line separating one person's preference from the team's: a manner rule for everyone is an edit to `voice.md`, made where the team can see it, never an entry promoted out of one person's file.

### Since the first review

Ten comments, all addressed; `default.md`, `operators/README.md` and `scripts/check-operator-entries.sh` all went away rather than getting fixed.

- `default.md` and `README.md` were both reserved names in a directory keyed on GitHub logins, and both are real logins. Dropping them leaves `operators/` holding nothing but `<handle>.md`, so the collision class is gone rather than narrowed.
- The README's surviving content is two clauses in `voice.md`, which every session already loads. A path-globbed rule would have loaded when a session *touches* `operators/` — after you have decided to write an entry; the moment that matters is when someone states a preference, which happens anywhere.
- `check-operator-entries.sh` guarded a case mismatch the hook can no longer produce: the login is lowercased once, and that form is both what the message prints and what names the file.
- The catalog stops listing a skill's own files — `voice.md` and `operators/` fold into the `/plainly` row, disposition "adopt — rewrite its `operators/` entries".

## QA Checklist

- [ ] `handle` — start a fresh session in this repo and read the first lines of context: it should name you and print your entry verbatim, with no tool call spent resolving it.
- [ ] `greeting` — that session's first reply opens by greeting you by name, not by handle.
- [ ] `no-name` — stub `gh` to return an empty third field; the message falls back to `@handle` alone and the reply greets you by nothing.
- [ ] `uppercase-login` — stub `gh` to return `VZakharov\tUser\tVova Zakharov`; it must still resolve `vzakharov.md`.
- [ ] `no-entry` — `git mv .claude/skills/plainly/operators/vzakharov.md /tmp/`, run `.claude/hooks/session-start.sh`, confirm it reports no entry **and still exits 0 with output** (this path died silently before the `|| true` fix).
- [ ] `bot-token` — stub `gh` to return `something[bot]\tBot\t`, run the hook, confirm it names no operator and says to ask.
- [ ] `gh-down` — run the hook with `gh` absent from `PATH` (coreutils intact) and with a `gh` that exits 1; both should report the operator unresolved and exit 0.
- [ ] `no-import` — confirm `CLAUDE.md` has no `@.claude/skills/plainly/operators` line and that a session's context no longer carries anyone else's entry.
- [ ] `local` — run the hook with `CLAUDE_CODE_REMOTE` unset: job 3 runs, the `gh` shim and dependency install stay skipped.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `handle` | integration | ❌ | No test drives the hook. Would stub `gh` and assert the printed line. |
| `greeting` | manual-only | — | Whether a reply opens with a greeting is model behavior, not something this repo can assert. |
| `no-name` | integration | ❌ | Assert the message degrades to `@handle` with no name in it. |
| `uppercase-login` | integration | ❌ | The case the deleted check guarded; now the hook's own job, so it is the one that most wants a test. |
| `no-entry` | integration | ❌ | The regression that matters most — assert non-empty stdout and exit 0 with no entry file. |
| `bot-token` | integration | ❌ | Stub `gh` to emit a `Bot` type; assert no handle is asserted as the operator. |
| `gh-down` | integration | ❌ | Two stubs: `gh` absent from `PATH`, and `gh` exiting non-zero. |
| `no-import` | manual-only | — | What reaches a session's context is a harness behavior. |
| `local` | integration | ❌ | Assert job 3's line is present and the shim is not written when `CLAUDE_CODE_REMOTE` is unset. |

**Coverage gap worth naming, now wider than it was:** six of nine rows are uncovered and nothing here is automated at all, `check-operator-entries.sh` having been the one check and now deleted. This branch is where the hook's behavior got two silent-failure bugs — the `set -e` death on a missing entry file, and a `[ -n "$name" ] && …` one-liner that would have killed the hook for every operator whose profile has no name. Both were caught by hand.

There is also a trap any test must handle, found by walking into it. Job 1 resolves the real `gh` from `PATH` on every run, so running the hook with a stubbed `PATH` makes it write `~/.local/bin/gh` pointing at the stub — and `~/.local/bin` is first on `PATH`, so `gh` breaks for the rest of the session the moment the stub is cleaned up. Job 1 and 2 are already gated on `CLAUDE_CODE_REMOTE`, so a job-3 test unsets it: `env -u CLAUDE_CODE_REMOTE PATH=<stub> .claude/hooks/session-start.sh` exercises the operator lookup and leaves the shim untouched.

`scripts/test_authorship.py` is the precedent for a test at this layer, so a `test_session_start.py` is feasible — worth filing rather than doing here.

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

### `.claude/hooks/session-start.sh`:149 — resolved

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

### `.claude/hooks/session-start.sh`:48 — unresolved

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

---

### `.claude/hooks/session-start.sh`:100 — unresolved

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

---

### `.claude/skills/update-muthur/catalog.md`:118 — unresolved

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

---

### `.claude/hooks/session-start.sh`:1 — unresolved

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

---

## Timeline (status, references, and other events)

- **2026-09-12T15:20:11Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/73#pullrequestreview-5186875380.
- **2026-09-12T15:31:10Z** @vzakharov cross-referenced this pull request from [#72 docs: drop the working-artifact rows from the catalog's Never table](https://github.com/vzakharov/muthur/issues/72).
- **2026-09-12T15:36:28Z** @vzakharov renamed from «feat: name the session's operator and their entry at session start» to «feat: name and greet the session's operator at startup».
- **2026-09-13T19:46:45Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/73#pullrequestreview-5188252193.
