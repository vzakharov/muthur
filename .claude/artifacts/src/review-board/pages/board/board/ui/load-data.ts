import { el } from "#src/review-board/shared/lib/dom.ts";
import { DATA_ID } from "#src/review-board/shared/lib/page-ids.ts";
import {
  parseReviewData,
  type ReviewData,
} from "#src/review-board/shared/review-data/index.ts";

/** The payload the build embeds in the page; a missing or malformed one throws. */
function readReviewData(): ReviewData {
  const node = document.getElementById(DATA_ID);
  if (node === null) throw new Error("the page carries no review data");
  return parseReviewData(JSON.parse(node.textContent));
}

function showFatal(root: HTMLElement, error: unknown): void {
  const box = el("div", "fatal");
  box.append(
    el("h1", "fatal-title", "The review board could not load"),
    el("pre", "fatal-detail", String(error)),
  );
  root.replaceChildren(box);
}

/** The embedded payload; on failure the error is shown in `root` and rethrown. */
export function loadReviewData(root: HTMLElement): ReviewData {
  try {
    return readReviewData();
  } catch (error) {
    showFatal(root, error);
    throw error;
  }
}
