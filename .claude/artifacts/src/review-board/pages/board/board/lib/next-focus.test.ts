import assert from "node:assert/strict";
import { test } from "node:test";
import { nextFocus } from "./next-focus.ts";

test("the first step lands on the first unviewed item", () => {
  assert.equal(nextFocus(null, [false, false]), 0);
  assert.equal(nextFocus(null, [true, false, false]), 1);
});

test("a step skips viewed items and wraps around", () => {
  assert.equal(nextFocus(0, [false, true, false]), 2);
  assert.equal(nextFocus(2, [false, true, false]), 0);
  assert.equal(nextFocus(1, [true, false, true]), 1);
});

test("once every item is viewed, steps go through them all in turn", () => {
  assert.equal(nextFocus(null, [true, true]), 0);
  assert.equal(nextFocus(0, [true, true]), 1);
  assert.equal(nextFocus(1, [true, true]), 0);
});

test("no items, no step", () => {
  assert.equal(nextFocus(null, []), null);
});
