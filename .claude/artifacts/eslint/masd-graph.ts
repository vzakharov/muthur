/**
 * The app graph of Multi-App Sliced Design — `src/masd.json`, each app naming
 * its parents — and the questions every reader of it asks. The only loader of
 * that file: the boundaries config, `lint:fsd`'s per-app runs and
 * `scripts/masd-check.ts` all go through it.
 *
 * Importers reach it by relative path: it sits outside `src/`, where the `#src/`
 * alias does not point.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";

/** The specifier prefix package.json `imports` maps to `./src/`. */
export const SRC_ALIAS = "#src/";

/** FSD's sliced layers, highest first; `app` and `shared` are segmented. */
export const SLICED_LAYERS = ["pages", "widgets", "features", "entities"];

/** FSD's layers, highest first. */
export const LAYERS = ["app", ...SLICED_LAYERS, "shared"];

/**
 * The segments a slice is cut into: FSD's standard ones, a slice's catalogue
 * being `config/i18n.ts`. Any other folder directly in a slice or a sub-slice
 * is a sub-slice.
 */
export const SEGMENTS = ["ui", "model", "lib", "api", "config"];

/**
 * The sub-slices a file below a slice root sits in, outermost first, as their
 * paths from that root: the folders leading its path before the first segment.
 * `dirs` are the folders between the slice root and the file.
 */
export function subSlicePath(dirs: readonly string[]): string[] {
  const segment = dirs.findIndex((dir) => SEGMENTS.includes(dir));
  return dirs
    .slice(0, segment === -1 ? dirs.length : segment)
    .map((_, index) => dirs.slice(0, index + 1).join("/"));
}

/**
 * A slice's or a segment's entry points. A closed list, so any other
 * `index.*.ts` is still reaching into internals.
 */
export const PUBLIC_API = ["index.ts"];

/** Whether `file`'s name is one of `PUBLIC_API`'s, whatever folder holds it. */
export const isPublicApi = (file: string): boolean =>
  PUBLIC_API.includes(path.basename(file));

/** The entry point only test code may take, beside the public API. */
export const TEST_API = "index.test-only.ts";

/** What several tests of a slice share, imported by test code alone. */
export const TEST_KIT = "**/*.test-kit.ts";

/** Test code: the tests, and the kits they share. */
export const TEST_CODE = ["**/*.test.ts", TEST_KIT];

/** `TEST_CODE`'s files, for a reader matching a path rather than a glob. */
export const TEST_FILE = /\.test(-kit)?\.tsx?$/;

/** Test code, its own entry into a slice included. */
export const isTest = (file: string): boolean =>
  TEST_FILE.test(file) || path.basename(file) === TEST_API;

const GRAPH_FILE = path.resolve(import.meta.dirname, "..", "src", "masd.json");

// Kebab-case also keeps every key non-numeric, which is what makes JS hand the
// keys back in the order they were written.
const appName = z
  .string()
  .regex(/^[a-z][\da-z-]*$/, "an app name is kebab-case");

const graphSchema = z.record(appName, z.array(appName));

/** App → its parents, in the order the file declares the apps. */
export type MasdGraph = ReadonlyMap<string, readonly string[]>;

/**
 * Validates a parsed graph. A parent declared above its child is the whole of
 * the acyclicity check: a cycle needs some app whose parent comes after it.
 */
export function parseGraph(raw: unknown): MasdGraph {
  const graph = new Map(Object.entries(graphSchema.parse(raw)));
  const seen = new Set<string>();
  for (const [app, parents] of graph) {
    for (const parent of parents) {
      if (!graph.has(parent)) {
        throw new Error(`masd: ${app} names ${parent}, which is no app`);
      }
      if (!seen.has(parent)) {
        throw new Error(
          `masd: ${app} is declared above its parent ${parent}; a parent comes first`,
        );
      }
    }
    if (new Set(parents).size !== parents.length) {
      throw new Error(`masd: ${app} names a parent twice`);
    }
    seen.add(app);
  }
  return graph;
}

export function loadGraph(file: string = GRAPH_FILE): MasdGraph {
  return parseGraph(JSON.parse(readFileSync(file, "utf8")));
}

/** Every app `app` inherits from, transitively; `app` itself excluded. */
export function ancestors(graph: MasdGraph, app: string): ReadonlySet<string> {
  const found = new Set<string>();
  const pending = [...(graph.get(app) ?? [])];
  for (let next = pending.pop(); next !== undefined; next = pending.pop()) {
    if (found.has(next)) continue;
    found.add(next);
    pending.push(...(graph.get(next) ?? []));
  }
  return found;
}

/** Every app inheriting from `app`, transitively; `app` itself excluded. */
export function descendants(
  graph: MasdGraph,
  app: string,
): ReadonlySet<string> {
  return new Set(
    [...graph.keys()].filter((other) => ancestors(graph, other).has(app)),
  );
}

/** Apps earned no better than an insignificant slice: exactly one child. */
export function insignificantApps(graph: MasdGraph): string[] {
  return [...graph.keys()].filter(
    (app) =>
      [...graph.values()].filter((parents) => parents.includes(app)).length ===
      1,
  );
}

/** The apps the graph and `src/`'s directories disagree on, as messages. */
export function directoryMismatches(
  graph: MasdGraph,
  directories: readonly string[],
): string[] {
  return [
    ...[...graph.keys()]
      .filter((app) => !directories.includes(app))
      .map((app) => `masd: ${app} is in the graph but has no directory`),
    ...directories
      .filter((directory) => !graph.has(directory))
      .map((directory) => `masd: src/${directory} is not in the graph`),
  ];
}
