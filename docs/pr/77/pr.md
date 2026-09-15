# PR #77: feat: split long PR exports into an index plus per-file threads

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/77
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/pr-export-split-2oszov
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-14T23:44:00Z
- **Updated:** 2026-09-15T10:29:35Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- **The quoted diff is now the reviewer's own selection.** GitHub's `diff_hunk` runs from the start of the enclosing hunk to the commented line, so a rewritten Markdown file arrives as `@@ -1,99 +1,158 @@` — 230 lines quoted to point at three. `trim_hunk` keeps the `@@` header, a marker for what was dropped, three lines of run-up and `start_line`..`line` **byte for byte**; only the run-up is ever shortened. Across the example PR's 182 comments the hunks carried 11,955 lines against 390 selected.
- **`pr.md` opens its review section with an index** — one row per thread carrying the path, the resolved state, the tail author's `(agent)`/`(human)` label, its timestamp and a preview. That is exactly what `/handle`'s tail test reads, so the lane stops loading bodies to find the few threads it acts on.
- **Past 400 rendered lines the bodies hoist out in stages**: threads into `docs/pr/<n>/threads/<NN>-<path-slug>.md` grouped by the file each hangs off, then — only if that was not enough — conversation comments into `docs/pr/<n>/comments.md`. Header, PR body and timeline never move. Under the budget nothing moves and the export is one file, so the consumer's instruction is one sentence either way: read the index, follow the link.
- **Measured on the export the operator pointed at** (`vovazakharov.com` PR #43): 6,219 lines and 600 KB become a 330-line, 56 KB `pr.md` indexing all 69 threads, plus 13 thread files. This repo's own PR #77 re-exports as a single 98-line file, unchanged in shape.
- **Wider than the plan on one point, on purpose:** issue exports get the comment index too, and hoist past the same budget. The plan had said `issue.md` keeps its current shape; holding it there would have meant a second rendering path for comments to suppress an index that is useful wherever a thread is long. `/issue` now names the extra file.
- **The loop's own self-tests now sit behind one vet line**, on review. `scripts/vet.sh` had grown a line per test file, and each one reached an adopting repo as a separate accept-or-reject alongside that repo's real checks. `scripts/check-muthur.sh` runs `check-repo-identity.sh` and every `scripts/test_*.py`, so a new test joins by matching the pattern rather than by editing `vet.sh`. Membership is "would the adopting repo run this?", not "is it a test": `check-skill-catalog.sh` and `check-squash-message.sh` stay outside it, measuring as they do that repo's own skills and its own branches.
- Time-gap chunking — the opening idea — is measured and rejected in the plan: that PR ran inside 15 hours, so a gap threshold yields 2–4 files all still 100–200 KB. The bulk sits inside threads, not across time.

## QA Checklist

- [ ] `long-pr` — re-export a long PR (`python3 scripts/export-github-item.py 43 --repo vzakharov/vovazakharov.com`); `pr.md` is under 400 lines, `threads/` holds one file per commented path, and every thread appears exactly once in the index
- [ ] `selection-intact` — for three threads, compare the rendered diff against `gh api repos/<owner>/<repo>/pulls/comments/<id> --jq '.start_line, .line'`; the quoted lines match that range exactly and are not truncated
- [ ] `index-tail` — from the index alone, answer `/handle`'s tail test for each thread: state, tail author's `(agent)`/`(human)` label, tail timestamp, and enough preview to decide whether to open it
- [ ] `no-path` — a PR-level conversation comment and a review body both stay in `pr.md`, and a file-level (`subject_type: "file"`) review comment indexes under its path with no `:<line>`
- [ ] `short-pr` — re-export a short PR (`python3 scripts/export-github-item.py 77`); output is a single `pr.md` with no `threads/` directory, and the index links resolve inside the file
- [ ] `re-export` — re-export a long PR into a directory that already holds a bigger one's `threads/`; no file from the previous run survives unlinked
- [ ] `issue-export` — export an issue; `issue.md` gains a comment index and nothing else, and a long one's `comments.md` is reachable from it
- [ ] `vet-bundle` — `./scripts/vet.sh` is green and names the repo-identity check plus both test files in its output; rename a test file out of `scripts/test_*.py` and `scripts/check-muthur.sh` fails rather than passing on an empty bucket
- [ ] `finalize-sweep` — run `/finalize`'s working-artifact sweep on a branch carrying a split export; the whole `docs/pr/<n>/` tree including `threads/` is gone from the last commit

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `long-pr` | unit | ✅ | `test_export_split.py` — grouping by path, `NN` ordering, per-group overflow into `-2.md` |
| `selection-intact` | unit | ✅ | `TrimHunk` — single-line, multi-line, outdated, file-level, short-hunk, overlong run-up; the range asserted byte for byte |
| `index-tail` | unit | ✅ | `ThreadIndex` — every field asserted, plus one row rendered end to end through `split_export` |
| `no-path` | unit | ✅ | `test_a_comment_attached_to_no_file_hoists_by_its_own_stage`, `test_a_file_level_comment_indexes_without_a_line` |
| `short-pr` | unit | ✅ | `test_under_the_budget_nothing_moves`; also confirmed against the live PR #77 export |
| `re-export` | integration | ❌ | `_clear_previous_hoists` runs only in `main()`, which the unit tests do not reach — would need a fixture export directory |
| `issue-export` | integration | ❌ | Same: the issue/PR fork lives in `main()` |
| `vet-bundle` | manual-only | — | Shell; no harness runs it. The empty-glob branch is the guard, and running the script is the check |
| `finalize-sweep` | manual-only | — | `/finalize` already sweeps `docs/pr/<m>/` whole; this confirms the subdirectory rides along |

https://claude.ai/code/session_01LvYEfcEwvrwBEmMZvBcx5t

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-14T23:44:18Z — "Proposed squash title/body: ``` feat: split long PR exports…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-14T23:44:18Z

[https://github.com/vzakharov/muthur/pull/77#issuecomment-5672423508](https://github.com/vzakharov/muthur/pull/77#issuecomment-5672423508)

Proposed squash title/body:

```
feat: split long PR exports into an index plus per-file threads (pr #77)
```

```
A PR export grew without bound: one docs/pr/<n>/pr.md holding every
review thread in full. On a long PR that is 600 KB nobody reads, and
the bulk is mechanical — diff hunks are 74% of the file, and their
overlapping context repeats the same prose about five times. The
sharper cost is that a consumer cannot select: a thread's resolved
state and whose post it ends on are buried in the bodies, so
/handle's review lane loads the whole document to reach the few
threads it acts on.

The quoted diff is now the reviewer's own selection: start_line
through line, byte for byte, preceded by the @@ header, a marker for
what was elided and three lines of run-up. What it replaces was
whatever GitHub padded around that selection — across the same PR's
182 comments the hunks ran to 11,955 lines against 390 selected.
pr.md opens its review section with an index — one line per thread
carrying the path, the state, the tail author's agent/human label, its
timestamp and a preview — which is exactly what the tail test reads.

Past 400 rendered lines the bodies hoist out in stages: threads to
docs/pr/<n>/threads/ grouped by the file each hangs off, then, if that
was not enough, conversation comments to comments.md. The header, PR
body and timeline never move, being what the file is opened for.
Under the budget nothing moves and the export stays one file, so the
consumer's instruction is the same sentence either way: read the
index, follow the link. Issues share the comment stage, so an issue
export gains the same index and the same budget.

Riding along: the vet run grew a line per test file, and each one
reached an adopting repo as its own accept-or-reject alongside that
repo's real checks. scripts/check-muthur.sh is now the single line for
everything that tests only this repo's machinery — the repo-identity
check and every scripts/test_*.py, which a new test joins by matching
rather than by editing vet.sh. The skill-catalog and squash-message
checks stay outside it, measuring as they do the adopting repo's own
skills and its own branches.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

- **T01** `scripts/test_export_split.py`:1 — unresolved — last: @vzakharov (agent) 2026-09-15T10:28:47Z — "Сделано в 9987e00 — `scripts/vet.sh` теперь зовёт одну строк…" → [↓](#t01)

<a id="t01"></a>

### `scripts/test_export_split.py`:1 — unresolved

**@vzakharov (human)** — 2026-09-15T10:21:14Z

мне не нравится, что мы раз за разом добавляем новые тесты, которые адоптеры должны принимать/отклонять поштучно наряду с их, "настоящими", чекерами. Давай ride along объединение всех muthur чеков в один. (Имеются в виду именно чеки, связанные с функционалом muthur -- то есть, например, проверить squash message сюда не выходит -- это тест и для принимающей репы.) Тогда их можно всех скопом "отклонить" (потому что принимающей репе они ни к чему", а не по одиночке.

**@vzakharov (agent)** — 2026-09-15T10:28:47Z

Сделано в 9987e00 — `scripts/vet.sh` теперь зовёт одну строку, `scripts/check-muthur.sh`, а она уже гоняет `check-repo-identity.sh` и все `scripts/test_*.py` по маске. То есть следующий тест приезжает к адоптеру внутри этой строки, а `vet.sh` не трогает вовсе — их собственный `vet.sh`, переписанный под их стек, теперь не конфликтует.

Границу провёл по твоему критерию — «нужно ли это принимающей репе», а не «тест ли это». Снаружи остались `check-skill-catalog.sh` и `check-squash-message.sh`: они меряют скиллы и ветки самой принимающей репы. Внутрь ушло то, что меряет вендоренный код, который адоптер не правит, — поэтому связка заодно ключуется на каталог и ниже по течению выходит с нулём.

Заодно: строка `scripts/vet.sh` в каталоге ссылалась на `scripts/check-operator-entries.sh` — скрипт, которого в дереве не было никогда.

---

## Timeline (status, references, and other events)

- **2026-09-15T10:21:19Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/77#pullrequestreview-5208613697.
