import assert from "node:assert/strict";
import { test } from "node:test";
import type { ReviewFile } from "#src/review-board/shared/review-data/index.ts";
import { matchesPath } from "./path-filter.ts";

const file = (path: string, oldPath: string | null = null): ReviewFile => ({
  path,
  oldPath,
  status: oldPath === null ? "modified" : "renamed",
  binary: false,
  revisions: [{ commit: "c", path: "f", blob: "b", size: 1 }],
});

test("an empty or blank query passes every file", () => {
  assert.equal(matchesPath(file("a/b.ts"), ""), true);
  assert.equal(matchesPath(file("a/b.ts"), "   "), true);
});

test("the query is a case-insensitive substring of the full path, folders included", () => {
  const target = file("src/Review-Board/pages/Card.ts");
  assert.equal(matchesPath(target, "card"), true);
  assert.equal(matchesPath(target, "review-board/pages"), true);
  assert.equal(matchesPath(target, "src/review-board/pages/card.ts"), true);
  assert.equal(matchesPath(target, "toolbar"), false);
});

test("a renamed file also matches its old path", () => {
  const renamed = file("new/name.ts", "old/place.ts");
  assert.equal(matchesPath(renamed, "old/place"), true);
  assert.equal(matchesPath(renamed, "new/name"), true);
  assert.equal(matchesPath(renamed, "elsewhere"), false);
});
