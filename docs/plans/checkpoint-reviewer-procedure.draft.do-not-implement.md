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
   its route (`Skill` call, `Read` of the `SKILL.md`, typed command), timestamp
   and the head commit then. **The reviewer picks the cutoff, the script does
   not:** a `Read` counts as an entry, and a session reads a `SKILL.md` to
   research it as often as to run it (this session read `go` and `finalize`
   while planning), so the cutoff under review is the skill the log shows the
   session working through and closing — the last entry after which the session
   did that skill's work. Its head then is `<from>`. Read
   `git diff <from>..HEAD` (what the run produced) and
   `git diff origin/<base>...HEAD` (the branch around it), `<base>` being the
   PR's `baseRefName` (`gh pr view`), else the repository's default branch; the
   plan file under `docs/plans/` and the PR are found from the branch.
3. **The parent's full log.** Run `python3 scripts/session-qa.py`: every
   operator message verbatim, mid-turn ones included, and every assistant text
   reply, in order, with the cutoff markers. Read all of it, not the tail — a
   later operator message amends an earlier one. `--tools` adds one line per
   tool call when what the session did matters, not only what it said. For a
   record the script does not cover, `.claude/costs/CLAUDE.md` § "Reading a
   transcript" is where the format is written down.
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
   cannot answer `revise`. A follow-up reaches the reviewer through
   `SendMessage`, which no hook gates, so step 1 covers it too: anything in a
   follow-up beyond "look N" is the session's opinion and is not input.

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

- an operator message as `## Q <timestamp>` and its text verbatim; an assistant
  `text` block as `## A <timestamp>` and its text verbatim; thinking, tool
  results, hook attachments, skill bodies, keepalive wakes and subagent
  hand-backs are left out. **An operator message has two record shapes:** a
  prompt that starts a turn is a `user` record, one sent mid-turn is a
  `queued_command` attachment, and both carry `origin.kind == "human"` — a
  subagent hand-back is the same attachment with `origin.kind == "peer"`, which
  is how the two are told apart. A typed slash command arrives wrapped in a
  `<command-name>` envelope and is unwrapped to `/<name> <args>` before it is
  shown or tested for an entry. (Subagent records live in their own files under
  `<session>/subagents/`, so the main transcript holds none.)
- a cutoff marker line wherever the parent entered `plan`, `go` or `finalize`,
  with its route and the head commit at that time
  (`git rev-list -1 --first-parent --before=<timestamp> HEAD` — first-parent, so
  a base commit merged in later is not taken for the branch's head; if git fails
  the marker says so rather than omitting it).
