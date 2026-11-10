/**
 * The harness for `pnpm check:masd`'s end-to-end tests: each case writes a
 * throwaway tree to the OS temp directory and runs the real script there,
 * which reads everything from its working directory.
 */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const SCRIPT = path.resolve(import.meta.dirname, "masd-check.ts");

/** Fixture files, keyed by path relative to the tree's root. */
export type Tree = Record<string, string>;

// kernel ← blog ← site, kernel ← game: `blog` has one child, so the graph is
// only clean with a second one — `other`.
const GRAPH = JSON.stringify({
  kernel: [],
  blog: ["kernel"],
  site: ["blog"],
  other: ["blog"],
  game: ["kernel"],
});

const BASE: Tree = {
  "src/masd.json": GRAPH,
  "src/kernel/shared/ui/index.ts": "export const ui = 1;",
  "src/blog/pages/documents/index.ts": "export const documents = 1;",
  "src/site/pages/home/index.ts": "export const home = 1;",
  "src/other/pages/about/index.ts": "export const about = 1;",
  "src/game/pages/play/index.ts": "export const play = 1;",
};

/** Runs the check over the base tree with `tree`'s files laid over it. */
export function run(tree: Tree): { status: number; stderr: string } {
  const dir = mkdtempSync(path.join(tmpdir(), "masd-check-"));
  for (const [file, text] of Object.entries({ ...BASE, ...tree })) {
    const full = path.join(dir, file);
    mkdirSync(path.dirname(full), { recursive: true });
    writeFileSync(full, text);
  }
  const { error, status, stderr } = spawnSync(process.execPath, [SCRIPT], {
    cwd: dir,
    encoding: "utf8",
  });
  assert.equal(error, undefined);
  return { status: status ?? -1, stderr };
}
