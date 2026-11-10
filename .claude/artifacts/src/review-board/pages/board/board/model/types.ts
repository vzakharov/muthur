import type { CommentTarget } from "#src/review-board/entities/file/index.ts";

/** What a comments module hands the board; without one the board hides its comment controls. */
export interface CommentsHook {
  /** A comment control was used: `at` is the control's row or button, `target` what it addresses. */
  onComment(target: CommentTarget, at: Element): void;
  /**
   * What is on screen may have changed: after a pan or zoom, a card body or
   * panel scroll, a re-pack, a range change or the panel opening or closing.
   * Called at most once per animation frame.
   */
  visibleChanged(): void;
}

export interface BoardOptions {
  comments?: CommentsHook;
}

/** What a comments module needs to place pins and reveal a comment. */
export interface BoardHandle {
  /** The card showing `path`, or undefined for a path that is not in the review. */
  cardElement(path: string): HTMLElement | undefined;
  /** The commits (SHAs among the file's revisions) the file's diff currently spans. */
  effectiveRange(path: string): { from: string; to: string } | undefined;
  /** Centres the camera on the file's card, keeping the zoom. */
  panTo(path: string): void;
  /** Shows the file's full diff in the side panel. */
  openPanel(path: string): void;
  /** The side panel while it is open, else undefined. */
  panelElement(): HTMLElement | undefined;
  destroy(): void;
}
