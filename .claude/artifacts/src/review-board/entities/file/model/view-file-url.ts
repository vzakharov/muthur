import type {
  ReviewData,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import type { EffectiveRange } from "./range.ts";

/**
 * GitHub's page for the file as the range's `to` commit has it, or, where the
 * file is absent there (deleted), as `from` had it. Null without a known
 * repository or a version that exists. A renamed file's base revision lives
 * under its old path.
 */
export function viewFileUrl(
  data: ReviewData,
  file: ReviewFile,
  range: EffectiveRange,
): string | null {
  if (data.repo === null) return null;
  const [commit, present] =
    range.toBlob === null
      ? [range.from, range.fromBlob !== null]
      : [range.to, true];
  if (!present) return null;
  const path =
    commit === data.base.sha ? (file.oldPath ?? file.path) : file.path;
  const encoded = path.split("/").map(encodeURIComponent).join("/");
  return `https://github.com/${data.repo}/blob/${commit}/${encoded}`;
}
