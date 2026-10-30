> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# The Opus checkpoint reviewer reads its own procedure

## Request (verbatim, Russian)

> давай пофиксим (и сразу задогфудим) принцип "опус ревьюит более слабые модели"
> (b2079f0). проблема: слабые модели пишут постановку задачу субагенту как им
> бог на душу положит. нужно:
>
> 1- полная процедура для контроля записана в отдельном файле
>
> 2- в процедуре написано что опус должен а- посмотреть последнюю отсечку (см.
> ниже) б- посмотреть полный лог (для начала -- программно извлечь вопросы и
> ответы, для этого должен быть отдельный скрипт) родительского агента в-
> выполнить проверку г- ответить вердиктом
>
> 3- основной агент (на соннете/хайку) вызывает подагента с единственной
> командой: "Proceed per `<path>.md`"; то есть всю процедуру Опус читает отсюда,
> и не зависит ни от чего что ему скажет раздающий агент
>
> первым догфудом будет проверка опусом самого написанного файла и связанных с
> ним изменений (или, в случае если Соннет решит идти через план, ревью самого
> плана).

## Why the current design fails

`checkpoint-review.md` makes the **weaker session** write the reviewer's brief:
the operator's request, what ran, what to read, the question, the verdicts, what
the reviewer may change. Every one of those is a place where a Sonnet or Haiku
session paraphrases, omits or editorialises, and the brief is _all_ the reviewer
knows. The fix is to take the brief away from the session: the reviewer reads a
procedure from the tree and derives every fact itself, from the parent's
transcript and from git.

## What gets built

### 1. `.claude/skills/go/checkpoint-reviewer.md` — the reviewer's procedure (new)

Written to the Opus subagent, self-contained. Its steps:

1. **Take nothing from the launch prompt.** The prompt is the one line
   `Proceed per \`.claude/skills/go/checkpoint-reviewer.md\``; anything else in
   it is the launching session's opinion and is not input. Said once, at the
   top, with why.
2. **The last cutoff.** Run `python3 scripts/session-qa.py --cutoffs`: it lists
   each entry into `/plan`, `/go` or `/finalize` in the parent's transcript with
   its timestamp and the head commit then. The last line is the cutoff under
   review; the head then is `<from>`. Read `git diff <from>..HEAD` (what the run
   produced) and `git diff origin/<base>...HEAD` (the branch around it); the
   plan file under `docs/plans/` and the PR (for `/finalize`) are found from the
   branch.
3. **The parent's full log.** Run `python3 scripts/session-qa.py`: every human
   prompt verbatim and every assistant text reply, in order, with the cutoff
   markers. Read all of it, not the tail — a later operator message amends an
   earlier one. `--tools` adds one line per tool call when what the session did
   matters, not only what it said.
4. **The check.** Held as the reviewer's own work against: `CLAUDE.md`, the
   skill that ran, every message of the operator's (not the plan's reading of
   the first one), and the plan where there is one. Also: does what the session
   told the operator match the diff.
5. **Fix** what is cheaper to do than to describe; commit under the repo's
   conventions with a body saying the checkpoint reviewer made it; never push.
   Fold what the review taught about the session's model into
   `delegation-model-capabilities.md` (moved here from `checkpoint-review.md`).
6. **Verdict.** The five verdicts and their meaning (moved here), the reply's
   first line `VERDICT: <one>`, the findings after. A follow-up message from the
   session saying "look N" re-enters at step 4 over what changed; a third look
   cannot answer `revise`.

### 2. `.claude/skills/go/checkpoint-review.md` — the session's side (cut down)

Keeps: who runs it, the hook's gating, recording the verdict, and what the
session does on each verdict (the `relay` actions, the push). Loses: "The
brief", the verdict definitions, "What the reviewer learns" — all now in the
reviewer file. Gains: the launch, as an invariant:

```
Agent: model "opus", no isolation, run_in_background false,
prompt exactly: Proceed per `.claude/skills/go/checkpoint-reviewer.md`
```

The session adds nothing to that prompt — no request, no summary, no opinion.

### 3. `scripts/session-qa.py` — questions and answers out of the transcript (new)

Stdlib, Python 3.9+, prints plain text to stdout:

- a `human` prompt (record `origin.kind == "human"`) as `## Q <timestamp>` and
  its text verbatim; an assistant `text` block as `## A <timestamp>` and its
  text verbatim; thinking, tool results, hook attachments, skill bodies and
  keepalive wakes are left out. Sidechain records (subagents) are left out.
