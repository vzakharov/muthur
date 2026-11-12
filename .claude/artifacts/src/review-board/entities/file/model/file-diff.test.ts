import assert from "node:assert/strict";
import { test } from "node:test";
import type {
  ReviewData,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import { fileDiff } from "./file-diff.ts";
import type { EffectiveRange } from "./range.ts";

const data: ReviewData = {
  repo: null,
  branch: "b",
  pr: null,
  head: "c1",
  base: { ref: "main", sha: "B" },
  collectedAt: "t",
  commits: [],
  files: [],
  focus: [],
  blobs: { old: "a\nb\n", next: "a\nc\n" },
};
const file: ReviewFile = {
  path: "x.txt",
  oldPath: null,
  status: "modified",
  binary: false,
  revisions: [
    { commit: "B", path: "f", blob: "old", size: 4 },
    { commit: "c1", path: "f", blob: "next", size: 4 },
  ],
};
const range = (fromBlob: string | null, toBlob: string | null) =>
  ({
    from: "B",
    to: "c1",
    fromBlob,
    toBlob,
    fromExplicit: false,
    toExplicit: false,
    viewed: false,
    viewedMark: null,
  }) satisfies EffectiveRange;

test("diffs the two blobs of the range", () => {
  const result = fileDiff(data, file, range("old", "next"), false);
  assert.equal(result.kind, "text");
  assert.equal(result.diff.added, 1);
  assert.equal(result.diff.removed, 1);
});

test("after is the text at the range's to, null where absent", () => {
  const shown = fileDiff(data, file, range("old", "next"), false);
  assert.equal(shown.kind === "text" && shown.after, "a\nc\n");
  const gone = fileDiff(data, file, range("old", null), false);
  assert.equal(gone.kind === "text" && gone.after, null);
});

test("an absent side is empty text", () => {
  const added = fileDiff(data, file, range(null, "next"), false);
  assert.equal(added.kind === "text" && added.diff.added, 2);
  const deleted = fileDiff(data, file, range("old", null), false);
  assert.equal(deleted.kind === "text" && deleted.diff.removed, 2);
});

test("a binary file reports its sizes", () => {
  const binary: ReviewFile = {
    ...file,
    binary: true,
    revisions: [
      { commit: "B", path: "f", blob: "x", size: 10 },
      { commit: "c1", path: "f", blob: "y", size: 30 },
    ],
  };
  assert.deepEqual(fileDiff(data, binary, range("x", "y"), false), {
    kind: "binary",
    fromSize: 10,
    toSize: 30,
  });
});

test("a file with no known grammar has no syntax", () => {
  const result = fileDiff(data, file, range("old", "next"), false);
  assert.equal(result.kind, "text");
  assert.equal(result.syntax(), null);
});

test("a known grammar highlights each side, an absent one as no lines", () => {
  const code: ReviewFile = { ...file, path: "x.ts" };
  const blobs = { ...data.blobs, ts: "const a = 1;\n" };
  const result = fileDiff({ ...data, blobs }, code, range(null, "ts"), false);
  assert.equal(result.kind, "text");
  const syntax = result.syntax();
  assert.ok(syntax !== null);
  assert.deepEqual(syntax.old, []);
  const first = syntax.new[0] ?? [];
  assert.equal(first.map((token) => token.text).join(""), "const a = 1;");
  assert.ok(first.some((token) => token.scope === "hljs-keyword"));
});

test("a blob missing from the payload is an error", () => {
  assert.throws(() => fileDiff(data, file, range("old", "ghost"), false));
});
