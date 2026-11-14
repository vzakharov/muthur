import assert from "node:assert/strict";
import { test } from "node:test";
import type { ReviewFile } from "#src/review-board/shared/review-data/index.ts";
import {
  baseMerges,
  commitOrder,
  effectiveRange,
  snapToRevision,
  viewedToken,
} from "./range.ts";

const commit = (sha: string) => ({
  sha,
  subject: sha,
  author: "a",
  date: "2026-01-01T00:00:00Z",
  baseMerge: false,
});
const order = commitOrder({
  base: { ref: "main", sha: "B" },
  commits: ["c0", "c1", "c2", "c3"].map(commit),
});

// Touched by c1 and c3 only.
const file: ReviewFile = {
  path: "a.ts",
  oldPath: null,
  status: "modified",
  binary: false,
  revisions: [
    { commit: "B", path: "f", blob: "b0", size: 1 },
    { commit: "c1", path: "f", blob: "b1", size: 1 },
    { commit: "c3", path: "f", blob: "b3", size: 1 },
  ],
};
const whole = { from: null, to: null };

test("the default is base to the file's last revision", () => {
  const range = effectiveRange({ file, order, board: whole });
  assert.deepEqual(range, {
    from: "B",
    to: "c3",
    fromBlob: "b0",
    toBlob: "b3",
    fromExplicit: false,
    toExplicit: false,
    viewed: false,
    viewedMark: null,
  });
});

test("a board commit that did not touch the file snaps to the latest revision at or before it", () => {
  assert.equal(snapToRevision(file, order, "c2")?.commit, "c1");
  assert.equal(snapToRevision(file, order, "c0")?.commit, "B");
  assert.equal(snapToRevision(file, order, "nope"), undefined);
  const range = effectiveRange({
    file,
    order,
    board: { from: "c1", to: "c2" },
  });
  assert.equal(range.from, "c1");
  assert.equal(range.to, "c1");
});

test("an unknown board commit falls back to the default end", () => {
  const range = effectiveRange({
    file,
    order,
    board: { from: "gone", to: "gone" },
  });
  assert.equal(range.from, "B");
  assert.equal(range.to, "c3");
});

test("the override replaces the board range per end", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    override: { from: "c1", to: null, at: "2026-01-02T00:00:00Z" },
  });
  assert.equal(range.from, "c1");
  assert.equal(range.fromExplicit, true);
  assert.equal(range.to, "c3");
  assert.equal(range.toExplicit, false);
});

test("a newer shift beats the override and leaves `to` on the board", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    override: { from: "B", to: "c1", at: "2026-01-02T00:00:00Z" },
    shift: { from: "c1", at: "2026-01-03T00:00:00Z" },
  });
  assert.equal(range.from, "c1");
  assert.equal(range.to, "c3");
  assert.equal(range.toExplicit, false);
});

test("a newer override beats the shift", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    override: { from: "B", to: "c1", at: "2026-01-04T00:00:00Z" },
    shift: { from: "c3", at: "2026-01-03T00:00:00Z" },
  });
  assert.deepEqual([range.from, range.to], ["B", "c1"]);
});

test("an override with both ends null is only a stamp and yields to a shift", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    override: { from: null, to: null, at: "2026-01-09T00:00:00Z" },
    shift: { from: "c1", at: "2026-01-03T00:00:00Z" },
  });
  assert.equal(range.from, "c1");
});

test("a shift to a commit outside the branch is ignored", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    shift: { from: "gone", at: "2026-01-03T00:00:00Z" },
  });
  assert.equal(range.from, "B");
});

test("a shift snaps to the file's revisions", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    shift: { from: "c2", at: "2026-01-03T00:00:00Z" },
  });
  assert.equal(range.from, "c1");
});

test("a from past the to is pulled back onto it", () => {
  const range = effectiveRange({
    file,
    order,
    board: { from: null, to: "c1" },
    override: { from: "c3", to: null, at: "2026-01-02T00:00:00Z" },
  });
  assert.deepEqual([range.from, range.to], ["c1", "c1"]);
  const clamped = effectiveRange({
    file,
    order,
    board: { from: null, to: "c1" },
    shift: { from: "c3", at: "2026-01-02T00:00:00Z" },
  });
  assert.deepEqual([clamped.from, clamped.to], ["c1", "c1"]);
});

test("a file absent at its last commit reports a null blob", () => {
  const deleted: ReviewFile = {
    ...file,
    status: "deleted",
    revisions: [
      { commit: "B", path: "f", blob: "b0", size: 1 },
      { commit: "c2", path: "f", blob: null, size: null },
    ],
  };
  const range = effectiveRange({ file: deleted, order, board: whole });
  assert.equal(range.toBlob, null);
});

