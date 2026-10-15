---
description: Working in a session with several repositories attached — wire the hooks, resolve the target repo, and run that repo's own copy of each skill
paths:
  - scripts/find-repo.py
  - scripts/multi-repo-hooks.py
---

# Sessions with several repositories attached

Such a session starts in the clones' common parent (`/home/user`), which the
environment block shows as a primary working directory that is not a git
repository. Claude Code loads no repository's hooks there, and nothing the
skills run — `git`, `gh`, `scripts/…`, a relative path — names a repository
until the agent says which. `CLAUDE.md` points here so this file is read on such
a session's first turn; its `paths:` keep it out of every other session.

**First, the hooks.** When `/home/user/.claude/multi-repo-hooks.sha256` is
absent, the environment setup script's hook did not run the generator
(`docs/adopting/web-remote.md`), so run it before anything else:

```bash
python3 /home/user/<repo>/scripts/multi-repo-hooks.py --primary <first source>
```

`<first source>` is the directory name of the first repository in
`session_context.sources` from `get_session` (Claude Code Remote tools), called
with no id — the repository the UI lists first. Its output is the `SessionStart`
hooks' context, the operator's entry among it: read it as if a hook had printed
it. Every later event fires the attached repositories' hooks on its own.

**Then, for every skill that acts on a branch, PR or issue, resolve its target
repository first** and keep it for the rest of the task:

```bash
python3 /home/user/<repo>/scripts/find-repo.py <branch | #N | GitHub URL>
```

It prints the repository's path. Exit 2 names the several repositories the
target is in — the session's own auto-branch is in all of them — and the
operator picks; exit 1 or 3 is reported, not guessed past. Work with no such
target ("add a page to the blog") belongs to the repository the request names;
ask when it names none.

**Once the target is known, everything resolves against it:**

- **Every Bash call starts with `cd <repo> &&`**, because the shell returns to
  `/home/user` between turns, so one `cd` does not hold.
- **`scripts/…` and `@.claude/skills/…` mean the target's**, never those of the
  repository the loaded skill came from: `/finalize` run over another repository
  runs that repository's `scripts/vet.sh`.
- **The skill that loaded is only the entry point.** Where repositories carry
  skills of the same name, the session lists one copy, the first source's. When
  the loaded skill's base directory lies outside the target, `Read`
  `<repo>/.claude/skills/<name>/SKILL.md` and follow that copy from where you
  are; when the target has no such skill, say so and stop.
- **Files are read and written by absolute path inside the target**, and a
  `Read` of something in a directory comes before a `Write` there, which is what
  delivers its nested conventions.

**Two costs the operator carries, said when they bite:** a skill collision goes
to the first source, so the repository they work in belongs first in the
session's list; and `/relay` starts its successor on the target repository
alone, without the others attached.
