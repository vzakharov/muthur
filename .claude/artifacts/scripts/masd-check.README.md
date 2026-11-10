# Why `check:masd` and `masd:clusters` decide as they do

The headers of `scripts/masd-check.ts` and `scripts/masd-clusters.ts` state what
the two checkers hold. This file is the why, for whoever changes what either
decides or disputes a verdict: each section is an alternative that was tried or
proposed and lost.

## Significance has a checker of its own

Steiger's `insignificant-slice`, run per app root, counts only that root's
references, which is wrong in both directions: a kernel slice used once in
kernel and twice in descendants looks insignificant, and one used by a single
descendant looks fine from the descendant. Run on the parent of several roots,
it finds no FSD root at all. The rule's whole input is one root's reference map
and the defect is that input, so `check:masd` reimplements the rule rather than
wrapping it, counting references across the slice's own app and every
descendant, tests left out. Its messages are Steiger's word for word, so a
reader of either recognises the other.

**Not extracted: a `masd` package or a Steiger plugin.** A plugin's rule sees
one root, which is the problem; a package earns nothing a script and one data
file do not already give.

## Modularity is the bar

Counting consumers alone would keep a one-page app a single slice, since every
lower slice it cuts out has one consumer. So one consumer is enough for a slice
whose term of Newman's modularity, `e − a²`, is positive: `e` the share of the
graph's file-import edges with both ends in the slice, `a` the share of edge
ends on it, so `a²` is what a rewiring keeping every file's degree would put
inside. **Nothing is tuned; the null model is the bar.** It replaced an
API-width threshold of one third, which had no better reason to be a third than
a quarter.

**The graph is the slice's own app alone**, tests and scripts out: an app cannot
know who will use it, and cutting it into modules by who happens to use it is
backwards. Counting the app with its descendants agreed on every real slice, but
admitted a slice of ten random scene files, the descendants' unrelated edges
lowering every slice's bar.

**Boundary-versus-internal edges were tried first and rejected**: they cannot
tell a module from a grab bag, because a well-layered slice imports downward and
so its edges leave it.

A sub-slice and a cluster are held one level down by the same bar, on their
parent unit's own graph, the cut's gain computed as an integer
(`scripts/lib/slice-graph.ts`) so that no float residue reads as a gain. The
app's graph is the wrong one there: past a few hundred edges, modularity's
resolution limit lets no split inside a slice pay for its one door. A sub-slice
two siblings import passes without it: a dominator subtree takes things from the
rest of its unit, and cut off, those files have to sit below both the subtree
and what imports its root, a piece the graph rarely calls a module of its own.

## A cluster is a dominator subtree

`masd:clusters` first took a file with everything it reaches, which grabbed
files the rest of the slice shares, so a candidate could not be cut out as it
stood. A dominator subtree — what is reached only through its root — is exactly
what leaves behind one door. Its gain is symmetric across the cut, so the
construction alone decides which side is "the cluster"; the leftover is held to
the same bar, which is what stops a cut under a thin page that would leave only
a wrapper behind. `scripts/masd-clusters.ts`'s header lists every condition.

## Where the promotion trace stops

The trace reads static imports and the barrels' `export { … } from` lines. A
name behind `export *` is untraced and never fires it, and an `import()` is not
seen at all, so a consumer taking the rest of a slice dynamically would be
flagged.
