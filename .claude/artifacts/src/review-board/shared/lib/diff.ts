export type DiffLineKind = "context" | "add" | "del";

export interface DiffLine {
  kind: DiffLineKind;
  text: string;
  oldLine: number | null;
  newLine: number | null;
}

export interface DiffHunk {
  oldStart: number;
  oldCount: number;
  newStart: number;
  newCount: number;
  lines: DiffLine[];
}

export interface DiffResult {
  hunks: DiffHunk[];
  added: number;
  removed: number;
}

export interface DiffOptions {
  ignoreWhitespace: boolean;
}

const CONTEXT = 3;
const EQUAL = 0;
const DELETE = 1;
const INSERT = 2;

/** A missing final newline and a present one yield the same lines; CRLF stays in the text. */
export function splitLines(text: string): string[] {
  if (text === "") return [];
  const lines = text.split("\n");
  if (lines[lines.length - 1] === "") lines.pop();
  return lines;
}

/**
 * Shortest edit script over integer line ids, as ops from the end to the
 * start. Keeps one snapshot of the furthest-reaching frontier per edit
 * distance, so memory is O(D^2) and time O((N+M)D).
 */
function myers(a: Int32Array, b: Int32Array): number[] {
  const n = a.length;
  const m = b.length;
  const max = n + m;
  const offset = max + 1;
  const v = new Int32Array(2 * max + 3);
  const trace: Int32Array[] = [];

  let found = false;
  for (let d = 0; d <= max && !found; d++) {
    trace.push(v.slice(offset - d - 1, offset + d + 2));
    for (let k = -d; k <= d; k += 2) {
      let x =
        k === -d ||
        (k !== d && (v[offset + k - 1] ?? 0) < (v[offset + k + 1] ?? 0))
          ? (v[offset + k + 1] ?? 0)
          : (v[offset + k - 1] ?? 0) + 1;
      let y = x - k;
      while (x < n && y < m && a[x] === b[y]) {
        x++;
        y++;
      }
      v[offset + k] = x;
      if (x >= n && y >= m) {
        found = true;
        break;
      }
    }
  }

  const ops: number[] = [];
  let x = n;
  let y = m;
  for (let d = trace.length - 1; d >= 0; d--) {
    const snap = trace[d];
    if (snap === undefined) throw new Error("diff trace is missing a frontier");
    const at = (k: number) => snap[k + d + 1] ?? 0;
    const k = x - y;
    const prevK =
      k === -d || (k !== d && at(k - 1) < at(k + 1)) ? k + 1 : k - 1;
    const prevX = at(prevK);
    const prevY = prevX - prevK;
    while (x > prevX && y > prevY) {
      ops.push(EQUAL);
      x--;
      y--;
    }
    if (d > 0) ops.push(x === prevX ? INSERT : DELETE);
    x = prevX;
    y = prevY;
  }
  return ops;
}

export function diffLines(
  oldText: string,
  newText: string,
  options: DiffOptions,
): DiffResult {
  const oldLines = splitLines(oldText);
  const newLines = splitLines(newText);
  const key = options.ignoreWhitespace
    ? (line: string) => line.replace(/\s+/g, "")
    : (line: string) => line;

  const ids = new Map<string, number>();
  const toIds = (lines: string[]) =>
    Int32Array.from(lines, (line) => {
      const k = key(line);
      let id = ids.get(k);
      if (id === undefined) {
        id = ids.size;
        ids.set(k, id);
      }
      return id;
    });
  const a = toIds(oldLines);
  const b = toIds(newLines);

  let prefix = 0;
  while (prefix < a.length && prefix < b.length && a[prefix] === b[prefix])
    prefix++;
  let suffix = 0;
  while (
    suffix < a.length - prefix &&
    suffix < b.length - prefix &&
    a[a.length - 1 - suffix] === b[b.length - 1 - suffix]
  ) {
    suffix++;
  }

  const middle = myers(
    a.subarray(prefix, a.length - suffix),
    b.subarray(prefix, b.length - suffix),
  );
  const ops: number[] = [
    ...new Array<number>(prefix).fill(EQUAL),
    ...middle.reverse(),
    ...new Array<number>(suffix).fill(EQUAL),
  ];

  const all: DiffLine[] = [];
  let i = 0;
  let j = 0;
  let added = 0;
  let removed = 0;
  for (const op of ops) {
    if (op === EQUAL) {
      all.push({
        kind: "context",
        text: newLines[j] ?? "",
        oldLine: i + 1,
        newLine: j + 1,
      });
      i++;
      j++;
    } else if (op === DELETE) {
      all.push({
        kind: "del",
        text: oldLines[i] ?? "",
        oldLine: i + 1,
        newLine: null,
      });
      i++;
      removed++;
    } else {
      all.push({
        kind: "add",
        text: newLines[j] ?? "",
        oldLine: null,
        newLine: j + 1,
      });
      j++;
      added++;
    }
  }

  return { hunks: toHunks(all), added, removed };
}

function toHunks(all: DiffLine[]): DiffHunk[] {
  const hunks: DiffHunk[] = [];
  let index = 0;
  while (index < all.length) {
    while (index < all.length && all[index]?.kind === "context") index++;
    if (index >= all.length) break;

    const start = Math.max(0, index - CONTEXT);
    let lastChange = index;
    let scan = index;
    // A gap of at most 2*CONTEXT unchanged lines joins two changes into one hunk.
    while (scan < all.length && scan - lastChange <= 2 * CONTEXT + 1) {
      if (all[scan]?.kind !== "context") lastChange = scan;
      scan++;
    }
    const end = Math.min(all.length, lastChange + CONTEXT + 1);
    hunks.push(makeHunk(all.slice(start, end)));
    index = end;
  }
  return hunks;
}

function makeHunk(lines: DiffLine[]): DiffHunk {
  const first = lines[0];
  if (first === undefined) throw new Error("empty hunk");
  const oldCount = lines.filter((line) => line.kind !== "add").length;
  const newCount = lines.filter((line) => line.kind !== "del").length;
  const oldStart = lines.find((line) => line.oldLine !== null)?.oldLine ?? 0;
  const newStart = lines.find((line) => line.newLine !== null)?.newLine ?? 0;
  return { oldStart, oldCount, newStart, newCount, lines };
}
