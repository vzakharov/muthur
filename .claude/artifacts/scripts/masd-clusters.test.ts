/**
 * End-to-end tests for `pnpm masd:clusters`, after `masd-check.test.ts`: each
 * case writes a throwaway tree to the OS temp directory and runs the real script
 * there, which reads everything from its working directory.
 */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, it } from "node:test";

const SCRIPT = path.resolve(import.meta.dirname, "masd-clusters.ts");

/** Fixture files, keyed by path relative to the tree's root. */
type Tree = Record<string, string>;

const SLICE = "src/app/features/feed";

/** A file of the slice importing each of `imports`, relative to the slice. */
const importing = (...imports: string[]): string =>
  [
    ...imports.map((file, index) => `import * as m${index} from './${file}';`),
    `export const used = [${imports.map((_, index) => `m${index}`).join(", ")}];`,
  ].join("\n");

function run(tree: Tree): { status: number; stdout: string } {
  const dir = mkdtempSync(path.join(tmpdir(), "masd-clusters-"));
  for (const [file, text] of Object.entries(tree)) {
    const full = path.join(dir, file);
    mkdirSync(path.dirname(full), { recursive: true });
    writeFileSync(full, text);
  }
  const { error, status, stdout } = spawnSync(process.execPath, [SCRIPT], {
    cwd: dir,
    encoding: "utf8",
  });
  assert.equal(error, undefined);
  return { status: status ?? -1, stdout };
}

// The slice's door enters two subtrees: `top` with the files only it reaches,
// and `other` with its helper.
const FEED: Tree = {
  [`${SLICE}/index.ts`]: importing("ui/top.ts", "ui/other.ts"),
  [`${SLICE}/ui/top.ts`]: importing("x.ts", "../model/y.ts"),
  [`${SLICE}/ui/x.ts`]: importing("../model/y.ts"),
  [`${SLICE}/model/y.ts`]: "export const y = 1;",
  [`${SLICE}/ui/other.ts`]: importing("../lib/z.ts"),
  [`${SLICE}/lib/z.ts`]: "export const z = 1;",
};

// The same slice with `other` reaching `top`'s model too.
const SHARED_Y: Tree = {
  ...FEED,
  [`${SLICE}/ui/other.ts`]: importing("../lib/z.ts", "../model/y.ts"),
};