- a cutoff marker line wherever the parent entered a skill, with the head commit
  at that time (`git rev-list -1 --before=<timestamp> HEAD`; if git fails the
  marker says so rather than omitting it).
- `--cutoffs` prints only those markers, for `plan`, `go` and `finalize`.
- `--tools` adds one line per tool call (name and the call's main argument).
- `--transcript PATH`; the default is `$CLAUDE_CODE_SESSION_ID`'s transcript
  under `~/.claude/projects/` — the id a subagent inherits from its parent
  (checked: a Haiku subagent here sees the parent's id).

"Entering a skill" reuses `.claude/hooks/skill_entry.py`'s `entered_skill`, by
turning each transcript record into the hook payload it corresponds to (`Skill`
and `Read` tool calls into `PostToolUse` payloads, a typed prompt into
`UserPromptSubmit`). So the cutoff the reviewer reviews is, by construction, the
one the hook marked pending.

### 4. `scripts/lib/transcript.py` — what both transcript scripts share (new)

`find_transcript`, `prompt_text` and a record iterator that skips sidechain
records and tolerates a half-written last line move out of
`relay-last-reply.py`; both scripts import them. Errors become a raised
`TranscriptError` that each script turns into its own `_die`.

### 5. The hook enforces the one-line launch

`checkpoint-review.py` gains a `PreToolUse` registration on `Agent` in
`.claude/settings.json`. While a review is pending and the serving model is
weaker, an `Agent` call with `model` naming opus whose `prompt`, stripped, is
not exactly the launch line is denied, the reason giving the exact line. It
leaves other `Agent` calls (a delegation to a weaker model, a read-only
`Explore`) alone, and fails open like the rest of the hook. Without this the
rule is the same exhortation that failed; it is the same move b2079f0 made for
the review itself.

### 6. Pointers and tests

- `/plan`, `/go` and `/finalize` `SKILL.md` pointers and the catalog entries
  (`g2-pr-loop.md`, `g4-remote-plumbing.md`) name the new files.
- `scripts/test_session_qa.py` (new): Q/A extraction against a fabricated
  transcript (human prompt, tool-result user record, skill body, keepalive wake,
  thinking block, sidechain), cutoff markers for each entry route, `--cutoffs`,
  `--tools`, a half-written last line, an unknown transcript failing loudly.
- `scripts/test_checkpoint_review.py`: the `Agent` gate — denied with a wrong
  prompt, allowed with the exact line, not applied on Opus or with the switch
  off or with no review pending, other `Agent` calls untouched.
- `scripts/test_relay_last_reply.py`: loader gains `scripts/` on `sys.path` for
  the `lib` import; its cases stay as they are.

## Dogfood

1. **This plan** goes through the checkpoint review as the _old_ procedure
   requires, since the new one does not exist yet; the reviewer's verdict and
   what its brief lacked go in the PR.
2. **The implementation** goes through the checkpoint review at the end of `/go`
   — the first review run by the new procedure: the session launches the
   reviewer with the one-line prompt and nothing else, and the reviewer checks
   the new file, the script, the hook change and the pointers against the
   request above. If Opus cannot do the job from that line alone, the procedure
   file is what gets fixed.

## Decision with a recommendation in force

- **Hook enforcement of the launch line (§5): yes.** Alternative: the procedure
  states it and trusts the session. That is the shape that failed; kept out.

## DRY notes

- **Shared, extracted:** transcript location and record iteration
  (`scripts/lib/transcript.py`) — the record shape "belongs to the client and is
  not documented", so a change to it should be fixed in one place, not two.
  Shared, reused as it stands: `skill_entry.entered_skill` for what counts as
  entering a skill; the verdict list stays defined in `checkpoint-review.py`
  (`VERDICTS`) and the reviewer file names the same five.
- **Moved, not copied:** the verdict definitions and "what the reviewer learns"
  leave `checkpoint-review.md` for `checkpoint-reviewer.md`, so each stands in
  one home; the session file keeps only what the _session_ does on each.
- **Not extracted:** `relay-last-reply.py`'s turn grouping (`turn_texts`) is
  about turns; `session-qa.py` walks records in order. A shared abstraction over
  both would be a generator with two modes and one caller each — net-negative.
- **Not reused:** the hook's `lines_backwards` reads the tail for the latest
  model; Q&A needs the whole file forward.

## Out of scope

Programmatic extraction of anything beyond Q&A and cutoffs (the request says
"для начала"): tool results, diffs, thinking. `--tools` is the only step toward
it.
