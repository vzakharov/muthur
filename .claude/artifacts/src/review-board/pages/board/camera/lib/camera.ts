/**
 * The board's camera: a pan offset and a zoom applied to the world layer as
 * one CSS transform, with the screen ↔ world conversions every gesture needs.
 */

import type { Point, Rect } from "#src/review-board/shared/lib/geometry.ts";

export type Zoomed = Point & { zoom: number };

const MIN_ZOOM = 0.05;
const MAX_ZOOM = 3;

const clampZoom = (zoom: number): number =>
  Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom));

export const toWorld = (camera: Zoomed, screen: Point): Point => ({
  x: (screen.x - camera.x) / camera.zoom,
  y: (screen.y - camera.y) / camera.zoom,
});

/** `camera` zoomed by `factor`, the world point under `anchor` staying put. */
export function zoomAt(camera: Zoomed, anchor: Point, factor: number): Zoomed {
  const zoom = clampZoom(camera.zoom * factor);
  const world = toWorld(camera, anchor);
  return {
    zoom,
    x: anchor.x - world.x * zoom,
    y: anchor.y - world.y * zoom,
  };
}

/** The camera showing all of `bounds` inside a `viewport`, with a margin. */
export function fitTo(bounds: Rect, viewport: Rect, margin = 48): Zoomed {
  const zoom = clampZoom(
    Math.min(
      (viewport.width - 2 * margin) / Math.max(bounds.width, 1),
      (viewport.height - 2 * margin) / Math.max(bounds.height, 1),
      1,
    ),
  );
  return {
    zoom,
    x:
      viewport.x + (viewport.width - bounds.width * zoom) / 2 - bounds.x * zoom,
    y:
      viewport.y +
      (viewport.height - bounds.height * zoom) / 2 -
      bounds.y * zoom,
  };
}

export function union(rects: readonly Rect[]): Rect | undefined {
  if (rects.length === 0) return undefined;
  const left = Math.min(...rects.map((r) => r.x));
  const top = Math.min(...rects.map((r) => r.y));
  const right = Math.max(...rects.map((r) => r.x + r.width));
  const bottom = Math.max(...rects.map((r) => r.y + r.height));
  return { x: left, y: top, width: right - left, height: bottom - top };
}

export const centreOf = (rect: Rect): Point => ({
  x: rect.x + rect.width / 2,
  y: rect.y + rect.height / 2,
});

/** `camera` moved so the world point `target` sits at the screen point `at`. */
export const centred = (camera: Zoomed, target: Point, at: Point): Zoomed => ({
  zoom: camera.zoom,
  x: at.x - target.x * camera.zoom,
  y: at.y - target.y * camera.zoom,
});
