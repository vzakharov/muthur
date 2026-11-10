import type { BoardHandle } from "#src/review-board/pages/board/board/index.ts";
import type { LineAnchor } from "../lib/anchor.ts";

/** Where a thread's subject is drawn: a diff row or a card header. */
export interface Subject {
  element: HTMLElement;
  /** The element whose box clips the subject: the card body, the panel body or the viewport. */
  clip: Element | null;
  /** The file's card is a stub and its diff opens in the panel. */
  inPanelOnly: boolean;
}

const rowSelector = (anchor: LineAnchor): string =>
  `.row[data-side="${anchor.side ?? ""}"][data-line="${String(anchor.line)}"]`;

/**
 * Whether the file still shows the side the anchor was written on: an `R` line
 * while the file's "to" is the anchor's, an `L` line while its "from" is.
 */
function showsSide(board: BoardHandle, anchor: LineAnchor): boolean {
  const range = board.effectiveRange(anchor.path);
  if (range === undefined) return false;
  return anchor.side === "L"
    ? range.from.startsWith(anchor.from)
    : range.to.startsWith(anchor.to);
}

/** The rendered element an anchor names, or undefined when it is not drawn. */
export function locate(
  board: BoardHandle,
  anchor: LineAnchor,
): Subject | undefined {
  const card = board.cardElement(anchor.path);
  if (card === undefined) return undefined;
  const viewport = card.closest(".viewport");
  const inPanelOnly = card.querySelector(".card-body.has-diff") === null;
  if (anchor.side === null) {
    const head = card.querySelector<HTMLElement>(".card-head");
    return head === null
      ? undefined
      : { element: head, clip: viewport, inPanelOnly };
  }
  if (!showsSide(board, anchor)) return undefined;
  const panel = board.panel();
  const containers =
    panel?.path === anchor.path ? [panel.element, card] : [card];
  for (const container of containers) {
    const row = container.querySelector<HTMLElement>(rowSelector(anchor));
    if (row !== null) {
      return {
        element: row,
        clip: row.closest(".card-body, .panel-body"),
        inPanelOnly,
      };
    }
  }
  return { element: card, clip: null, inPanelOnly };
}

const intersects = (a: DOMRect, b: DOMRect): boolean =>
  a.bottom > b.top && a.top < b.bottom && a.right > b.left && a.left < b.right;

/**
 * The document point a visible subject's pin goes to — the row's left gutter
 * or the header's right end — or null while it is scrolled or panned out of
 * sight. A subject standing in for an undrawn row is never placed.
 */
export function pinPoint(subject: Subject): Claude.comments.DocPoint | null {
  const { element, clip } = subject;
  if (!element.matches(".row, .card-head")) return null;
  const rect = element.getBoundingClientRect();
  if (rect.width === 0 && rect.height === 0) return null;
  const clips = [clip, element.closest(".viewport")];
  for (const box of clips) {
    if (box !== null && !intersects(rect, box.getBoundingClientRect()))
      return null;
  }
  const x = element.matches(".row") ? rect.left + 6 : rect.right - 6;
  return {
    x: x + window.scrollX,
    y: rect.top + rect.height / 2 + window.scrollY,
  };
}
