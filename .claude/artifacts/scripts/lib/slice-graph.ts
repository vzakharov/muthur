/**
 * The file-import graph modularity is judged on, an app's or a slice's: shipped
 * files only, so a test reaching across a wall never counts as the code's
 * shape. `eslint/masd-graph.ts` is the other graph, of apps.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import ts from "typescript";

import {
  isTest,
  SLICED_LAYERS,
  subSlicePath,
} from "../../eslint/masd-graph.ts";
import { resolveImport, sourceFile } from "./import-graph.ts";

const SLICED = new Set<string>(SLICED_LAYERS);

/** An importing file and the file it imports. */
export type Edge = readonly [string, string];

/** Whether `file` sits anywhere under `directory`. */
export const within = (file: string, directory: string): boolean =>
  file.startsWith(directory + path.sep);

/** `src/<app>/<layer>/<slice>` of a shipped file in a sliced layer. */
export function sliceOf(file: string): string | undefined {
  const parts = file.split(path.sep);
  if (parts[0] !== "src" || parts.length < 5 || isTest(file)) {
    return undefined;
  }
  return SLICED.has(parts[2] ?? "")
    ? parts.slice(0, 4).join(path.sep)
    : undefined;
}

/** The sub-slices a file in `slice` sits in, outermost first, as full paths. */
export const subSlicesOf = (file: string, slice: string): string[] => {
  const below = path.relative(slice, path.dirname(file));
  return below === ""
    ? []
    : subSlicePath(below.split(path.sep)).map((sub) => path.join(slice, sub));
};

/** `slice` and the sub-slices a file in it sits in, outermost first. */
export const unitsOf = (file: string, slice: string): string[] => [
  slice,
  ...subSlicesOf(file, slice),
];

/** Every file each shipped file imports, tests left out on both ends. */
export function importsOf(files: readonly string[]): Map<string, Set<string>> {
  const imports = new Map<string, Set<string>>();
  for (const file of files) {
    if (isTest(file)) continue;
    const { importedFiles } = ts.preProcessFile(
      readFileSync(file, "utf8"),
      true,
      true,
    );
    const targets = new Set<string>();
    for (const { fileName } of importedFiles) {
      const resolved = resolveImport(file, fileName);
      if (resolved === undefined) continue;
      const imported = sourceFile(resolved);
      if (imported !== undefined && imported !== file && !isTest(imported)) {
        targets.add(imported);
      }
    }
    imports.set(file, targets);
  }
  return imports;
}

/** The edges among `members`. */
export const edgesWithin = (
  members: readonly string[],
  imports: ReadonlyMap<string, ReadonlySet<string>>,
): Edge[] => {
  const inside = new Set(members);
  return members.flatMap((from) =>
    [...(imports.get(from) ?? [])]
      .filter((to) => inside.has(to))
      .map((to): Edge => [from, to]),
  );
};

/** The edges with one end in a part, and the edge ends on it, counted once. */
function meeting(
  inPart: (file: string) => boolean,
  edges: readonly Edge[],
): { crossing: number; ends: number } {
  let crossing = 0;
  let ends = 0;
  for (const [from, to] of edges) {
    const inside = Number(inPart(from)) + Number(inPart(to));
    if (inside === 1) crossing++;
    ends += inside;
  }
  return { crossing, ends };
}

/**
 * `ΔQ` of cutting `part` off the rest of a graph: the edges the cut crosses are
 * lost, and the product of the two sides' degree shares is what a
 * degree-keeping rewiring would have put across it. The numerator is an
 * integer, so a cut that gains nothing reads exactly 0 rather than as rounding
 * noise either side of it.
 */
export function cutGain(
  part: ReadonlySet<string>,
  edges: readonly Edge[],
): number {
  const m = edges.length;
  if (m === 0) return 0;
  const { crossing, ends } = meeting((file) => part.has(file), edges);
  // `−crossing/m + 2s(1 − s)` with `s = ends/2m`, over the common `2m²`.
  return (ends * (2 * m - ends) - 2 * m * crossing) / (2 * m * m);
}
