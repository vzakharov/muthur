import type { ReviewFile } from "#src/review-board/shared/review-data/index.ts";

/**
 * Whether a file passes the board's name filter: the trimmed query is a
 * case-insensitive substring of its full path, folders included, or of the path
 * it was renamed from. An empty query passes every file.
 */
export function matchesPath(file: ReviewFile, query: string): boolean {
  const needle = query.trim().toLowerCase();
  if (needle === "") return true;
  return [file.path, file.oldPath].some((path) =>
    path?.toLowerCase().includes(needle),
  );
}
