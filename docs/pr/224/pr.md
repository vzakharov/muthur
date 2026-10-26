# PR #224: feat: [attn adopters] a private muthur hub of the operator's matters

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/224
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/muthur-hub-discussion-u6b63n
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-10-25T19:15:44Z
- **Updated:** 2026-10-26T02:09:08Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Awaiting an answer: 5

_Unresolved threads whose newest post is a human's, and human reviews and comments that are new since the last export or that no agent post has followed (no export committed on the branch yet). Resolved threads never count; an `(agent)` tail is a reply already given._

- **T01** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:120 — unresolved — last: @vzakharov (human) 2026-10-26T01:57:50Z — "для одного аккаунта (дефолтного) label может быть пустой" → [↓](#t01)
- **T02** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:29 — unresolved — last: @vzakharov (human) 2026-10-26T02:05:17Z — "тут подумал, что всё-таки нужен какой-то скилл, именно в соз…" → [↓](#t02)
- **T03** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:37 — unresolved — last: @vzakharov (human) 2026-10-26T02:05:47Z — "подумать не перенести ли сюда и operator voice как-то" → [↓](#t03)
- **T04** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:78 — unresolved — last: @vzakharov (human) 2026-10-26T02:06:49Z — "если только на этот момент уже не создана приватная репо" → [↓](#t04)
- **T05** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:110 — unresolved — last: @vzakharov (human) 2026-10-26T02:09:06Z — ""says" здесь относится к кому? кто говорит?" → [↓](#t05)

---

## Body

## Summary

- An operator who opts in gets a private `<handle>/muthur-hub` whose **issues are their matters** — one per piece of live work, discussion or task, across every muthur adopter — so the dozens of claude.ai pins give way to a list GitHub already knows how to filter, label and close.
- A `Stop`-hook sync keeps each matter current with the operator's own `gh` token: sessions on the branch, the PR, and a `status:*` label derived from the plan file and PR state. A matter is keyed by repository and branch, so relays and `/from-branch` land in the same one; a merged PR closes it; a closed one is never reopened.
- Every per-operator flag (`hub`, and `manualRelay`, which moves out of `.claude/context-budget/manual-relay/<handle>`) lives in one settings object — a secret gist by default, so one answer covers every adopter, and a repo file when the operator refuses the gist, at the price of being asked again per adopter.
- `hub` unset → asked once; yes runs an allowlisted `create.sh`, then `/hub` gives the tour and offers seeding from `list_sessions` (grouped by repo and branch, merged ones dropped).

Plan: `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`. The GitHub Project board over the issues is #225.

## QA Checklist

- [ ] `ask-once` — in a session with `hub` unset, the first reply asks about the hub; after "no", a new session asks nothing
- [ ] `gist-consent` — the first settings write explains the secret gist (unlisted, not private) before creating it; refusing writes `.claude/operator-settings/<handle>.json` instead
- [ ] `create` — "yes" creates a private `<handle>/muthur-hub` with its README and `status:*` labels, with no permission prompt for the script
- [ ] `matter-created` — after one turn on a feature branch, the hub has an issue carrying the branch's marker, `repo:` and `status:discussion` labels, and the session link
- [ ] `status-follows` — writing a draft plan, flipping it to in-progress, and marking the PR ready move the label to planning / in-progress / review
- [ ] `relay-same-matter` — a `/relay take` successor's link is added to the same issue, no new issue appears
- [ ] `merged-closes` — merging the PR closes the issue with a comment
- [ ] `closed-stays` — closing a matter by hand and taking another turn on the branch leaves it closed and says so once
- [ ] `two-accounts` — a turn on the same branch from a second claude.ai account (same GitHub account) adds its session to the same issue, labelled with that account
- [ ] `rename` — `/branch-rename` after the first turn moves the marker rather than leaving a duplicate
- [ ] `manual-relay` — `manualRelay: true` in the store makes the context-budget pause offer the relay instead of running it
- [ ] `seed` — `/hub seed` proposes the last two weeks' unmerged branches, one entry per branch, and creates only what the operator keeps
- [ ] `write-fails` — with the hub unreachable, the turn's stop is blocked once with `gh`'s message

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `ask-once` | unit | — | Settings hook output with the key unset / set, stub `gh` |
| `gist-consent` | manual-only | — | The wording put to the operator is the agent's |
| `create` | integration | — | `create.sh` against a stub `gh`: repo flags, labels |
| `matter-created` | integration | — | `hub.py sync` with a stub `gh`, assert the issue payload |
| `status-follows` | unit | — | Status derivation per plan suffix and PR state |
| `relay-same-matter` | integration | — | Two syncs, two session ids, one branch → one issue |
| `merged-closes` | integration | — | Stub PR state `MERGED` → close call |
| `closed-stays` | integration | — | Closed issue in the listing → no reopen, one notice |
| `two-accounts` | integration | — | Two transcripts with different `userEmail`, one branch → one issue, two labelled lines |
| `rename` | integration | — | `hub.py rename` rewrites the marker |
| `manual-relay` | unit | — | Context-budget hook reading the cached settings |
| `seed` | manual-only | — | Needs `list_sessions`, an MCP tool |
| `write-fails` | integration | — | Stub `gh` exit 1 → hook exit 2 once, bail on `stop_hook_active` |

https://claude.ai/code/session_01EURbXzdjguX7AxfYRDF6mu

---

## Comments

- **C01** @vzakharov (agent) — 2026-10-25T19:15:59Z — "Proposed squash body: ``` An operator working across many mu…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-10-25T19:15:59Z

[https://github.com/vzakharov/muthur/pull/224#issuecomment-6402000887](https://github.com/vzakharov/muthur/pull/224#issuecomment-6402000887)

Proposed squash body:

```
An operator working across many muthur adopters tracked their live work
as claude.ai pins, which say nothing about repository, purpose or stage
and had grown to dozens. An operator who opts in now gets a private
<handle>/muthur-hub whose issues are their matters: one per piece of
live work, a discussion or a task, keyed by repository and branch, so a
relay or /from-branch lands in the same matter and new work gets its
own.

A Stop hook keeps each matter current with the operator's own gh token:
the branch's sessions, its PR, and a status:* label derived from the
plan file and PR state. A merged PR closes the matter; one the operator
closed stays closed. Labels other than repo:* and status:* are the
operator's. /hub gives the tour and seeds the hub once from the last two
weeks' unmerged sessions.

Every per-operator flag now lives in one settings object, read by
.claude/operator-settings/: a secret gist by default, so one answer
holds in every adopter, or a file in the repository when the operator
refuses the gist and accepts being asked again per adopter. The hub
opt-in is asked once while unset; manualRelay moves into the same
object.

Adopters: an operator's .claude/context-budget/manual-relay/<handle>
file moves into their settings store as manualRelay; write it there
with their consent to the store, then delete the file.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:120 — unresolved — last: @vzakharov (human) 2026-10-26T01:57:50Z — "для одного аккаунта (дефолтного) label может быть пустой" → [↓](#t01)
- **T02** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:29 — unresolved — last: @vzakharov (human) 2026-10-26T02:05:17Z — "тут подумал, что всё-таки нужен какой-то скилл, именно в соз…" → [↓](#t02)
- **T03** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:37 — unresolved — last: @vzakharov (human) 2026-10-26T02:05:47Z — "подумать не перенести ли сюда и operator voice как-то" → [↓](#t03)
- **T04** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:78 — unresolved — last: @vzakharov (human) 2026-10-26T02:06:49Z — "если только на этот момент уже не создана приватная репо" → [↓](#t04)
- **T05** `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:110 — unresolved — last: @vzakharov (human) 2026-10-26T02:09:06Z — ""says" здесь относится к кому? кто говорит?" → [↓](#t05)

<a id="t01"></a>

### `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:120 — unresolved

```diff
@@ -109,6 +109,15 @@ hook, tests. `settings.py` goes into `.claude/settings.json`
 - **A closed matter stays closed.** The sync never reopens one — closing is the
   operator's "no longer live" — and says once, in the next turn's context, that
   this branch's matter is closed in the hub.
+- **One GitHub account, several claude.ai accounts, one hub.** The hub follows
+  the `gh` token, so an operator working one repository from a personal and a
+  corporate claude.ai account has one hub, and both accounts' sessions on a
+  branch share its matter. A session link opens only in the account that owns
+  it, so each session line names the account: its label from the `accounts`
+  setting (`{"<email>": "<label>"}`), else the email's domain. The email is the
+  `userEmail` of the transcript's `session_context` record, read beside
+  `.claude/costs/lib/identity.py`'s other readers. Several GitHub accounts are
+  out of scope.
```

**@vzakharov (human)** — 2026-10-26T01:57:50Z

для одного аккаунта (дефолтного) label может быть пустой

---

<a id="t02"></a>

### `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:29 — unresolved

```diff
@@ -0,0 +1,195 @@
… 23 lines elided …
+  attached scope (checked: `ADMIN` on `vzakharov/life` from a session attached
+  to `vzakharov/muthur`). No GitHub Action: a private repo's minutes are not
+  free.
+- **Storage is issues**, so two sessions never race on one file, and labels give
+  priority and the rest room to grow. A GitHub Project board over them is the
+  follow-up issue filed with this plan, not this PR.
```

**@vzakharov (human)** — 2026-10-26T02:05:17Z

тут подумал, что всё-таки нужен какой-то скилл, именно в создаваемой приватной репе, который мониторит любые matter-ов и ведёт один файл (избегая таким образом race-ов). Типа, вместо кучи пинов у тебя будет ровно один пин, где ты (например с утра) запускаешь этот скилл, и она мониторит изменения issues и при любых изменениях перегенерирует единый файл с разбивкой по репам, приоритетам и т.п. При этом нужно подумать должен ли вообще это делать агент, или это всё можно будет сделать программно на хуках. Если агент -- позаботиться, чтобы все обновления делали подагенты, чтобы контекста родительского агента хватало на как можно дольше. А когда не хватает (помним, что в автосоздаваемой репе нет всех muthur-овских приблуд, то есть агент запущенный оттуда не будет знать что такое "релей"), порождает новую сессию около 200-300к.

---

<a id="t03"></a>

### `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:37 — unresolved

```diff
@@ -0,0 +1,195 @@
… 29 lines elided …
+- **The code name is `matter`**; people see an issue.
+- **A cross-repo matter** is not modelled — later.
+
+## Operator settings
+
+One JSON object per operator holds every per-operator muthur flag — `hub` and
+`manualRelay` now — read by one helper, so a new flag is a key, not a new file
+layout.
```

**@vzakharov (human)** — 2026-10-26T02:05:47Z

подумать не перенести ли сюда и operator voice как-то

---

<a id="t04"></a>

### `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:78 — unresolved

```diff
@@ -0,0 +1,195 @@
… 74 lines elided …
+  plainly, what the hub is and that it creates a private repo. An existing
+  `<handle>/muthur-hub` with `hub` unset is a yes already: the hook sets `true`
+  and asks nothing.
+- **`/update-muthur` asks too** when it ports the hub group, since the session
```

**@vzakharov (human)** — 2026-10-26T02:06:49Z

если только на этот момент уже не создана приватная репо

---

<a id="t05"></a>

### `docs/plans/muthur-hub-discussion.draft.do-not-implement.md`:110 — unresolved

```diff
@@ -0,0 +1,195 @@
… 106 lines elided …
+  PR closes the issue with a comment; a closed-unmerged one leaves it to the
+  operator.
+- **A closed matter stays closed.** The sync never reopens one — closing is the
+  operator's "no longer live" — and says once, in the next turn's context, that
```

**@vzakharov (human)** — 2026-10-26T02:09:06Z

"says" здесь относится к кому? кто говорит?

---

## Timeline (status, references, and other events)

- **2026-10-25T19:16:22Z** @vzakharov cross-referenced this pull request from [#225 Add a GitHub Project board over the muthur hub's matters](https://github.com/vzakharov/muthur/issues/225).
- **2026-10-26T02:09:08Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/224#pullrequestreview-5646604827.
