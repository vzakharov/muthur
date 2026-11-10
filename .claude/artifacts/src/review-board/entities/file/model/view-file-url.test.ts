import assert from "node:assert/strict";
import { test } from "node:test";
import type {
  ReviewData,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import type { EffectiveRange } from "./range.ts";
import { viewFileUrl } from "./view-file-url.ts";

const data: ReviewData = {
  repo: "o/r",
  branch: "b",
  head: "c1",
  base: { ref: "main", sha: "B" },
  collectedAt: "t",
  commits: [],
  files: [],
  focus: [],
  blobs: {},
};
const file: ReviewFile = {
  path: "docs/a b.md",
  oldPath: null,
  status: "modified",
  binary: false,
  revisions: [],
};
const range = (
  to: string,
  fromBlob: string | null,
  toBlob: string | null,
): EffectiveRange => ({
  from: "B",
  to,
  fromBlob,
  toBlob,
  fromExplicit: false,
  toExplicit: false,
  viewed: false,
  viewedMark: null,
});

test("links the file at the range's to commit, path encoded per segment", () => {
  assert.equal(
    viewFileUrl(data, file, range("c1", "x", "y")),
    "https://github.com/o/r/blob/c1/docs/a%20b.md",
  );
});

test("a file absent at to links its from version", () => {
  assert.equal(
    viewFileUrl(data, file, range("c1", "x", null)),
    "https://github.com/o/r/blob/B/docs/a%20b.md",
  );
});

test("a rename's base version is under the old path", () => {
  assert.equal(
    viewFileUrl(
      data,
      { ...file, path: "n.md", oldPath: "o.md" },
      range("c1", "x", null),
    ),
    "https://github.com/o/r/blob/B/o.md",
  );
});

test("no repository, or no version at all, is no link", () => {
  assert.equal(
    viewFileUrl({ ...data, repo: null }, file, range("c1", "x", "y")),
    null,
  );
  assert.equal(viewFileUrl(data, file, range("c1", null, null)), null);
});
