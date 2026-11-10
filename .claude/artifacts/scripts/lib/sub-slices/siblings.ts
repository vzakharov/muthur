/**
 * The sub-slices' checks that read how siblings — the sub-slices one unit
 * holds — import one another: no cycle among them, and none unearned.
 */

import path from "node:path";

import {
  cutGain,
  edgesWithin,
  sliceOf,
  unitsOf,
  within,
} from "../slice-graph.ts";

/** Each child sub-slice of a unit, and the siblings it imports. */
export type Siblings = Map<string, Set<string>>;

/** Per unit holding sub-slices, its children and their imports of one another. */
export function siblingGraphs(
  slices: ReadonlyMap<string, readonly string[]>,
  imports: ReadonlyMap<string, ReadonlySet<string>>,
): Map<string, Siblings> {
  const graphs = new Map<string, Siblings>();
  const graphOf = (parent: string): Siblings => {
    const graph = graphs.get(parent) ?? new Map<string, Set<string>>();
    graphs.set(parent, graph);
    return graph;
  };
  for (const [slice, members] of slices) {
    for (const from of members) {
      const chain = unitsOf(from, slice);
      for (const [index, child] of chain.entries()) {
        const parent = chain[index - 1];
        if (parent !== undefined && !graphOf(parent).has(child)) {
          graphOf(parent).set(child, new Set());
        }
      }
      for (const to of imports.get(from) ?? []) {
        if (sliceOf(to) !== slice) continue;
        const other = unitsOf(to, slice);
        const fork = chain.findIndex((unit, index) => other[index] !== unit);
        const [child, sibling, parent] = [
          chain[fork],
          other[fork],
          chain[fork - 1],
        ];
        if (child === undefined || sibling === undefined) continue;
        if (parent === undefined) continue;
        graphOf(parent).get(child)?.add(sibling);
      }
    }
  }
  return graphs;
}

/** Every sibling `from` reaches by importing, itself only through a cycle. */
export function reaches(graph: Siblings, from: string): Set<string> {
  const seen = new Set<string>();
  const stack = [...(graph.get(from) ?? [])];
  for (let node = stack.pop(); node !== undefined; node = stack.pop()) {
    if (seen.has(node)) continue;
    seen.add(node);
    stack.push(...(graph.get(node) ?? []));
  }
  return seen;
}

/**
 * Sibling sub-slices importing one another in a cycle. Each enters the other by
 * its barrel, which madge sees as a file like any other, so files can form a
 * DAG while the sub-slices holding them go round.
 */
export const siblingCycles = (
  graphs: ReadonlyMap<string, Siblings>,
): string[] =>
  [...graphs].flatMap(([parent, graph]) =>
    cycles(graph).map(
      (cycle) =>
        `${parent}: its sub-slices ${cycle.map((sub) => `"${path.basename(sub)}"`).join(", ")} import one another in a cycle; siblings import in one direction only, so move what they share into a sub-slice of its own or merge them`,
    ),
  );

/** The strongly connected components of more than one node, each sorted. */
function cycles(graph: Siblings): string[][] {
  const reach = new Map(
    [...graph.keys()].map((node) => [node, reaches(graph, node)]),
  );
  const found = new Map<string, string[]>();
  for (const [node, reached] of reach) {
    const component = [...reached]
      .filter((other) => reach.get(other)?.has(node) === true)
      .toSorted();
    if (component.length > 1) found.set(component.join("\n"), component);
  }
  return [...found.values()];
}

/**
 * Sub-slices earned neither way: their cut does not raise the modularity of
 * their parent's graph, and fewer than two siblings import them. The second is
 * what keeps a piece two siblings share below both of them, and only while both
 * still do.
 */
export function insignificant(
  slices: ReadonlyMap<string, readonly string[]>,
  imports: ReadonlyMap<string, ReadonlySet<string>>,
  graphs: ReadonlyMap<string, Siblings>,
): string[] {
  const shared = (sub: string, parent: string): boolean =>
    [...(graphs.get(parent) ?? [])].filter(([, targets]) => targets.has(sub))
      .length >= 2;
  return [...slices].flatMap(([slice, members]) => {
    const parents = new Map<string, string>();
    for (const file of members) {
      const chain = unitsOf(file, slice);
      for (const [index, sub] of chain.entries()) {
        if (index > 0) parents.set(sub, chain[index - 1] ?? slice);
      }
    }
    return [...parents].flatMap(([sub, parent]) => {
      const family = members.filter((file) => within(file, parent));
      const part = new Set(family.filter((file) => within(file, sub)));
      return cutGain(part, edgesWithin(family, imports)) > 0 ||
        shared(sub, parent)
        ? []
        : [
            `${sub}: This sub-slice neither raises the modularity of its parent's imports nor is imported by two of its siblings. Consider folding it into "${parent}".`,
          ];
    });
  });
}
