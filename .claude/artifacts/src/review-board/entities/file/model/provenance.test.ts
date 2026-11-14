import assert from "node:assert/strict";
import { test } from "node:test";
import { provenance } from "./provenance.ts";

test("a file git did not rename has none", () => {
  assert.equal(provenance({ path: "src/a.ts", oldPath: null }), null);
});

test("a new name in the same directory is renamed from the old name", () => {
  assert.deepEqual(
    provenance({ path: "src/lib/new-name.ts", oldPath: "src/lib/old-name.ts" }),
    { kind: "renamed", from: "old-name.ts" },
  );
  assert.deepEqual(provenance({ path: "b.ts", oldPath: "a.ts" }), {
    kind: "renamed",
    from: "a.ts",
  });
});

test("a changed directory is moved from the old full path, name kept or not", () => {
  assert.deepEqual(
    provenance({
      path: "src/board/scripts/lib/board-file.ts",
      oldPath: "src/island-board/scripts/lib/board-file.ts",
    }),
    { kind: "moved", from: "src/island-board/scripts/lib/board-file.ts" },
  );
  assert.deepEqual(provenance({ path: "lib/b.ts", oldPath: "a.ts" }), {
    kind: "moved",
    from: "a.ts",
  });
});
