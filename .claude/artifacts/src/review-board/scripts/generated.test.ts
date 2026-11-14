import assert from "node:assert/strict";
import { test } from "node:test";
import { generatedPaths } from "./generated.ts";

const output = (entries: [string, string][]): string =>
  entries
    .map(([path, value]) => `${path}\0linguist-generated\0${value}\0`)
    .join("");

test("keeps the paths marked set or true", () => {
  const paths = generatedPaths(
    output([
      ["gen/bare.ts", "set"],
      ["gen/explicit.ts", "true"],
      ["src/plain.ts", "unspecified"],
      ["src/opted-out.ts", "false"],
      ["src/negated.ts", "unset"],
    ]),
  );
  assert.deepEqual([...paths], ["gen/bare.ts", "gen/explicit.ts"]);
});

test("keeps a path with spaces whole", () => {
  assert.deepEqual(
    [...generatedPaths(output([["gen/a b.ts", "true"]]))],
    ["gen/a b.ts"],
  );
});

test("reads empty output as no generated paths", () => {
  assert.equal(generatedPaths("").size, 0);
});
