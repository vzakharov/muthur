import fsd from "@feature-sliced/steiger-plugin";
import { defineConfig } from "steiger";

import { loadGraph } from "./eslint/masd-graph.ts";
import { slicesWithSubSlices } from "./scripts/lib/sub-slices/index.ts";

// Loaded from `.claude/artifacts/`, where `lint:fsd` runs Steiger.
const subSliced = slicesWithSubSlices([...loadGraph().keys()]);

// A literal, so the override inside the conditional spread keeps the severity
// type `defineConfig` wants rather than widening to `string`.
const OFF = "off" as const;

export default defineConfig([
  ...fsd.configs.recommended,
  {
    // Steiger runs once per app root and counts only that root's references,
    // so a slice entered from a descendant app reads as unused.
    // `scripts/masd-check.ts` counts across the composition instead.
    rules: {
      "fsd/insignificant-slice": "off",
    },
  },
  {
    // A folder in a slice not named for a segment is a sub-slice, cut into
    // segments of its own, so a segment's name below it is exactly what the
    // rule forbids. `scripts/masd-check.ts` keeps what it still guards: a
    // segment's name inside a segment.
    files: ["./src/*/{pages,widgets,features,entities}/**"],
    rules: {
      "fsd/no-reserved-folder-names": "off",
    },
  },
  ...(subSliced.length === 0
    ? []
    : [
        {
          // Steiger reads a sub-slice as a slice of a group named for its
          // parent, so it flags a sibling import as sideways and the parent
          // as a slice with no segments. Both are checked here already —
          // every import by `boundaries`, the sub-sliced slice's shape by
          // `scripts/masd-check.ts` — so the two rules go off in such
          // slices alone.
          files: subSliced.flatMap((slice) => [`./${slice}`, `./${slice}/**`]),
          rules: {
            "fsd/forbidden-imports": OFF,
            "fsd/no-segmentless-slices": OFF,
          },
        },
      ]),
]);
