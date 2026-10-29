# Checkpoint review: the six improvements from the comparing session

## Task, as asked

The comparing session (`session_01DaohkCDf1JN4Vapypm9WVz`) sent six improvements
for #251, listed in `docs/remove-before-merging/relay-1.md` § "Next step". The
operator's go-ahead, verbatim: «ты же мог перепроверить, но да :)» — all six.
Claims checked so far: #252's `review-gate.md` (on
`origin/claude/opus-quality-gate-tmds1o`) does place its review before the
`*.completed.md` flip, carries the request verbatim, and prefers `revise`; this
session's transcript tags every assistant entry with `message.model`
(`claude-opus-5-5`, 127 of 127).

## Done

Nothing of the six yet; the estimate is revised for the hook.

## Left — in this order

1. **`checkpoint-review.md` prose** (items 1, 3, 4):
   - the brief always carries the operator's request verbatim, plus the plan
     path where there is one; it carries facts, never the session's opinion of
     its work — a reviewer handed a conclusion tends to return it confirmed;
   - `fixed` is the exception: the reviewer prefers `revise` and fixes itself
     only what is cheaper to do than to describe, since its edits bill at Opus
     rates (#252 measured `fixed` $1.21 against two Haiku `revise` rounds
     $0.81);
   - the foreground reviewer's report can arrive as a hand-back message on the
     next turn; that is normal, the session waits for it and launches no second
     reviewer.
2. **`/go` placement** (item 2): move the pointer from after the
   `*.completed.md` flip to between `/polish` and the flip, and say a relay
   verdict leaves the plan `*.paused.md` per § "Stopping partway releases the
   plan".
3. **Hook `.claude/hooks/checkpoint-review.py`** (item 5), stdlib, modelled on
   `go-delegation.py` and `session_state.py`:
   - **Model:** the last assistant entry's `message.model` in the payload's
     `transcript_path`, skipping `<synthetic>`; weaker = the id names `sonnet`
     or `haiku`. No transcript or no entry → do nothing.
   - **Entry** (PostToolUse `Skill|Read`, UserPromptSubmit typed command — same
     three routes as `go-delegation.py`) into `plan`, `go`/`implement`,
     `finalize` on a weaker model: add that skill to the session's pending set
     in `tmp/checkpoint-review/<session>` (JSON), and on the first entry deliver
     `checkpoint-review.md` as `additionalContext`, naming the session id for
     the verdict command.
   - **Gate** (PreToolUse `Bash`, deny via
     `hookSpecificOutput.permissionDecision`): a `git mv` out of
     `*.draft.do-not-implement.md` while `plan` is pending; a `git mv` to
     `*.completed.md` while `go` is pending; `gh pr ready` (not `--undo`) while
     `finalize` is pending. The deny reason says to run the review and record
     the verdict. This is what makes `/plan`'s review fire before a same-session
     `/go` flips the plan.
   - **Verdict:**
     `python3 .claude/hooks/checkpoint-review.py verdict <session-id> <pass|revise|fixed|fixed-relay|relay>`;
     anything but `revise` clears the pending set. `checkpoint-review.md` tells
     the session to run it.
   - **Switch** (item 6): `MUTHUR_CHECKPOINT_REVIEW=off` makes the hook a no-op;
     the pointers then read as if the review did not exist, as
     `MUTHUR_DELEGATION` does for delegation.
   - Fails open on a bad payload, unreadable transcript or unwritable state.
   - Wire it in `.claude/settings.json` (PostToolUse `Skill|Read`,
     UserPromptSubmit, PreToolUse `Bash`); settings.json is not prompt text, so
     no staging.
4. **Pointers** in `/plan`, `/go`, `/finalize`: from "On a model below Opus" to
   "When `.claude/hooks/checkpoint-review.py` delivered `checkpoint-review.md`
   this session", with the no-hooks fallback `go/SKILL.md` uses for delegation
   (check the system prompt's model line yourself unless the switch is `off`).
   `checkpoint-review.md` § "Who runs it" says the same.
5. **Tests** `scripts/test_checkpoint_review.py` in `test_go_delegation.py`'s
   style: entry and delivery on a weaker model only, silence on Opus, the three
   gates deny while pending and allow after a verdict, `revise` keeps them shut,
   the switch, fail-open cases. Run by path.
6. **Catalog** (`g2-pr-loop.md`): an entry for the hook beside
   `go-delegation.py`; mention the switch in `/go`'s entry.
7. Fix this plan's predecessor claim: `opus-checkpoint-review.completed.md` §
   "DRY notes" rejected a hook on a false premise — leave the completed file,
   but the squash proposal and PR body must describe the hook.
8. `/polish`, flip this plan to `*.completed.md`, `/pr` refresh, re-sync the
   squash proposal.

## DRY notes

- `session_state.py` for the state path; `go-delegation.py`'s entry detection is
  the same three routes — copy the shape, or extract a shared `entered_skill`
  helper into `session_state.py`'s neighbourhood if the two would otherwise hold
  identical code (likely: decide when writing it).
- Transcript parsing: `scripts/relay-last-reply.py` and the keepalive already
  read the transcript; reuse a reader if one is importable from
  `.claude/hooks/`, otherwise a few lines local to the hook.
