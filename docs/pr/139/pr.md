# PR #139: feat: estimate comment justifies the team, not the work

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/139
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/estimate-justifies-team-7qjkt5
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-04T20:19:14Z
- **Updated:** 2026-10-04T20:22:39Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- The human-hour estimate's comment asked "why the task is this size", and agents answered with a summary of what the session did. The cost row and the commits already hold that summary, and it gives nobody a way to check the figure.
- The `UserPromptSubmit` notice now asks for the case for the team instead: for each `--part`, why that role, at that grade, for those hours. It gives an example and rules out a work summary. Both texts say this: the one that asks for a first estimate and the one that asks for a revision.
- `estimate.py set --help` describes the `comment` argument the same way. `lib/estimate.py`'s docstring and `.claude/costs/CLAUDE.md` § "Human-hour estimates" are reworded to match, and the CLAUDE.md section gains a bullet on why: only a per-part justification lets a reader check the estimate instead of taking it on trust.

## QA Checklist

- [ ] `notice-first` — pipe `{"session_id":"x-test","cwd":"<repo>"}` into `bash .claude/costs/hooks/estimate-notice.sh` with no estimate set. The context asks for a per-part justification, quotes the example, and says "never a summary of the work".
- [ ] `notice-revise` — set an estimate for a session, then run the hook again. The revision line asks to justify each part's role, grade and hours, and rules out a work summary and a narrative of how the figure moved.
- [ ] `help` — `python3 .claude/costs/estimate.py set --help` shows the new help text for `comment`.
- [ ] `in-session` — in a fresh session, the first estimate the agent sets has a comment that justifies each part rather than recapping the work.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `notice-first` | integration | ❌ | Run the hook with a payload and assert the context contains the justification wording |
| `notice-revise` | integration | ❌ | Same, after writing a pending estimate |
| `help` | unit | ❌ | Parse `--help` output for the `comment` help string |
| `in-session` | manual-only | — | Depends on how a model reads the notice, which needs judgement |

Closes #138

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-04T20:19:36Z — "Proposed squash title/body: ``` feat: #138 estimate comment…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-04T20:19:36Z

[https://github.com/vzakharov/muthur/pull/139#issuecomment-5984004201](https://github.com/vzakharov/muthur/pull/139#issuecomment-5984004201)

Proposed squash title/body:

```
feat: #138 estimate comment justifies the team, not the work (pr #139)
```

```
The human-hour estimate's comment was asked to say why the task is its
size, and agents answered with a summary of what the session did. The
cost row and the commits already carry that summary, and it gives no
reader a way to check the figure.

The UserPromptSubmit estimate notice now asks for the case for the team
instead: for each --part, why that role, at that grade, for those hours.
It gives an example and rules out a summary of the work, and the
revision prompt asks the same of the parts as they now stand. The help
text for estimate.py's comment, lib/estimate.py's docstring and the
"Human-hour estimates" section of .claude/costs/CLAUDE.md all match. The
CLAUDE.md section also records why: a reader can only check an estimate
whose comment justifies each part. Otherwise they have to take it on
trust.

Closes #138

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/remove-before-merging/squash-message.md`:4 — unresolved — last: @vzakharov (human) 2026-10-04T20:22:34Z — "fix?" → [↓](#t01)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:4 — unresolved

```diff
@@ -0,0 +1,30 @@
+Proposed squash title/body:
+
+```
+feat: #138 estimate comment justifies the team, not the work (pr #139)
```

**@vzakharov (human)** — 2026-10-04T20:22:34Z

fix?

---

## Timeline (status, references, and other events)

- **2026-10-04T20:22:39Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/139#pullrequestreview-5407984510.
