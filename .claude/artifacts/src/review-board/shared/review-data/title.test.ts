import assert from "node:assert/strict";
import { test } from "node:test";
import { boardTitle } from "./title.ts";

test("the title names the PR and the branch", () => {
  assert.equal(boardTitle("feat/board", 42), "Review #42 · feat/board");
});

test("a branch with no PR is named alone", () => {
  assert.equal(boardTitle("feat/board", null), "Review · feat/board");
});

test("a detached HEAD falls back to the PR, then to the generic name", () => {
  assert.equal(boardTitle("", 7), "Review #7");
  assert.equal(boardTitle("", null), "Review board");
});
