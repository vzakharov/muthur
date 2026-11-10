import assert from "node:assert/strict";
import { test } from "node:test";
import { lineCount, parseFocus } from "./focus.ts";

const counts = new Map<string, number | null>([
  ["src/a.ts", 40],
  ["logo.png", null],
]);

const parse = (entries: unknown): ReturnType<typeof parseFocus> =>
  parseFocus(JSON.stringify(entries), counts);

test("keeps valid entries as written", () => {
  const entries = [
    { path: "src/a.ts", why: "the new state machine", lines: [[3, 12]] },
    { path: "logo.png", why: "the brand change" },
  ];
  assert.deepEqual(parse(entries), entries);
});

test("rejects a path that is not among the changed files", () => {
  assert.throws(
    () => parse([{ path: "src/b.ts", why: "x" }]),
    /not among the changed files/,
  );
});

test("rejects a path listed twice", () => {
  assert.throws(
    () =>
      parse([
        { path: "src/a.ts", why: "x" },
        { path: "src/a.ts", why: "y" },
      ]),
    /listed twice/,
  );
});

test("rejects an empty reason", () => {
  assert.throws(() => parse([{ path: "src/a.ts", why: " " }]), /no reason/);
});

test("rejects lines outside the file or running backwards", () => {
  for (const lines of [[[0, 3]], [[5, 4]], [[30, 41]], [[1.5, 3]]]) {
    assert.throws(
      () => parse([{ path: "src/a.ts", why: "x", lines }]),
      /not within its 40 lines/,
    );
  }
});

test("rejects lines in a file with no text at HEAD", () => {
  assert.throws(
    () => parse([{ path: "logo.png", why: "x", lines: [[1, 2]] }]),
    /no text at HEAD/,
  );
});

test("rejects a file that is not a list of entries", () => {
  assert.throws(() => parse({ path: "src/a.ts", why: "x" }));
});

test("counts lines with and without a final newline", () => {
  assert.equal(lineCount(""), 0);
  assert.equal(lineCount("a"), 1);
  assert.equal(lineCount("a\n"), 1);
  assert.equal(lineCount("a\nb"), 2);
});
