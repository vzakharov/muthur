import type { Point, Rect } from "#src/review-board/shared/lib/geometry.ts";
import {
  centreOf,
  centred,
  fitTo,
  zoomAt,
  type Zoomed,
} from "../lib/camera.ts";
import { scrollsInside } from "./scroll.ts";

export interface ViewportOptions {
  /** Whether a drag starting on `target` pans (background, card headers) rather than belonging to it (a diff body). */
  isPanSurface(target: EventTarget): boolean;
  onChange(camera: Zoomed): void;
}

export interface Viewport {
  fit(bounds: Rect): void;
  zoomBy(factor: number): void;
  /** Centres a world rectangle in the viewport, keeping the zoom. */
  panTo(worldRect: Rect): void;
  camera(): Zoomed;
  destroy(): void;
}

interface Drag {
  start: Point;
  camera: Zoomed;
  pointerId: number;
  active: boolean;
}
interface Pinch {
  distance: number;
  centre: Point;
  camera: Zoomed;
}

const DRAG_THRESHOLD = 3;
const LINE_HEIGHT = 16;

const distance = (a: Point, b: Point): number =>
  Math.hypot(a.x - b.x, a.y - b.y);

/**
 * Applies a pan/zoom camera to `world` as a CSS transform. The viewport takes
 * `touch-action: none` so pinches reach it as pointer events.
 */
export function attachViewport(
  viewport: HTMLElement,
  world: HTMLElement,
  opts: ViewportOptions,
): Viewport {
  let camera: Zoomed = { x: 0, y: 0, zoom: 1 };
  let drag: Drag | undefined;
  let pinch: Pinch | undefined;
  const pointers = new Map<number, Point>();
  const abort = new AbortController();
  const { signal } = abort;

  viewport.style.touchAction = "none";
  world.style.transformOrigin = "0 0";

  const screenPoint = (event: { clientX: number; clientY: number }): Point => {
    const box = viewport.getBoundingClientRect();
    return { x: event.clientX - box.left, y: event.clientY - box.top };
  };

  const size = (): { width: number; height: number } => {
    const { width, height } = viewport.getBoundingClientRect();
    return { width, height };
  };

  function set(next: Zoomed): void {
    camera = next;
    world.style.transform = `translate(${camera.x}px, ${camera.y}px) scale(${camera.zoom})`;
    opts.onChange(camera);
  }

  const screenCentre = (): Point => {
    const { width, height } = size();
    return { x: width / 2, y: height / 2 };
  };

  function startPinch(): void {
    const [a, b] = [...pointers.values()];
    if (a === undefined || b === undefined) return;
    pinch = {
      distance: Math.max(distance(a, b), 1),
      centre: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 },
      camera,
    };
    drag = undefined;
  }

  viewport.addEventListener(
    "pointerdown",
    (event) => {
      const point = screenPoint(event);
      pointers.set(event.pointerId, point);
      if (pointers.size === 2) {
        startPinch();
        return;
      }
      if (
        pointers.size === 1 &&
        event.button === 0 &&
        event.target !== null &&
        opts.isPanSurface(event.target)
      )
        drag = {
          start: point,
          camera,
          pointerId: event.pointerId,
          active: false,
        };
    },
    { signal },
  );

  viewport.addEventListener(
    "pointermove",
    (event) => {
      if (!pointers.has(event.pointerId)) return;
      const point = screenPoint(event);
      pointers.set(event.pointerId, point);
      const [a, b] = [...pointers.values()];
      if (pinch !== undefined && a !== undefined && b !== undefined) {
        set(
          zoomAt(pinch.camera, pinch.centre, distance(a, b) / pinch.distance),
        );
        return;
      }
      if (drag?.pointerId !== event.pointerId) return;
      const dx = point.x - drag.start.x;
      const dy = point.y - drag.start.y;
      if (!drag.active) {
        if (Math.hypot(dx, dy) <= DRAG_THRESHOLD) return;
        drag.active = true;
        // Captured only once it is a drag, so a plain click still reaches what it landed on.
        viewport.setPointerCapture(event.pointerId);
      }
      set({ ...drag.camera, x: drag.camera.x + dx, y: drag.camera.y + dy });
    },
    { signal },
  );

  function endPointer(event: PointerEvent): void {
    pointers.delete(event.pointerId);
    if (pointers.size < 2) pinch = undefined;
    if (drag?.pointerId === event.pointerId) drag = undefined;
  }
  viewport.addEventListener("pointerup", endPointer, { signal });
  viewport.addEventListener("pointercancel", endPointer, { signal });

  viewport.addEventListener(
    "wheel",
    (event) => {
      const scale =
        event.deltaMode === WheelEvent.DOM_DELTA_LINE ? LINE_HEIGHT : 1;
      const dx = event.deltaX * scale;
      const dy = event.deltaY * scale;
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault();
        set(zoomAt(camera, screenPoint(event), Math.exp(-dy / 200)));
        return;
      }
      if (scrollsInside(event.target, viewport, dx, dy)) return;
      event.preventDefault();
      set({ ...camera, x: camera.x - dx, y: camera.y - dy });
    },
    { signal, passive: false },
  );

  return {
    fit(bounds) {
      set(fitTo(bounds, { x: 0, y: 0, ...size() }));
    },
    zoomBy(factor) {
      set(zoomAt(camera, screenCentre(), factor));
    },
    panTo(worldRect) {
      set(centred(camera, centreOf(worldRect), screenCentre()));
    },
    camera: () => camera,
    destroy() {
      abort.abort();
    },
  };
}
