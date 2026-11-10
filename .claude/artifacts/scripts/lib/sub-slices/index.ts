/**
 * `check:masd`'s checks on sub-slices — folders in a slice not named for a
 * segment (`subSlicePath` in `eslint/masd-graph.ts`). Every path is relative to
 * the working directory.
 */

import { importsOf, sliceOf } from "../slice-graph.ts";
import { promotions } from "./promotion.ts";
import { insignificant, siblingCycles, siblingGraphs } from "./siblings.ts";
import { mixed, nestedSegments } from "./tree.ts";

export { slicesWithSubSlices } from "./tree.ts";

/** Every problem with the sub-slices of `files`, the apps' source files. */
export function subSliceProblems(
  apps: readonly string[],
  files: readonly string[],
): string[] {
  const imports = importsOf(files);
  const slices = Map.groupBy(
    files.filter((file) => sliceOf(file) !== undefined),
    (file) => sliceOf(file) ?? "",
  );
  const graphs = siblingGraphs(slices, imports);
  return [
    ...nestedSegments(apps),
    ...mixed(apps),
    ...siblingCycles(graphs),
    ...insignificant(slices, imports, graphs),
    ...promotions(files, imports, graphs),
  ];
}
