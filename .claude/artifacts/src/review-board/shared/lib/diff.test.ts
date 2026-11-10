import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { type DiffHunk, diffLines, splitLines } from "./diff.ts";

const strict = { ignoreWhitespace: false };
const lenient = { ignoreWhitespace: true };

test("identical inputs give no hunks", () => {
  const result = diffLines("a\nb\nc\n", "a\nb\nc\n", strict);
  assert.deepEqual(result, { hunks: [], added: 0, removed: 0 });
});

test("both sides empty", () => {
  assert.deepEqual(diffLines("", "", strict), {
    hunks: [],
    added: 0,
    removed: 0,
  });
});

test("empty old side is all additions with 1-based new numbers", () => {
  const result = diffLines("", "x\ny\n", strict);
  assert.equal(result.added, 2);
  assert.equal(result.removed, 0);
  assert.deepEqual(result.hunks[0]?.lines, [
    { kind: "add", text: "x", oldLine: null, newLine: 1 },
    { kind: "add", text: "y", oldLine: null, newLine: 2 },
  ]);
});

test("empty new side is all deletions", () => {
  const result = diffLines("x\ny\n", "", strict);
  assert.equal(result.removed, 2);
  assert.deepEqual(result.hunks[0]?.lines, [
    { kind: "del", text: "x", oldLine: 1, newLine: null },
    { kind: "del", text: "y", oldLine: 2, newLine: null },
  ]);
});

test("a missing final newline is just the last line", () => {
  assert.deepEqual(diffLines("a\nb", "a\nb\n", strict), {
    hunks: [],
    added: 0,
    removed: 0,
  });
  assert.deepEqual(splitLines("a\n"), ["a"]);
  assert.deepEqual(splitLines("a\n\n"), ["a", ""]);
  assert.deepEqual(splitLines(""), []);
});

test("CRLF is kept verbatim in the text", () => {
  const result = diffLines("a\r\nb\r\n", "a\r\nc\r\n", strict);
  assert.deepEqual(result.hunks[0]?.lines, [
    { kind: "context", text: "a\r", oldLine: 1, newLine: 1 },
    { kind: "del", text: "b\r", oldLine: 2, newLine: null },
    { kind: "add", text: "c\r", oldLine: null, newLine: 2 },
  ]);
});

test("a hunk carries three lines of context and nearby changes merge", () => {
  const old = Array.from({ length: 20 }, (_, i) => `l${i + 1}`);
  const next = [...old];
  next[9] = "changed";
  const result = diffLines(old.join("\n"), next.join("\n"), strict);
  assert.equal(result.hunks.length, 1);
  const hunk = result.hunks[0];
  assert.equal(hunk?.oldStart, 7);
  assert.equal(hunk?.oldCount, 7);
  assert.equal(hunk?.newStart, 7);
  assert.equal(hunk?.newCount, 7);

  const far = [...next];
  far[0] = "first";
  far[19] = "last";
  assert.equal(
    diffLines(old.join("\n"), far.join("\n"), strict).hunks.length,
    3,
  );

  const near = [...old];
  near[2] = "x";
  near[9] = "y";
  assert.equal(
    diffLines(old.join("\n"), near.join("\n"), strict).hunks.length,
    1,
  );
});

test("ignoreWhitespace compares without whitespace and shows the new side", () => {
  const result = diffLines("a  b\n\tc\nd\n", "a b\n  c\ne\n", lenient);
  assert.equal(result.added, 1);
  assert.equal(result.removed, 1);
  assert.deepEqual(result.hunks[0]?.lines, [
    { kind: "context", text: "a b", oldLine: 1, newLine: 1 },
    { kind: "context", text: "  c", oldLine: 2, newLine: 2 },
    { kind: "del", text: "d", oldLine: 3, newLine: null },
    { kind: "add", text: "e", oldLine: null, newLine: 3 },
  ]);
  assert.equal(diffLines("a\n", " a \n", lenient).hunks.length, 0);
  assert.equal(diffLines("a\n", " a \n", strict).added, 1);
});

test("a 5,000-line file with a few hundred changes diffs quickly", () => {
  const rng = seeded(7);
  const old = Array.from({ length: 5000 }, (_, i) => `line ${i}`);
  const next: string[] = [];
  for (const line of old) {
    const roll = rng();
    if (roll < 0.04) continue;
    next.push(roll < 0.08 ? `${line} edited` : line);
    if (roll > 0.97) next.push(`inserted ${next.length}`);
  }
  const started = performance.now();
  const result = diffLines(old.join("\n"), next.join("\n"), strict);
  assert.ok(performance.now() - started < 2000);
  assert.ok(result.added > 100 && result.removed > 100);
});

