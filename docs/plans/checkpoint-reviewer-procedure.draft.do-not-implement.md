> ⛔ **DRAFT — DO NOT IMPLEMENT.** This plan is not approved. Do not edit source
> while this file is named `*.draft.do-not-implement.md` — prep and spikes go in
> `tmp/`. On an explicit operator go-ahead, `git mv` it to `*.in-progress.md`
> and delete this banner (quoting the go-ahead in the commit) _before_ touching
> code.

# The Opus reviewer reads its procedure from `/polish`

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

## The operator's review of the first draft

The first draft built a standalone reviewer file, a cutoff-by-transcript scheme
and a hook with a narrowed gate. The review (PR threads) turned it into this:

> «а что если нам просто завернуть всё это в polish? т.е. а) polish всегда
> делает опус, б) последним шагом он проверяет не конкретные вещи (как в
> dry/tend-prose), а всё вместе (но желательно не читая весь дифф ещё раз,
> конечно). тогда много из механики схлопывается, остаётся лишь точно так же
> поправить скилл polish -- чтобы агенты вызывали их с минимум текста (типа
> просто `/polish <some token arg>`, а всё остальное подагент уже смотрел в
> соответствующем ранбуке»

Also from the review: the harness can refuse a bad launch programmatically (hook
on the skill/`Agent` launch), reading the parent's transcript is a _may_ rather
than a _must_, the reviewer fixes what it cannot describe in a form the
session's model follows, the capabilities file is renamed and moved, the change
is a `fix:`, and the plan review runs the way the real flow will.

## Why the current design fails

`checkpoint-review.md` makes the **weaker session** write the reviewer's brief:
the request, what ran, what to read, the question, the verdicts, what the
reviewer may change. Each is a place where a Sonnet or Haiku session
paraphrases, omits or editorialises, and the brief is _all_ the reviewer knows.
The fix takes the brief away from the session: the reviewer reads a procedure
from the tree and derives every fact itself.

`/polish` already has the machinery that needs: it runs in a fresh subagent from
a minimal prompt, resolves its own scope, and marks where it last ran (the
`polish:` floor, `passes.md` § "The floor"). The review becomes its third pass
instead of a parallel mechanism.

## What gets built

### 1. The review pass — `.claude/skills/polish/passes.md`

A third pass, run last, after `/dry` and `/tend-prose`. It checks the work **as
a whole**, which the other two do not: against the operator's request, the plan
where there is one, `CLAUDE.md` and the skills that ran, and what the session
told the operator against what the diff does. It does not re-read the whole
diff: it works from what the earlier passes reported, `git log --stat` over the
scope, and opens a diff only where a claim needs it.

- **The request** comes from the plan's verbatim `## Request` section, the PR
  and linked issue, any relay summary under `docs/remove-before-merging/` (a
  relayed session's own transcript starts after the request), and — optionally —
  the parent's questions and answers (§ 4). The procedure says the transcript is
  available, not that it must be read: with the procedure clear, the reviewer
  decides whether the written record is enough.
- **Fixing.** The reviewer edits itself what is cheaper to do than to describe,
  _or_ what it cannot describe in a form the session's model is known to follow
  — judged from the capabilities file's **Misses** (§ 5) and what the review
  just saw. It answers `revise` only for what is describable that way. Edits are
  commits under the repository's conventions; the pass never pushes beyond what
  `passes.md` § "Push before reporting" already does.
- **Learning.** What the review shows about the session's model goes into that
  model's **Handles**/**Misses** in the capabilities file, committed with the
  fixes or alone after a `pass` that taught something.
- **Verdict.** The five verdicts (`pass`, `revise`, `fixed`, `fixed-relay`,
  `relay`) and their meanings move here from `checkpoint-review.md`. The report
  ends with the line `VERDICT: <one>`. The review pass makes the run's last
  commit — its own fixes, or empty — so that commit is the floor, and its body
  carries `Review: <verdict>` and, for a `revise`, the findings. The next run
  starts from that floor, so it reads the findings from there and checks the
  session's commits against them; and a run whose last two review commits both
  say `Review: revise` cannot answer `revise` a third time — it fixes the rest
  or escalates.

`passes.md` also changes its intro ("Two passes" → three), its § "Do NOT" ("Skip
either pass. Two passes are the whole skill") and the order argument: the review
is last because it judges what survives the other two.

### 2. The launch — `.claude/skills/polish/SKILL.md`

The session launches one `general-purpose` subagent, `model: "opus"`,
foreground, and its prompt is the launch line and nothing else:

```
Proceed per `.claude/skills/polish/passes.md`
```

plus, when `/polish` was given an argument, one further line
`Argument: <the argument, verbatim>`. `passes.md` finds the plan under
`docs/plans/` itself. The skill says the model is always Opus, so a polish run
costs the same whichever model drives the session; nothing enforces it.

**`passes.md` opens by ruling out the launcher's words.** If the prompt that
started the run looks like a request to polish, the reviewer follows this file
and the `Argument:` line, if any, and nothing else the launching agent wrote —
not what to check, skip or conclude. A launcher that writes a long brief anyway
changes nothing the reviewer does. This is the accepted cost: on a Sonnet or
Haiku session the two older passes now bill at Opus rates too, and every
session, Opus included, pays for the review pass.

The skill's `description:` names the passes, so it changes too, through a staged
copy (`.claude/skills/CLAUDE.md`, `@.claude/rules/staging.md`).

`checkpoint-review.md` shrinks to the session's side: when the cutoff runs
`/polish` (below), how the hook gates it, and what the session does on each
verdict. Its brief and verdict sections move to `passes.md`; the session records
nothing, since the verdict is the polish commit's `Review:` line.

Where polish runs: `/go` Step 3 and `/finalize` already do. **`/plan` has no
polish today**; its publish step gains one when the session is below Opus (the
only cutoff the first draft covered that polish does not). `/dry` has nothing to
find on a plan, `/tend-prose` reads its prose, and the review pass is the point.

### 3. The closing gate reads the verdict from git — `.claude/hooks/checkpoint-review.py`

`revise` is answered by the session making the changes and running `/polish`
again, which a new subagent starts from the new floor; no follow-up message to
the reviewer is needed.

**The closing-command gate reads the verdict from git.** The weaker session runs
no recording command, so the `verdict` command goes. What stays per session is
which cutoffs it **entered**, marked on entry as today: the gate guards only
those, because a branch-wide condition would also deny a Sonnet `/go` the
go-ahead flip of a plan an Opus `/plan` wrote, which no polish ever reviewed.
Entries from a subagent's own reads are not marked (the reviewer opens skill
files); the `/go` spike checks which payload field tells a subagent's tool call
from the session's.

For an entered cutoff, the existing `Bash` gate (`git mv` out of the draft name,
`git mv` to `*.completed.md`, `gh pr ready`) denies the command on a weaker
session unless the branch's newest `polish:` commit
(`git log origin/<base>..HEAD`, as `polish/passes.md` § "The floor" finds it)
carries a `Review:` line other than `revise`, **and** nothing since it needs
review: `polish/passes.md`'s virtual-merge diff from that commit to `HEAD` — the
same recipe, so a base merge does not count and its conflict resolution does —
touches only the loop's working artifacts. Those are any change under
`docs/issue/`, `docs/pr/` and `docs/remove-before-merging/` (`/handle`'s
PR-export commit, relay summaries, the squash proposal), and a deletion or pure
rename under `docs/plans/` (`/finalize` step 3's sweep, the lifecycle flips); an
edit to a plan's text is the plan cutoff's own subject, so it counts. A session
that skips polish, edits after it, or fixes a vet failure or a merge conflict
after it finds the gate shut, and the deny reason says to run `/polish`, which
reviews just that.

The `Bash` gate matches the command itself, never the body of a commit message
or a heredoc: a `git commit -m` that quotes `gh pr ready` is not that command.
The pattern is anchored to command position, with a test for it.

What the gate cannot see, stated so nobody counts on more: whether the reviewer
that wrote a `Review:` line was Opus, or was launched from the line alone; and a
`Review:` line a session types into a commit message by hand. It guards the
common failure, a review skipped or outdated by later edits, not a session set
on getting past it.

### 4. `scripts/session-qa.py` — the parent's questions and answers (new)

Stdlib, Python 3.9+, plain text to stdout: an operator message as
`## Q <timestamp>` with its text verbatim, an assistant `text` block as
`## A <timestamp>`; thinking, tool results, hook attachments, skill bodies,
keepalive wakes and subagent hand-backs are left out. An operator message has
two record shapes: a prompt that starts a turn is a `user` record, one sent
mid-turn is a `queued_command` attachment, both with `origin.kind == "human"` (a
subagent hand-back is the same attachment with `origin.kind == "peer"`). A typed
slash command arrives in a `<command-name>` envelope and is unwrapped to
`/<name> <args>`. `--tools` adds one line per tool call. `--transcript PATH`;
the default is `$CLAUDE_CODE_SESSION_ID`'s transcript under
`~/.claude/projects/` (a Haiku subagent here sees the parent's id).

It prints the whole transcript by default, since the request usually opens it,
well before any floor. `--since <commit>` starts at that commit's committer
time, compared with each record's `timestamp`, so the reviewer can read the
conversation since the floor.

### 5. Rename and move the capabilities file

`.claude/skills/go/delegation-model-capabilities.md` →
`.claude/model-capabilities.md`. The file now serves the polish review as well
as delegation, so it sits at the `.claude/` root.
`grep -rn delegation-model-capabilities` finds every reference — docs,
`go/delegation.md`, `.claude/hooks/go-delegation.py`, the catalog under
`.claude/skills/update-muthur/catalog/`, the 100-line cap in `scripts/vet.sh`,
`scripts/test_go_delegation.py` — and one commit updates them all, `git mv`
keeping the history. The file's keeping rules, now in `go/delegation.md`, gain
the reviewer as a second writer.

### 6. Shared transcript helpers — `scripts/lib/transcript.py` (new)

`find_transcript`, `prompt_text`, `operator_message` and a record iterator that
tolerates a half-written last line. `find_transcript` and `prompt_text` move out
of `relay-last-reply.py`; `operator_message` (with the `origin` check) out of
`extract-session-images.py`, which already reads both record shapes.
`relay-last-reply.py`, `extract-session-images.py` and `session-qa.py` import
them. Errors become a raised `TranscriptError` each script turns into its own
failure.

### 7. Pointers and tests

- `/plan`, `/go` and `/finalize` `SKILL.md` pointers, `polish/SKILL.md`, and the
  catalog entries (`g2-pr-loop.md`, `g4-remote-plumbing.md`) name the changed
  files.
- `scripts/test_session_qa.py` (new): Q/A extraction against a transcript built
  from real record shapes — a human `user` record, a `queued_command` human
  attachment, a `queued_command` peer hand-back, a tool-result `user` record, a
  skill body, a keepalive wake, a thinking block, a command-envelope prompt —
  plus `--tools`, a half-written last line, an unknown transcript failing
  loudly.
- `scripts/test_checkpoint_review.py`: the `Bash` gate on a throwaway repo: open
  after a `Review: pass` polish commit followed only by a PR-export commit, a
  base merge, or the `docs/plans/` sweep; shut with no review, a
  `Review: revise`, a code commit or a plan-text edit after it, or a conflict
  resolution; untouched for a cutoff the session never entered.
- `scripts/test_relay_last_reply.py`, `scripts/test_extract_session_images.py`:
  loaders gain `scripts/` on `sys.path` for the `lib` import; their cases stay.

## Dogfood

1. **This plan** goes through the review the way the real flow will: an Opus
   subagent whose prompt is
   `Proceed with the reviewer role per docs/plans/checkpoint-reviewer-procedure.<state>.md, as if it was already implemented`
   — the plan standing in for `passes.md`, which does not exist yet. Its verdict
   and anything the stand-in prompt lacked go in the PR.
2. **The implementation** is reviewed by the real `/polish` at the end of `/go`:
   the session launches it with the one-line prompt, and the review pass checks
   the new pass, the gate change, the script, the rename and the pointers
   against the request above. If Opus cannot do the job from that line alone,
   the procedure file is what gets fixed.

## Decisions with a recommendation in force

- **Fold the review into `/polish`** rather than building a separate reviewer
  file and a transcript-cutoff mechanism. The floor already answers "since
  when", the subagent launch already exists, and one pass added to `passes.md`
  replaces the reviewer file, `--cutoffs`, route markers and the `skill_entry`
  import the first draft needed. The cost is Opus rates for the older passes on
  weaker sessions.
- **The reviewer is told to ignore the launcher; no hook inspects the launch.**
  Recognising a polish launch from its prompt is a heuristic, and a launcher
  that writes a long brief simply avoids it, so a hook would give an assurance
  it does not hold. The reviewer's own rule holds for any prompt, and the
  closing gate (git) is the one hard check. Alternatives: an `Agent` hook that
  rewrites the model and denies extra text; a subagent definition under
  `.claude/agents/` pinning Opus — both guard against a session set on getting
  past the review, which is not the failure being fixed.
- **The verdict lives in the polish commit, not in session state.** One commit
  closes the run, so there is no window between the passes and the review.
  Alternatives: a separate review commit or cutoff marker, which a run can stop
  short of; or the session recording the verdict with a command, which leaves
  the step to the weaker model. The gate still keys on the cutoffs the session
  entered, since the branch alone cannot say whose cutoff a flip closes.
- **`/plan` gains a polish step for sessions below Opus** so that plan reviews
  run the same procedure as code reviews.

## DRY notes

- **Shared, extracted:** transcript location, prompt text, the operator-message
  shapes and record iteration (`scripts/lib/transcript.py`), from
  `relay-last-reply.py` and `extract-session-images.py` — the record shape
  "belongs to the client and is not documented", so a change to it is fixed in
  one place, not three.
- **Reused as it stands:** the polish floor, the scope resolution and the empty
  marker commit for _since when_ and _what_; `checkpoint-review.py`'s `weaker`,
  `emit`, `state_file` and `VERDICTS`.
- **Moved, not copied:** the verdict definitions and "what the reviewer learns"
  leave `checkpoint-review.md` for `passes.md`; the capabilities file moves from
  `go/` to `.claude/`.
- **Other transcript readers, not reused:** `.claude/costs/lib/transcript.py`
  reads responses and usage for billing, a different job from reading prompts
  and text. `.claude/costs/lib/identity.py` holds `COMMAND_ENVELOPE`; the costs
  tree is its own shipping group and `session-qa.py` ships without it, so
  `lib/transcript.py` carries its own copy of that one-line pattern and
  `test_session_qa.py` holds the two equal, as `test_relay_last_reply.py` does
  for the keepalive mark.
- **Not extracted:** `relay-last-reply.py`'s turn grouping (`turn_texts`) is
  about turns; `session-qa.py` walks records in order. A shared abstraction over
  both would be a generator with two modes and one caller each — net-negative.
- **Not reused:** the hook's `lines_backwards` reads the tail for the latest
  model; Q&A needs the whole file forward.

## Out of scope

Programmatic extraction of anything beyond Q&A (the request says "для начала"):
tool results, diffs, thinking. `--tools` is the only step toward it.
