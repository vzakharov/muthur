# PR #83: feat: re-export and commit a /handle branch's PR every turn

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/83
- **Author:** @vzakharov (human)
- **Base ← Head:** main ← claude/handle-pr-export-ip1a9z
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-16T12:20:08Z
- **Updated:** 2026-09-16T21:31:06Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **`/handle` Step 2 takes the PR export every turn and commits it.** A PR moves while the branch works, so `docs/pr/<n>/pr.md` existing says only that someone took a snapshot once. The committed sequence is a record for the person reviewing the branch first: consecutive exports differ by the comments and thread resolutions each turn was answering, which the turn's own commits do not say.
- **A new `UserPromptSubmit` hook has the taking done before the turn.** It resolves the prompt's target (the last token if it names a real branch, otherwise the branch HEAD is on) to a PR through `gh`, re-exports it, and reports what arrived as a `git diff` against the export the previous turn committed. An empty diff is the answer to "has anything changed?", not the absence of one.
- **The root cause was a rule, not an oversight.** `/finalize`'s sweep told a resumed agent — post-compaction handoff, parallel session — to read the committed export instead of re-exporting, and said it of `docs/issue/` and `docs/pr/` in one breath. True for an issue thread, which is a snapshot; wrong for a PR. That sentence now covers issues only, and names what separates the two: an issue is committed once, a PR every time it is re-taken.
- **A bare `/handle` now targets the branch the session is on** rather than stopping to ask — that being what a session types once it is already attached, which is the same post-compaction moment. The trunk keeps the old behaviour, having no work to read off it.
- `/from-branch` Step 2 exempts an untracked `docs/pr/<n>/` from its work-to-lose check: the hook writes it before the turn, on whatever branch HEAD was on, and `git checkout` carries it across to be committed there.
- `project_root` moves into `.claude/hooks/lib.sh` — three hooks resolved it by hand and the `CLAUDE_PROJECT_DIR`-over-payload-`cwd` preference is a rule they have to agree on.

## QA Checklist

- [ ] `repeat-handle` — on a branch with an open PR, submit `/handle <that branch>` twice, committing the export in between as Step 2 says. The second turn's injected context reports an empty `git diff` and that nothing has arrived.
- [ ] `changed-pr` — post a comment on that PR between the two `/handle` prompts. The second turn's context carries the `git diff` showing it.
- [ ] `audit-trail` — after several `/handle` turns, `git log -p -- docs/pr/<n>` reads as the sequence of PR states each turn answered, thread resolutions included.
- [ ] `bare-handle` — on a feature branch with a PR, submit a bare `/handle`. It exports that branch's PR with no target in the prompt.
- [ ] `trunk` — check out `main` and submit `/handle`. Nothing is exported; the hook says so on stderr.
- [ ] `no-pr` — on a fresh harness auto-branch, submit `/handle`. Nothing is exported and nothing is injected.
- [ ] `flag-after-target` — submit `/handle <branch> and finalize`. The hook misses by design; the agent runs the export itself per Step 2.
- [ ] `never-fails` — run the hook with `gh` off `PATH`, with an unreachable network, and with a `cwd` that does not exist. Each exits 0 and the turn proceeds.
- [ ] `sweep` — run `/finalize` on a branch carrying committed exports. `git rm -rf` removes them, and an untracked leftover from the same turn's hook goes too.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `repeat-handle` | integration | ❌ | Two synthetic `UserPromptSubmit` payloads against a fixture PR, committing between; assert the empty-diff wording |
| `changed-pr` | integration | ❌ | Same, mutating the committed export between runs; assert a fenced `diff` block appears |
| `audit-trail` | manual-only | — | A judgement about what a human reads out of the branch history |
| `bare-handle` | integration | ❌ | Payload with a bare `/handle` prompt on a branch that has a PR |
| `trunk` | unit | ❌ | Trunk guard: `/handle main` emits no context and exits 0 |
| `no-pr` | integration | ❌ | Branch with no PR emits nothing |
| `flag-after-target` | unit | ❌ | Last-token resolution rejects `finalize` as a branch |
| `never-fails` | integration | ❌ | Each failure path exits 0 — the contract every hook here keeps |
| `sweep` | integration | ❌ | Tracked and untracked `docs/pr/<n>/` both gone after the sweep step |

The repo has no harness for bash hooks today — `scripts/test_*.py` cover the exporter's Python internals only — so every automatable row is uncovered for the same reason. Each was exercised by hand against synthetic payloads and a real PR while building.

https://claude.ai/code/session_01LoQarnxZ16ZUg8UUZ9nwni

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-16T12:20:40Z — "Proposed squash title/body: ``` feat: re-export and commit a…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-16T12:20:40Z

