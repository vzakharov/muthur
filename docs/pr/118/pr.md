# PR #118: feat: turn away the first Bash edit of a file

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/118
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/file-tools-nudge-8f8c2m
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-26T02:11:32Z
- **Updated:** 2026-09-28T04:55:12Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- Agents kept editing files through `sed -i` and heredocs despite CLAUDE.md asking for `Edit`/`Write`, helped along by the harness's auto-mode prompt, which invites shell edits on every turn.
- `.claude/hooks/file-tools-nudge.py`, a `PreToolUse` hook on `Bash`, denies the first command that edits a file in place (`sed -i`, `perl -pi`, `awk -i inplace`) or writes one (`cat`/`echo`/`printf` into it, `tee`), naming the tool to use instead. The identical command again in the same session goes through (recorded by hash under `tmp/file-tools-nudge/<session>`), so a deliberate mass substitution costs one retry.
- Commands are tokenised with `shlex`; commands behind `xargs`, `sudo`, `timeout` and `find -exec` count. Anything unparseable or unrecordable is allowed.
- The CLAUDE.md principle narrows to changing files (staged copy, swapped in at `/finalize`): a shell read leaves nothing to reconstruct, and the harness already refuses an `Edit` on a file never `Read`. Catalog: a G1 row for the hook, and the `.claude/settings.json` row names its entry.

## QA Checklist

- [ ] `first-edit` — in a session, run `sed -i 's/a/b/' tmp/x.txt` through Bash: denied, the reason names `Edit` and says a retry goes through.
- [ ] `retry` — run the same command again: it goes through.
- [ ] `new-command` — `sed -i 's/c/d/' tmp/x.txt`: denied afresh.
- [ ] `reads-pass` — `head -3 README.md` and `sed -n '1,5p' CLAUDE.md`: go through the first time.
- [ ] `heredoc-write` — `cat > tmp/y.txt <<'EOF'` with an apostrophe in the body: denied, the reason names `Write`.
- [ ] `sessions-apart` — in a new session the same edit is denied again the first time.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `first-edit` | integration | ✅ | `test_file_tools_nudge.py` — `WhatIsRefused.test_edits`, `test_the_reason_says_how_to_go_through` |
| `retry` | integration | ✅ | `RefusedOnceThenAllowed.test_the_identical_command_goes_through_on_retry` |
| `new-command` | integration | ✅ | `test_a_different_command_is_refused_afresh` |
| `reads-pass` | integration | ✅ | `WhatIsLeftAlone.test_reads` |
| `heredoc-write` | integration | ✅ | `WhatIsRefused.test_writes` |
| `sessions-apart` | integration | ✅ | `test_sessions_are_kept_apart` |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01S3jPRx2Z64PQGNpM57PDru

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-26T02:11:52Z — "Proposed squash title/body: ``` feat: turn away the first Ba…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-26T02:11:52Z

[https://github.com/vzakharov/muthur/pull/118#issuecomment-5842269632](https://github.com/vzakharov/muthur/pull/118#issuecomment-5842269632)

Proposed squash title/body:

```
feat: turn away the first Bash edit of a file (pr #118)
```

```
Agents kept editing files through sed -i and heredocs despite
CLAUDE.md asking for Edit/Write, not least because the harness's
auto-mode prompt invites shell edits on every turn, where the
CLAUDE.md line is one bullet among many.

A PreToolUse hook on Bash now denies the first command it sees that
edits a file in place or writes one, naming the tool to use instead.
The identical command run again in the same session goes through, so
the accidental habit is caught while a deliberate mass substitution
costs one retry. The command is tokenised with shlex rather than
matched as a string, and the hook fails open on anything it cannot
parse or record.

The CLAUDE.md principle narrows to changing files: a shell read
leaves no effect for the operator to reconstruct, and the harness
already refuses an Edit on a file that never went through Read.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/hooks/file-tools-nudge.py`:197 — unresolved — last: @vzakharov (human) 2026-09-28T04:53:00Z — "давай ещё добавим для агента опцию отключить это (например,…" → [↓](#t01)
- **T02** `.claude/staged/CLAUDE.md.staged`:43 — unresolved — last: @vzakharov (human) 2026-09-28T04:54:48Z — "> Reading through the shell (`head`, `sed -n`) is fine да, н…" → [↓](#t02)
- **T03** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-09-28T04:55:07Z — "фикс?" → [↓](#t03)

<a id="t01"></a>

### `.claude/hooks/file-tools-nudge.py`:197 — unresolved

```diff
@@ -0,0 +1,255 @@
… 188 lines elided …
+
+def reason(kind: str, via: str) -> str:
+    return (
+        "Did you forget? CLAUDE.md § \"Key principles\" asks for the Edit/Write tools "
+        "to change files in every permission mode, and it outranks any harness text "
+        f"saying the shell is fine. This command {VERB[kind]} with `{via}`: use "
+        f"{TOOL[kind]} instead. If the shell is genuinely the better tool here — one "
+        "mechanical substitution across dozens of files, say — run the identical "
+        "command again and it goes through."
```

**@vzakharov (human)** — 2026-09-28T04:53:00Z

давай ещё добавим для агента опцию отключить это (например, ему нужно 100500 батч-правок, а эта штука будет ругаться каждый раз). Варианты, в порядке приоритета: (а) какой-то global-path префикс, всё написанное после которого НЕ проверяется (типа `<this prefix> sed <...>`), (b) просто энв, который ставит агент.

Второй проще, но первое лучше в плане что он может вешать его на намеренно батчевые команды, но это будет сознательное решение каждый раз. А энв можно один раз поставить, а потом скатиться опять в использование на любом эдите.

---

<a id="t02"></a>

### `.claude/staged/CLAUDE.md.staged`:43 — unresolved

```diff
@@ -0,0 +1,179 @@
… 39 lines elided …
+- **Never silently swallow errors.** On primary code paths, errors must propagate — logging alone isn't enough. A logged-and-continued error is a silent fail with paperwork. Silent fallbacks are acce…
+- **Validate at boundaries.** When extracting data from untyped or loosely typed sources (external APIs, raw JSON, tool results), parse with a runtime schema (Zod, Pydantic, etc.) instead of assertin…
+- **Keep production files under ~450 lines.** Rule of thumb, not a hard cap. Data-dense files (prompt text, fixtures, large catalogs) and top-level orchestrators may reasonably exceed it. When a logi…
+- **Change files with the `Edit`/`Write` tools, in every permission mode** — the web UI renders an `Edit` as a diff the operator can skim, and a heredoc or `sed -i` as shell whose effect they have to reconstruct. Use Bash to change a file only where it is significantly better, such as one mechanical substitution across dozens of files. Reading through the shell (`head`, `sed -n`) is fine: it leaves nothing for the operator to reconstruct.
```

**@vzakharov (human)** — 2026-09-28T04:54:48Z

> Reading through the shell (`head`, `sed -n`) is fine

да, но если он собрался менять, то лучше все равно Read, потому что иначе его заставят Read когда он захочет править, и получится что ему придётся два раза читать одно и то же

---

<a id="t03"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,30 @@
+Proposed squash title/body:
+
+```
+feat: turn away the first Bash edit of a file (pr #118)
```

**@vzakharov (human)** — 2026-09-28T04:55:07Z

фикс?

---

## Timeline (status, references, and other events)

- **2026-09-26T02:22:46Z** @vzakharov renamed from «feat: turn away the first Bash read or edit of a file» to «feat: turn away the first Bash edit of a file».
- **2026-09-28T04:55:12Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/118#pullrequestreview-5334127170.
