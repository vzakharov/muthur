// A thread's anchor is the name Claude reads back as the comment's location,
// so it stays legible: `<path>@<from7>..<to7>`, then `:R<n>` for line n of the
// file at `to`, or `:L<n>` for line n of the file at `from` (a deleted line).
// The platform keeps at most 128 bytes of it, so a long path loses whole
// segments from the left, behind `…/`.

export type Side = "R" | "L";

export interface LineAnchor {
  path: string;
  from: string;
  to: string;
  side: Side | null;
  line: number | null;
}

export const ANCHOR_BYTES = 128;
const SHORT = 7;
const ELIDED = "…/";
const GRAMMAR =
  /^(.+)@([0-9a-f]{7,40})\.\.([0-9a-f]{7,40})(?::([RL])([1-9]\d*))?$/;

const bytes = (text: string): number => new TextEncoder().encode(text).length;

/** The longest tail of `path` that fits `budget` bytes behind `…/`. */
function shorten(path: string, budget: number): string {
  const segments = path.split("/");
  for (let start = 1; start < segments.length; start++) {
    const tail = ELIDED + segments.slice(start).join("/");
    if (bytes(tail) <= budget) return tail;
  }
  // A file name alone past the budget keeps its last characters.
  const chars = [...(segments.at(-1) ?? path)];
  while (chars.length > 0 && bytes(ELIDED + chars.join("")) > budget) {
    chars.shift();
  }
  return ELIDED + chars.join("");
}

export function encodeAnchor(anchor: LineAnchor): string {
  const range = `@${anchor.from.slice(0, SHORT)}..${anchor.to.slice(0, SHORT)}`;
  const line =
    anchor.side === null || anchor.line === null
      ? ""
      : `:${anchor.side}${anchor.line}`;
  const suffix = range + line;
  const whole = anchor.path + suffix;
  if (bytes(whole) <= ANCHOR_BYTES) return whole;
  return shorten(anchor.path, ANCHOR_BYTES - bytes(suffix)) + suffix;
}

/** The file a shortened path's tail names, whole segments matched first. */
const elided = (tail: string, paths: readonly string[]): string | undefined =>
  paths.find((candidate) => candidate.endsWith(`/${tail}`)) ??
  paths.find((candidate) => candidate.endsWith(tail));

/**
 * The anchor a thread names, its path resolved against the board's files;
 * undefined for any other anchor — the shell's own CSS paths, or a file the
 * board no longer shows.
 */
export function decodeAnchor(
  anchor: string,
  paths: readonly string[],
): LineAnchor | undefined {
  const match = GRAMMAR.exec(anchor);
  if (match === null) return undefined;
  const [, named = "", from = "", to = "", side, line] = match;
  const path = named.startsWith(ELIDED)
    ? elided(named.slice(ELIDED.length), paths)
    : paths.find((candidate) => candidate === named);
  if (path === undefined) return undefined;
  return {
    path,
    from,
    to,
    side: side === "R" || side === "L" ? side : null,
    line: line === undefined ? null : Number(line),
  };
}
