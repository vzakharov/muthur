import type { ReviewData } from "#src/review-board/shared/review-data/index.ts";

const short = (sha: string): string => sha.slice(0, 7);

/** Commit SHA → "abc1234 subject", the base included, for selects and the panel; an unknown SHA gets its short form. */
export function commitLabels(data: ReviewData): (sha: string) => string {
  const labels = new Map<string, string>([
    [data.base.sha, `${short(data.base.sha)} base (${data.base.ref})`],
  ]);
  for (const commit of data.commits)
    labels.set(commit.sha, `${short(commit.sha)} ${commit.subject}`);
  return (sha) => labels.get(sha) ?? short(sha);
}
