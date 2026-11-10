import assert from "node:assert/strict";
import { test } from "node:test";

import {
  ANCHOR_BYTES,
  decodeAnchor,
  encodeAnchor,
  type LineAnchor,
} from "./anchor.ts";

const FROM = "0123456789abcdef0123456789abcdef01234567";
const TO = "fedcba9876543210fedcba9876543210fedcba98";
const bytes = (text: string): number => new TextEncoder().encode(text).length;

test("a short anchor names the path, the range and the line", () => {
  const anchor = encodeAnchor({
    path: "src/a.ts",
    from: FROM,
    to: TO,
    side: "R",
    line: 12,
  });
  assert.equal(anchor, "src/a.ts@0123456..fedcba9:R12");
  assert.deepEqual(decodeAnchor(anchor, ["src/a.ts", "src/b.ts"]), {
    path: "src/a.ts",
    from: "0123456",
    to: "fedcba9",
    side: "R",
    line: 12,
  });
});

test("a file-level anchor carries no line", () => {
  const whole: LineAnchor = {
    path: "a b/c@d.md",
    from: FROM,
    to: TO,
    side: null,
    line: null,
  };
  const anchor = encodeAnchor(whole);
  assert.equal(anchor, "a b/c@d.md@0123456..fedcba9");
  assert.deepEqual(decodeAnchor(anchor, ["a b/c@d.md"]), {
    ...whole,
    from: "0123456",
    to: "fedcba9",
  });
});

test("a long path loses whole segments from the left", () => {
  const path = `${"deep/".repeat(30)}tail/file.ts`;
  const anchor = encodeAnchor({ path, from: FROM, to: TO, side: "L", line: 3 });
  assert.ok(bytes(anchor) <= ANCHOR_BYTES);
  assert.match(anchor, /^…\/(deep\/)*tail\/file\.ts@0123456\.\.fedcba9:L3$/);
  assert.equal(decodeAnchor(anchor, ["x/file.ts", path])?.path, path);
});

test("a file name past the budget keeps its last characters", () => {
  const path = `dir/${"n".repeat(200)}.ts`;
  const anchor = encodeAnchor({ path, from: FROM, to: TO, side: "R", line: 1 });
  assert.ok(bytes(anchor) <= ANCHOR_BYTES);
  assert.equal(decodeAnchor(anchor, [path])?.path, path);
});

test("multi-byte paths are measured in bytes", () => {
  const path = `${"путь/".repeat(20)}файл.ts`;
  const anchor = encodeAnchor({ path, from: FROM, to: TO, side: "R", line: 9 });
  assert.ok(bytes(anchor) <= ANCHOR_BYTES);
  assert.equal(decodeAnchor(anchor, [path])?.path, path);
});

test("anchors the board did not mint decode to nothing", () => {
  assert.equal(decodeAnchor("body > div:nth-child(2)", ["a.ts"]), undefined);
  assert.equal(decodeAnchor("a.ts@0123456..fedcba9:R0", ["a.ts"]), undefined);
  assert.equal(decodeAnchor("gone.ts@0123456..fedcba9", ["a.ts"]), undefined);
});
