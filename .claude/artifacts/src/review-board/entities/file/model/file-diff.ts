import {
  diffLines,
  type DiffResult,
} from "#src/review-board/shared/lib/diff.ts";
import {
  highlightLines,
  languageOf,
  type HighlightedLine,
  type Language,
} from "#src/review-board/shared/lib/highlight.ts";
import type {
  ReviewData,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import type { EffectiveRange } from "./range.ts";

/** Each side's highlighted lines, line n at index n − 1, for the diff's line numbers to index. */
export interface DiffSyntax {
  old: readonly HighlightedLine[];
  new: readonly HighlightedLine[];
}

export type FileDiff =
  | {
      kind: "text";
      diff: DiffResult;
      /** The file's text at the range's `to`, or null where it is absent there. */
      after: string | null;
      /** Null for a file with no known grammar, or a side past the highlighting budget. */
      syntax: () => DiffSyntax | null;
    }
  | { kind: "binary"; fromSize: number | null; toSize: number | null };

// A side this long is shown plain: highlighting it would stall the page.
const MAX_HIGHLIGHT_CHARS = 500_000;

// Blob ids name immutable content, so a diff between two of them never changes,
// and neither do a blob's highlighted lines.
const cache = new Map<string, DiffResult>();
const highlighted = new Map<string, HighlightedLine[]>();

function textOf(data: ReviewData, blob: string | null): string {
  if (blob === null) return "";
  const text = data.blobs[blob];
  if (text === undefined) throw new Error(`blob ${blob} is not in the payload`);
  return text;
}

function highlightBlob(
  data: ReviewData,
  blob: string | null,
  language: Language,
): HighlightedLine[] {
  if (blob === null) return [];
  const key = `${language}|${blob}`;
  let lines = highlighted.get(key);
  if (lines === undefined) {
    lines = highlightLines(textOf(data, blob), language);
    highlighted.set(key, lines);
  }
  return lines;
}

function diffSyntax(
  data: ReviewData,
  path: string,
  range: EffectiveRange,
): DiffSyntax | null {
  const language = languageOf(path);
  if (language === null) return null;
  const tooLong = (blob: string | null): boolean =>
    blob !== null && textOf(data, blob).length > MAX_HIGHLIGHT_CHARS;
  if (tooLong(range.fromBlob) || tooLong(range.toBlob)) return null;
  return {
    old: highlightBlob(data, range.fromBlob, language),
    new: highlightBlob(data, range.toBlob, language),
  };
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
  // Highlighting waits for a caller that draws the diff, which an oversized or viewed card never does.
  return {
    kind: "text",
    diff,
    after: range.toBlob === null ? null : textOf(data, range.toBlob),
    syntax: () => diffSyntax(data, file.path, range),
  };
}
