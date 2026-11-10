import * as z from "zod/mini";
import {
  focusSchema,
  type Focus,
} from "#src/review-board/shared/review-data/index.ts";

/** Where a branch's author lists the review's focus; read from HEAD, so its line numbers match the board's. */
export const FOCUS_PATH = "docs/remove-before-merging/review-focus.json";

const focusFileSchema = z.array(focusSchema);

/** The number of lines in `text`, a final newline ending the last one rather than starting another. */
export const lineCount = (text: string): number =>
  text === "" ? 0 : text.split("\n").length - (text.endsWith("\n") ? 1 : 0);

/**
 * Parses the focus file against the changed files' line counts at HEAD (null
 * for a file with no text there), throwing on any entry the board could not
 * show as written: an unknown or repeated path, an empty reason, or lines
 * outside the file.
 */
export function parseFocus(
  text: string,
  lineCounts: ReadonlyMap<string, number | null>,
): Focus[] {
  const entries = focusFileSchema.parse(JSON.parse(text));
  const seen = new Set<string>();
  for (const entry of entries) {
    const where = `${FOCUS_PATH}: ${entry.path}`;
    if (!lineCounts.has(entry.path))
      throw new Error(`${where} is not among the changed files`);
    if (seen.has(entry.path)) throw new Error(`${where} is listed twice`);
    seen.add(entry.path);
    if (entry.why.trim() === "") throw new Error(`${where} has no reason`);
    const count = lineCounts.get(entry.path) ?? null;
    for (const [first, last] of entry.lines ?? []) {
      if (count === null)
        throw new Error(`${where} has no text at HEAD to mark lines in`);
      const whole = Number.isInteger(first) && Number.isInteger(last);
      if (!whole || first < 1 || last < first || last > count)
        throw new Error(
          `${where} lines ${String(first)}-${String(last)} are not within its ${String(count)} lines at HEAD`,
        );
    }
  }
  return entries;
}
