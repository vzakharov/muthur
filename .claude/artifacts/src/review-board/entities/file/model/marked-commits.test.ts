import assert from "node:assert/strict";
import { test } from "node:test";
import type { ReviewFile } from "#src/review-board/shared/review-data/index.ts";
import { markedCommits } from "./marked-commits.ts";

const file: ReviewFile = {
  path: "a",
  oldPath: null,
  status: "modified",
  binary: false,
  revisions: [
    { commit: "c1", path: "f", blob: "b1", size: 1 },
    { commit: "c2", path: "f", blob: "b2", size: 1 },
    { commit: "c3", path: "f", blob: "b2", size: 1 },
  ],
};

test("a commit is marked when its blob carries a Viewed mark", () => {
  const marked = markedCommits(file, new Map([["b1", "t1"]]));
  assert.deepEqual([...marked], [["c1", "t1"]]);
});

test("commits sharing a marked blob are all marked", () => {
  const marked = markedCommits(file, new Map([["b2", "t2"]]));
  assert.deepEqual(
    [...marked],
    [
      ["c2", "t2"],
      ["c3", "t2"],
    ],
  );
});

test("no marks, no marked commits", () => {
  assert.equal(markedCommits(file, new Map()).size, 0);
});