- `--cutoffs` prints only those markers.
- `--tools` adds one line per tool call (name and the call's main argument).
- `--transcript PATH`; the default is `$CLAUDE_CODE_SESSION_ID`'s transcript
  under `~/.claude/projects/` — the id a subagent inherits from its parent
  (checked: a Haiku subagent here sees the parent's id).

"Entering a skill" reuses `.claude/hooks/skill_entry.py`'s `entered_skill`, by
turning each transcript record into the hook payload it corresponds to (`Skill`
and `Read` tool calls into `PostToolUse` payloads, an unwrapped typed command
into `UserPromptSubmit`), so the script and the hook agree on what an entry is.
They share its flaw too — a research `Read` is an entry — which is why the
reviewer, not the script, picks the cutoff. The import needs a `sys.path` insert
of `.claude/hooks` in `session-qa.py`, which `scripts/lib` otherwise avoids; the
alternative seam, moving `skill_entry.py` under `scripts/`, would make the hooks
do the insert instead, and costs more places.

### 4. `scripts/lib/transcript.py` — what the transcript scripts share (new)

`find_transcript`, `prompt_text`, `operator_message` and a record iterator that
tolerates a half-written last line. `find_transcript` and `prompt_text` move out
of `relay-last-reply.py`; `operator_message` (with the `origin` check) moves out
of `extract-session-images.py`, which already reads both record shapes.
`relay-last-reply.py`, `extract-session-images.py` and `session-qa.py` import
them. Errors become a raised `TranscriptError` that each script turns into its
own failure.

### 5. The hook enforces the one-line launch

`checkpoint-review.py` gains a `PreToolUse` registration on `Agent` in
`.claude/settings.json`. While a review is pending and the serving model is
weaker, an `Agent` call is denied when it is a review launch gone wrong: its
`model` names opus and its `prompt`, stripped, is not exactly the launch line,
or its `prompt` is the launch line and its `model` is not opus (which would
inherit the session's own). The reason gives the exact call. Other `Agent` calls
— a delegation to a weaker model, a read-only `Explore` — pass, and the hook
fails open like the rest of it.

What it still misses, stated so nobody counts on more: a review launched on a
non-opus model with another prompt; a `SendMessage` follow-up, covered by the
procedure's step 1 instead; a session that skips the review and records no
verdict, which is the closing-command gate's job. What it wrongly denies: an
operator-requested Opus `Agent` call made while a review is pending (pending
runs from entering the skill to its verdict), whose recourse is
`MUTHUR_CHECKPOINT_REVIEW=off`. Marks set by a research `Read` widen the window;
that is the existing marking, not changed here.

### 6. Pointers and tests

- `/plan`, `/go` and `/finalize` `SKILL.md` pointers and the catalog entries
  (`g2-pr-loop.md`, `g4-remote-plumbing.md`) name the new files.
- `scripts/test_session_qa.py` (new): Q/A extraction against a transcript built
  from real record shapes — this session's own, trimmed (a human `user` record,
  a `queued_command` human attachment, a `queued_command` peer hand-back, a
  tool-result `user` record, a skill body, a keepalive wake, a thinking block, a
  command-envelope prompt) — cutoff markers for each entry route and a
  first-parent head after a merge, `--cutoffs`, `--tools`, a half-written last
  line, an unknown transcript failing loudly.
- `scripts/test_checkpoint_review.py`: the `Agent` gate — denied with an opus
  call and a wrong prompt, denied with the exact line on a non-opus model,
  allowed with the exact line on opus, not applied on an Opus session or with
  the switch off or with no review pending, other `Agent` calls untouched.
- `scripts/test_relay_last_reply.py` and
  `scripts/test_extract_session_images.py`: loaders gain `scripts/` on
  `sys.path` for the `lib` import; their cases stay as they are.

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

- **Hook enforcement of the launch line (§5): yes, narrowed to review launches
  gone wrong.** Alternatives: the procedure states it and trusts the session,
  which is the shape that failed; or the gate denies every Opus `Agent` call
  while a review is pending, which also stops an operator's own request. The
  narrowed gate trades the misses and the wrong denial §5 lists for not blocking
  more than the launch.

## DRY notes

- **Shared, extracted:** transcript location, prompt text, the operator-message
  shapes and record iteration (`scripts/lib/transcript.py`), from
  `relay-last-reply.py` and `extract-session-images.py` — the record shape
  "belongs to the client and is not documented", so a change to it should be
  fixed in one place, not three. Shared, reused as it stands:
  `skill_entry.entered_skill` for what counts as entering a skill; the verdict
  list stays defined in `checkpoint-review.py` (`VERDICTS`) and the reviewer
  file names the same five.
- **Other transcript readers, not reused:** `.claude/costs/lib/transcript.py`
  reads responses and usage for billing, a different job from reading prompts
  and text. `.claude/costs/lib/identity.py` holds `COMMAND_ENVELOPE`; the costs
  tree is its own shipping group and `session-qa.py` ships without it, so
  `lib/transcript.py` carries its own copy of that one-line pattern and
  `test_session_qa.py` holds the two equal, as `test_relay_last_reply.py` does
  for the keepalive mark.
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
