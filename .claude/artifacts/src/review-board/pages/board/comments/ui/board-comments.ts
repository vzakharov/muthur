import type { CommentTarget } from "#src/review-board/entities/file/index.ts";
import type {
  BoardHandle,
  CommentsHook,
} from "#src/review-board/pages/board/board/index.ts";
import { claudeRuntime } from "#src/review-board/shared/lib/runtime.ts";
import { decodeAnchor, encodeAnchor } from "../lib/anchor.ts";
import { attachAreaSelect, type AreaSelect } from "./area-select.ts";
import { locate, pinPoint } from "./locate.ts";
import { fileTarget, rowTarget } from "./targets.ts";

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

const isPermanent = (error: unknown): boolean =>
  typeof error === "object" &&
  error !== null &&
  "code" in error &&
  typeof error.code === "string" &&
  PERMANENT.has(error.code);

function label(target: CommentTarget, through: number | null = null): string {
  if (target.line === null) return target.path;
  const side = target.side === "L" ? "old" : "new";
  return through === null
    ? `${target.path}, ${side} line ${String(target.line)}`
    : `${target.path}, ${side} lines ${String(target.line)}–${String(through)}`;
}

/** What a viewer reads a control as: its accessible name, else its text. */
const nameOf = (control: Element): string =>
  (control.ariaLabel ?? control.getAttribute("title") ?? control.textContent)
    .replace(/\s+/g, " ")
    .trim();

const CONTROLS =
  ".toolbar-title, button, select, label, .tool-label, .tally, .panel-title";
/** The board's own comment buttons, which open the composer themselves. */
const OWN_CONTROLS = ".plus, .comment-btn";

const overlaps = (a: DOMRect, b: DOMRect): boolean =>
  a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;

/** The names of the controls a drawn rectangle covers, in document order. */
function covered(root: Element, box: DOMRect): string[] {
  const names = [...root.querySelectorAll(CONTROLS)]
    .filter((control) => overlaps(control.getBoundingClientRect(), box))
    .map(nameOf)
    .filter((name) => name !== "");
  return [...new Set(names)];
}

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

/** The element a shell CSS-path anchor names; null for a name that is not a selector. */
function select(name: string): Element | null {
  try {
    return document.querySelector(name);
  } catch (error) {
    if (error instanceof DOMException && error.name === "SyntaxError")
      return null;
    throw error;
  }
}

/** The shell keeps at most 1024 UTF-16 units of a label or detail and rejects more. */
const clip = (text: string): string =>
  text.length <= 1000 ? text : `${text.slice(0, 999)}…`;

/**
 * Comments on the board through the shell's `customAnchors` override, which
 * switches the shell's own click-to-comment off, so comment mode is the
 * board's to run: a click on a line, a file or a control opens the shell's
 * composer there instead of acting, a drag across lines or over the toolbar
 * draws an area, and every thread whose subject is on screen is reported for
 * its pin.
 */
