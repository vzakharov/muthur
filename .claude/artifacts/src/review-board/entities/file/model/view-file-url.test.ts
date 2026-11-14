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
  pr: null,
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
  revisions: [
    { commit: "B", path: "docs/a b.md", blob: "x", size: 1 },
    { commit: "c1", path: "docs/a b.md", blob: "y", size: 1 },
  ],
};
const range = (
  to: string,
  fromBlob: string | null,
  toBlob: string | null,
  from = "B",
): EffectiveRange => ({
  from,
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

test("a renamed file's versions before the rename are under the old path", () => {
  const renamed: ReviewFile = {
    ...file,
    path: "n.md",
    oldPath: "o.md",
    status: "renamed",
    revisions: [
      { commit: "B", path: "o.md", blob: "x", size: 1 },
      { commit: "c1", path: "o.md", blob: "y", size: 1 },
      { commit: "c2", path: "n.md", blob: "z", size: 1 },
    ],
  };
  assert.equal(
    viewFileUrl(data, renamed, range("c1", "x", "y")),
    "https://github.com/o/r/blob/c1/o.md",
  );
  assert.equal(
    viewFileUrl(data, renamed, range("c2", "y", "z", "c1")),
    "https://github.com/o/r/blob/c2/n.md",
  );
});

test("no repository, or no version at all, is no link", () => {
  assert.equal(
    viewFileUrl({ ...data, repo: null }, file, range("c1", "x", "y")),
    null,
  );
  assert.equal(viewFileUrl(data, file, range("c1", null, null)), null);
});
