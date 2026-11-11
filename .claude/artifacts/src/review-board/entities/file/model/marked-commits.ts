import type { ReviewFile } from "#src/review-board/shared/review-data/index.ts";
import { viewedToken } from "./range.ts";

/**
 * The commits at which a file carries a Viewed mark, each with when it was
 * marked: every revision whose blob has a mark, so commits sharing a blob share
 * the mark.
 */
export function markedCommits(
  file: ReviewFile,
  viewedAt: ReadonlyMap<string, string>,
): ReadonlyMap<string, string> {
  const marked = new Map<string, string>();
  for (const revision of file.revisions) {
    const at = viewedAt.get(viewedToken(revision.blob));
    if (at !== undefined) marked.set(revision.commit, at);
  }
  return marked;
}
