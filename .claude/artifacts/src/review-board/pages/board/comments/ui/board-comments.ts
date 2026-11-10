import type { CommentTarget } from "#src/review-board/entities/file/index.ts";
import type {
  BoardHandle,
  CommentsHook,
} from "#src/review-board/pages/board/board/index.ts";
import { decodeAnchor, encodeAnchor } from "../lib/anchor.ts";
import { locate, pinPoint } from "./locate.ts";

type Controller = Claude.comments.CustomAnchors;
type Thread = Claude.comments.OverrideThread;

/** Codes after which this view cannot comment from the page at all. */
const PERMANENT = new Set<string>([
  "forbidden",
  "unavailable",
  "not_granted",
  "capability_disabled",
  "capability_removed",
]);

const errorCode = (error: unknown): string | undefined =>
  typeof error === "object" &&
  error !== null &&
  "code" in error &&
  typeof error.code === "string"
    ? error.code
    : undefined;

const label = (target: CommentTarget): string =>
  target.line === null
    ? target.path
    : `${target.path}, ${target.side === "L" ? "old" : "new"} line ${String(target.line)}`;

export interface BoardComments {
  /** Handed to `mountBoard`, before the board exists. */
  hook: CommentsHook;
  /**
   * Takes over comment anchoring for the mounted board and shows its comment
   * controls; a view that cannot comment leaves them hidden. Rejects only on a
   * failure that is not one of those designed absences.
   */
  connect(board: BoardHandle): Promise<void>;
}

/**
 * Comments on the board through the shell's `customAnchors` override: the
 * board's controls and, in comment mode, a click on any line open the shell's
 * composer at that line's anchor, and every thread whose line is on screen is
 * reported for its pin.
 */
export function boardComments(): BoardComments {
  let board: BoardHandle | undefined;
  let controller: Controller | undefined;
  let threads: Thread[] = [];
  let composing = false;
  let composed: string | undefined;

  function report(): void {
    if (board === undefined || controller === undefined) return;
    const placed: Record<string, Claude.comments.DocPoint | null> = {};
    for (const thread of threads) {
      const point = pointOf(board, thread.anchor);
      if (point !== null) placed[thread.id] = point;
    }
    if (composing && composed !== undefined)
      placed["composer"] = pointOf(board, composed);
    controller.placed(placed);
  }

  function pointOf(
    handle: BoardHandle,
    name: string,
  ): Claude.comments.DocPoint | null {
    const anchor = decodeAnchor(name, handle.paths);
    if (anchor === undefined) return null;
    const subject = locate(handle, anchor);
    return subject === undefined ? null : pinPoint(subject);
  }

  function disable(): void {
    controller?.release();
    controller = undefined;
    board?.setCommentsEnabled(false);
  }

  function compose(target: CommentTarget, at: Element): void {
    if (board === undefined || controller === undefined) return;
    const range = board.effectiveRange(target.path);
    if (range === undefined) return;
    const anchor = encodeAnchor({ ...target, ...range });
    composed = anchor;
    controller
      .compose(anchor, at, { label: label(target) })
      .catch((error: unknown) => {
        if (PERMANENT.has(errorCode(error) ?? "")) {
          disable();
          return;
        }
        throw error;
      });
  }

  function reveal(id: string): void {
    const thread = threads.find((candidate) => candidate.id === id);
    if (board === undefined || thread === undefined) return;
    const anchor = decodeAnchor(thread.anchor, board.paths);
    if (anchor === undefined) return;
    board.panTo(anchor.path);
    const first = locate(board, anchor);
    if (first?.inPanelOnly === true && anchor.side !== null)
      board.openPanel(anchor.path);
    const subject = locate(board, anchor);
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    subject?.element.scrollIntoView({
      block: "center",
      inline: "nearest",
      behavior: reduced ? "auto" : "smooth",
    });
    report();
  }

  /** In comment mode a click anywhere on a line comments on that line. */
  function onModeClick(event: MouseEvent): void {
    const target = event.target;
    if (!(target instanceof Element) || target.closest(".plus") !== null)
      return;
    const row = target.closest<HTMLElement>(".row[data-line]");
    if (row === null) return;
    // A row in the panel belongs to the panel's file; a card names its own.
    const path =
      row.closest<HTMLElement>(".card")?.dataset["path"] ??
      board?.panel()?.path;
    const side = row.dataset["side"];
    if (path === undefined || (side !== "R" && side !== "L")) return;
    event.stopPropagation();
    compose({ path, side, line: Number(row.dataset["line"]) }, row);
  }

  const callbacks: Claude.comments.CustomAnchorsCallbacks = {
    mode(on) {
      board?.element.classList.toggle("comment-mode", on);
      if (on) board?.element.addEventListener("click", onModeClick, true);
      else {
        board?.element.removeEventListener("click", onModeClick, true);
        threads = [];
      }
    },
    threads(list) {
      threads = list;
      report();
    },
    reveal,
    composing(open) {
      composing = open;
      if (!open) composed = undefined;
      report();
    },
  };

  return {
    hook: {
      onComment: compose,
      visibleChanged: report,
    },
    async connect(handle) {
      board = handle;
      // The runtime types declare `window.claude`; a page opened off disk has none.
      if (!("claude" in window)) return;
      const api = await window.claude.use("comments");
      if (api === null) return;
      try {
        controller = await api.customAnchors(callbacks);
      } catch (error) {
        if (PERMANENT.has(errorCode(error) ?? "")) return;
        throw error;
      }
      handle.setCommentsEnabled(true);
      report();
    },
  };
}
