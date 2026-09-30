# PR #123: feat: cap CLAUDE.md and its imports with hysteresis at 30k/29k chars

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/123
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/claude-md-size-cap-vn0pdj
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-30T15:33:26Z
- **Updated:** 2026-09-30T17:07:16Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **vet fails when the CLAUDE.md a branch will land, plus everything it `@`-imports, passes 30,000 characters. A branch that took the total past that point has to land it at 29,000 or under.** This is `scripts/check-claude-md-size.sh`. With a single cap, every session would trim back to just under the line, and the next session would start right at it again. The 1,000-character gap means one trim makes room for many additions.
- **Imports count because the harness loads them into the same prefix as CLAUDE.md**, so moving text into one would cut nothing. An import is what the harness treats as one: an `@<path>` at line start or after whitespace, outside code spans and fenced blocks, naming a file that exists, resolved against the importing file's directory, up to five hops deep. Backticked `@.claude/…` citations load nothing and are not counted. On this tree that is CLAUDE.md (23,609) plus `.claude/voice/voice.md` (3,692) — the same two files a session transcript records as loaded. `.claude/rules/` is left for separate work.
- **Whether the branch went over is read from its history, so nothing is stored.** The check looks at every commit since the branch split from origin's default branch, plus the worktree. A base that is already over counts as crossed on the branch's first commit. With no base to compare against, only the ceiling is checked, and the output says so.
- **Each file is measured as the branch will land it**: its staged copy under `.claude/staged/` where there is one, the file itself otherwise. So a staged trim of an oversized file passes before `/finalize` swaps it in, and a staged copy that grew past the ceiling fails. The failure message lists every file with its size and, like `.claude/rules/staging.md`, says to hand the trim to a subagent: the trim is never what the PR is for, and its cut-and-remeasure loop would use up the session's context. The count is characters rather than bytes. There is no env override: an adopter with its own idea of the right size edits the two constants in its copy.

## QA Checklist

- [ ] `ok` — on this branch, `scripts/check-claude-md-size.sh` prints `ok — CLAUDE.md and its imports are 27301/30000 chars (CLAUDE.md 23609, .claude/voice/voice.md 3692)` and exits 0.
- [ ] `ceiling` — in a scratch clone, grow CLAUDE.md past the ceiling and commit: the check exits 1, names the commit, says `lands at 29000 or under`, and says to hand the trim to a subagent.
- [ ] `hysteresis` — in the same clone, trim the total to 29,500 and commit: it still fails and says how much more to cut. Trim to 29,000: it passes and says `back under 29000`.
- [ ] `import` — move a large chunk of CLAUDE.md into a new file and put `@<that file>` on its own line in CLAUDE.md: the total does not drop, and the file appears in the breakdown. Wrap the same `@<file>` in backticks: it drops out.
- [ ] `staged` — `scripts/staged.sh stage CLAUDE.md` and grow the copy past the ceiling: the check fails on the copy although the real file fits.
- [ ] `vet-line` — `./scripts/vet.sh` prints the `check-claude-md-size:` line between `staged.sh check` and `check-muthur.sh`.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `ok` | unit | ✅ | `test_growth_up_to_the_ceiling_passes`; the real repo is exercised by every vet run |
| `ceiling` | unit | ✅ | `test_a_file_over_the_ceiling_fails_and_names_the_target`, `test_an_uncommitted_file_over_the_ceiling_fails` |
| `hysteresis` | unit | ✅ | `test_trimming_back_under_the_ceiling_alone_still_fails`, `test_trimming_to_the_target_passes`, `test_a_crossing_on_the_base_is_not_this_branchs` |
| `import` | unit | ✅ | `test_an_import_counts_toward_the_total`, `test_imports_are_followed_transitively_from_each_files_directory`, `test_a_cited_path_is_not_an_import`, `test_imports_past_the_hop_limit_are_not_followed`, `test_an_import_cycle_is_counted_once` |
| `staged` | unit | ✅ | `test_a_staged_copy_over_the_ceiling_fails_though_the_real_file_fits`, `test_a_staged_trim_passes_though_the_real_file_is_over`, `test_the_swap_commit_measures_the_real_file_again`, `test_an_imports_staged_copy_is_what_counts` |
| `vet-line` | manual-only | — | Wiring in `vet.sh`, visible in its output |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01GXYBayCsJLcxyatvbENoSC
https://claude.ai/code/session_01Jjw1GivQpJUKwPscRjQKAj

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-30T15:33:44Z — "Proposed squash title/body: ``` feat: cap CLAUDE.md and its…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-30T15:33:44Z

