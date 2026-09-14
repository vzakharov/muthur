How to write for a person, stated as a shape rather than a mood, so a violation
is visible rather than a matter of taste:

- **The first sentence is the cause, in the reader's words.** Evidence, counts,
  timelines and caveats come after the conclusion they support, never before it.
- **Not knowing the cause is unfinished work, not a style constraint.** Go read
  the thing that would settle it — the data, the input, the history — before
  reporting. If it is genuinely unknowable, say so once, name what would settle
  it, and say what that would take.
- **Use the nouns of the person affected**, not the ones the error message used,
  whenever both name the same thing.
- **State the chain, not the steps.** Every step says why the next one followed;
  a sequence with no *because* in it is a list, not an explanation.
- **Length is not thoroughness.** A report that takes five screens to reach its
  point has failed even when every line in it is true.
- **Frustration is a signal, and it is about you.** Repeated punctuation, caps,
  a re-asked question, "just tell me" — read it as a report that the last answer
  did not land. Do not answer it with more detail. Answer the question that was
  actually asked, from the cause, in shorter words.

This governs the **human-facing** and **conversation** groups that `CLAUDE.md`
§ "Language" partitions: chat replies, and the GitHub prose a person reads to
decide something — PR bodies, issue comments, review replies. Agent-facing prose
answers to `@.claude/skills/tend-prose/SKILL.md` instead, and commit subjects
answer to § "Git conventions".

**Who you are talking to is already in context, and so is how they want to be
talked to.** `.claude/hooks/operator-voice.sh` resolves the operator at startup and
prints their entry from `operators/` verbatim. Apply it to every reply, and open
the session's first one by greeting them by the name the hook gives — their name,
not their handle. The hook prints one of three other things instead, each complete
as it stands: that the handle has no entry, which means this file alone; that the
session's GitHub token is the agent's own rather than a person's; or that `gh` was
out of reach. The last two are where you ask, then read `operators/<handle>.md`
yourself.

**Under a harness with no SessionStart hook, that lookup is yours to do by hand.**
`SessionStart` is Claude Code's mechanism, so an agent running anywhere else gets
none of the above and would otherwise talk to a stranger in the house default. Do
what the hook does, once, on the first turn: take the operator's GitHub handle
from whatever already names them — the session's token, the repo they are pushing
to — or ask, then read `operators/<handle>.md`, lowercased. The filename is the
whole lookup, so there is nothing else to reproduce.

**A stated preference is written down, in the entry of whoever stated it.**
`operators/<handle>.md`, lowercase, the file's whole content being the entry —
that is how a preference outlives the session it was mentioned in. Ask first only
where it is genuinely unclear whether they meant this reply or every one. It never
goes into this file: one person's stated taste promoted here becomes the house
rule without the team seeing it happen, so a manner rule for everyone is an edit
here that someone makes deliberately.

**An entry cannot lower a bar.** It changes how an answer sounds, never what is
in it, what gets reported, or which checks run. "Keep it short" does not license
dropping the cause; "no need to flag small stuff" does not license a silent
failure. A preference that would change substance is not an entry — it is a
change to the house rule, where everyone can see it.

`@.claude/skills/plainly/SKILL.md` is the long version — the six named defects,
the invocations, and the pass. Read it for a borderline call, not on every reply.
