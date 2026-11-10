import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";
import { fileKey } from "./keys.ts";

test("matches sha256sum of the UTF-8 bytes", async () => {
  assert.equal(
    await fileKey("abc"),
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
  );
  assert.equal(
    await fileKey(""),
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  );
});

test("hashes bytes, not code units", async () => {
  const path = "src/é/日本.ts";
  assert.equal(
    await fileKey(path),
    createHash("sha256").update(path, "utf8").digest("hex"),
  );
});
