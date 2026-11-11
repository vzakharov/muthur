import assert from "node:assert/strict";
import { test } from "node:test";
import type {
  ReviewBranch,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import { ageShades, SHADE_LEVELS } from "./age-shade.ts";

const at = (minutes: number): string =>
  new Date(Date.UTC(2026, 0, 1) + minutes * 60_000).toISOString();

const commit = (sha: string, minutes: number, baseMerge = false) => ({
  sha,
  subject: sha,
  author: "a",
  date: at(minutes),
  baseMerge,
});

const fileAt = (path: string, ...commits: string[]): ReviewFile => ({
  path,
  oldPath: null,
  status: "modified",
  binary: false,
  revisions: commits.map((sha) => ({
    commit: sha,
    path,
    blob: `${path}@${sha}`,
    size: 1,
  })),
});

// Two follow-ups minutes apart, a day later a second session, and a base merge in between.
const data: ReviewBranch = {
  base: { ref: "main", sha: "B" },
  commits: [
    commit("c0", 0),
    commit("c1", 5),
    commit("m", 600, true),
    commit("c2", 24 * 60),
    commit("c3", 24 * 60 + 4),
  ],
};

test("commits minutes apart share a shade, an older session is darker", () => {
  const shades = ageShades(
    data,
    [
      fileAt("a", "c0"),
      fileAt("b", "c1"),
      fileAt("c", "c2"),
      fileAt("d", "c3"),
    ],
    null,
  );
  assert.equal(shades.get("a")?.level, shades.get("b")?.level);
  assert.equal(shades.get("c")?.level, shades.get("d")?.level);
  assert.equal(shades.get("c")?.level, 0);
  assert.equal(shades.get("a")?.level, SHADE_LEVELS);
});

test("a file takes the shade of its last own change, base merges ignored", () => {
  const shades = ageShades(data, [fileAt("a", "c0", "m")], null);
  assert.equal(shades.get("a")?.commit, "c0");
  assert.equal(ageShades(data, [fileAt("only-merge", "m")], null).size, 0);
});

test("shades are weighed against the board's to, later commits ignored", () => {
  const shades = ageShades(data, [fileAt("a", "c0"), fileAt("b", "c3")], "c1");
  assert.equal(shades.get("a")?.level, 0);
  assert.equal(shades.has("b"), false);
});

test("a branch of one session is all the newest shade", () => {
  const shades = ageShades(
    { base: data.base, commits: [commit("c0", 0), commit("c1", 3)] },
    [fileAt("a", "c0")],
    null,
  );
  assert.equal(shades.get("a")?.level, 0);
});

test("the shade names the commit and its date", () => {
  const shade = ageShades(data, [fileAt("a", "c2")], null).get("a");
  assert.ok(shade);
  assert.equal(shade.commit, "c2");
  assert.equal(shade.date, at(24 * 60));
});
