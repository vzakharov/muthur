import {
  markLines,
  renderDiff,
  renderMarkdown,
  type CommentTarget,
  type EffectiveRange,
  type FileDiff,
} from "#src/review-board/entities/file/index.ts";
import type { DiffResult } from "#src/review-board/shared/lib/diff.ts";
import { checkbox, el, setOptions } from "#src/review-board/shared/lib/dom.ts";
import type {
  Focus,
  LineSpan,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";

/** Above this many added plus removed lines a card shows a stub and the diff opens in the panel. */
const CHANGED_LINES_CAP = 200;

export interface CardState {
  range: EffectiveRange;
  viewed: boolean;
  /** The Viewed mark or range was changed here and no write of it has succeeded. */
  unsaved: boolean;
  diff: FileDiff;
  /** New-side lines to mark as the review's focus; empty while the diff does not end at HEAD. */
  marks: readonly LineSpan[];
  /** GitHub's page for the file's shown version; null where there is none. */
  viewUrl: string | null;
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

const MARKDOWN = /\.md$/i;

const formatSize = (bytes: number | null): string =>
  bytes === null ? "absent" : `${bytes.toLocaleString("en-US")} B`;

const COPY_LABEL = "⧉";

/** The file's name alone, since the folder boxes around the card show its directory, and a button copying its repo-relative path. */
function pathParts(path: string): HTMLElement[] {
  const name = el("strong", "path", path.slice(path.lastIndexOf("/") + 1));
  name.title = path;
  const copy = el("button", "copy-path", COPY_LABEL);
  copy.type = "button";
  copy.title = `Copy ${path}`;
  copy.ariaLabel = copy.title;
  copy.addEventListener("click", () => {
    navigator.clipboard.writeText(path).then(
      () => {
        flash(copy, "✓", `Copied ${path}`);
      },
      (error: unknown) => {
        flash(copy, "✗", `Copy failed: ${String(error)}`);
      },
    );
  });
  return [name, copy];
}

function flash(button: HTMLButtonElement, mark: string, title: string): void {
  const { title: before } = button;
  button.textContent = mark;
  button.title = title;
  setTimeout(() => {
    button.textContent = COPY_LABEL;
    button.title = before;
  }, 1500);
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
 * collapses the card to its header. A file in the review's focus carries a
 * badge and its reason under the header. A Markdown file's "Rendered" switch
 * replaces the diff with the file's text at the range's `to`, rendered.
 */
export function createCard(
  file: ReviewFile,
  focus: Focus | undefined,
  labelOf: (sha: string) => string,
  handlers: CardHandlers,
): Card {
  const element = el("article", `card status-${file.status}`);
  element.dataset["path"] = file.path;
  element.classList.toggle("is-focus", focus !== undefined);

  const header = el("header", "card-head");
  const { box: viewedBox, label: viewedLabel } = checkbox(
    "Viewed",
    (viewed) => {
      handlers.onViewed(viewed);
    },
    "viewed",
  );

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
      label: labelOf(revision.commit),
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

  const focusBadge =
    focus === undefined ? [] : [el("span", "badge focus", "focus")];

  const viewFile = el("a", "view-file", "View file");
  viewFile.target = "_blank";
  viewFile.rel = "noopener noreferrer";
  viewFile.title = "Open this version on GitHub";

  let preview = false;
  let last: CardState | undefined;
  const { box: previewBox, label: previewLabel } = checkbox(
    "Rendered",
    (on) => {
      preview = on;
      if (last !== undefined) renderBody(last);
    },
    "preview-toggle",
  );
  previewLabel.hidden = !MARKDOWN.test(file.path);

  header.append(
    viewedLabel,
    ...pathParts(file.path),
    badge,
    ...focusBadge,
    counts,
    range,
    previewLabel,
    viewFile,
    comment,
  );
  const body = el("div", "card-body");
  element.append(header);
  if (focus !== undefined) element.append(el("p", "focus-why", focus.why));
  element.append(body);

  let rendered: DiffResult | string | undefined;

  function renderBody(state: CardState): void {
    const asDocument = preview && state.diff.kind === "text";
    const key =
      state.diff.kind === "text"
        ? asDocument
          ? `doc:${state.diff.after ?? ""}:${state.diff.after === null}`
          : state.diff.diff
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
    body.classList.toggle("has-doc", false);
    if (state.diff.kind === "binary") {
      body.replaceChildren(
        stubBody(
          `Binary file — ${formatSize(state.diff.fromSize)} → ${formatSize(state.diff.toSize)}`,
        ),
      );
      return;
    }
    if (asDocument) {
      const { after } = state.diff;
      if (after === null) {
        body.replaceChildren(stubBody("File absent at this revision"));
        return;
      }
      body.classList.add("has-doc");
      body.replaceChildren(renderMarkdown(after));
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
        syntax: state.diff.syntax(),
        onComment: (target, at) => {
          handlers.onComment(target, at);
        },
      }),
    );
  }

  return {
    element,
    update(state) {
      last = state;
      previewBox.checked = preview;
      viewFile.hidden = state.viewUrl === null;
      if (state.viewUrl !== null) viewFile.href = state.viewUrl;
      element.classList.toggle("is-viewed", state.viewed);
      viewedBox.checked = state.viewed;
      viewedLabel.classList.toggle("is-unsaved", state.unsaved);
      viewedLabel.title = state.unsaved ? "Not saved yet" : "";
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
      markLines(body, state.marks);
    },
  };
}
