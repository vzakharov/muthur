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

### 1. Trim the diff hunk to the lines the comment is about

GitHub's `diff_hunk` ends at the commented line, so the informative part is its tail. Keep the `@@` header (it carries the line numbers), an elision marker naming how many lines were dropped, and the commented range plus `HUNK_CONTEXT_LINES = 3` lines before it. A multi-line comment's range starts at `start_line` / `original_start_line`, so the kept window starts there.

Context lines are additionally capped at `CONTEXT_LINE_CHARS = 200` with a trailing `…`; the commented line(s) are never truncated, being the subject of the comment. On PR #43 this takes ~280 KB of hunks down to roughly 25–30 KB, and the repetition goes with it.

The full hunk stays one click away on GitHub, which is why no `--full-hunks` flag is worth carrying.

### 2. Give `pr.md` a thread index

A `## Review threads` section that opens with one line per thread, carrying exactly the fields a consumer selects on:

```
- **T07** `.claude/skills/dictation/SKILL.md`:168 — unresolved — last: @vzakharov (human) 2026-09-14T21:16Z — "why not just make the…" → [threads/03-claude-skills-dictation-skill-md.md](threads/03-claude-skills-dictation-skill-md.md#t07)
```

`/handle`'s tail test reads off that line: the state, the tail author's `(agent)` / `(human)` label, the tail timestamp against the head commit, and enough preview to judge whether the thread needs opening. 69 threads make a ~10 KB index — one read that replaces a 380 KB one.

Each rendered thread gets an explicit `<a id="t07"></a>` anchor so the index link resolves the same way whether the thread sits in `pr.md` or in a sibling file.

### 3. Split thread bodies out above a size threshold

When the rendered document would exceed `SPLIT_THRESHOLD_CHARS = 50_000`, thread bodies move to `docs/pr/<n>/threads/<NN>-<path-slug>.md`, **grouped by the file the thread hangs off** — that is the unit the reader works in, and it is where the overlapping hunks live. `NN` is the order of the path's first thread, so the directory sorts chronologically. A single path whose threads blow the budget on their own splits further into `<NN>-<slug>-2.md`.

Below the threshold nothing moves: one `pr.md`, exactly as today. The index is emitted either way, so the consumer's instruction is one sentence in both shapes — *read the index, follow the link* — and only the link target differs.

Review **bodies** (`### Review by … — COMMENTED`) stay in `pr.md` regardless; they are small and they are the reviewer's framing of everything else.

The resulting layout:

```
docs/pr/<n>/
  pr.md                    header, body, conversation comments, review bodies,
                           the thread index, timeline
  threads/<NN>-<slug>.md   thread bodies, only above the threshold
  attachments/             unchanged
```

`/finalize` already sweeps `docs/pr/<m>/` whole, so nothing about landing changes.

### Not changing: `issue.md`

Issues carry no review threads, and conversation comments were 2 % of the worst export on record. The splitter is keyed to the review section; issue exports keep their current single-file shape until something measures otherwise.

## Implementation

1. **`scripts/gh_export/reviews.py`** — add `trim_hunk(hunk, start_line, line)`; split the current `review_section` into `render_thread(chain, …) -> str` (one thread, anchored) and `thread_summary(chain, …)` returning the index fields (id, path, line, state, tail author + label, tail timestamp, preview). `review_section` becomes the composer over both.
2. **`scripts/gh_export/split.py`** (new) — takes the rendered threads plus their summaries and a character budget, returns the index Markdown and the extra files to write, keyed by path relative to the export directory. Owns the path slugging and the `NN` numbering; owns nothing about GitHub.
3. **`scripts/export-github-item.py`** — `main()` writes a list of `(path, text)` instead of one path, and reports the count. Its module docstring describes the new layout.
4. **`scripts/test_export_split.py`** (new) — stdlib `unittest`, run by path like `scripts/test_authorship.py`: hunk trimming (single-line, multi-line, hunk shorter than the window, overlong context line), the threshold boundary in both directions, and one index row rendered end to end.
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
- Re-export a real long PR and a short one, and check the numbers: `python3 scripts/export-github-item.py 43 --repo vzakharov/vovazakharov.com` should land `pr.md` in the low tens of KB with a complete index, and `python3 scripts/export-github-item.py 73` (short, this repo) should produce one unchanged-shape file.
- Read the resulting index and confirm `/handle`'s tail test is answerable from it alone.

## Decisions taken

Three forks were open when this was written; the plan is written with the recommended option of each already in force, so it is implementable as it stands. Rejected, in one line each: **time-gap chunking** (the operator's opening idea) — measured above, it splits this export into 2–4 files that are all still too big, because the bulk is inside threads rather than spread across time; **one file per thread** — 69 files where 8 match how the work is actually done; **dropping hunks entirely** — the quoted line is what tells the reader what the comment is about, and after trimming it is cheap.
