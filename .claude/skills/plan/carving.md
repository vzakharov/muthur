# Carving a task into issues

What to do once `@.claude/skills/plan/SKILL.md` § "Carving a task into issues"
has answered yes — that skill holds the bar the answer is measured against.

Two readers, one procedure: `/plan` writes the proposal and `/go` files it,
stated together because the filing half is written against the shape the
proposal takes.

**Only the next slice has to be manageable.** Spell out the immediate work in full and give a **coarse** view of what follows — smaller than the original umbrella, but not fully decomposed. Parked slices are placeholders and ordering hints, not mini-specs; you owe no implementation DAG and no per-child plans up front.

## What the plan file carries

Under a heading of its own, the plan names every issue it proposes — the parent and each child — with a title and a one-line scope each, in dependency order, saying which child this plan specs. That list is the proposal the operator approves by approving the plan.

**Dedupe each proposed issue read-only, and write the matches into the list.** Run `@.claude/skills/propose-issue/SKILL.md` Steps 1–2 — search and triage, which touch nothing — for every slice, and record what they found beside the slice it matched. So a duplicate is something the operator rules on while reviewing the carve, not an interruption after it, and a slice already tracked gets linked as the sub-issue instead of filed twice.

**A match on the parent stops and reports.** Somebody else already tracking the whole umbrella is what changes the operator's judgment about whether to carve at all, which is a different question from whether one child is a duplicate.

**The parent.** Arriving from `/take-issue` it exists already. Arriving from bare prose the plan proposes one and `/go` creates it. It stays open as a grouping artifact and is never what the PR closes — **every slice is a child, the first included.** Filing children 2..n and doing slice 1 "under the parent" leaves the PR nothing to close and makes the parent both umbrella and work item. The parent closes once its children are done, which is the operator's call.

Because the children do not exist yet, the PR for this slice carries **`Closes #<tbd>`** — `@.claude/skills/pr/SKILL.md` Step 4 owns that marker and `/propose-issue` Step 3 fills it in.

## What `/go` files on the go-ahead

`@.claude/skills/go/SKILL.md` Step 1 runs `/propose-issue` Step 3 once per slice, parent and children alike, creating what the operator approved. Three things belong to the parent-child *relation* rather than to creating an issue, so they are stated here rather than in that skill:

**Link each child natively — mandatory.** `Part of #<parent>` prose is a pointer for humans, not a relation GitHub can track. Keep that line in the child's body, and **also** attach it through the sub-issues API — the GitHub MCP `sub_issue_write` tool (`method: "add"`, `issue_number: <parent>`, `sub_issue_id: <child's database id>`), or plain `gh`:

```bash
REPO=<owner>/<repo>
PARENT=<parent issue number>
for n in <child issue numbers…>; do
  cid=$(gh api "repos/$REPO/issues/$n" --jq '.id')
  gh api "repos/$REPO/issues/$PARENT/sub_issues" -F sub_issue_id=$cid
done
```

Two traps, either of which 422s: `sub_issue_id` is the child's numeric **database `id`**, not its issue number; and it must be sent with **`-F`**, not `-f`, which would send the integer as a string.

Without the relation the parent has no machine-readable notion of its children, so "the parent closes when its children are done" is unverifiable and the umbrella silently rots. Skipping the native link breaks the carve; it is not an omitted nicety.

**Size each slice so it is worth its own PR.** One child ships as one PR — that mapping is fixed; don't bundle several children into one PR or carve one child across several. The lever is the **granularity of the carve itself**: each child should be **substantial enough to justify a PR**, roughly **≥5 files of real change**. A prospective child touching only **1–3 files is too fine a cut** — group it with the other small, cohesive items into a single child that, taken together, is PR-worthy (within it, one commit per underlying item keeps the diff readable). A QA roundup of six small defects is usually one or two children, not six.

- **Group by cohesion, not just to hit a count.** Bundle items that sit in the same area or move together — several modal tweaks, a cluster of responsive-CSS fixes.
- **Keep blocked or uncertain items as their own child** even when small. A fix needing an environment or investigation this run can't cover — a value to pixel-match against a running deployment, a root cause needing in-browser repro, an item someone else marked *in progress* — gets its own deferred child with a note on what it's blocked on. Grouping merges trivial *ready* fixes; it never justifies shipping a guess.

**Carry an enumerated parent's reports into each child.** When the parent reads as an **enumeration of distinct bugs or requests** — a QA roundup, a bullet list of unrelated defects — copy each original item's **verbatim text and its attachments** into the child that covers it, so the child carries the reporter's own words and screenshots rather than your paraphrase. (Distinct from the other reason to carve: a **single cohesive problem statement** merely too vast for one PR has no per-item original text to distribute, so don't force it.)

- Put the original text and attachments in the child's **body** at creation; if the bodies already exist without them, post them as a **comment** on each child instead.
- **Reuse the parent's attachment URLs** so images and videos render: GitHub serves them at `https://github.com/user-attachments/assets/<asset-id>`, and the exporter rewrites those to `docs/issue/<n>/attachments/<asset-id>.<ext>` — so the **filename stem is the asset id**. Reconstruct the original URL from it, or read the parent's raw body through the API where the `user-attachments` links are intact, rather than re-uploading. Screenshots use `<img …>`; a bare video URL on its own line auto-embeds.
- Quote the reporter verbatim, in a blockquote, attributed, keeping related items grouped under the child they map to.
- **When unsure** whether the parent is an enumeration or one cohesive problem, **ask the operator** — in the plan's questions, where every other fork goes.
