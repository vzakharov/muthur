/** The board's name — the page's `<title>`, which names the artifact, and the toolbar's heading. */
export function boardTitle(branch: string, pr: number | null): string {
  const review = pr === null ? "Review" : `Review #${pr}`;
  if (branch !== "") return `${review} · ${branch}`;
  return pr === null ? "Review board" : review;
}
