import type { CommentTarget } from "#src/review-board/entities/file/index.ts";
import type { BoardHandle } from "#src/review-board/pages/board/board/index.ts";

/** The file whose diff `element` sits in: its card's, or the panel's. */
function pathOf(board: BoardHandle, element: Element): string | undefined {
  const card = element.closest<HTMLElement>(".card");
  if (card !== null) return card.dataset["path"];
  return element.closest(".panel") === null ? undefined : board.panel()?.path;
}

/** The line a diff row shows, or undefined for a row with no number on its side. */
export function rowTarget(
  board: BoardHandle,
  row: HTMLElement,
): CommentTarget | undefined {
  const path = pathOf(board, row);
  const side = row.dataset["side"];
  const line = Number(row.dataset["line"]);
  if (path === undefined || (side !== "R" && side !== "L")) return undefined;
  if (!Number.isInteger(line) || line < 1) return undefined;
  return { path, side, line };
}

/**
 * The whole file `element` belongs to — anywhere on a card, or in the panel's
 * diff off a numbered row — or undefined for the board's chrome.
 */
export function fileTarget(
  board: BoardHandle,
  element: Element,
): CommentTarget | undefined {
  if (element.closest(".card, .panel-body") === null) return undefined;
  const path = pathOf(board, element);
  return path === undefined ? undefined : { path, side: null, line: null };
}
