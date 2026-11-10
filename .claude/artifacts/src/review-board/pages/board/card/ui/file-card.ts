import {
  renderDiff,
  type CommentTarget,
  type EffectiveRange,
  type FileDiff,
} from "#src/review-board/entities/file/index.ts";
import type { DiffResult } from "#src/review-board/shared/lib/diff.ts";
import { el, setOptions } from "#src/review-board/shared/lib/dom.ts";
import type { ReviewFile } from "#src/review-board/shared/review-data/index.ts";

/** Above this many added plus removed lines a card shows a stub and the diff opens in the panel. */
const CHANGED_LINES_CAP = 200;

export interface CardState {
  range: EffectiveRange;
  viewed: boolean;
  diff: FileDiff;
}

export interface CardHandlers {
  onViewed(viewed: boolean): void;
  /** A null commit clears that end of the file's own range back to the board's. */
  onRange(end: "from" | "to", commit: string | null): void;
  onOpen(): void;
  onComment(target: CommentTarget, at: Element): void;
}

export interface Card {
  element: HTMLElement;
  update(state: CardState): void;
}

const BOARD_RANGE = "";

const formatSize = (bytes: number | null): string =>
  bytes === null ? "absent" : `${bytes.toLocaleString("en-US")} B`;

function pathParts(path: string): HTMLElement {
  const slash = path.lastIndexOf("/");
  const node = el("span", "path");
  node.title = path;
  if (slash >= 0) node.append(el("span", "dir", path.slice(0, slash + 1)));
  node.append(el("strong", "name", path.slice(slash + 1)));
  return node;
}

function stubBody(text: string, onOpen?: () => void): HTMLElement {
  const stub = el("div", "stub");
  if (onOpen === undefined) {
    stub.textContent = text;
    return stub;
  }
  const open = el("button", "stub-open", text);
  open.type = "button";
  open.addEventListener("click", onOpen);
  stub.append(open);
  return stub;
}

function select(label: string, onChange: (value: string) => void) {
  const node = el("select", "range-select");
  node.ariaLabel = label;
  node.title = label;
  node.addEventListener("change", () => {
    onChange(node.value);
  });
  return node;
}

/**
 * A file's rectangle on the board: a header (path, status, counts, viewed,
 * range selectors, comment) over a diff body capped in height and scrolling
 * inside. Past the line cap the body is a stub that opens the panel; viewed
 * collapses the card to its header.
 */
export function createCard(
  file: ReviewFile,
  labels: ReadonlyMap<string, string>,
  handlers: CardHandlers,
): Card {
  const element = el("article", `card status-${file.status}`);
  element.dataset["path"] = file.path;

  const header = el("header", "card-head");
  const viewedBox = el("input", "viewed-box");
  viewedBox.type = "checkbox";
  viewedBox.addEventListener("change", () => {
    handlers.onViewed(viewedBox.checked);
  });
  const viewedLabel = el("label", "viewed");
  viewedLabel.append(viewedBox, el("span", "viewed-text", "Viewed"));

  const badge = el("span", `badge ${file.status}`, file.status);
  if (file.oldPath !== null) badge.title = `renamed from ${file.oldPath}`;
  const counts = el("span", "counts");
  const added = el("span", "added");
  const removed = el("span", "removed");
  counts.append(added, " ", removed);

  const comment = el("button", "comment-btn", "Comment");
  comment.type = "button";
  comment.title = "Comment on this file";
  comment.addEventListener("click", () => {
    handlers.onComment({ path: file.path, side: null, line: null }, comment);
  });

  const options = [
    { value: BOARD_RANGE, label: "Board range" },
    ...file.revisions.map((revision) => ({
      value: revision.commit,
      label: labels.get(revision.commit) ?? revision.commit.slice(0, 7),
    })),
  ];
  const from = select("Diff from", (value) => {
    handlers.onRange("from", value === BOARD_RANGE ? null : value);
  });
  const to = select("Diff to", (value) => {
    handlers.onRange("to", value === BOARD_RANGE ? null : value);
  });
  const range = el("span", "range");
  range.append(from, el("span", "arrow", "→"), to);

  header.append(
    viewedLabel,
    pathParts(file.path),
    badge,
    counts,
    range,
    comment,
  );
  const body = el("div", "card-body");
  element.append(header, body);

  let rendered: DiffResult | string | undefined;

  function renderBody(state: CardState): void {
    const key =
      state.diff.kind === "text"
        ? state.diff.diff
        : `binary:${state.diff.fromSize}:${state.diff.toSize}`;
    if (state.viewed) {
      body.hidden = true;
      body.replaceChildren();
      rendered = undefined;
      return;
    }
    body.hidden = false;
    if (key === rendered) return;
    rendered = key;
    body.classList.toggle("has-diff", false);
    if (state.diff.kind === "binary") {
      body.replaceChildren(
        stubBody(
          `Binary file — ${formatSize(state.diff.fromSize)} → ${formatSize(state.diff.toSize)}`,
        ),
      );
      return;
    }
    const { diff } = state.diff;
    const changed = diff.added + diff.removed;
    if (changed > CHANGED_LINES_CAP) {
      body.replaceChildren(
        stubBody(`${changed} changed lines — open`, () => {
          handlers.onOpen();
        }),
      );
      return;
    }
    body.classList.add("has-diff");
    body.replaceChildren(
      renderDiff(diff, {
        path: file.path,
        onComment: (target, at) => {
          handlers.onComment(target, at);
        },
      }),
    );
  }

  return {
    element,
    update(state) {
      element.classList.toggle("is-viewed", state.viewed);
      viewedBox.checked = state.viewed;
      const { diff, range: current } = state;
      added.textContent = diff.kind === "text" ? `+${diff.diff.added}` : "";
      removed.textContent = diff.kind === "text" ? `−${diff.diff.removed}` : "";
      setOptions(
        from,
        options,
        current.fromExplicit ? current.from : BOARD_RANGE,
      );
      setOptions(to, options, current.toExplicit ? current.to : BOARD_RANGE);
      renderBody(state);
    },
  };
}