test("viewed means the marked blob is the one now shown", () => {
  const viewedAs = (viewedBlob: string | null, target: ReviewFile = file) =>
    effectiveRange({
      file: target,
      order,
      board: whole,
      viewedBlobs: new Set(viewedBlob === null ? [] : [viewedBlob]),
    }).viewed;
  assert.equal(viewedAs("b3"), true);
  assert.equal(viewedAs("b1"), false);
  assert.equal(viewedAs(null), false);
  const deleted: ReviewFile = {
    ...file,
    revisions: [
      { commit: "B", path: "f", blob: "b0", size: 1 },
      { commit: "c2", path: "f", blob: null, size: null },
    ],
  };
  assert.equal(viewedAs(viewedToken(null), deleted), true);
  assert.equal(viewedAs(viewedToken(null)), false);
});

// c1 and c3 merge the base in; the file is touched by c0, both merges and c2.
const merged = {
  base: { ref: "main", sha: "B" },
  commits: ["c0", "c1", "c2", "c3"].map((sha) => ({
    ...commit(sha),
    baseMerge: sha === "c1" || sha === "c3",
  })),
};
const mergedFile: ReviewFile = {
  ...file,
  revisions: [
    { commit: "B", path: "f", blob: "b0", size: 1 },
    { commit: "c0", path: "f", blob: "m0", size: 1 },
    { commit: "c1", path: "f", blob: "m1", size: 1 },
    { commit: "c2", path: "f", blob: "m2", size: 1 },
    { commit: "c3", path: "f", blob: "m3", size: 1 },
  ],
};
const acrossMerges = (viewedBlob: string, to: string | null = null) =>
  effectiveRange({
    file: mergedFile,
    order: commitOrder(merged),
    merges: baseMerges(merged),
    board: { from: null, to },
    viewedBlobs: new Set([viewedBlob]),
  });

test("a file only base merges changed since it was viewed stays viewed", () => {
  const range = acrossMerges("m0", "c1");
  assert.equal(range.viewed, true);
  assert.equal(range.fromExplicit, false);
  assert.equal(range.viewedMark, "m0");
});

test("a file changed after a base merge diffs from the merge", () => {
  const range = acrossMerges("m0", "c2");
  assert.equal(range.viewed, false);
  assert.equal(range.viewedMark, null);
  assert.deepEqual([range.from, range.to], ["c1", "c2"]);
});

test("a base merge after the branch's own change does not hide that change", () => {
  const range = acrossMerges("m1");
  assert.equal(range.viewed, false);
  assert.deepEqual([range.from, range.to], ["c1", "c3"]);
});

test("a file viewed at an earlier revision shows only what changed since", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    viewedBlobs: new Set(["b1"]),
  });
  assert.equal(range.from, "c1");
  assert.equal(range.to, "c3");
  assert.equal(range.fromExplicit, true);
});

test("a file viewed at its shown revision keeps the board's range", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    viewedBlobs: new Set(["b3"]),
  });
  assert.equal(range.from, "B");
  assert.equal(range.fromExplicit, false);
});

test("a viewed revision at or before the range's start changes nothing", () => {
  const range = effectiveRange({
    file,
    order,
    board: { from: "c1", to: null },
    viewedBlobs: new Set(["b0"]),
  });
  assert.equal(range.from, "c1");
});

test("with several marked revisions the base is the latest before to", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    viewedBlobs: new Set(["b0", "b1"]),
  });
  assert.equal(range.from, "c1");
  assert.equal(range.viewed, false);
});

test("a mark on to makes the file viewed and keeps the board's base", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    viewedBlobs: new Set(["b1", "b3"]),
  });
  assert.equal(range.viewed, true);
  assert.equal(range.from, "B");
});

test("moving to back to a marked revision shows that revision as viewed", () => {
  const range = effectiveRange({
    file,
    order,
    board: { from: null, to: "c1" },
    viewedBlobs: new Set(["b1", "b3"]),
  });
  assert.equal(range.viewed, true);
  assert.equal(range.to, "c1");
});

test("the viewer's own from outranks the viewed revision", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    override: { from: "B", to: null, at: "2026-01-02T00:00:00Z" },
    viewedBlobs: new Set(["b1"]),
  });
  assert.equal(range.from, "B");
});

test("a later viewed revision outranks an earlier shift", () => {
  const range = effectiveRange({
    file,
    order,
    board: whole,
    shift: { from: "B", at: "2026-01-02T00:00:00Z" },
    viewedBlobs: new Set(["b1"]),
  });
  assert.equal(range.from, "c1");
});
