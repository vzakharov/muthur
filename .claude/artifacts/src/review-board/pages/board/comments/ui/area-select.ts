import { ROW } from "./targets.ts";

const DRAG_THRESHOLD = 3;

export interface AreaHandlers {
  /** Whether an area may be drawn right now. */
  enabled(): boolean;
  /** A drag across diff rows ended: the rows it covered on its first row's side, in order. */
  rows(rows: HTMLElement[]): void;
  /** A rectangle drawn over the board's chrome ended, in client coordinates. */
  rect(box: DOMRect): void;
}

export interface AreaSelect {
  /** Clears the drawn selection off the screen. */
  clear(): void;
  /** True once for the click a finished drag leaves behind, which is not a comment gesture. */
  consumeClick(): boolean;
  destroy(): void;
}

type Drawing =
  | { kind: "rows"; start: HTMLElement; pointerId: number; active: boolean }
  | {
      kind: "rect";
      x: number;
      y: number;
      pointerId: number;
      active: boolean;
      box: DOMRect;
    };

/** Rows from `start` to `end` inclusive, on `start`'s side of its diff. */
function rowsBetween(start: HTMLElement, end: HTMLElement): HTMLElement[] {
  const diff = start.closest(".diff");
  if (!diff?.contains(end)) return [start];
  const side = start.dataset["side"] ?? "";
  const all = [...diff.querySelectorAll<HTMLElement>(ROW)];
  const [a, b] = [all.indexOf(start), all.indexOf(end)].sort((x, y) => x - y);
  if (a === undefined || b === undefined || a < 0) return [start];
  return all.slice(a, b + 1).filter((row) => row.dataset["side"] === side);
}

/**
 * Lets the viewer draw a comment area in comment mode: a drag across diff rows
 * selects a line range, and a drag over the board's chrome (toolbar, panel
 * head) draws a rectangle. A drag starting on the canvas still pans.
 */
export function attachAreaSelect(
  root: HTMLElement,
  handlers: AreaHandlers,
): AreaSelect {
  let drawing: Drawing | undefined;
  let marked: HTMLElement[] = [];
  let overlay: HTMLElement | undefined;
  let swallowClick = false;
  const abort = new AbortController();
  const { signal } = abort;

  function mark(rows: HTMLElement[]): void {
    for (const row of marked) row.classList.remove("area-selected");
    marked = rows;
    for (const row of marked) row.classList.add("area-selected");
  }

  function clear(): void {
    mark([]);
    overlay?.remove();
    overlay = undefined;
  }

  function onDown(event: PointerEvent): void {
    swallowClick = false;
    if (event.button !== 0 || !event.isPrimary || !handlers.enabled()) return;
    const target = event.target;
    if (!(target instanceof Element)) return;
    const row = target.closest<HTMLElement>(ROW);
    if (row !== null) {
      drawing = {
        kind: "rows",
        start: row,
        pointerId: event.pointerId,
        active: false,
      };
      return;
    }
    // The canvas pans, and the panel's diff scrolls; neither draws.
    if (target.closest(".viewport, .panel-body") !== null) return;
    drawing = {
      kind: "rect",
      x: event.clientX,
      y: event.clientY,
      pointerId: event.pointerId,
      active: false,
      box: new DOMRect(event.clientX, event.clientY, 0, 0),
    };
  }

  function onMove(event: PointerEvent): void {
    if (drawing?.pointerId !== event.pointerId) return;
    if (!drawing.active) {
      // A press that stays on its row is a click on that line, not a range.
      const begun =
        drawing.kind === "rows"
          ? leftStart(drawing.start, event)
          : Math.hypot(event.clientX - drawing.x, event.clientY - drawing.y) >
            DRAG_THRESHOLD;
      if (!begun) return;
      drawing.active = true;
      clear();
      root.setPointerCapture(event.pointerId);
    }
    event.preventDefault();
    if (drawing.kind === "rows") {
      const over = document
        .elementFromPoint(event.clientX, event.clientY)
        ?.closest<HTMLElement>(ROW);
      if (over !== null && over !== undefined)
        mark(rowsBetween(drawing.start, over));
      else if (marked.length === 0) mark([drawing.start]);
      return;
    }
    drawing.box = new DOMRect(
      Math.min(drawing.x, event.clientX),
      Math.min(drawing.y, event.clientY),
      Math.abs(event.clientX - drawing.x),
      Math.abs(event.clientY - drawing.y),
    );
    overlay ??= root.appendChild(document.createElement("div"));
    overlay.className = "area-rect";
    overlay.style.left = `${drawing.box.x}px`;
    overlay.style.top = `${drawing.box.y}px`;
    overlay.style.width = `${drawing.box.width}px`;
    overlay.style.height = `${drawing.box.height}px`;
  }

  function onUp(event: PointerEvent): void {
    if (drawing?.pointerId !== event.pointerId) return;
    const finished = drawing;
    drawing = undefined;
    if (!finished.active) return;
    swallowClick = true;
    if (finished.kind === "rows") handlers.rows(marked);
    else handlers.rect(finished.box);
  }

  function onCancel(event: PointerEvent): void {
    if (drawing?.pointerId !== event.pointerId) return;
    drawing = undefined;
    clear();
  }

  root.addEventListener("pointerdown", onDown, { capture: true, signal });
  root.addEventListener("pointermove", onMove, { capture: true, signal });
  root.addEventListener("pointerup", onUp, { capture: true, signal });
  root.addEventListener("pointercancel", onCancel, { capture: true, signal });

  return {
    clear,
    consumeClick() {
      const swallowed = swallowClick;
      swallowClick = false;
      return swallowed;
    },
    destroy() {
      abort.abort();
      clear();
    },
  };
}

/** Whether the pointer has left the row the drag started on, vertically. */
function leftStart(start: Element, event: PointerEvent): boolean {
  const rect = start.getBoundingClientRect();
  return event.clientY < rect.top || event.clientY >= rect.bottom;
}
