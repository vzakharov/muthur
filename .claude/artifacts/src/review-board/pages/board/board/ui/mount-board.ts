import {
  ageShades,
  createFileStore,
  fileDiff,
  matchesPath,
  viewFileUrl,
  type AgeShade,
  type EffectiveRange,
} from "#src/review-board/entities/file/index.ts";
import { attachViewport } from "#src/review-board/pages/board/camera/index.ts";
import { createCard } from "#src/review-board/pages/board/card/index.ts";
import { buildTree, pack } from "#src/review-board/pages/board/layout/index.ts";
import { createPanel } from "#src/review-board/pages/board/panel/index.ts";
import { createToolbar } from "#src/review-board/pages/board/toolbar/index.ts";
import { el } from "#src/review-board/shared/lib/dom.ts";
import { perFrame } from "#src/review-board/shared/lib/frame.ts";
import type { Rect } from "#src/review-board/shared/lib/geometry.ts";
import {
  boardTitle,
  type LineSpan,
  type ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import { commitLabels, commitTimes } from "../lib/labels.ts";
import { nextFocus } from "../lib/next-focus.ts";
import type {
  BoardHandle,
  BoardOptions,
  CommentsHook,
} from "../model/types.ts";
import { createFolderLayer, type FolderViewed } from "./folders.ts";
import { loadReviewData } from "./load-data.ts";
import { revealFocus } from "./reveal-focus.ts";

const PACK = { headerHeight: 28, padding: 12, gap: 16 };

/**
 * Mounts the review board into `root`: parses the embedded payload, renders a
 * card per file, packs them into folder rectangles on a pannable canvas and
 * keeps cards, toolbar and panel in step with the file store. A payload that
 * does not parse renders an error in place of the board and is rethrown.
 */
export function mountBoard(
  root: HTMLElement,
  options: BoardOptions = {},
): BoardHandle {
  const data = loadReviewData(root);
  const { comments } = options;
  const setCommentsEnabled = (enabled: boolean): void => {
    root.classList.toggle("no-comments", !enabled);
  };
  setCommentsEnabled(false);

  const store = createFileStore(data);
  const labelOf = commitLabels(data);
  const timeOf = commitTimes(data);
  const filesByPath = new Map(data.files.map((file) => [file.path, file]));
  const rects = new Map<string, Rect>();
  let bounds: Rect | undefined;
  let fitted = false;
  let panelPath: string | undefined;
  /** Files left off the board by an unchecked "Show viewed" (viewed, or no textual change), "Focus only" or the name filter. */
  const hidden = new Set<string>();
  let nameFilter = "";
  const focusByPath = new Map(data.focus.map((item) => [item.path, item]));
  let focusAt: number | null = null;

  /** Focus lines are numbered in the file at HEAD, so they mark only a diff ending on that content. */
  const marksFor = (file: ReviewFile, range: EffectiveRange): LineSpan[] => {
    const lines = focusByPath.get(file.path)?.lines;
    const head = file.revisions[file.revisions.length - 1];
    return lines !== undefined && range.toBlob === head?.blob ? lines : [];
  };

  const notifyVisible = perFrame(() => comments?.visibleChanged());
  const onComment: CommentsHook["onComment"] = (target, at) =>
    comments?.onComment(target, at);

  /** The files a folder's Viewed box marks: all under it but the focus files, which are viewed one by one. */
  const governed = (folder: string): ReviewFile[] =>
    data.files.filter(
      (file) =>
        file.path.startsWith(`${folder}/`) && !focusByPath.has(file.path),
    );
  const folderViewed = (folder: string): FolderViewed => {
    const files = governed(folder);
    if (files.length === 0) return null;
    const viewed = files.filter((file) => store.isViewed(file.path)).length;
    return {
      checked: viewed === files.length,
      mixed: viewed > 0 && viewed < files.length,
    };
  };

  const world = el("div", "world");
  const folders = createFolderLayer((folder, viewed) => {
    for (const file of governed(folder)) store.setViewed(file.path, viewed);
  });
  const cardLayer = el("div", "cards");
  world.append(folders.element, cardLayer);
  const viewportEl = el("div", "viewport");
  viewportEl.append(world);

  const viewport = attachViewport(viewportEl, world, {
    onChange: notifyVisible,
  });

  const closePanel = (): void => {
    panelPath = undefined;
    panel.close();
    notifyVisible();
  };
  const panel = createPanel({ onClose: closePanel, onComment });

  const cards = new Map(
    data.files.map((file) => [
      file.path,
      createCard(file, focusByPath.get(file.path), labelOf, timeOf, {
        onViewed: (viewed) => {
          store.setViewed(file.path, viewed);
        },
        onRange: (end, commit) => {
          store.setRange(
            file.path,
            end === "from" ? { from: commit } : { to: commit },
          );
        },
        onOpen: () => {
          openPanel(file.path);
        },
        onComment,
      }),
    ]),
  );
  for (const card of cards.values()) cardLayer.append(card.element);

  const toolbar = createToolbar(
    boardTitle(data.branch, data.pr),
    data.commits,
    data.base.sha,
    data.focus.length,
    labelOf,
    timeOf,
    {
      onFocus() {
        focusAt = nextFocus(
          focusAt,
          data.focus.map((focus) => store.isViewed(focus.path)),
        );
        const item = focusAt === null ? undefined : data.focus[focusAt];
        if (item !== undefined) stepTo(item.path);
        renderSoon();
      },
      onFit() {
        if (bounds !== undefined) viewport.fit(bounds);
      },
      onZoom: (factor) => {
        viewport.zoomBy(factor);
      },
      onRange(end, commit) {
        if (end === "to") {
          store.setBoard({ to: commit });
          return;
        }
        const to = store.board().to;
        const index = (sha: string): number =>
          data.commits.findIndex((candidate) => candidate.sha === sha);
        const stale =
          commit !== null && to !== null && index(to) <= index(commit);
        store.setBoard(stale ? { from: commit, to: null } : { from: commit });
      },
      onShowWhitespace: (show) => {
        store.setBoard({ showWhitespace: show });
      },
      // A filter changes which files are packed, so the next layout fits them anew.
      onShowViewed: (show) => {
        fitted = false;
        store.setBoard({ showViewed: show });
      },
      onFocusOnly: (only) => {
        fitted = false;
        store.setBoard({ focusOnly: only });
      },
      onFilter: (text) => {
        fitted = false;
        nameFilter = text;
        render();
      },
    },
  );

  const main = el("div", "main");
  main.append(viewportEl, panel.element);
  const app = el("div", "app");
  app.append(toolbar.element, main);
  root.replaceChildren(app);
  if (data.files.length === 0)
    viewportEl.append(el("div", "empty-board", "No changed files"));

  /** Until the viewer's saved state arrives, or the store is given up on, the board would show defaults it is about to replace. */
  const settled = (): boolean => {
    const status = store.status();
    return status !== "connecting" && status !== "loading";
  };

  const shadeOf = (
    shade: AgeShade | undefined,
  ): { level: number; tooltip: string } | null =>
    shade === undefined
      ? null
      : {
          level: shade.level,
          tooltip: `Last changed in ${labelOf(shade.commit)}, ${new Date(shade.date).toLocaleString()}`,
        };

  function render(): void {
    viewportEl.classList.toggle("is-loading", !settled());
    const board = store.board();
    let viewed = 0;
    hidden.clear();
    const shades = ageShades(data, data.files, board.to);
    for (const file of data.files) {
      const range = store.effective(file.path);
      const isViewed = store.isViewed(file.path);
      if (isViewed) viewed++;
      const offFocus =
        board.focusOnly && data.focus.length > 0 && !focusByPath.has(file.path);
      const diff = fileDiff(data, file, range, !board.showWhitespace);
      const empty = diff.kind === "text" && diff.diff.hunks.length === 0;
      if (
        ((isViewed || empty) && !board.showViewed) ||
        offFocus ||
        !matchesPath(file, nameFilter)
      )
        hidden.add(file.path);
      const card = cards.get(file.path);
      if (card === undefined) continue;
      card.element.hidden = hidden.has(file.path);
      card.update({
        range,
        viewed: isViewed,
        viewedAt: store.viewedAt(file.path),
        diff,
        marks: marksFor(file, range),
        viewUrl: viewFileUrl(data, file, range),
        shade: shadeOf(shades.get(file.path)),
      });
    }
    toolbar.update({
      from: board.from,
      to: board.to,
      showWhitespace: board.showWhitespace,
      showViewed: board.showViewed,
      focusOnly: board.focusOnly,
      viewed,
      total: data.files.length,
      status: store.status(),
      focusUnviewed: data.focus.filter((item) => !store.isViewed(item.path))
        .length,
    });
    renderPanel();
    layoutSoon();
    notifyVisible();
  }

  function renderPanel(): void {
    const file =
      panelPath === undefined ? undefined : filesByPath.get(panelPath);
    if (file === undefined) return;
    const range = store.effective(file.path);
    const diff = fileDiff(data, file, range, !store.board().showWhitespace);
    if (diff.kind !== "text") return;
    panel.show({
      path: file.path,
      diff: diff.diff,
      syntax: diff.syntax,
      fromLabel: labelOf(range.from),
      toLabel: labelOf(range.to),
      marks: marksFor(file, range),
    });
  }

  /**
   * Zooms to a focus file and brings its first marked line into view — in the
   * card, or in the panel when the card shows only a stub. A panel left open on
   * another file closes, so it never stands in for the file stepped to.
   */
  function stepTo(path: string): void {
    // The panel narrows the viewport, so the camera fits only once it is open or closed.
    const fit = (): void => {
      const rect = rects.get(path);
      if (rect !== undefined) viewport.fit(rect);
    };
    const body =
      cards.get(path)?.element.querySelector<HTMLElement>(".card-body") ?? null;
    const shown = body !== null && !body.hidden ? body : null;
    const stub = shown !== null && shown.querySelector(".row") === null;
    if (!stub || focusByPath.get(path)?.lines === undefined) {
      if (panelPath !== undefined && panelPath !== path) closePanel();
      fit();
      if (shown !== null) revealFocus(shown);
      return;
    }
    openPanel(path);
    fit();
    const panelBody = panel.element.querySelector<HTMLElement>(".panel-body");
    if (panelBody !== null) revealFocus(panelBody);
  }

  function layout(): void {
    const packed = pack(
      buildTree(
        data.files.map((file) => file.path).filter((path) => !hidden.has(path)),
      ),
      (path) => {
        const element = cards.get(path)?.element;
        return {
          width: element?.offsetWidth ?? 0,
          height: element?.offsetHeight ?? 0,
        };
      },
      PACK,
    );
    folders.sync(packed.folders, folderViewed);
    rects.clear();
    for (const placed of packed.files) {
      rects.set(placed.path, placed.rect);
      const element = cards.get(placed.path)?.element;
      if (element === undefined) continue;
      element.style.left = `${placed.rect.x}px`;
      element.style.top = `${placed.rect.y}px`;
    }
    bounds = packed.bounds;
    if (!fitted && settled() && data.files.length > 0) {
      fitted = true;
      viewport.fit(packed.bounds);
    }
    notifyVisible();
  }
  const layoutSoon = perFrame(layout);

  function openPanel(path: string): void {
    const file = filesByPath.get(path);
    if (file === undefined || file.binary) return;
    panelPath = path;
    renderPanel();
    notifyVisible();
  }

  const resizes = new ResizeObserver(layoutSoon);
  for (const card of cards.values()) resizes.observe(card.element);
  const renderSoon = perFrame(render);
  const unsubscribe = store.subscribe(renderSoon);
  viewportEl.addEventListener("scroll", notifyVisible, { capture: true });
  panel.element.addEventListener("scroll", notifyVisible, { capture: true });

  render();
  layout();

  return {
    element: root,
    paths: data.files.map((file) => file.path),
    setCommentsEnabled,
    cardElement: (path) => cards.get(path)?.element,
    effectiveRange(path) {
      if (!filesByPath.has(path)) return undefined;
      const { from, to } = store.effective(path);
      return { from, to };
    },
    panTo(path) {
      const rect = rects.get(path);
      if (rect !== undefined) viewport.panTo(rect);
    },
    openPanel,
    panel() {
      const path = panel.path();
      return path === undefined ? undefined : { path, element: panel.element };
    },
    destroy() {
      unsubscribe();
      store.destroy();
      resizes.disconnect();
      viewport.destroy();
    },
  };
}
