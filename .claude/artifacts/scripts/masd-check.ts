#!/usr/bin/env node

/**
 * What no single-root checker can see in Multi-App Sliced Design, run from
 * `.claude/artifacts/`:
 *
 *   pnpm check:masd
 *
 * - the graph's own checks: `src/masd.json` parses, each parent above its
 *   child, an app per directory under `src/` and a directory per app, and no
 *   app earned no better than an insignificant slice;
 * - Steiger's `insignificant-slice`, with each slice's references counted
 *   across the composition — its own app and every descendant — rather than
 *   within one app root, its messages kept word for word; a slice with one
 *   reference passes when it is a module by its own app's imports;
 * - the sub-slices' checks, `scripts/lib/sub-slices/`.
 *
 * Reads `src/` under the working directory, so a test runs it against a tree of
 * its own. `scripts/masd-check.README.md` says why it decides as it does.
 */

import { existsSync } from "node:fs";
import path from "node:path";

import {
  directoryMismatches,
  insignificantApps,
  loadGraph,
  type MasdGraph,
  SLICED_LAYERS,
  TEST_FILE,
} from "../eslint/masd-graph.ts";
import { appFiles, subdirectories } from "./lib/import-graph.ts";
import { carriesMarker } from "./lib/masd-marker.ts";
import { cutGain, type Edge, importsOf, within } from "./lib/slice-graph.ts";
import { subSliceProblems } from "./lib/sub-slices/index.ts";

const SLICED = new Set(SLICED_LAYERS);
// The sliced layers Steiger checks; a page has nothing above it to be
// referenced by.
const CHECKED_LAYERS = SLICED_LAYERS.filter((layer) => layer !== "pages");

const ROOT = process.cwd();

const stays = (slice: string): boolean =>
  carriesMarker(path.join("src", slice, "index.ts"), "insignificant");

/**
 * Where a file sits: `<app>/<layer>/<slice>` in a sliced layer,
 * `<app>/<layer>` in a segmented one.
 */
function locate(file: string): string | undefined {
  const parts = file.split(path.sep);
  if (parts[0] !== "src" || parts.length < 4) return undefined;
  const [, app = "", layer = "", slice = ""] = parts;
  // An app's scripts and the tests are tooling, not consumers: a slice only
  // they reach is still one nothing shipped needs.
  if (layer === "scripts" || TEST_FILE.test(file)) return undefined;
  return SLICED.has(layer) ? `${app}/${layer}/${slice}` : `${app}/${layer}`;
}

// Every location under `src/` opens with its app.
const appOfLocation = (location: string): string =>
  location.slice(0, location.indexOf("/"));

/**
 * Whether a slice holds more of its app's import edges than chance would: its
 * term of Newman's modularity, `e − a²`, is positive — `e` the share of edges
 * with both ends in it, `a` the share of edge ends on it, so `a²` is what a
 * rewiring keeping every file's degree would put inside. That is the sign of
 * `cutGain`, whose two-way cut gains twice the part's term. `edges` are the
 * slice's own app's alone.
 */
function modular(slice: string, edges: readonly Edge[]): boolean {
  const directory = path.join("src", slice);
  const part = new Set(edges.flat().filter((file) => within(file, directory)));
  return cutGain(part, edges) > 0;
}

function graphProblems(graph: MasdGraph) {
  return [
    ...directoryMismatches(graph, subdirectories("src")),
    ...insignificantApps(graph).map(
      (app) => `masd: ${app} has exactly one child; fold it into its child`,
    ),
  ];
}

function sliceProblems(
  references: ReadonlyMap<string, ReadonlySet<string>>,
  edges: ReadonlyMap<string, readonly Edge[]>,
) {
  return [...references].flatMap(([slice, sources]) => {
    if (stays(slice)) return [];
    const [reference, ...others] = sources;
    if (reference === undefined) {
      return [
        `src/${slice}: This slice has no references. Consider removing it.`,
      ];
    }
    if (
      others.length > 0 ||
      modular(slice, edges.get(appOfLocation(slice)) ?? [])
    ) {
      return [];
    }
    const [, layer = "", sourceSlice] = reference.split("/");
    if (sourceSlice !== undefined) {
      return [
        `src/${slice}: This slice has only one reference in slice "${layer}/${sourceSlice}". Consider merging them.`,
      ];
    }
    return layer === "app"
      ? []
      : [
          `src/${slice}: This slice has only one reference on layer "${layer}". Consider moving this code to "${layer}".`,
        ];
  });
}

function check(): string[] {
  let graph: MasdGraph;
  try {
    graph = loadGraph(path.join(ROOT, "src", "masd.json"));
  } catch (error) {
    return [error instanceof Error ? error.message : String(error)];
  }

  const references = new Map<string, Set<string>>();
  for (const app of graph.keys()) {
    for (const layer of CHECKED_LAYERS) {
      const directory = path.join("src", app, layer);
      if (!existsSync(directory)) continue;
      for (const slice of subdirectories(directory)) {
        references.set(`${app}/${layer}/${slice}`, new Set());
      }
    }
  }

  const edges = new Map(
    [...graph.keys()].map((app): [string, Edge[]] => [app, []]),
  );
  const files = appFiles();
  for (const [file, imported] of importsOf(files)) {
    const source = locate(file);
    if (source === undefined) continue;
    const app = appOfLocation(source);
    for (const target of imported) {
      const location = locate(target);
      if (location === undefined) continue;
      if (appOfLocation(location) === app) edges.get(app)?.push([file, target]);
      if (location !== source) references.get(location)?.add(source);
    }
  }

  return [
    ...graphProblems(graph),
    ...sliceProblems(references, edges),
    ...subSliceProblems([...graph.keys()], files),
  ];
}

const problems = check();
for (const problem of problems) process.stderr.write(`${problem}\n`);
if (problems.length > 0) process.exitCode = 1;