describe("masd:clusters", () => {
  it("prints the best subtree and each next one it does not overlap, and fails", () => {
    const { status, stdout } = run(FEED);
    assert.equal(status, 1);
    assert.equal(
      stdout,
      [
        `${SLICE} (6 files)`,
        "  ui/top.ts: 3 files, ΔQ 0.32",
        "    model/y.ts",
        "    ui/top.ts",
        "    ui/x.ts",
        "  ui/other.ts: 2 files, ΔQ 0.21",
        "    lib/z.ts",
        "    ui/other.ts",
        "1 of 1 slices and sub-slices hold a cluster.",
        'Cut each into a sub-slice entered by its root, and what it takes from the rest into a sub-slice of its own unless the rest is nothing more. Where one should stay, ask the operator, and on their yes put "// masd-disable cluster -- <why it stays>" in its root.',
        "",
      ].join("\n"),
    );
  });

  it("prints what a subtree takes from the rest, as the sub-slice below both", () => {
    const { stdout } = run(SHARED_Y);
    assert.match(
      stdout,
      /^ {4}ui\/x\.ts\n {4}it takes from the rest, a sub-slice below both:\n {6}model\/y\.ts$/m,
    );
  });

  it("reports a sub-slice as a unit of its own, and roots none of its files in the parent", () => {
    const TOP = `${SLICE}/top`;
    const { stdout } = run({
      [`${SLICE}/index.ts`]: importing("top/index.ts", "ui/other.ts"),
      [`${TOP}/index.ts`]: importing("ui/top.ts", "ui/side.ts"),
      [`${TOP}/ui/top.ts`]: importing("x.ts", "../model/y.ts"),
      [`${TOP}/ui/x.ts`]: importing("../model/y.ts"),
      [`${TOP}/model/y.ts`]: "export const y = 1;",
      [`${TOP}/ui/side.ts`]: importing("../lib/q.ts"),
      [`${TOP}/lib/q.ts`]: "export const q = 1;",
      [`${SLICE}/ui/other.ts`]: importing("../lib/z.ts"),
      [`${SLICE}/lib/z.ts`]: "export const z = 1;",
    });
    assert.ok(stdout.startsWith(`${TOP} (6 files)\n  ui/top.ts:`), stdout);
    assert.doesNotMatch(stdout, /^ {2}top\//m);
    assert.match(stdout, /^1 of 2 slices and sub-slices hold a cluster\.$/m);
  });

  it("leaves out of a subtree a file the rest of the slice reaches too", () => {
    const { stdout } = run(SHARED_Y);
    assert.match(stdout, /^ {2}ui\/top\.ts: 2 files,/m);
    assert.doesNotMatch(stdout, /^ {4}model\/y\.ts$/m);
  });

  it("drops a cut whose rest is no unit: one file, or files apart", () => {
    const page: Tree = {
      [`${SLICE}/ui/page.ts`]: importing("player.ts"),
      [`${SLICE}/ui/player.ts`]: importing("../model/a.ts", "../model/b.ts"),
      [`${SLICE}/model/a.ts`]: importing("b.ts"),
      [`${SLICE}/model/b.ts`]: "export const b = 1;",
    };
    const thin = run({
      ...page,
      [`${SLICE}/index.ts`]: importing("ui/page.ts"),
    });
    assert.equal(thin.status, 0, thin.stdout);
    const apart = run({
      ...page,
      [`${SLICE}/index.ts`]: importing("ui/page.ts", "lib/meta.ts"),
      [`${SLICE}/lib/meta.ts`]: "export const meta = 1;",
    });
    assert.equal(apart.status, 0, apart.stdout);
  });

  it("lets a cluster stay whose root carries the marker", () => {
    const { status, stdout } = run({
      ...FEED,
      [`${SLICE}/ui/top.ts`]: `// masd-disable cluster -- the operator keeps it whole\n${importing("x.ts", "../model/y.ts")}`,
      [`${SLICE}/ui/other.ts`]: `// masd-disable cluster -- likewise\n${importing("../lib/z.ts")}`,
    });
    assert.equal(status, 0, stdout);
  });

  it("drops a closure made of whole segments", () => {
    const { stdout } = run({
      [`${SLICE}/index.ts`]: importing("ui/top.ts", "ui/other.ts", "lib/z.ts"),
      [`${SLICE}/ui/top.ts`]: importing("x.ts"),
      [`${SLICE}/ui/x.ts`]: "export const x = 1;",
      [`${SLICE}/ui/other.ts`]: importing("../lib/z.ts"),
      [`${SLICE}/lib/z.ts`]: importing("q.ts"),
      [`${SLICE}/lib/q.ts`]: "export const q = 1;",
    });
    assert.match(stdout, /^ {2}ui\/top\.ts:/m);
    assert.doesNotMatch(stdout, /lib\/z\.ts:/);
  });

  it("reads no test code as part of a slice", () => {
    const { stdout } = run({
      ...FEED,
      [`${SLICE}/index.test-only.ts`]: importing("ui/x.ts"),
      [`${SLICE}/ui/x.test.ts`]: importing("x.ts", "top.ts"),
    });
    assert.equal(stdout, run(FEED).stdout);
  });

  it("reports a slice with no cluster as none", () => {
    const { status, stdout } = run({
      [`${SLICE}/index.ts`]: importing("ui/a.ts", "ui/b.ts"),
      [`${SLICE}/ui/a.ts`]: "export const a = 1;",
      [`${SLICE}/ui/b.ts`]: "export const b = 1;",
    });
    assert.equal(status, 0);
    assert.equal(stdout, "0 of 1 slices and sub-slices hold a cluster.\n");
  });
});
