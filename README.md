# muthur

> _"The option to ignore agentic coding expires in T minus five minutes."_
>
> — Alien (well, almost)

Agent-first infrastructure that survives being adapted.

Fork it into any project, change it to fit that project, and keep pulling
later improvements forward — the part a copied skill directory can't do.
Stack-agnostic.

What it is: a `CLAUDE.md` seed carrying only conventions that hold regardless of
stack, **31 skills** (23 working out of the box, 8 stubs awaiting hydration) that
compose into a plan → implement → PR → land loop, the path-scoped `.claude/rules/`
mechanism, a SessionStart hook that makes `gh` work in remote sessions, and the
scripts behind it all.

The "keep pulling" part runs on
[`watermark.json`](.claude/skills/update-muthur/watermark.json), which records
where your copy came from, the commit you last synced to, and what you adopted
or declined.
`/update-muthur` diffs the source since that commit and triages it one commit at a
time against the copy you have since edited — so a skill you rewrote stays
rewritten, a fix to one you left alone lands, and something you turned down is
remembered rather than offered again.

Per-item descriptions live in
**[`.claude/skills/update-muthur/catalog.md`](.claude/skills/update-muthur/catalog.md)** — one row
per skill, script and file, grouped so you can tell how much of it you need:

| Group | What it covers |
| --- | --- |
| **G0** | The sync path, both directions: `/update-muthur` pulls later changes forward (ships as a stub; hydrating it is filling in the watermark), `/spinoff` pushes a new sibling repo out. |
| **G1** | Prose & principles: `CLAUDE.md`, `.claude/rules/`, `/dry`, `/tend-prose`, `/plainly` and the voice rule it expands. |
| **G2** | The PR loop: `/plan`, `/go`, `/pr`, `/finalize` and the mechanical pieces they compose. |
| **G3** | Issue & backlog: `/take-issue`, `/propose-issue`, `/audit-github-backlog`. |
| **G4** | Remote-session plumbing — the `gh` shim that makes the rest work on the web. |
| **G5** | CI & landing: `/bootstrap-workflow-dispatch`, `/watch-ci`, and its polling scripts. |
| **G6** | Seven stack-bound stubs — hydrate the ones you need, delete the rest. |

The Python scripts are stdlib-only (3.9+) and use `$GH_TOKEN` or `gh auth token`;
the shell scripts need `gh`, `jq`, and `git`.

## Why `/plan` and `/go` exist

They started as a workaround: Claude Code's web/remote sessions re-emit stacked
plan-mode and `AskUserQuestion` prompts after idling, silently losing answers
([anthropics/claude-code#72704](https://github.com/anthropics/claude-code/issues/72704)).
So a plan became a file the operator can pull and review from another machine,
and questions became prose that survives in the transcript.

**The file turned out to be worth more than the bug it routed around** — enough
that these stay whether or not the bug is still there. A plan on disk can carry
sections native plan mode has nowhere to put, notably the mandatory **DRY notes**
that force the reuse-vs-duplication call to be argued *before* implementation.
Its filename doubles as the approval gate (`.draft.do-not-implement.md` until the
operator says otherwise), and `/plan` publishes it as a draft PR, so the plan is
reviewed as a diff — inline comments and threads — rather than as chat prose. The
turn ends by handing over a copy-pasteable `/go <branch>` line, so the next
session starts with the approval already recorded rather than re-litigated.

## Getting it

Two routes. Both are documented in **[`ADOPTING.md`](ADOPTING.md)**, which owns
the procedure end to end.

### Create a new project from this template

Click **"Use this template" → "Create a new repository"** in the GitHub UI, or:

```bash
gh repo create <owner>/<your-new-repo> \
  --template vzakharov/muthur \
  --public \
  --clone
```

(Use `--private` for private repos.) Then open a session in the new repo and run:

```
/detemplate <what you're building>
```

The fork ships that skill for exactly this: it publishes the prune as a
reviewable plan before anything is deleted, then deletes itself once the tree is
a project. A session that opens in an undetemplated fork and is asked to build
something routes there first on its own. [`ADOPTING.md` § Template
fork](ADOPTING.md#template-fork) says what the run is in for, if you want to know
before forking.

### Adopt into an existing repo

Paste this into an agent session in the target repo:

```
Adopt the agent infrastructure from https://github.com/vzakharov/muthur
into this repo: clone it somewhere temporary, read ADOPTING.md, and follow it.
```

The agent selects a subset against your repo's actual shape, mostly by
inspection — expect them to ask only about your session type and your
deploy/test surface.

Either way, later changes here come forward with `/update-muthur`, whose
shipped watermark already names this repo — you fill in the rest (see
[`ADOPTING.md`](ADOPTING.md) § "Hydrate the sync stub"). The infrastructure is
adoptable **and** re-syncable; a fork is not a dead end.

## More

`CLAUDE.md` carries the conventions themselves, and each
`.claude/skills/*/SKILL.md` carries its own full contract.
