---
description: Editing a file that loads on every turn — stage it, and let /finalize swap it in
paths:
  - CLAUDE.md
  - .claude/voice/voice.md
  - .claude/rules/**
  - .claude/staged/**
---

# Staging always-loaded files

A file rendered into the prefix of every request invalidates the prompt cache of
every session on the branch each time it changes, since everything after it has
to be re-read. So on a branch such a file is edited only through a staged copy,
and the real file changes once, at `/finalize`.

**The set is the files whose text sits in that prefix:**

- the root `CLAUDE.md`, and every file it `@`-imports, transitively;
- every `.claude/rules/*.md` with no `paths:`;
- a skill's frontmatter `description:`, which the skill listing carries — so a
  `SKILL.md` is staged when its description changes, and edited in place when
  only its body does, because the body loads on invocation.

A nested `CLAUDE.md` is outside it: it arrives on the first read of its
directory, appended where the session is, so an edit invalidates nothing before
it. Hook output is outside it too, since it is printed once and an edit reaches
only the next session.

**`scripts/staged.sh` owns the mechanics** — its header is the reference:

- `scripts/staged.sh stage <path>…`, then commit that alone, before any edit:
  the copy is byte-identical, so every later commit reads as a diff against the
  original. Edit the copy, `.claude/staged/<path>.staged`, never the real file.
- The `.staged` suffix is what keeps a copy inert: under its real name it
  would load as a nested `CLAUDE.md`, rule or skill the first time a file
  there is read. `vet` fails a file in `.claude/staged/` without it.
- `scripts/staged.sh list` shows what is staged, each real path beside its copy.
- `/finalize` runs `swap` before its quality passes, merging in anything the
  real file gained meanwhile, and nothing deletes a copy by hand.
- The operator can ask for the swap mid-branch ("swap it in", "unstage"), when
  the change has to be live on the branch to be tried out. Run `swap`, commit
  (`chore: swap the staged always-loaded files in early`), and push; the cache
  is paid once, and the next edit to the file stages it again.

The PR's file view shows a staged copy as a new file; its diff against the
original is the range from the staging commit to the head.
