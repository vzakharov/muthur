# PR #187: feat: hard-wrap Markdown at 80 columns with prettier

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/187
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/md-prettier-no-tables-5qxf9h
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-13T17:32:16Z
- **Updated:** 2026-10-14T08:41:16Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 5

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `.claude/rules/markdown-wrap.md`:20 — unresolved — last: @vzakharov (human) 2026-10-14T08:33:29Z — "хм, вроде не всегда -- например export пиара сам создаёт .md…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:1 — unresolved — last: @vzakharov (human) 2026-10-14T08:36:01Z — "вопрос, а что prettier делает с таблицами? там же by design…" → [↓](#t02)
- **T03** `.claude/skills/finalize/SKILL.md`:1 — unresolved — last: @vzakharov (human) 2026-10-14T08:37:00Z — "440 строк -- на пределе. получились ли у нас какие-то в резу…" → [↓](#t03)
- **T04** `.prettierignore`:1 — unresolved — last: @vzakharov (human) 2026-10-14T08:40:02Z — "а, то есть ты их уже заигнорил, ок" → [↓](#t04)
- **T05** `.prettierrc.json`:3 — unresolved — last: @vzakharov (human) 2026-10-14T08:41:00Z — "это стандартная ширина ведь, да? всё время недоумеваю почему…" → [↓](#t05)

---

## Body

## Summary

- Every tracked `.md` is hard-wrapped at 80 columns by prettier (`proseWrap: always`), because an unwrapped paragraph is one physical line and any edit to it rewrites the whole paragraph in the diff. The reflow is its own `style:` commit (e4f4507) and changes no words: beyond line breaks it only turns `*em*` into `_em_`, adds blockquote `>` markers, and drops the padding of one double-backtick span.
- prettier is pinned in `scripts/prettier.sh` (through `npx`, no `package.json`). A `PostToolUse` hook (`.claude/hooks/format-md.sh`) wraps each `.md` an agent edits, `scripts/check-markdown-wrap.sh` checks it in `vet.sh`, and `install-deps.sh` fetches it at session start. CLAUDE.md and voice.md are reflowed through staged copies and swap in at `/finalize`.
- Text that becomes a GitHub body or comment is never wrapped, since GitHub renders its newlines as line breaks: `.prettierignore` exempts `docs/pr/`, `docs/issue/`, the squash proposal and `tmp/`, and the hook skips anything outside the tree. `embeddedLanguageFormatting: off` keeps prettier out of ```` ```markdown ```` fences (the `/finalize` and `/qa-checklist` templates) and YAML frontmatter, so no skill description changes.
- `check-skill-catalog.sh` now matches a `CLAUDE.md § "…"` citation split across lines, which wrapping makes common. The convention is its own rule, `.claude/rules/markdown-wrap.md`, separate from the opt-in `markdown.md` so that deleting that one to keep tables doesn't drop it too. Adopters are told (`[attn adopters]`) to skip the reflow and wrap with their own tooling.

## QA Checklist

- [ ] `wrapped` — `scripts/check-markdown-wrap.sh` passes over every tracked `.md`, reading CLAUDE.md and voice.md through their staged copies
- [ ] `pure-reflow` — `git show -w --word-diff=plain --word-diff-regex='[^[:space:]]+' e4f4507` shows no word changes beyond `*em*`→`_em_`, blockquote `>` markers and one code span's padding
- [ ] `fences-frontmatter` — the fenced templates in `.claude/skills/finalize/SKILL.md` and `.claude/skills/qa-checklist/SKILL.md`, and every file's frontmatter, are byte-identical to `main`
- [ ] `hook` — in a session, `Edit` a long line into any `.md`; the file comes back wrapped at 80
- [ ] `hook-ignored` — edit `docs/pr/<n>/body.md`, a `tmp/` draft, or a `.md` in the scratchpad; it stays unwrapped
- [ ] `hook-failure` — with `npx` broken, edit a `.md`; the agent sees prettier's error rather than a silent pass
- [ ] `citations` — `scripts/check-skill-catalog.sh` passes, and still fails on a `CLAUDE.md § "…"` citation naming a missing heading across a line break
- [ ] `claude-md-size` — `scripts/check-claude-md-size.sh` passes on the staged, wrapped CLAUDE.md (29409/30000)

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `wrapped` | unit | ✅ | The vet check itself; `test_markdown_wrap.py` covers it on fixtures |
| `pure-reflow` | manual-only | — | One-time read of the reformat commit |
| `fences-frontmatter` | unit | — | A diff of fence and frontmatter text against `main` |
| `hook` | integration | ✅ | `test_markdown_wrap.py` runs the hook on a fixture path |
| `hook-ignored` | integration | ✅ | `test_markdown_wrap.py`: ignored and outside-the-tree paths stay unchanged |
| `hook-failure` | integration | ✅ | `test_markdown_wrap.py`: a fake failing `npx` gives exit 2 and its stderr |
| `citations` | unit | — | Checked by hand on a fixture; `check-skill-catalog.sh` has no test file |
| `claude-md-size` | unit | ✅ | The existing size check, run by vet |

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_012uo4RmMJ46ZKeThV456vR2

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-13T17:32:30Z — "Proposed squash title/body: ``` feat: [attn adopters] hard-w…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-13T17:32:30Z

[https://github.com/vzakharov/muthur/pull/187#issuecomment-6151386934](https://github.com/vzakharov/muthur/pull/187#issuecomment-6151386934)

Proposed squash title/body:

```
feat: [attn adopters] hard-wrap Markdown at 80 columns with prettier (pr #187)
```

```
Markdown here is read raw, by agents and in diffs, and an unwrapped
paragraph is one physical line, so editing one clause rewrote the whole
paragraph in the diff.

All tracked Markdown is hard-wrapped at 80 columns by prettier, pinned
in scripts/prettier.sh and run through npx, with no package.json to
mark the repo as a JS project. A PostToolUse hook,
.claude/hooks/format-md.sh, wraps each .md an agent edits;
scripts/check-markdown-wrap.sh checks every tracked one in vet.sh; and
install-deps.sh warms prettier up at session start. The convention is
its own rule, .claude/rules/markdown-wrap.md, apart from the opt-in
no-tables rule so that deleting that one keeps it.
check-skill-catalog.sh now matches CLAUDE.md § citations split across
lines.

Text that becomes a GitHub body or comment stays unwrapped, since
GitHub renders its newlines as line breaks: .prettierignore exempts
docs/pr/, docs/issue/, the squash proposal and tmp/, and the hook skips
files outside the tree. embeddedLanguageFormatting is off, so fenced
templates and YAML frontmatter come through untouched.

Adopters: split the sync at this commit. Port everything before it as
usual. From this commit take only the tooling (scripts/prettier.sh,
.prettierrc.json, .prettierignore, .claude/hooks/format-md.sh,
scripts/check-markdown-wrap.sh), the settings.json hook entry, the
vet.sh and install-deps.sh lines, the rule file and the
check-skill-catalog.sh citation fix, never its reflow of existing
Markdown. Wrap your own Markdown with your own tooling (the prettier
files are optional), keeping the GitHub-bound exemptions, then port
what follows as usual. No operator approval is needed beyond what a
sync already asks.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `.claude/rules/markdown-wrap.md`:20 — unresolved — last: @vzakharov (human) 2026-10-14T08:33:29Z — "хм, вроде не всегда -- например export пиара сам создаёт .md…" → [↓](#t01)
- **T02** `docs/remove-before-merging/squash-message.md`:1 — unresolved — last: @vzakharov (human) 2026-10-14T08:36:01Z — "вопрос, а что prettier делает с таблицами? там же by design…" → [↓](#t02)
- **T03** `.claude/skills/finalize/SKILL.md`:1 — unresolved — last: @vzakharov (human) 2026-10-14T08:37:00Z — "440 строк -- на пределе. получились ли у нас какие-то в резу…" → [↓](#t03)
- **T04** `.prettierignore`:1 — unresolved — last: @vzakharov (human) 2026-10-14T08:40:02Z — "а, то есть ты их уже заигнорил, ок" → [↓](#t04)
- **T05** `.prettierrc.json`:3 — unresolved — last: @vzakharov (human) 2026-10-14T08:41:00Z — "это стандартная ширина ведь, да? всё время недоумеваю почему…" → [↓](#t05)

<a id="t01"></a>

### `.claude/rules/markdown-wrap.md`:20 — unresolved

```diff
@@ -0,0 +1,21 @@
… 15 lines elided …
+`scripts/vet.sh` checks every tracked one, both through `scripts/prettier.sh`.
+
+**Text bound for a GitHub issue or PR body, or a comment, is never wrapped**,
+because GitHub renders its newlines as line breaks. Such a draft goes under
+`tmp/` or outside the tree, which nothing wraps; a new home for such drafts
```

**@vzakharov (human)** — 2026-10-14T08:33:29Z

хм, вроде не всегда -- например export пиара сам создаёт .md в remove-before-merging?

---

<a id="t02"></a>

### `docs/remove-before-merging/squash-message.md`:1 — unresolved

**@vzakharov (human)** — 2026-10-14T08:36:01Z

вопрос, а что prettier делает с таблицами? там же by design иногда не может всё уместиться в 80 символов?

---

<a id="t03"></a>

### `.claude/skills/finalize/SKILL.md`:1 — unresolved

**@vzakharov (human)** — 2026-10-14T08:37:00Z

440 строк -- на пределе. получились ли у нас какие-то в результате md больше 450 строк?

+в обоснование зачем это делаем помимо диффов можно добавить, что позволяет at a glance оценить размер документа без необходимости подсчёта символов

---

<a id="t04"></a>

### `.prettierignore`:1 — unresolved

**@vzakharov (human)** — 2026-10-14T08:40:02Z

а, то есть ты их уже заигнорил, ок

---

<a id="t05"></a>

### `.prettierrc.json`:3 — unresolved

```diff
@@ -0,0 +1,11 @@
+{
+  "proseWrap": "always",
+  "printWidth": 80,
```

**@vzakharov (human)** — 2026-10-14T08:41:00Z

это стандартная ширина ведь, да? всё время недоумеваю почему для commit messages исторически используется другая

---

## Timeline (status, references, and other events)

- **2026-10-13T18:02:47Z** @vzakharov cross-referenced this pull request from [#189 Replace Markdown tables with lists or sections](https://github.com/vzakharov/muthur/issues/189).
- **2026-10-13T18:03:40Z** @vzakharov renamed from «feat: hard-wrapped, table-free Markdown under prettier» to «feat: hard-wrap Markdown at 80 columns with prettier».
- **2026-10-13T19:40:06Z** @vzakharov referenced this pull request in a commit: https://api.github.com/repos/vzakharov/muthur/commits/4e5c04153f4ac9fe5ed35371461b998f2fdb0ce7.
- **2026-10-14T08:41:15Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/187#pullrequestreview-5515163713.
