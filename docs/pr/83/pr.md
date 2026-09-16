# PR #83: feat: re-export and commit a /handle branch's PR every turn

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/83
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/handle-pr-export-ip1a9z
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-16T12:20:08Z
- **Updated:** 2026-09-16T21:46:33Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **`/handle` Step 2 takes the PR export every turn and commits it.** The export is a snapshot of something that moves: a `pr.md` in the tree says what the PR held when some turn took it, and the comment the session came to answer may have arrived since. The committed sequence is a record for the person reviewing the branch first: consecutive exports differ by the comments and thread resolutions each turn was answering, which the turn's own commits do not say.
- **A new `UserPromptSubmit` hook has the taking done before the turn.** It resolves the prompt's target (the last token if it names a real branch, otherwise the branch HEAD is on) to a PR through `gh`, re-exports it, and reports what arrived as a `git diff` against the export the previous turn committed. An empty diff is the answer to "has anything changed?", not the absence of one.
- **What was in the way was a rule, not an oversight.** `/finalize`'s sweep told a resumed agent — post-compaction handoff, parallel session — to read the committed export instead of re-exporting, and said it of `docs/issue/` and `docs/pr/` in one breath. True for an issue thread, which is a snapshot; wrong for a PR. That sentence now covers issues only, and names what separates the two: an issue is committed once, a PR every time it is re-taken.
- **A bare `/handle` now targets the branch the session is on** rather than stopping to ask — that being what a session types once it is already attached, which is the same post-compaction moment. The trunk keeps the old behaviour, having no work to read off it.
- **An export is one file however long the PR.** Bodies no longer hoist into `docs/pr/<n>/threads/` and `comments.md` past 400 lines: committed on every re-take, that layout turned a single arriving comment into a ten-file commit of thread bodies the reviewer already knows. The index survives — it is how a reader picks threads to open — and a re-export clears what an earlier layout left beside it.
- **`/pr` Step 5 records the `gh pr edit` failure that leaves the PR unchanged** — it asks for project cards on every edit, so `repository.pullRequest.projectCards` comes back as a GraphQL error while the title and body stay as they were. The verification and the REST route around it (`scripts/pr-body.py`) live there; `/qa-checklist` points at it rather than restating it.
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
- [ ] `one-file` — export a PR with enough threads to pass 400 lines (#78 is one). It lands as a single `pr.md`, every index row's anchor resolving inside it.
- [ ] `stale-siblings` — put a `threads/` directory and a `comments.md` beside an export, re-export, and watch both go.
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
| `one-file` | integration | ❌ | A fixture PR past the old 400-line budget renders one file |
| `stale-siblings` | integration | ❌ | Both paths are gone after a re-export |
| `sweep` | integration | ❌ | Tracked and untracked `docs/pr/<n>/` both gone after the sweep step |

The repo has no harness for bash hooks today — `scripts/test_*.py` cover the exporter's Python internals only — so every automatable row is uncovered for the same reason. Each was exercised by hand against synthetic payloads and a real PR while building.

https://claude.ai/code/session_01LoQarnxZ16ZUg8UUZ9nwni

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-16T12:20:40Z — "Proposed squash title/body: ``` feat: re-export and commit a…" → [↓](#c01)
- **C02** @vzakharov (agent) — 2026-09-16T21:41:19Z — "Ride along сделан — оказалось не сложно, так что без `/plan`…" → [↓](#c02)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-16T12:20:40Z

[https://github.com/vzakharov/muthur/pull/83#issuecomment-5697320253](https://github.com/vzakharov/muthur/pull/83#issuecomment-5697320253)

Proposed squash title/body:

```
feat: re-export and commit a /handle branch's PR every turn (pr #83)
```

```
`/handle` spent a round-trip of its own on the PR export before it could
say whether anything had arrived, and a session that skipped that step
answered off whatever export an earlier turn had left in the tree. A
`UserPromptSubmit` hook now takes the export before the turn starts: it
resolves the prompt's target — the last token when it names a real
branch, otherwise the branch HEAD is on — to a PR through `gh`, and
re-exports it.

The turn then commits what it read, so the next export arrives as a
`git diff` against it. An empty diff is the answer to "has anything
changed?", not the absence of one. Committing is first of all a record
for the person reviewing the branch: consecutive exports differ by the
comments and thread resolutions each turn was answering, which the
turn's own commits do not say. `/finalize` sweeps the tree before the
PR goes ready, so the adds and that delete cancel out in the squash —
and its sweep stops telling a resumed session to read the committed
export rather than re-take it, that being true of an issue thread,
which is a snapshot, and not of a PR.

An export is one file however long the PR: bodies no longer hoist into
`threads/` and `comments.md` past 400 lines. The index survives, being
how a reader picks threads to open, but the hoist turned a single
arriving comment into a ten-file commit — and the diff is what the
next turn reads anyway.

Three smaller things. A bare `/handle` targets the branch the session
is on, that being what a session types once it is already attached; on
the trunk it still stops and asks. `/from-branch` exempts an untracked
`docs/pr/<n>/` from its work-to-lose check, a hook writing one before
the turn on whatever branch HEAD was on. And `/pr` records the
`Projects (classic)` GraphQL failure that leaves `gh pr edit` printing
an error while the PR keeps its old title and body, with the REST route
around it.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

<a id="c02"></a>

### Comment by @vzakharov (agent) on 2026-09-16T21:41:19Z

[https://github.com/vzakharov/muthur/pull/83#issuecomment-5704975252](https://github.com/vzakharov/muthur/pull/83#issuecomment-5704975252)

Ride along сделан — оказалось не сложно, так что без `/plan` (597c509).

Выгрузка теперь всегда один файл. Хойстинг за 400 строк (треды в `docs/pr/<n>/threads/`, сгруппированные по файлу, комменты в `comments.md`) убран целиком; `gh_export/split.py` стал `gh_export/index.py` — элемент, его якорь и одна функция, которая рендерит «строки индекса, потом тела». Индекс остался: он и есть то, по чему выбираются треды, которые стоит открыть, а с коммитом выгрузки каждый ход диффа хватает, чтобы понять, что приехало — ради чего хойстинг когда-то и заводился.

Проверил на настоящем длинном пиаре: #78 (10 тредов, 407 строк) выгружается одним `pr.md`, все якоря резолвятся внутри него. Повторная выгрузка вдобавок подчищает `threads/` и `comments.md`, если их оставила прошлая раскладка — иначе на ветках с уже закоммиченными хойстами остались бы висеть протухшие файлы, на которые ничто не ссылается.

Заодно записал известный обход (1cab778): `gh pr edit` спрашивает project cards на каждом редактировании, поэтому репозиторий, не имеющий к Projects (classic) никакого отношения, всё равно получает `repository.pullRequest.projectCards` — с ошибкой в stderr и нетронутыми title и body. Живёт в `/pr` Step 5 (там, где цикл это и ловит), вместе с проверкой «долетело ли» и маршрутом через REST; в `/qa-checklist` осталась ссылка вместо второго изложения.

---

## Review threads

### Review by @vzakharov (human) — COMMENTED

_2026-09-16T21:31:05Z_

пока мы этим занимаемся -- давай ride along следующее: пиар всё-таки выгружать одним файлом (благо дифф теперь можно посмотреть вне зависимости от размера этого самого файла), иначе получается вот такое: https://github.com/vzakharov/vovazakharov.com/commit/970c6f8c93b4d4d00614e0336e2194641ea93e20 -- десять изменённых файлов, отображающих ничего больше, как комменты по пиару, которые ревьюющему в следующем раунде, конечно, и так известны (замусоривают вид changes).

если это сложно, сделай сначала /plan (на этой же ветке)

- **T01** `docs/remove-before-merging/squash-message.md`:15 — resolved — last: @vzakharov (agent) 2026-09-16T21:41:02Z — "Согласен — первый абзац рассказывал не про то. Он вёл с `/fi…" → [↓](#t01)
- **T02** `.claude/skills/handle/SKILL.md`:37 — resolved — last: @vzakharov (agent) 2026-09-16T21:41:03Z — "Та же болезнь: фраза описывала сценарий («второй `/handle`,…" → [↓](#t02)
- **T03** `.claude/skills/pr/SKILL.md`:115 — unresolved — last: @vzakharov (human) 2026-09-16T21:44:47Z — "кажется, слишком затратно верифицировать каждый эдит" → [↓](#t03)
- **T04** `.claude/skills/take-issue/SKILL.md`:37 — unresolved — last: @vzakharov (human) 2026-09-16T21:45:20Z — "не уверен, но не медведь ли?" → [↓](#t04)
- **T05** `.claude/skills/update-muthur/catalog.md`:177 — unresolved — last: @vzakharov (human) 2026-09-16T21:45:37Z — "а это точно медведь" → [↓](#t05)
- **T06** `scripts/export-github-item.py`:16 — unresolved — last: @vzakharov (human) 2026-09-16T21:46:20Z — "и опять" → [↓](#t06)

<a id="t01"></a>

### `docs/remove-before-merging/squash-message.md`:15 — resolved

```diff
@@ -15,20 +15,24 @@ holds for an issue thread, which is a snapshot taken once and read
 forever. A PR moves while the branch works.
```

**@vzakharov (human)** — 2026-09-16T21:28:24Z

меня конфузит этот первый абзац. Изначально запрос был про то, чтобы при каждом /handle выгружался экспорт, чтобы агент не тратил на это сознательный раундтрип. А теперь тут непонятно откуда вылезли: "час назад", "finalize" (при чём тут вообще он -- handle посылается задолго до финализации"

**@vzakharov (agent)** — 2026-09-16T21:41:02Z

Согласен — первый абзац рассказывал не про то. Он вёл с `/finalize` и «часа назад», то есть с правила, которое мешало, а не с того, что изменение делает.

Переписал (0959971): теперь открывается с того, с чего запрос и начался — `/handle` тратил собственный раунд-трип на выгрузку, прежде чем мог сказать, приехало ли что-нибудь, а сессия, пропустившая этот шаг, отвечала по той выгрузке, которую оставил какой-то более ранний ход. `/finalize` остался одной клаузой в середине второго абзаца: его подметание раньше велело возобновлённой сессии читать закоммиченную выгрузку вместо новой, и эту фразу пришлось сузить до issue. Это следствие, а не завязка, и теперь стоит там, где следствию место.

---

<a id="t02"></a>

### `.claude/skills/handle/SKILL.md`:37 — resolved

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

**@vzakharov (agent)** — 2026-09-16T21:41:03Z

Та же болезнь: фраза описывала сценарий («второй `/handle`, отвечающий фактом часовой давности») вместо причины, да ещё и с выдуманным часом.

Причина простая, и теперь так и написано (171b027): выгрузка — снимок того, что движется. Лежащий в дереве `pr.md` говорит, что было в пиаре, когда какой-то ход его снял, и ничего о том, что там сейчас; комментарий, ради которого сессия и пришла, мог приехать после.

---

<a id="t03"></a>

### `.claude/skills/pr/SKILL.md`:115 — unresolved

```diff
@@ -112,6 +112,16 @@ If `gh` fails with "none of the git remotes … point to a known GitHub host" (t
 
 **In refresh mode**, swap the `create` for `gh pr edit <PR> --title … --body …`. Pass no `--base` — re-asserting it would silently undo a retarget someone made on purpose.
 
+**`gh pr edit` can fail on a repo it has nothing to do with**, reporting `GraphQL: Projects (classic) is being deprecated … (repository.pullRequest.projectCards)` — it asks for project cards on every edit, and the PR is left exactly as it was. The failure is loud but easy to read past, so **verify the edit landed** (`gh pr view <PR> --json title,body`) rather than trusting the exit. The route around it is REST, which `scripts/pr-body.py` already speaks:
```

**@vzakharov (human)** — 2026-09-16T21:44:47Z

кажется, слишком затратно верифицировать каждый эдит

---

<a id="t04"></a>

### `.claude/skills/take-issue/SKILL.md`:37 — unresolved

```diff
@@ -34,7 +34,7 @@ The script writes `docs/issue/<n>/issue.md` (body + comments + timeline) and dow
… 1 line elided …
 Consult the issue only through the export — never `gh issue view`, the GitHub MCP tools, or `WebFetch` in its place. `gh issue view` alone does **not** fetch attachments: GitHub's `private-user-image…
 
-**Then read** `docs/issue/<n>/issue.md` end to end, and **open the files under** `docs/issue/<n>/attachments/` when you need pixels (screenshots, mockups, design references). A long thread indexes it…
+**Then read** `docs/issue/<n>/issue.md` end to end, and **open the files under** `docs/issue/<n>/attachments/` when you need pixels (screenshots, mockups, design references). A long thread indexes its comments above their bodies, but the index is a way around the file, not a substitute for it — an issue is read whole rather than selectively.
```

**@vzakharov (human)** — 2026-09-16T21:45:20Z

не уверен, но не медведь ли?

---

<a id="t05"></a>

### `.claude/skills/update-muthur/catalog.md`:177 — unresolved

```diff
@@ -174,8 +174,8 @@ the project's first issue on the way through.
… 2 lines elided …
 | `/audit-github-backlog` | Sweep every open issue and PR against today's code and leave a reviewable close/refile/keep plan, prioritising `P0`–`P3` everything it keeps. Mutates nothing on GitHub. | …
-| `scripts/export-github-item.py` | Download an issue — body, comments, timeline, attachments — into `docs/issue/<n>/`, or a PR (plus review threads, each one's resolved/unresolved state, and the lin…
-| `scripts/gh_export/` | The exporter's pieces, one module per concern: argument parsing, the REST/GraphQL client, attachment download, the index-and-hoist layout, and a renderer each for the header …
+| `scripts/export-github-item.py` | Download an issue — body, comments, timeline, attachments — into `docs/issue/<n>/`, or a PR (plus review threads, each one's resolved/unresolved state, and the lines its comment hangs off) into `docs/pr/<n>/`. Threads and comments are always indexed above their bodies, in one file however long the thread. Stdlib-only. | `python3` ≥3.9, `$GH_TOKEN` or `gh auth token`, `scripts/lib/github.py` (G2), `scripts/gh_export/` | — | adopt |
```

**@vzakharov (human)** — 2026-09-16T21:45:37Z

а это точно медведь

---

<a id="t06"></a>

### `scripts/export-github-item.py`:16 — unresolved

```diff
@@ -12,11 +12,10 @@
… 6 lines elided …
-comments into docs/pr/<n>/comments.md. The header, body and timeline never move,
-being what the file is opened for.
+reads the index and follows a link to the body rather than the whole document.
+The export is one file however long the thread: it is committed on each re-take
```

**@vzakharov (human)** — 2026-09-16T21:46:20Z

и опять

---

## Timeline (status, references, and other events)

- **2026-09-16T18:06:12Z** @vzakharov renamed from «feat: re-export a /handle branch's PR ahead of every turn» to «feat: re-export and commit a /handle branch's PR every turn».
- **2026-09-16T21:31:05Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/83#pullrequestreview-5228547955.
- **2026-09-16T21:46:33Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/83#pullrequestreview-5228671620.
