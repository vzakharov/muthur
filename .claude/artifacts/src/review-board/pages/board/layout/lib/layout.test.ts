import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type { Rect, Sized } from "#src/review-board/shared/lib/geometry.ts";
import { pack } from "./pack.ts";
import type { PackOptions } from "./pack.ts";
import { buildTree } from "./tree.ts";
import type { FolderNode } from "./tree.ts";

const opts: PackOptions = { headerHeight: 30, padding: 10, gap: 10 };
const measure = (): Sized => ({ width: 300, height: 200 });

const overlaps = (a: Rect, b: Rect): boolean =>
  a.x < b.x + b.width &&
  b.x < a.x + a.width &&
  a.y < b.y + b.height &&
  b.y < a.y + a.height;

const inside = (inner: Rect, outer: Rect): boolean =>
  inner.x >= outer.x &&
  inner.y >= outer.y &&
  inner.x + inner.width <= outer.x + outer.width &&
  inner.y + inner.height <= outer.y + outer.height;

const names = (folder: FolderNode): string[] =>
  folder.children.map((child) => child.name);

describe("buildTree", () => {
  it("collapses a chain of single-folder folders into one node", () => {
    const tree = buildTree([
      ".claude/skills/review-board/SKILL.md",
      ".claude/skills/review-board/run.ts",
    ]);
    assert.deepEqual(names(tree), [".claude/skills/review-board"]);
    const [folder] = tree.children;
    assert.equal(folder?.path, ".claude/skills/review-board");
  });

  it("stops collapsing where a folder branches or holds a file", () => {
    const tree = buildTree([
      "a/b/c/x.ts",
      "a/b/d/y.ts",
      "p/q/z.ts",
      "p/top.ts",
    ]);
    assert.deepEqual(names(tree), ["a/b", "p"]);
    const [ab, p] = tree.children;
    assert.deepEqual(ab?.kind === "folder" ? names(ab) : [], ["c", "d"]);
    assert.deepEqual(p?.kind === "folder" ? names(p) : [], ["q", "top.ts"]);
    const q = p?.kind === "folder" ? p.children[0] : undefined;
    assert.equal(q?.path, "p/q");
  });

  it("does not collapse a folder into its only file", () => {
    const tree = buildTree(["docs/readme.md"]);
    assert.deepEqual(names(tree), ["docs"]);
    const [docs] = tree.children;
    assert.deepEqual(docs?.kind === "folder" ? names(docs) : [], ["readme.md"]);
  });

  it("orders folders before files, each group by name, and ignores duplicates", () => {
    const tree = buildTree([
      "z.ts",
      "b/x.ts",
      "a.ts",
      "c/x.ts",
      "a/x.ts",
      "a.ts",
    ]);
    assert.deepEqual(names(tree), ["a", "b", "c", "a.ts", "z.ts"]);
  });

  it("names one folder path differently once its siblings drop out", () => {
    const moved = [
      "src/board/app/styles/board.scss",
      "src/board/scripts/board.ts",
      "src/board/scripts/lib/board-file.ts",
      "src/cube/scripts/play-cube.ts",
    ];
    const folderAt = (tree: FolderNode, path: string) =>
      pack(tree, measure, opts).folders.find((folder) => folder.path === path);
    assert.equal(
      folderAt(buildTree(moved), "src/board/scripts")?.name,
      "scripts",
    );
    assert.equal(
      folderAt(buildTree(moved.slice(1)), "src/board/scripts")?.name,
      "board/scripts",
    );
  });
});

describe("pack", () => {
  const paths = [
    "src/a/one.ts",
    "src/a/two.ts",
    "src/b/c/three.ts",
    "src/b/four.ts",
    "src/b/five.ts",
    "README.md",
  ];

  it("is deterministic", () => {
    assert.deepEqual(
      pack(buildTree(paths), measure, opts),
      pack(buildTree([...paths].reverse()), measure, opts),
    );
  });

  it("gives every file its measured size and every folder a header", () => {
    const packed = pack(buildTree(paths), measure, opts);
    assert.equal(packed.files.length, paths.length);
    for (const file of packed.files) {
      assert.equal(file.rect.width, 300);
      assert.equal(file.rect.height, 200);
    }
    for (const folder of packed.folders) {
      assert.deepEqual(folder.header, {
        x: folder.rect.x,
        y: folder.rect.y,
        width: folder.rect.width,
        height: opts.headerHeight,
      });
    }
  });

  it("keeps every child inside its parent, below the header, and siblings apart", () => {
    const tree = buildTree(paths);
    const packed = pack(tree, measure, opts);
    const rects = new Map<string, Rect>([
      ...packed.folders.map((f) => [f.path, f.rect] as const),
      ...packed.files.map((f) => [f.path, f.rect] as const),
    ]);
    const check = (folder: FolderNode): void => {
      const parent = rects.get(folder.path);
      const kids = folder.children.map((child) => {
        const rect = rects.get(child.path);
        assert.ok(rect, child.path);
        if (parent !== undefined) {
          assert.ok(inside(rect, parent), `${child.path} in ${folder.path}`);
          assert.ok(rect.y >= parent.y + opts.headerHeight);
        } else assert.ok(inside(rect, packed.bounds));
        return rect;
      });
      kids.forEach((a, i) => {
        kids.slice(i + 1).forEach((b) => {
          assert.ok(!overlaps(a, b));
        });
      });
      for (const child of folder.children)
        if (child.kind === "folder") check(child);
    };
    check(tree);
  });

  it("puts folders ahead of files in reading order", () => {
    const packed = pack(buildTree(["b.ts", "a/x.ts"]), measure, opts);
    const folder = packed.folders[0]?.rect;
    const file = packed.files.find((f) => f.path === "b.ts")?.rect;
    assert.ok(folder && file);
    assert.ok(folder.y < file.y || (folder.y === file.y && folder.x < file.x));
  });

  it("aims a many-file folder at a 16:10 frame", () => {
    const many = Array.from(
      { length: 40 },
      (_, i) => `dir/f${String(i).padStart(2, "0")}.ts`,
    );
    const packed = pack(buildTree(many), measure, opts);
    const dir = packed.folders[0];
    assert.ok(dir);
    const aspect = dir.rect.width / dir.rect.height;
    assert.ok(aspect > 1.3 && aspect < 1.9, `aspect ${aspect}`);
  });

  it("handles no files", () => {
    const packed = pack(buildTree([]), measure, opts);
    assert.deepEqual(packed.files, []);
    assert.deepEqual(packed.bounds, { x: 0, y: 0, width: 0, height: 0 });
  });
});
