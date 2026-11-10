import type { ReviewData } from "#src/review-board/shared/review-data/index.ts";

/** Commit SHA → "abc1234 subject", the base included, for selects and the panel. */
export function commitLabels(data: ReviewData): Map<string, string> {
  const labels = new Map<string, string>([
    [data.base.sha, `${data.base.sha.slice(0, 7)} base (${data.base.ref})`],
  ]);
  for (const commit of data.commits)
    labels.set(commit.sha, `${commit.sha.slice(0, 7)} ${commit.subject}`);
  return labels;
}
