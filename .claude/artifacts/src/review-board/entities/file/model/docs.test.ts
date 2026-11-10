import assert from "node:assert/strict";
import { mock, test } from "node:test";
import {
  boardDocSchema,
  fileDocSchema,
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
    fileDocSchema.safeParse({ viewedBlob: null, from: "a", to: null, at: "t" })
      .success,
  );
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