function seeded(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const ALPHABET = ["a", "b", "c", " a", "b ", "a  b", "", "\tc"];

function randomText(rng: () => number): string {
  const count = Math.floor(rng() * 40);
  const lines = Array.from(
    { length: count },
    () => ALPHABET[Math.floor(rng() * ALPHABET.length)] ?? "",
  );
  return lines.map((line) => `${line}\n`).join("");
}

function gitNumstat(
  dir: string,
  ignoreWhitespace: boolean,
): { added: number; removed: number } {
  const args = ["diff", "--no-index", "--numstat", "--diff-algorithm=myers"];
  if (ignoreWhitespace) args.push("-w");
  args.push("old.txt", "new.txt");
  const run = spawnSync("git", args, { cwd: dir, encoding: "utf8" });
  // `--no-index` exits 1 when the files differ.
  if (run.error || (run.status !== 0 && run.status !== 1)) {
    throw new Error(`git diff failed: ${run.stderr}`);
  }
  const [added = "0", removed = "0"] = run.stdout.trim().split("\t");
  return { added: Number(added), removed: Number(removed) };
}

/** Rebuilds one side from the hunks alone; null when unchanged gaps leave holes. */
function sideLines(
  hunks: DiffHunk[],
  side: "old" | "new",
  total: number,
): string[] | null {
  const lines = new Array<string | undefined>(total).fill(undefined);
  for (const hunk of hunks) {
    for (const line of hunk.lines) {
      const n = side === "old" ? line.oldLine : line.newLine;
      if (n !== null) lines[n - 1] = line.text;
    }
  }
  const complete: string[] = [];
  for (const line of lines) {
    if (line === undefined) return null;
    complete.push(line);
  }
  return complete;
}

test("counts match git's Myers diff and hunks reconstruct both sides", () => {
  const dir = mkdtempSync(join(tmpdir(), "diff-test-"));
  try {
    const rng = seeded(42);
    for (let round = 0; round < 30; round++) {
      const oldText = randomText(rng);
      const newText = randomText(rng);
      writeFileSync(join(dir, "old.txt"), oldText);
      writeFileSync(join(dir, "new.txt"), newText);

      for (const ignoreWhitespace of [false, true]) {
        const result = diffLines(oldText, newText, { ignoreWhitespace });
        const expected = gitNumstat(dir, ignoreWhitespace);
        assert.deepEqual(
          { added: result.added, removed: result.removed },
          expected,
          `round ${round}, ignoreWhitespace=${ignoreWhitespace}`,
        );

        const oldLines = splitLines(oldText);
        const newLines = splitLines(newText);
        const changed = result.hunks
          .flatMap((h) => h.lines)
          .filter((l) => l.kind !== "context");
        assert.equal(changed.length, result.added + result.removed);

        // Deleted lines are old-side text; added lines are new-side text.
        for (const line of result.hunks.flatMap((h) => h.lines)) {
          if (line.kind === "del")
            assert.equal(line.text, oldLines[(line.oldLine ?? 0) - 1]);
          if (line.kind === "add")
            assert.equal(line.text, newLines[(line.newLine ?? 0) - 1]);
        }

        // Applying the hunks to the old file gives the new file; outside the
        // hunks the two sides are identical line for line.
        const applied: string[] = [];
        let cursor = 0;
        for (const hunk of result.hunks) {
          while (cursor < Math.max(hunk.oldStart - 1, 0)) {
            applied.push(oldLines[cursor++] ?? "");
          }
          for (const line of hunk.lines) {
            if (line.kind !== "del") applied.push(line.text);
            if (line.kind !== "add") cursor++;
          }
        }
        while (cursor < oldLines.length) applied.push(oldLines[cursor++] ?? "");
        if (!ignoreWhitespace) {
          assert.deepEqual(applied, newLines);
          const oldSide = sideLines(result.hunks, "old", oldLines.length);
          if (oldSide !== null) assert.deepEqual(oldSide, oldLines);
          const newSide = sideLines(result.hunks, "new", newLines.length);
          if (newSide !== null) assert.deepEqual(newSide, newLines);
        } else {
          assert.equal(applied.length, newLines.length);
        }
      }
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
