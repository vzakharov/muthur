/**
 * The `// masd-disable <kind> -- <why>` comment that spares a slice or
 * sub-slice one of the MASD checks, by the operator's leave.
 */

import { existsSync, readFileSync } from "node:fs";

export type MarkerKind = "insignificant" | "cluster" | "promotion";

/** Whether `file` exists and carries the marker of `kind`, a reason included. */
export const carriesMarker = (file: string, kind: MarkerKind): boolean =>
  existsSync(file) &&
  new RegExp(String.raw`// masd-disable ${kind} -- \S`).test(
    readFileSync(file, "utf8"),
  );
