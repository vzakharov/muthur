> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source while this file is named `*.draft.do-not-implement.md` — prep and spikes go in `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md` and delete this banner (quoting the go-ahead in the commit) *before* touching code.

# Make a long PR export readable without reading all of it

`scripts/export-github-item.py` writes one `docs/pr/<n>/pr.md` whatever the PR's size. On a long PR that file is unreadable and, worse, unskippable: the two things a consumer actually selects on — which threads are unresolved, and whose post each thread ends on — are buried inside the bodies, so `/handle`'s review lane has to load the whole document to find the handful of threads it will act on.

## What the size actually is

Measured on the export the operator pointed at (`vovazakharov.com` PR #43, 6,219 lines, 600 KB on disk / 381 K characters):

| slice | share of the export |
|---|---|
| `## Review threads` (69 threads) | **93.7 %** |
| — of which, diff hunks | 79 % of the section, **74 % of the whole file** |
| — of which, threads already **resolved** | 85 % of the section |
| `## Body` | 3.0 % |
| `## Comments` (3 of them) | 2.1 % |
| `## Timeline` | 0.3 % |

Two further findings decide the design:

- **The hunks repeat themselves.** 4,528 hunk lines across the export, only **892 distinct** — consecutive comments on the same prose file carry overlapping context, so the same paragraphs are emitted about five times. Distinct hunk text is 65 KB of the 280 KB.
- **Time is the wrong axis.** The whole PR happened inside 15 hours. Cutting a new file at every gap over 1 h yields 4 chunks; over 6 h, 2 chunks — each still 100–200 KB. A gap threshold splits this export into large files rather than into readable ones, because the bulk is not spread over time; it sits inside individual threads.

So the split is worth doing, but by itself it moves nothing here. The size is made of diff hunks, and the unreadability is made of a missing index.

## What changes

### 1. Trim the diff hunk to the lines the comment was attached to

**What the export renders today is not the reviewer's selection.** GitHub's `diff_hunk` is the whole enclosing hunk up to the commented line; the selection is `start_line`..`line`, and it is that hunk's tail. Across PR #43's 182 review comments the hunks carry **11,955 lines** between them, while the reviewer selected **390** — a factor of thirty, and the 11,565-line difference is what the reader currently pays for.

The worst case there is a comment on three selected lines whose hunk is `@@ -1,99 +1,158 @@` — a rewritten Markdown file arrives as one hunk, so the export quotes 230 lines / 14 KB to point at three. The three lines themselves cost 283 characters.

So the rule keeps the selection **whole and untruncated** — `start_line` / `original_start_line` through `line` / `original_line`, which is exactly what the reviewer highlighted — preceded by the `@@` header, an elision marker naming the dropped lines, and `HUNK_CONTEXT_LINES = 3` lines of run-up:

```diff
@@ -1,99 +1,158 @@
… 223 lines elided …
+  же тезис, применённый к себе: канал и есть образец того ограничения, о котором
+  речь. Если нужна концовка, она здесь, а не в «оставайтесь».
+- **Что резать в посте, но не в расшифровке.** Черногория и штрафы занимают
+  примерно треть записи — в посте это два предложения. «Настолько же им всё
+  равно» три раза подряд — риторика, в тексте на экране хватит двух.
```

Only the run-up lines are additionally capped, at `CONTEXT_LINE_CHARS = 200` with a trailing `…`. Nothing inside the selection is ever shortened. The full hunk stays one click away on GitHub, which is why no `--full-hunks` flag is worth carrying.

### 2. Give `pr.md` a thread index

A `## Review threads` section that opens with one line per thread, carrying exactly the fields a consumer selects on:

```
- **T07** `.claude/skills/dictation/SKILL.md`:168 — unresolved — last: @vzakharov (human) 2026-09-14T21:16Z — "why not just make the…" → [threads/03-claude-skills-dictation-skill-md.md](threads/03-claude-skills-dictation-skill-md.md#t07)
```

`/handle`'s tail test reads off that line: the state, the tail author's `(agent)` / `(human)` label, the tail timestamp against the head commit, and enough preview to judge whether the thread needs opening. 69 threads make a ~10 KB index — one read that replaces a 380 KB one.

Each rendered thread gets an explicit `<a id="t07"></a>` anchor so the index link resolves the same way whether the thread sits in `pr.md` or in a sibling file.

### 3. Hoist bodies out once `pr.md` passes 400 lines

`SPLIT_THRESHOLD_LINES = 400`, measured on the rendered `pr.md`. Over it, bodies are hoisted in stages, each stage re-measuring, stopping as soon as the document fits:

1. **Review threads** → `docs/pr/<n>/threads/<NN>-<path-slug>.md`, **grouped by the file the thread hangs off** — the unit the reader works in, and where the overlapping hunks live. `NN` is the order of the path's first thread, so the directory sorts chronologically. One path whose threads blow the budget alone splits further into `<NN>-<slug>-2.md`.
2. **Conversation comments** → `docs/pr/<n>/comments.md`, with index lines of the same shape left behind. This stage rarely fires, and exists because **a comment attached to no file is a first-class case**: PR-level conversation comments and review bodies belong to no path, so a layout keyed on paths has to say where they go rather than leave them to fall through.

Never hoisted: the header, the PR body and the timeline. They are what a reader opens `pr.md` **for**, and the index is useless away from them. The body in particular stays put also because `docs/pr/<n>/body.md` is already `scripts/pr-body.py`'s editable round-trip file — hoisting into that name would have two tools writing one path.

Below the threshold nothing moves: one `pr.md`, exactly as today. The index is emitted either way, so the consumer's instruction is one sentence in both shapes — *read the index, follow the link* — and only the link target differs.

The resulting layout:

```
docs/pr/<n>/
  pr.md                    header, body, review bodies, the indexes, timeline
                           (plus the comment and thread bodies, under 400 lines)
  threads/<NN>-<slug>.md   thread bodies, hoisted at stage 1
  comments.md              conversation comments, hoisted at stage 2
  attachments/             unchanged
```

Two path-shaped edge cases the grouping must not drop: a comment on an **outdated** line, where `line` is null and `original_line` carries it (already handled when reading, now also when grouping), and a **file-level** comment (`subject_type: "file"`), which has a path but no line and indexes as `<path>` with no `:<line>`.

`/finalize` already sweeps `docs/pr/<m>/` whole, so nothing about landing changes.

### Not changing: `issue.md`

Issues carry no review threads, and conversation comments were 2 % of the worst export on record. The splitter is keyed to the review section; issue exports keep their current single-file shape until something measures otherwise.

## Implementation

1. **`scripts/gh_export/reviews.py`** — add `trim_hunk(hunk, start_line, line)`; split the current `review_section` into `render_thread(chain, …) -> str` (one thread, anchored) and `thread_summary(chain, …)` returning the index fields (id, path, line, state, tail author + label, tail timestamp, preview). `review_section` becomes the composer over both.
2. **`scripts/gh_export/split.py`** (new) — takes the rendered sections as `(summary, body)` pairs plus a line budget, runs the two hoist stages until the document fits, and returns the index Markdown and the extra files to write, keyed by path relative to the export directory. Owns the path slugging, the `NN` numbering and the stage order; owns nothing about GitHub.
3. **`scripts/export-github-item.py`** — `main()` writes a list of `(path, text)` instead of one path, and reports the count. Its module docstring describes the new layout.
4. **`scripts/test_export_split.py`** (new) — stdlib `unittest`, run by path like `scripts/test_authorship.py`: hunk trimming (single-line, multi-line, outdated line, file-level comment, hunk shorter than the window, overlong run-up line), the 400-line boundary in both directions, both hoist stages firing in order, and one index row rendered end to end. The trimming tests assert the selected range survives **byte for byte** — that is the property the whole change turns on.
5. **`scripts/vet.sh`** — add the new test file to the four lines it already runs by path.
6. **Consumers** — `.claude/skills/handle/SKILL.md` (the review lane's "writes the whole thread to `docs/pr/<n>/pr.md`" sentence becomes the index-first instruction), `.claude/skills/from-branch/SKILL.md`, and the `scripts/export-github-item.py` row in `.claude/skills/update-muthur/catalog.md`.

## DRY notes

- **`trim_hunk` belongs in `reviews.py`, not its own module.** It is ~25 lines with exactly one caller, and it is about review comments specifically — the `start_line` semantics are the review API's. A `hunks.py` holding one function that nothing else can call is a file to open, not a seam.
- **`split.py` is a genuine seam.** File-layout-under-a-budget knows nothing about GitHub, and `reviews.py` should not learn about directories; `markdown.py` is documented as the sections *every* export carries, which these are not. It is also the piece a future issue-side split would reuse unchanged — the argument for keeping it free of review vocabulary.
- **The slug helper is new because there is none.** `scripts/lib/` carries `github.py` and `media.py`; neither slugs. It lives in `split.py` as a private function until a second caller exists.
- **The index and the thread bodies are rendered from one pass, not two.** `thread_summary` and `render_thread` both consume the already-grouped chain from `review_threads`, so the tail author/timestamp logic is computed once and the two renderings cannot disagree about what a thread's tail is.
- **Nothing is extracted for the below-threshold case.** It is the same renderer with one file in the output list, not a second code path.

## Verification

- `scripts/vet.sh` (the catalog check plus the new test file).
- Re-export a real long PR and a short one, and check the numbers: `python3 scripts/export-github-item.py 43 --repo vzakharov/vovazakharov.com` should land `pr.md` under 400 lines with all 69 threads in the index, and `python3 scripts/export-github-item.py 73` (short, this repo) should produce one unchanged-shape file.
- Spot-check three trimmed hunks against `gh api repos/<owner>/<repo>/pulls/comments/<id> --jq '.start_line, .line'`: the rendered selection must match that range exactly.
- Read the resulting index and confirm `/handle`'s tail test is answerable from it alone.

## Decisions taken

The operator settled all three forks: group by the file a thread hangs off, budget of 400 lines, and trimming that keeps the selection whole — the last one on the finding that today's export renders thirty times more diff than anyone selected.

Rejected, in one line each: **time-gap chunking** (the opening idea) — measured above, it splits this export into 2–4 files that are all still too big, because the bulk is inside threads rather than spread across time; **one file per thread** — 69 files where 8 match how the work is actually done; **dropping hunks entirely** — the selected lines are what the comment is about, and once trimmed they are nearly free.
