import assert from "node:assert/strict";
import { test } from "node:test";
import { hiddenInDiffs } from "./hidden-in-diffs.ts";

const output = (entries: [string, string][]): string =>
  entries
    .map(([path, value]) => `${path}\0linguist-generated\0${value}\0`)
    .join("");

test("keeps the paths marked set or true", () => {
  const paths = hiddenInDiffs(
    output([
      ["gen/bare.ts", "set"],
      ["pnpm-lock.yaml", "true"],
      ["src/plain.ts", "unspecified"],
      ["src/opted-out.ts", "false"],
      ["src/negated.ts", "unset"],
    ]),
  );
  assert.deepEqual([...paths], ["gen/bare.ts", "pnpm-lock.yaml"]);
});

test("keeps a path with spaces whole", () => {
  assert.deepEqual(
    [...hiddenInDiffs(output([["gen/a b.ts", "true"]]))],
    ["gen/a b.ts"],
  );
});

test("reads empty output as no hidden paths", () => {
  assert.equal(hiddenInDiffs("").size, 0);
});
