# Working a large review

Loaded by `@.claude/skills/handle/SKILL.md` Step 2 when the export's verdict
opens on `Large review`: one read of the file costs more than a context carries
beside the work it asks for — `scripts/gh_export/awaiting.py` owns the
threshold. A session that reads such an export itself spends its budget before
editing a file, and the successor a relay hands it to pays the same read again.

So read the verdict and nothing below it, and work the posts in two rounds of
subagents, because the grouping the work wants — by topic — is only known once
the posts are read:

1. **Read.** Cut the verdict's rows into batches in their order and launch one
   subagent per batch, in parallel, with the export's path and the batch's
   anchors. Each edits nothing and returns, per post: its anchor; the ask, in a
   sentence or two; whether it is a change to make, a question to answer or a
   point to push back on; the files and lines it touches; the posts it repeats,
   contradicts or depends on, by anchor; and the change or answer it proposes.
2. **Regroup.** From the digests, group the posts by topic: those touching the
   same files or turning on the same decision go together, a contradiction is
   settled here or put to the operator, and a question needing no edit is
   answered from its digest.
3. **Execute.** Launch one subagent per group with its digests, anchors and the
   export's path; each makes the group's edits and returns, per post, what it
   changed. Groups with disjoint files run in parallel, groups sharing a file
   one after another, since parallel edits to one file collide. None commits or
   posts.

The session keeps the commits and the GitHub replies, and opens a post itself
only where a digest leaves its ask unclear. Its first reply tells the operator
the review is going through subagents, with the warning's size, since this is
the lane's one departure from its ordinary course.
