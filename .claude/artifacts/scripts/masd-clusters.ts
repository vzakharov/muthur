#!/usr/bin/env node

/**
 * Clusters inside a slice or a sub-slice that would make a sub-slice of their
 * own, run from `.claude/artifacts/`:
 *
 *   pnpm masd:clusters
 *
 * A gate: it exits 1 while it prints a cluster. A candidate is a file's
 * dominator subtree — the file and everything inside its unit reached only
 * through it — so the sub-slice it becomes has one door, the root, and that
 * door becomes its barrel. Kept when:
 *
 * - its root is no door and no barrel: a subtree rooted at a file the unit is
 *   entered by reaches no further in than the unit's own entry does;
 * - its root sits in the unit itself, not in one of its sub-slices, which are
 *   reported as units of their own;
 * - it holds at least two files, and what stays holds at least two that are no
 *   barrel and import each other into one piece: the cut's gain is the same
 *   for both sides, so a leftover too thin to be a unit means the cut went
 *   around the unit rather than through it;
 * - it is not just whole segments or sub-slices, where the tree has already
 *   cut;
 * - its root carries no `// masd-disable cluster -- <why>`, which the operator
 *   approves for a cluster that should stay where it is;
 * - splitting it off raises the modularity of the unit's own graph, not the
 *   app's (`scripts/masd-check.README.md` says why).
 *
 * Per unit it prints the best candidate and each next best that overlaps none
 * already printed. Reads `src/` under the working directory.
 */

import path from "node:path";

import { isPublicApi } from "../eslint/masd-graph.ts";
import { appFiles } from "./lib/import-graph.ts";
import { carriesMarker } from "./lib/masd-marker.ts";
import {
  cutGain,
  edgesWithin,
  importsOf,
  sliceOf,
  unitsOf,
} from "./lib/slice-graph.ts";

/** `shared`: what the cluster takes from the rest, the sub-slice below both. */
interface Cluster {
  root: string;
  members: readonly string[];
  shared: readonly string[];
  gain: number;
}

/** The folder right below `unit` a file sits in, or the file itself at its root. */
const partOf = (file: string, unit: string): string => {
  const [first = "", ...rest] = path.relative(unit, file).split(path.sep);
  return rest.length > 0 ? path.join(unit, first) : file;
};

/**
 * Each file's immediate dominator, entered from `entries`: Cooper, Harvey and
 * Kennedy's iteration over reverse postorder. An entry's is `undefined`.
 */
function dominators(
  entries: readonly string[],
  below: (file: string) => readonly string[],
): Map<string, string | undefined> {
  const postorder: string[] = [];
  const visited = new Set<string>();
  const visit = (file: string): void => {
    if (visited.has(file)) return;
    visited.add(file);
    for (const target of below(file)) visit(target);
    postorder.push(file);
  };
  for (const entry of entries) visit(entry);
  const order = new Map(postorder.map((file, index) => [file, index]));
  const above = new Map<string, string[]>();
  for (const file of postorder) {
    for (const target of below(file)) {
      above.set(target, [...(above.get(target) ?? []), file]);
    }
  }

  // `null` is the virtual root standing above every entry.
  const idom = new Map<string, string | null>(
    entries.map((entry) => [entry, null]),
  );
  const rank = (file: string | null) =>
    file === null ? Infinity : (order.get(file) ?? -1);
  const intersect = (a: string | null, b: string | null): string | null => {
    while (a !== b) {
      while (rank(a) < rank(b)) a = a === null ? a : (idom.get(a) ?? null);
      while (rank(b) < rank(a)) b = b === null ? b : (idom.get(b) ?? null);
    }
    return a;
  };
  const entrySet = new Set(entries);
  for (let changed = true; changed; ) {
    changed = false;
    for (const file of postorder.toReversed()) {
      if (entrySet.has(file)) continue;
      const known = (above.get(file) ?? []).filter((pred) => idom.has(pred));
      const [first, ...rest] = known;
      if (first === undefined) continue;
      let next: string | null = first;
      for (const pred of rest) next = intersect(next, pred);
      if (idom.get(file) !== next) {
        idom.set(file, next);
        changed = true;
      }
    }
  }
  return new Map([...idom].map(([file, dom]) => [file, dom ?? undefined]));
}

/** Whether `files` import each other into one piece, either direction counting. */
function connected(
  files: readonly string[],
  imports: ReadonlyMap<string, ReadonlySet<string>>,
): boolean {
  const [start] = files;
  if (start === undefined) return false;
  const edges = edgesWithin(files, imports);
  const reached = new Set([start]);
  for (let grew = true; grew; ) {
    grew = false;
    for (const [from, to] of edges) {
      if (reached.has(from) !== reached.has(to)) {
        reached.add(from).add(to);
        grew = true;
      }
    }
  }
  return reached.size === files.length;
}

/**
 * Every file outside `cluster` it reaches. Cut off as the rest's sub-slice, the
 * rest still importing the root, these would close a cycle between the two, so
 * they go into a third below both. None imports the cluster back: the files
 * form no cycle, so nothing the cluster reaches reaches it.
 */
