---
description: Take a GitHub issue — export and read the thread, split it when the scope demands, then hand the work over to `/plan`. Invoke as `/issue <number|url>`; a prompt that reads like an issue title and ends in `#<N>`, with no slash command, is the same invocation.
---

End state of this skill: the issue is exported and committed on the branch, any split is filed on GitHub as sub-issues, and the work has been handed to `@.claude/skills/plan/SKILL.md` — which in an ordinary web session means a plan file published as a draft PR and a copyable `/go <branch>` handoff. Not code — that belongs to `/go`.

The chain is `/issue` → `/plan` → draft PR → (review loop via `/handle`) → `/go` → `/finalize`. Everything past the handover is owned by the skill that runs it.

## Step 0 — Mode gate: native plan mode is not supported

If the session is in **native plan mode** — the launch banner or system prompt says so, `ExitPlanMode` is the offered exit, or an edit is refused for that reason — **stop before running anything below.** Tell the operator:

- this flow is plan-**file**-based (`@.claude/skills/plan/SKILL.md`), and native plan mode cannot write the two artifacts it depends on: the export under `docs/issue/<n>/` and the plan under `docs/plans/`. Both must be committed and pushed, because the operator reviews from a different machine than the one you run on;
- the plan-mode approval UI is unreliable in web sessions regardless (anthropics/claude-code#72704);
- so switch to **accept-edits** or **auto** and send any reply — the run picks up from there; no re-invocation needed.

Do not work around it, and do not fall back to a chat-only plan.

## Step 1 — Export the issue locally (then read the export)

**First command:** run the bundled exporter:

```bash
python3 scripts/export-github-item.py <issue-number|https://github.com/OWNER/REPO/issues/N> [--repo OWNER/REPO]
```

The script writes `docs/issue/<n>/issue.md` (body + comments + timeline) and downloads any image / file attachments referenced in the thread to `docs/issue/<n>/attachments/`.

Consult the issue only through the export — never `gh issue view`, the GitHub MCP tools, or `WebFetch` in its place. `gh issue view` alone does **not** fetch attachments: GitHub's `private-user-images.githubusercontent.com` URLs require an authenticated request even when the issue is public, which is why the export script exists. `WebFetch` on a github.com issue page often fails outright in isolated environments. For a quick metadata check unrelated to the task at hand — labels, assignees, linked PRs — `gh issue view <n> --json title,body,labels,assignees,state,url` is still fine.

**Then read** `docs/issue/<n>/issue.md` end to end, and **open the files under** `docs/issue/<n>/attachments/` when you need pixels (screenshots, mockups, design references). A long thread indexes its comments and may hoist their bodies into `docs/issue/<n>/comments.md` — "end to end" includes that file, an issue being read whole rather than selectively.

**Auth:** the script reads `$GH_TOKEN` (or `$GITHUB_TOKEN`) first, then falls back to `gh auth token`. One of those must be available. **Deps:** stdlib Python 3.9+ only — no `pip install` needed.

**Repo:** if `--repo OWNER/REPO` is omitted and the argument isn't a full issue URL, the script reads `origin` from the current git checkout. Pass `--repo` explicitly when exporting an issue from a different repo than the one you're working in.

If the export fails, **stop and report** — do not start solving the task from the title alone. Tell the user what failed and how to proceed. The script exits non-zero on every failure — auth, network, repo not found, or an attachment that wouldn't download — so check the status, not just the last line. A partial attachment failure still writes the Markdown and prints `Downloaded 2/3 attachment(s)` plus each URL it missed: the thread is there, but you'd be reading it with pixels missing.

### Video attachments (screen recordings)

Exported attachments may have no extension (the filename stem is the asset id), so `file docs/issue/<n>/attachments/<asset-id>` to spot videos (e.g. `ISO Media, Apple QuickTime movie`). You can read **images** but not play **videos**. Extract frames with `ffmpeg`, if it's available, and read the frames as images:

```bash
mkdir -p tmp/frames   # tmp/ is gitignored — never commit frames
ffmpeg -y -i docs/issue/<n>/attachments/<asset-id> -vf fps=2 -q:v 3 tmp/frames/frame_%03d.jpg
```

- `fps=2` (two frames/sec) suits a short clip; lower to `fps=1` for long videos, raise to `fps=4` to catch a fast transient (a toast, a flashed error). Check length first with `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 <path>`.
- Read first/middle/last frames, then bisect toward the moment of interest. Frame `N` ≈ `N / fps` seconds, so you can map a frame back to a timestamp and correlate it with logs.
- Recovers visuals only (no audio) — usually enough for a UI/repro bug.

## Step 2 — Commit the export

```bash
git add docs/issue/<n> && git commit -m "docs: #<n> export the issue"
```

Commit it **now**, before any planning. The export is the source of truth for what the issue says, so an agent resuming this branch — after a context wipe, a handoff, or in a parallel session — re-reads the thread instead of re-exporting it, and committing it up front means that holds even if the session dies mid-plan. Never commit it on the trunk or a promotion branch.

`@.claude/skills/finalize/SKILL.md` deletes the whole `docs/issue/` tree in the last commit before `gh pr ready`, so this add and that delete cancel out in the squash. **You** must not delete it.

## Step 3 — Split, if and only if the scope demands it

The bar for splitting is high. Do **not** split because:

- the issue mentions several files (most do)
- you can imagine a "phase 1 / phase 2" framing (most things admit one)
- decomposition feels tidy

Default to taking the issue as-is. Only split when the size is obviously beyond a single PR and the seams between sub-tasks are real, not invented. **Genuinely large** means multiple unrelated subsystems, weeks of work, or distinct deliverables that ship independently — not "many files" or a tidy phase breakdown.

**Only a split stops for an answer.** Deciding _not_ to split is not a gate and never becomes one: say so in a line and move on to Step 4. Do not ask whether the issue looks big enough, do not offer a split you don't think is warranted, and do not treat a large-feeling issue as a reason to check in. If the operator disagrees they say so in the plan discussion one step later, which costs them a sentence — whereas a question here costs a round-trip on every issue.

For **truly** large work, only the **next** slice has to be manageable in this run (something you can plan and ship in one branch/PR). Sub-issues you park in the backlog may themselves stay large — they are placeholders and ordering hints, not mini-specs. You do **not** owe a full implementation DAG or per-child plans up front: spell out the **immediate** work in detail, and give a **coarse** view of what follows (smaller than the original umbrella, but not fully decomposed).

### If the issue is split-worthy

1. **Propose the split in your reply and stop for approval** — titles + one-line scope each, dependency order, and which child you take first. Create nothing yet.
2. Once the operator approves — which may take a round or two of back-and-forth — create **one sub-issue per slice, the first one included** (see below), each linked natively to the parent.
3. Comment on the parent listing the children and the ordering.
4. `python3 scripts/export-github-item.py <first child>` and commit that export too. From here on, "the issue" means that child.

The gate is there because filing sub-issues writes to the tracker on the operator's behalf and is awkward to undo — and because the carve is a judgement call they may want to make differently. It runs as prose in the chat rather than through a plan file: a split changes no files, so there is no diff to iterate over, and routing it through `/plan` would end the run at a `/go` handoff before any issue existed. Fold the enumeration-vs-cohesive question below into the same exchange when it's unclear.

#### Every slice is a sub-issue, including the first

Filing children 2..n and doing slice 1 "under the parent" leaves the PR nothing to close and makes the parent both umbrella and work item. So **every** slice gets its own sub-issue, the first included; the PR for the slice you take carries `Closes #<child>`, **never** the parent's number. The parent stays open as the umbrella and closes only once its children are done — the operator's call, not yours.

#### Link each child natively — mandatory

`Part of #<parent>` prose is a pointer for humans, not a relation GitHub can track. Keep that line in the child's body, and **also** attach it through the sub-issues API — the GitHub MCP `sub_issue_write` tool (`method: "add"`, `issue_number: <parent>`, `sub_issue_id: <child's database id>`), or plain `gh`:

```bash
REPO=<owner>/<repo>
PARENT=<parent issue number>
for n in <child issue numbers…>; do
  cid=$(gh api "repos/$REPO/issues/$n" --jq '.id')
  gh api "repos/$REPO/issues/$PARENT/sub_issues" -F sub_issue_id=$cid
done
```

Two traps, either of which 422s: `sub_issue_id` is the child's numeric **database `id`**, not its issue number; and it must be sent with **`-F`**, not `-f`, which would send the integer as a string.

Without the relation the parent has no machine-readable notion of its children, so "the parent closes when its children are done" is unverifiable and the umbrella silently rots. Skipping the native link breaks the split; it is not an omitted nicety.

#### Carry the original reports into each sub-issue

When the parent reads as an **enumeration of multiple distinct bugs/requests** — a QA roundup, a bullet list of unrelated defects, several separate "also this is broken" items — copy each original item's **verbatim text and its attachments** into the sub-issue that covers it, so the child carries the reporter's own words and screenshots, not just your paraphrase. (This is distinct from the other reason to split: a **single, cohesive problem statement** that's merely too vast for one PR — there, there's no per-item original text to distribute, so don't force it.)

- Put the original text + attachments in the sub-issue **body** when you create it. If you already created the bodies without them, post them as a **comment** on each child instead.
- **Reuse the parent's attachment URLs** so images/videos render: GitHub serves them at `https://github.com/user-attachments/assets/<asset-id>`, and the exporter rewrites those to local `docs/issue/<n>/attachments/<asset-id>.<ext>` — so the **filename stem is the asset id**. Reconstruct the original URL from it (or read the parent's raw body via the GitHub API, where the `user-attachments` links are intact) rather than re-uploading. Screenshots use `<img …>`, bare video URLs on their own line auto-embed.
- Quote the reporter verbatim (blockquote), attributed, and keep related items grouped under the sub-issue they map to.
- **When unsure** whether the parent qualifies as an enumeration (vs. one cohesive problem), **ask the operator** before deciding.

#### Size the split so each sub-issue is worth its own PR

**One sub-issue ships as one PR** — that mapping is fixed; don't bundle several sub-issues into one PR or carve one sub-issue across several. The lever you control is the **granularity of the split itself**: how finely you carve the parent into sub-issues. Carve it so each resulting sub-issue is **substantial enough to justify a PR** — roughly **≥5 files of real change**. A prospective sub-issue that would touch only **1–3 files is too fine a cut**: don't give it its own sub-issue/PR. Instead **group it with the other small, cohesive items into a single sub-issue** that, taken together, is PR-worthy (within that sub-issue, one commit per underlying item keeps the diff readable).

A QA roundup of six small defects is usually **not** six sub-issues — it's one or two sub-issues that each bundle several related fixes, each shipping as one PR.

- **Group by cohesion, not just to hit a count.** Bundle items that sit in the same area or move together (e.g. several modal/popup tweaks, a cluster of responsive-CSS fixes). When grouping, still carry each underlying item's verbatim report + attachments into the bundled sub-issue's body (per above), grouped item-by-item.
- **Keep blocked/uncertain items as their own sub-issue** even when small. A fix that needs an environment or investigation this run can't cover — a value to pixel-match against a running deployment, a root cause needing in-browser repro, an event with no traceable source in the code, an item someone else marked _in progress_ — gets its **own deferred sub-issue with a note on what it's blocked on**, rather than being grouped into a batch you can finish. Grouping merges trivial _ready_ fixes; it never justifies shipping a guess.

### If the issue is not split-worthy

The usual case. Say so in a line, and go straight to Step 4 — there is nothing to approve.

## Step 4 — Hand over to `/plan`

Load and follow `@.claude/skills/plan/SKILL.md`, passing what the issue asks in **one line** plus the export path (`docs/issue/<n>/issue.md`), and `<issue>` = the number the eventual PR must close: the chosen child when you split, otherwise the issue itself, **never** the parent. The handover happens in this session, so `/plan` runs with the thread you just read still in context and the export on the branch. Don't paraphrase the issue back at yourself.

`/plan`'s deliverable is the plan file, published as a draft PR by its § "Publishing the plan", and the copyable `/go <branch>` block. **That is normally where this run ends.** Do not implement here: `/go` runs in a later session and hands the finished work back to `/pr` to refresh.

The **only** waiver is the operator explicitly saying no plan is needed, which routes to `@.claude/skills/go/SKILL.md` § "Planless entry". It is not this skill's to grant on its own judgement.

**Branch name:** `@.claude/skills/branch-rename/SKILL.md` owns the form, and the rename lands before `/plan` writes the plan file, whose name derives from the slug. This skill contributes one requirement: the slug leads with the issue number, e.g. `claude/847-fix-sidebar-scroll-<hash>`.

**Reporting:** `/plan` and `/pr` report their own results. Add only what this skill alone knows — which issue you took, whether you split it, and links to the children.

**Split-only session:** if the operator says the run's deliverable is the sub-issues themselves, with no code to be written in it, stop after Step 3 and report — there is nothing to hand over.