[https://github.com/vzakharov/muthur/pull/83#issuecomment-5697320253](https://github.com/vzakharov/muthur/pull/83#issuecomment-5697320253)

Proposed squash title/body:

```
feat: re-export and commit a /handle branch's PR every turn (pr #83)
```

```
A second `/handle` on the same branch — the ordinary move after a
compaction boundary — answered "has anything arrived on the PR?" off an
export taken an hour earlier, and reported there was nothing to handle.
The agent was obeying a rule rather than skipping a step: `/finalize`'s
sweep told a resumed session to read the committed export instead of
re-exporting, and said it of issue and PR exports in one breath. That
holds for an issue thread, which is a snapshot taken once and read
forever. A PR moves while the branch works.

So the sweep's sentence covers issues only, and `/handle` Step 2 states
the opposite rule for PRs: take the export every time, then commit it. A
`UserPromptSubmit` hook normally has the taking done before the turn —
it resolves the prompt's target to a PR through `gh` and re-exports
whatever is already there — and reports what arrived as a `git diff`
against the export the previous turn committed. An empty diff is the
answer to "has anything changed?", not the absence of one.

Committing every export is a record for the person reviewing the branch
before it is anything for the agent: consecutive exports differ by the
comments and thread resolutions each turn was answering, which the
turn's own commits do not say. `/finalize` sweeps the tree either way,
so the adds and that delete cancel out in the squash.

A bare `/handle` now targets the branch the session is on, that being
what a session types once it is already attached; on the trunk it still
stops and asks, there being no work to read off it. And `/from-branch`
exempts an untracked `docs/pr/<n>/` from its work-to-lose check, a hook
writing one before the turn on whatever branch HEAD was on.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

### Review by @vzakharov (human) — COMMENTED

_2026-09-16T21:31:05Z_

пока мы этим занимаемся -- давай ride along следующее: пиар всё-таки выгружать одним файлом (благо дифф теперь можно посмотреть вне зависимости от размера этого самого файла), иначе получается вот такое: https://github.com/vzakharov/vovazakharov.com/commit/970c6f8c93b4d4d00614e0336e2194641ea93e20 -- десять изменённых файлов, отображающих ничего больше, как комменты по пиару, которые ревьюющему в следующем раунде, конечно, и так известны (замусоривают вид changes).

если это сложно, сделай сначала /plan (на этой же ветке)

- **T01** `docs/remove-before-merging/squash-message.md`:15 — unresolved — last: @vzakharov (human) 2026-09-16T21:28:24Z — "меня конфузит этот первый абзац. Изначально запрос был про т…" → [↓](#t01)
- **T02** `.claude/skills/handle/SKILL.md`:37 — unresolved — last: @vzakharov (human) 2026-09-16T21:29:07Z — "> and a second `/handle` on the same branch that reads the f…" → [↓](#t02)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:15 — unresolved

```diff
@@ -15,20 +15,24 @@ holds for an issue thread, which is a snapshot taken once and read
 forever. A PR moves while the branch works.
```

**@vzakharov (human)** — 2026-09-16T21:28:24Z

меня конфузит этот первый абзац. Изначально запрос был про то, чтобы при каждом /handle выгружался экспорт, чтобы агент не тратил на это сознательный раундтрип. А теперь тут непонятно откуда вылезли: "час назад", "finalize" (при чём тут вообще он -- handle посылается задолго до финализации"

---

<a id="t02"></a>

### `.claude/skills/handle/SKILL.md`:37 — unresolved

```diff
@@ -34,7 +34,15 @@ Two lanes, and which runs is read off the branch:
… 1 line elided …
   The realistic case is both at once — a fresh review _plus_ operator follow-ups on older threads — and the lane's input is their union. `python3 scripts/export-github-item.py <n>` writes the PR to `…
 
-  **Run the export every time, and never read an export you did not just take.** A PR moves while the session works, so `docs/pr/<n>/pr.md` existing says only that someone took a snapshot once — it i…
+  **Run the export every time, and never read an export you did not just take.** A PR moves while the session works, so `docs/pr/<n>/pr.md` existing says only that someone took a snapshot once — it is not evidence of anything about the PR now, and a second `/handle` on the same branch that reads the first one's export answers "has anything arrived?" with an hour-old fact. `.claude/hooks/prompt-handle-pr-export.sh` normally has this done before the turn; run the command yourself where it reported a failure, or where a tree adopted `/handle` without the hook.
```

**@vzakharov (human)** — 2026-09-16T21:29:07Z

> and a second `/handle` on the same branch that reads the first one's export answers "has anything arrived?" with an hour-old fact

не понимаю о чём это

---

## Timeline (status, references, and other events)

- **2026-09-16T18:06:12Z** @vzakharov renamed from «feat: re-export a /handle branch's PR ahead of every turn» to «feat: re-export and commit a /handle branch's PR every turn».
- **2026-09-16T21:31:05Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/83#pullrequestreview-5228547955.
