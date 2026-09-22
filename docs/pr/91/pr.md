# PR #91: feat: tend-prose sweeps the rewritten prose for negators

- **State:** open
- **URL:** https://github.com/vzakharov/muthur/pull/91
- **Author:** @vzakharov (agent)
- **Base ← Head:** main ← claude/prose-negation-tend-lens-qpbiuw
- **Draft:** yes
- **Merged:** _not merged_
- **Created:** 2026-09-22T17:27:37Z
- **Updated:** 2026-09-22T17:51:14Z
- **Closed:** _not closed_
- **Labels:** _none_

---

## Body

## Summary

- The negation lens's second tell, a negated predicate in clean present tense, had nothing searching for it. A change that removes a **property** rather than a noun (vzakharov/vovazakharov.com#78) therefore left the lens nothing to grep, and three bears got through to review.
- The lens also ran before durability, which writes bears: its own worked example rewrites "no longer parsed" as "Nothing parses".
- Step 3 now ends with a negator sweep that lens 4 owns. Once every fix is applied, it greps the **resulting** prose lines for a closed list of negators, and each hit goes through the constraint-vs-residue discriminator. The grep only proposes; the discriminator decides.
- On the issue's open question: a `no longer` hit counts as a durability miss and goes back to that lens. A durability-only pass also sweeps the lines it rewrote.

## QA Checklist

- [ ] `regex-bears` — pipe the three bears from vzakharov/vovazakharov.com#78 through the sweep's grep; all three match.
- [ ] `regex-noise` — `Knotty notation` gives no match; `--no-sandbox` matches, and the skill text tells the reader to discard it as code.
- [ ] `order` — read Step 3: the sweep comes after the resolve order, so a bear written by durability is in scope.
- [ ] `single-lens` — `/tend-prose durability` still sweeps the lines it rewrote.

| Item | Automatable | Covered? | Notes |
|------|-------------|----------|-------|
| `regex-bears` | yes | manual run in session | shell one-liner |
| `regex-noise` | yes | manual run in session | |
| `order` | no | — | prose read |
| `single-lens` | no | — | prose read |

Closes #90

https://claude.ai/code/session_013vdNtPWfoTLf44j6xJkhpr

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## Comments

- **C01** @vzakharov (agent) — 2026-09-22T17:27:48Z — "Proposed squash title/body: ``` feat: #90 tend-prose sweeps…" → [↓](#c01)

<a id="c01"></a>

### Comment by @vzakharov (agent) on 2026-09-22T17:27:48Z

[https://github.com/vzakharov/muthur/pull/91#issuecomment-5780971458](https://github.com/vzakharov/muthur/pull/91#issuecomment-5780971458)

Proposed squash title/body:

```
feat: #90 tend-prose sweeps the rewritten prose for negators (pr #91)
```

```
The negation lens had a search for only one of its two tells: removed
nouns. A change that removes a property instead leaves that grep empty,
and the lens also ran before durability, whose own fix turns narration
into present-tense denials. Three bears got through to
review on vzakharov/vovazakharov.com#78 that way.

/tend-prose Step 3 now ends with a negator sweep that lens 4 owns. Once
every fix is applied, it greps the resulting comment and Markdown lines
for a closed list of negators, and each hit goes through the
constraint-vs-residue discriminator: the grep proposes and the
discriminator decides. A "no longer" hit goes back to durability as a
miss, and a durability-only pass sweeps the lines it rewrote.

Closes #90

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## Review threads

_1 resolved thread omitted; re-run with `--include-resolved` to export it._

- **T01** `.claude/skills/tend-prose/SKILL.md`:225 — unresolved — last: @vzakharov (human) 2026-09-22T17:51:14Z — "я все равно не понимаю, о чём это. что этот буллет имеет цел…" → [↓](#t01)

<a id="t01"></a>

### `.claude/skills/tend-prose/SKILL.md`:225 — unresolved

```diff
@@ -216,11 +216,13 @@ the sentence in place** rather than delete it. The mention survives as its own
… 7 lines elided …
   generates X", "X is not a segment". No change verb, which is exactly why lens
-  2 waves it through.
+  2 waves it through. Step 3's negator sweep is its search, and the only one a
+  change gets when it removes a **property** rather than a noun — the PDFs
+  become build artifacts, and the PDFs, their manifests and their script all
+  still exist, so the removed-noun list comes back empty.
```

**@vzakharov (human)** — 2026-09-22T17:37:22Z

мы выше где-то говорили (в скилле) про пдфы, иначе они как-то случайно тут взялись (понятно что это из примера из тикета, но про него читатель не знает)

**@vzakharov (agent)** — 2026-09-22T17:38:54Z

Да, PDF взялись из тикета без контекста. Переписал пример в общем виде: «files that stop being committed and become build artifacts still exist» — f316828

**@vzakharov (human)** — 2026-09-22T17:51:14Z

я все равно не понимаю, о чём это. что этот буллет имеет целью сказать? на примере пжст

---

## Timeline (status, references, and other events)

- **2026-09-22T17:37:28Z** @vzakharov reviewed (COMMENTED): https://github.com/vzakharov/muthur/pull/91#pullrequestreview-5281533680.
