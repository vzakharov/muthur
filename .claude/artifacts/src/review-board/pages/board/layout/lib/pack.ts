import type { Rect, Sized } from "#src/review-board/shared/lib/geometry.ts";
import type { FolderNode, TreeNode } from "./tree.ts";

export interface PackOptions {
  /** Height of a folder's header strip. */
  headerHeight: number;
  /** Space between a folder's edge and its children. */
  padding: number;
  /** Space between siblings, in a row and between rows. */
  gap: number;
}

export interface PackedFolder {
  kind: "folder";
  path: string;
  name: string;
  rect: Rect;
  header: Rect;
}
export interface PackedFile {
  kind: "file";
  path: string;
  rect: Rect;
}

export interface Packed {
  /** The box around everything; the root itself has no rectangle of its own. */
  bounds: Rect;
  /** Parents before their children. */
  folders: PackedFolder[];
  files: PackedFile[];
}

/** Width over height of the frame the packing aims for. */
const TARGET_ASPECT = 1.6;

interface Placed<T> {
  item: T;
  x: number;
  y: number;
}

/** A node's size and, relative to its own origin, where its children sit. */
interface Block {
  size: Sized;
  node: TreeNode;
  placed: Placed<Block>[];
}

interface Flow<T> {
  size: Sized;
  placed: Placed<T>[];
}

/** `items` filled into rows no wider than `rowWidth`, in order. */
function flow<T extends { size: Sized }>(
  items: readonly T[],
  rowWidth: number,
  gap: number,
): Flow<T> {
  const placed: Placed<T>[] = [];
  let x = 0;
  let y = 0;
  let rowHeight = 0;
  let width = 0;
  for (const item of items) {
    if (x > 0 && x + item.size.width > rowWidth) {
      y += rowHeight + gap;
      x = 0;
      rowHeight = 0;
    }
    placed.push({ item, x, y });
    x += item.size.width + gap;
    rowHeight = Math.max(rowHeight, item.size.height);
    width = Math.max(width, x - gap);
  }
  return { size: { width, height: y + rowHeight }, placed };
}

/** How far a frame's aspect is from the target, symmetric in wide and tall. */
const miss = (width: number, height: number): number =>
  Math.abs(Math.log(width / Math.max(height, 1) / TARGET_ASPECT));

/**
 * The flow whose frame (content plus `chrome` around it) is closest to the
 * target aspect; ties go to the smaller area, then the narrower row.
 */
function bestFlow<T extends { size: Sized }>(
  items: readonly T[],
  gap: number,
  chrome: Sized,
): Flow<T> {
  const widest = Math.max(...items.map((item) => item.size.width));
  const area = items.reduce(
    (sum, item) => sum + item.size.width * item.size.height,
    0,
  );
  const candidates = new Set<number>([
    widest,
    Math.max(widest, Math.sqrt(area * TARGET_ASPECT)),
  ]);
  let run = -gap;
  for (const item of items) {
    run += gap + item.size.width;
    candidates.add(Math.max(widest, run));
  }
  let best: { layout: Flow<T>; score: number; area: number } | undefined;
  for (const rowWidth of [...candidates].sort((a, b) => a - b)) {
    const layout = flow(items, rowWidth, gap);
    const width = layout.size.width + chrome.width;
    const height = layout.size.height + chrome.height;
    const score = miss(width, height);
    const frameArea = width * height;
    if (
      best === undefined ||
      score < best.score - 1e-9 ||
      (Math.abs(score - best.score) <= 1e-9 && frameArea < best.area)
    )
      best = { layout, score, area: frameArea };
  }
  if (best === undefined) throw new Error("no candidate row width");
  return best.layout;
}

function measureNode(
  node: TreeNode,
  measure: (filePath: string) => Sized,
  opts: PackOptions,
  isRoot: boolean,
): Block {
  if (node.kind === "file")
    return { size: measure(node.path), node, placed: [] };
  const kids = node.children.map((child) =>
    measureNode(child, measure, opts, false),
  );
  const padding = isRoot ? 0 : opts.padding;
  const header = isRoot ? 0 : opts.headerHeight;
  const chrome = { width: 2 * padding, height: header + 2 * padding };
  if (kids.length === 0) return { size: chrome, node, placed: [] };
  const layout = bestFlow(kids, opts.gap, chrome);
  return {
    size: {
      width: layout.size.width + chrome.width,
      height: layout.size.height + chrome.height,
    },
    node,
    placed: layout.placed.map(({ item, x, y }) => ({
      item,
      x: padding + x,
      y: header + padding + y,
    })),
  };
}

function emit(
  block: Block,
  x: number,
  y: number,
  opts: PackOptions,
  out: Packed,
  isRoot: boolean,
): void {
  const { node, size } = block;
  const rect = { x, y, ...size };
  if (node.kind === "file") {
    out.files.push({ kind: "file", path: node.path, rect });
    return;
  }
  if (!isRoot)
    out.folders.push({
      kind: "folder",
      path: node.path,
      name: node.name,
      rect,
      header: { x, y, width: size.width, height: opts.headerHeight },
    });
  for (const child of block.placed)
    emit(child.item, x + child.x, y + child.y, opts, out, false);
}

/**
 * Absolute rectangles for every folder and file of `tree`, rooted at the
 * origin. A file is as big as `measure` says; a folder is its header, its
 * children packed into rows aiming at 16:10, and padding around them.
 */
export function pack(
  tree: FolderNode,
  measure: (filePath: string) => Sized,
  opts: PackOptions,
): Packed {
  const root = measureNode(tree, measure, opts, true);
  const out: Packed = {
    bounds: { x: 0, y: 0, ...root.size },
    folders: [],
    files: [],
  };
  emit(root, 0, 0, opts, out, true);
  return out;
}
