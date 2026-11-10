import {
  diffLines,
  type DiffResult,
} from "#src/review-board/shared/lib/diff.ts";
import type {
  ReviewData,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import type { EffectiveRange } from "./range.ts";

export type FileDiff =
  | { kind: "text"; diff: DiffResult }
  | { kind: "binary"; fromSize: number | null; toSize: number | null };

// Blob ids name immutable content, so a diff between two of them never changes.
const cache = new Map<string, DiffResult>();

function textOf(data: ReviewData, blob: string | null): string {
  if (blob === null) return "";
  const text = data.blobs[blob];
  if (text === undefined) throw new Error(`blob ${blob} is not in the payload`);
  return text;
}

/** The unified diff a file shows for its effective range; an absent side diffs as empty text. */
export function fileDiff(
  data: ReviewData,
  file: ReviewFile,
  range: EffectiveRange,
  ignoreWhitespace: boolean,
): FileDiff {
  if (file.binary) {
    const sizeAt = (commit: string): number | null =>
      file.revisions.find((revision) => revision.commit === commit)?.size ??
      null;
    return {
      kind: "binary",
      fromSize: sizeAt(range.from),
      toSize: sizeAt(range.to),
    };
  }
  const key = `${range.fromBlob ?? "-"}|${range.toBlob ?? "-"}|${ignoreWhitespace}`;
  let diff = cache.get(key);
  if (diff === undefined) {
    diff = diffLines(textOf(data, range.fromBlob), textOf(data, range.toBlob), {
      ignoreWhitespace,
    });
    cache.set(key, diff);
  }
  return { kind: "text", diff };
}