[https://github.com/vzakharov/muthur/pull/123#issuecomment-5914494358](https://github.com/vzakharov/muthur/pull/123#issuecomment-5914494358)

Proposed squash title/body:

```
feat: cap CLAUDE.md and its imports with hysteresis at 30k/29k chars (pr #123)
```

```
Every character of the root CLAUDE.md is paid on every turn of every
session, and nothing pushed back on its growth: each addition passed its
own test while the total drifted up. Across the repos built on this
template it had reached 24-61k characters before hand trims.

vet now fails when the CLAUDE.md the branch will land, plus everything
it @-imports, passes 30,000 characters, and a branch that took it past
that must land it at 29,000 or under. The imports count because the
harness loads them into the same prefix, so moving text into one would
cut nothing; backticked @-citations load nothing and are not counted,
and .claude/rules/ is left for separate work. A single cap would be
trimmed back to just under itself every session; the gap makes one
trim buy room for many additions. "Crossed" is read off the branch's
own commits since its merge-base, so no state is kept. Each file is
measured as its staged copy where there is one, so a staged trim of an
oversized file passes before /finalize swaps it in.

The count is characters rather than bytes. There is no env override:
an adopter with its own idea of the right size
edits the two constants in its copy. The failure message and the staging
rule send the trim to a subagent: it is never the PR's own work, and its
cut-and-remeasure loop would spend the session's context.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

_2 resolved threads omitted; re-run with `--include-resolved` to export them._

- **T01** `scripts/check-claude-md-size.sh`:122 — unresolved — last: @vzakharov (human) 2026-09-30T17:07:01Z — "это что за язык?" → [↓](#t01)

<a id="t01"></a>

### `scripts/check-claude-md-size.sh`:122 — unresolved

```diff
@@ -66,27 +73,93 @@ merge_base_with_default() {
… 29 lines elided …
+# The import candidates in the text on stdin, one repo-relative path per line,
+# resolved against directory $1. A `~` or absolute path names a file outside what
+# the branch lands, and a path that climbs out of the repo resolves to nothing.
+imports_in() {
+  awk -v dir="$1" '
+    function normalize(p,   parts, n, i, k, out, j) {
+      n = split(p, parts, "/")
+      k = 0
+      for (i = 1; i <= n; i++) {
+        if (parts[i] == "" || parts[i] == ".") continue
+        if (parts[i] == "..") { if (k == 0) return ""; k--; continue }
+        out[++k] = parts[i]
+      }
+      p = ""
+      for (j = 1; j <= k; j++) p = p (j > 1 ? "/" : "") out[j]
+      return p
+    }
+    /^[ \t]*(```|~~~)/ { fenced = !fenced; next }
+    fenced { next }
+    {
+      gsub(/`[^`]*`/, "")
+      n = split($0, words, /[ \t]+/)
+      for (i = 1; i <= n; i++) {
+        if (words[i] !~ /^@[^~\/]/) continue
+        path = normalize(dir "/" substr(words[i], 2))
+        if (path != "") print path
+      }
+    }
+  '
+}
```

**@vzakharov (human)** — 2026-09-30T17:07:01Z

это что за язык?

---

## Timeline (status, references, and other events)

- **2026-09-30T15:40:11Z** @vzakharov renamed from «feat: cap the CLAUDE.md a branch lands at 25k characters» to «feat: cap CLAUDE.md with hysteresis at 25.5k/24.5k characters».
- **2026-09-30T16:44:43Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/123#pullrequestreview-5369247524.
- **2026-09-30T16:59:10Z** @vzakharov renamed from «feat: cap CLAUDE.md with hysteresis at 25.5k/24.5k characters» to «feat: cap CLAUDE.md and its imports with hysteresis at 29k/28k chars».
- **2026-09-30T16:59:54Z** @vzakharov renamed from «feat: cap CLAUDE.md and its imports with hysteresis at 29k/28k chars» to «feat: cap CLAUDE.md and its imports with hysteresis at 30k/29k chars».
- **2026-09-30T17:07:16Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/123#pullrequestreview-5369496622.
