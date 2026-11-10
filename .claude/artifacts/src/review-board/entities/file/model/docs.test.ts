import assert from "node:assert/strict";
import { mock, test } from "node:test";
import {
  boardDocSchema,
  fileDocSchema,
  filePrefsOf,
  parseDoc,
  shiftDocSchema,
} from "./docs.ts";

test("a well-formed doc parses and drops unknown fields", () => {
  const parsed = parseDoc(
    shiftDocSchema,
    { path: "a.ts", from: "abc", at: "2026-01-01T00:00:00Z", extra: 1 },
    "shifts/k",
  );
  assert.deepEqual(parsed, {
    path: "a.ts",
    from: "abc",
    at: "2026-01-01T00:00:00Z",
  });
});

test("null range ends are valid in board and file docs", () => {
  assert.ok(
    boardDocSchema.safeParse({
      whitespace: true,
      from: null,
      to: null,
      at: "t",
    }).success,
  );
  assert.ok(
    fileDocSchema.safeParse({ viewed: [], from: "a", to: null, at: "t" })
      .success,
  );
});

test("a doc saved with the single viewedBlob reads as a one-mark list", () => {
  const doc = parseDoc(
    fileDocSchema,
    { viewedBlob: "b1", from: null, to: null, at: "2026-01-01T00:00:00Z" },
    "k",
  );
  assert.ok(doc);
  assert.deepEqual(filePrefsOf(doc), {
    value: {
      viewed: [{ blob: "b1", at: "2026-01-01T00:00:00Z" }],
      from: null,
      to: null,
    },
    at: "2026-01-01T00:00:00Z",
  });
});

test("a doc with a list keeps it, and one with neither is unviewed", () => {
  const marks = [{ blob: "b1", at: "t0" }];
  const listed = parseDoc(
    fileDocSchema,
    { viewed: marks, viewedBlob: "old", from: null, to: null, at: "t" },
    "k",
  );
  assert.ok(listed);
  assert.deepEqual(filePrefsOf(listed).value.viewed, marks);
  const bare = parseDoc(
    fileDocSchema,
    { viewedBlob: null, from: null, to: null, at: "t" },
    "k",
  );
  assert.ok(bare);
  assert.deepEqual(filePrefsOf(bare).value.viewed, []);
});

test("a malformed doc is ignored with a warning naming its path", () => {
  const warn = mock.method(console, "warn", () => undefined);
  try {
    const parsed = parseDoc(
      fileDocSchema,
      { viewedBlob: 3, from: null, to: null, at: "t" },
      "data/users/u/b/files/k",
    );
    assert.equal(parsed, null);
    assert.equal(warn.mock.callCount(), 1);
    assert.match(
      String(warn.mock.calls[0]?.arguments[0]),
      /data\/users\/u\/b\/files\/k/,
    );
  } finally {
    warn.mock.restore();
  }
});