function takenFromRest(
  cluster: ReadonlySet<string>,
  below: (file: string) => readonly string[],
): Set<string> {
  const found = new Set<string>();
  const stack = [...cluster].flatMap((file) => below(file));
  for (let file = stack.pop(); file !== undefined; file = stack.pop()) {
    if (cluster.has(file) || found.has(file)) continue;
    found.add(file);
    stack.push(...below(file));
  }
  return found;
}

function unitClusters(
  unit: string,
  members: readonly string[],
  imports: ReadonlyMap<string, ReadonlySet<string>>,
  roots: readonly string[],
): Cluster[] {
  const inUnit = new Set(members);
  const below = (file: string) =>
    [...(imports.get(file) ?? [])].filter((target) => inUnit.has(target));
  const edges = edgesWithin(members, imports);
  if (edges.length === 0) return [];
  const importedInside = new Set(edges.map(([, to]) => to));
  const doors = new Set(
    [...imports]
      .filter(([from]) => !inUnit.has(from))
      .flatMap(([, targets]) => [...targets])
      .filter((target) => inUnit.has(target)),
  );
  const entries = members.filter(
    (file) => doors.has(file) || !importedInside.has(file),
  );
  const idom = dominators(entries, below);
  const children = Map.groupBy(
    [...idom].filter(([, dom]) => dom !== undefined),
    ([, dom]) => dom ?? "",
  );
  const subtree = (root: string): Set<string> => {
    const found = new Set<string>();
    const stack = [root];
    for (let file = stack.pop(); file !== undefined; file = stack.pop()) {
      found.add(file);
      stack.push(...(children.get(file) ?? []).map(([child]) => child));
    }
    return found;
  };

  const parts = Map.groupBy(members, (file) => partOf(file, unit));
  const candidates: Cluster[] = [];
  for (const root of roots) {
    if (doors.has(root) || isPublicApi(root) || !idom.has(root)) {
      continue;
    }
    const cluster = subtree(root);
    const stays = members.filter(
      (file) => !cluster.has(file) && !isPublicApi(file),
    );
    if (
      cluster.size < 2 ||
      stays.length < 2 ||
      !connected(stays, imports) ||
      [...cluster].every((file) =>
        (parts.get(partOf(file, unit)) ?? []).every((peer) =>
          cluster.has(peer),
        ),
      ) ||
      carriesMarker(root, "cluster")
    ) {
      continue;
    }
    candidates.push({
      root,
      members: [...cluster].toSorted(),
      shared: [...takenFromRest(cluster, below)].toSorted(),
      gain: cutGain(cluster, edges),
    });
  }

  const taken = new Set<string>();
  return candidates
    .filter((candidate) => candidate.gain > 0)
    .toSorted((a, b) => b.gain - a.gain)
    .filter((candidate) => {
      if (candidate.members.some((file) => taken.has(file))) return false;
      for (const file of candidate.members) taken.add(file);
      return true;
    });
}

/** Each slice and sub-slice, with every shipped file under it. */
function units(files: readonly string[]): Map<string, string[]> {
  const found = new Map<string, string[]>();
  for (const file of files) {
    const slice = sliceOf(file);
    if (slice === undefined) continue;
    for (const unit of unitsOf(file, slice)) {
      found.set(unit, [...(found.get(unit) ?? []), file]);
    }
  }
  return found;
}

function report(): { text: string; flagged: number } {
  const files = appFiles();
  const imports = importsOf(files);
  const all = units(files);
  const lines: string[] = [];
  let flagged = 0;
  for (const [unit, members] of [...all].toSorted(([a], [b]) =>
    a.localeCompare(b),
  )) {
    const roots = members.filter((file) => {
      const slice = sliceOf(file) ?? "";
      return unitsOf(file, slice).at(-1) === unit;
    });
    const clusters = unitClusters(unit, members, imports, roots);
    if (clusters.length === 0) continue;
    flagged++;
    lines.push(`${unit} (${members.length} files)`);
    for (const { root, members: cluster, shared, gain } of clusters) {
      lines.push(
        `  ${path.relative(unit, root)}: ${cluster.length} files, ΔQ ${gain.toPrecision(2)}`,
        ...cluster.map((file) => `    ${path.relative(unit, file)}`),
      );
      if (shared.length > 0) {
        lines.push(
          "    it takes from the rest, a sub-slice below both:",
          ...shared.map((file) => `      ${path.relative(unit, file)}`),
        );
      }
    }
  }
  lines.push(`${flagged} of ${all.size} slices and sub-slices hold a cluster.`);
  if (flagged > 0) {
    lines.push(
      'Cut each into a sub-slice entered by its root, and what it takes from the rest into a sub-slice of its own unless the rest is nothing more. Where one should stay, ask the operator, and on their yes put "// masd-disable cluster -- <why it stays>" in its root.',
    );
  }
  return { text: `${lines.join("\n")}\n`, flagged };
}

const { text, flagged } = report();
process.stdout.write(text);
process.exitCode = flagged > 0 ? 1 : 0;