export function boardComments(): BoardComments {
  let board: BoardHandle | undefined;
  let controller: Controller | undefined;
  let area: AreaSelect | undefined;
  let threads: Thread[] = [];
  let composing = false;
  let composed: string | undefined;
  /** Chrome elements this view anchored threads to, found before the anchor is parsed as a selector. */
  const minted = new Map<string, Element>();

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
    if (anchor === undefined) return chromePoint(name);
    const subject = locate(handle, anchor);
    return subject === undefined ? null : pinPoint(subject);
  }

  /** Where the pin of a thread on one of the board's controls goes, or null while it is not shown. */
  function chromePoint(name: string): Claude.comments.DocPoint | null {
    if (controller === undefined) return null;
    const element = minted.get(name) ?? select(name);
    if (!element?.isConnected) return null;
    const rect = element.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) return null;
    return controller.domAnchor(element)[1];
  }

  function disable(): void {
    controller?.release();
    controller = undefined;
    area?.destroy();
    area = undefined;
    board?.setCommentsEnabled(false);
  }

  function open(
    anchor: string,
    at: Element | Claude.comments.DocPoint,
    opts: Claude.comments.ComposeOptions,
  ): void {
    if (controller === undefined) return;
    controller.compose(anchor, at, opts).then(
      (result) => {
        if (!result.opened && opts.area === true) area?.clear();
      },
      (error: unknown) => {
        area?.clear();
        if (isPermanent(error)) {
          disable();
          return;
        }
        throw error;
      },
    );
  }

  /** Opens the composer on a line, a range of lines through `through`, or a whole file. */
  function compose(
    target: CommentTarget,
    at: Element,
    through: number | null = null,
    drawn = false,
  ): void {
    if (board === undefined) return;
    const range = board.effectiveRange(target.path);
    if (range === undefined) return;
    const anchor = encodeAnchor({ ...target, ...range, through });
    composed = anchor;
    open(anchor, at, { label: label(target, through), area: drawn });
  }

  /** Opens the composer on one of the board's controls, anchored the way the shell anchors a DOM element. */
  function composeOnChrome(
    element: Element,
    at: { clientX: number; clientY: number },
    opts: Claude.comments.ComposeOptions,
  ): void {
    if (controller === undefined) return;
    const [anchor, point] = controller.domAnchor(element, at);
    minted.set(anchor, element);
    // The composer stays where the shell opened it: no report moves it.
    composed = undefined;
    open(anchor, point, opts);
  }

  function onRows(rows: HTMLElement[]): void {
    const first = rows[0];
    const last = rows.at(-1);
    const start =
      board === undefined || first === undefined
        ? undefined
        : rowTarget(board, first);
    const end =
      board === undefined || last === undefined
        ? undefined
        : rowTarget(board, last)?.line;
    if (first === undefined || start === undefined || end == null) {
      area?.clear();
      return;
    }
    compose(start, first, end === start.line ? null : end, true);
  }

  function onRect(box: DOMRect): void {
    const x = box.left + box.width / 2;
    const y = box.top + box.height / 2;
    const element = document.elementFromPoint(x, y);
    if (board === undefined || element === null) {
      area?.clear();
      return;
    }
    const names = covered(board.element, box);
    composeOnChrome(
      element,
      { clientX: x, clientY: y },
      {
        area: true,
        label: clip(names.slice(0, 3).join(", ")),
        detail: names.length === 0 ? "" : clip(`Covers: ${names.join(", ")}`),
      },
    );
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

  /**
   * In comment mode a click comments on what it lands on — a line, else the
   * file whose card or diff it is in, else a folder's head, else the control
   * — and never activates it. The board's own comment buttons keep their handlers.
   */
  function onModeClick(event: MouseEvent): void {
    const target = event.target;
    if (board === undefined || !(target instanceof Element)) return;
    const afterDrag = area?.consumeClick() === true;
    if (!afterDrag && target.closest(OWN_CONTROLS) !== null) return;
    event.preventDefault();
    event.stopPropagation();
    if (afterDrag) return;
    const row = target.closest<HTMLElement>(".row[data-line]");
    const line = row === null ? undefined : rowTarget(board, row);
    if (row !== null && line !== undefined) {
      compose(line, row);
      return;
    }
    const file = fileTarget(board, target);
    if (file !== undefined) {
      compose(file, target);
      return;
    }
    const folder = target.closest<HTMLElement>(".folder-head");
    if (folder !== null) {
      composeOnChrome(folder, event, {
        label: clip(`${folder.dataset["path"] ?? ""}/ folder`),
      });
      return;
    }
    // The canvas between the cards and folder heads is no subject.
    if (target.closest(".viewport") !== null) return;
    const control = target.closest(CONTROLS) ?? target;
    composeOnChrome(target, event, { label: clip(nameOf(control)) });
  }

  /** Keeps a press in comment mode from focusing, selecting or opening a dropdown. */
  function onModeDown(event: MouseEvent): void {
    const target = event.target;
    if (target instanceof Element && target.closest(OWN_CONTROLS) === null)
      event.preventDefault();
  }

  const callbacks: Claude.comments.CustomAnchorsCallbacks = {
    mode(on) {
      const root = board?.element;
      root?.classList.toggle("comment-mode", on);
      if (on) {
        root?.addEventListener("click", onModeClick, true);
        root?.addEventListener("mousedown", onModeDown, true);
      } else {
        root?.removeEventListener("click", onModeClick, true);
        root?.removeEventListener("mousedown", onModeDown, true);
        threads = [];
        area?.clear();
      }
    },
    threads(list) {
      threads = list;
      report();
    },
    reveal,
    composing(open) {
      composing = open;
      if (!open) {
        composed = undefined;
        area?.clear();
      }
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
      const runtime = claudeRuntime();
      if (runtime === null) return;
      const api = await runtime.use("comments");
      if (api === null) return;
      try {
        controller = await api.customAnchors(callbacks);
      } catch (error) {
        if (isPermanent(error)) return;
        throw error;
      }
      area = attachAreaSelect(handle.element, {
        enabled: () => controller?.areas === true,
        rows: onRows,
        rect: onRect,
      });
      handle.setCommentsEnabled(true);
      report();
    },
  };
}
