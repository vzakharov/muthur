import {
  markedCommits,
  markLines,
  renderDiff,
  renderMarkdown,
  type CommentTarget,
  type EffectiveRange,
  type FileDiff,
} from "#src/review-board/entities/file/index.ts";
import type { DiffResult } from "#src/review-board/shared/lib/diff.ts";
import { checkbox, el } from "#src/review-board/shared/lib/dom.ts";
import {
  createPicker,
  type PickerOption,
} from "#src/review-board/shared/lib/picker.ts";
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
  /** When each blob of the file was marked viewed, by blob token. */
  viewedAt: ReadonlyMap<string, string>;
  diff: FileDiff;
  /** New-side lines to mark as the review's focus; empty while the diff does not end at HEAD. */
  marks: readonly LineSpan[];
  /** GitHub's page for the file's shown version; null where there is none. */
  viewUrl: string | null;
  /** How recently the file last changed on the branch, for the header's tint; null for a file with no change of its own. */
  shade: { level: number; tooltip: string } | null;
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

/**
 * The file's name alone, since the folder boxes around the card show its
 * directory, linked to GitHub, and a button copying its repo-relative path.
 */
function pathParts(path: string): {
  link: HTMLAnchorElement;
  parts: HTMLElement[];
} {
  const name = el("strong", "path");
  name.title = path;
  const link = el("a", "path-link", path.slice(path.lastIndexOf("/") + 1));
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  name.append(link);
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
  return { link, parts: [name, copy] };
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

const SVG_NS = "http://www.w3.org/2000/svg";

function eyeIcon(): SVGSVGElement {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.classList.add("icon");
  const lid = document.createElementNS(SVG_NS, "path");
  lid.setAttribute("d", "M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z");
  const pupil = document.createElementNS(SVG_NS, "circle");
  pupil.setAttribute("cx", "12");
  pupil.setAttribute("cy", "12");
  pupil.setAttribute("r", "3");
  svg.append(lid, pupil);
  return svg;
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
  timeOf: (sha: string) => string,
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

  const open = el("button", "open-btn");
  open.append(eyeIcon());
  open.type = "button";
  open.title = "Open in the side panel";
  open.ariaLabel = open.title;
  open.hidden = file.binary;
  open.addEventListener("click", () => {
    handlers.onOpen();
  });

  const comment = el("button", "comment-btn", "Comment");
  comment.type = "button";
  comment.title = "Comment on this file";
  comment.addEventListener("click", () => {
    handlers.onComment({ path: file.path, side: null, line: null }, comment);
  });

  const optionsFor = (marked: ReadonlyMap<string, string>): PickerOption[] => [
    { value: BOARD_RANGE, label: "Board range" },
    ...file.revisions.map((revision) => {
      const committed = timeOf(revision.commit);
      const viewedAt = marked.get(revision.commit);
      return {
        value: revision.commit,
        label: labelOf(revision.commit),
        lines: [
          ...(committed === "" ? [] : [`committed ${committed}`]),
          ...(viewedAt === undefined
            ? []
            : [`✓ viewed ${new Date(viewedAt).toLocaleString()}`]),
        ],
        marked: viewedAt !== undefined,
      };
    }),
  ];
  const from = createPicker("Diff from", (value) => {
    handlers.onRange("from", value === BOARD_RANGE ? null : value);
  });
  const to = createPicker("Diff to", (value) => {
    handlers.onRange("to", value === BOARD_RANGE ? null : value);
  });
  const range = el("span", "range");
  range.append(from.element, el("span", "arrow", "→"), to.element);

  const focusBadge =
    focus === undefined ? [] : [el("span", "badge focus", "focus")];

  const { link: nameLink, parts: pathElements } = pathParts(file.path);

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
    ...pathElements,
    badge,
    ...focusBadge,
    counts,
    range,
    previewLabel,
    open,
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
      if (state.viewUrl === null) nameLink.removeAttribute("href");
      else nameLink.href = state.viewUrl;
      element.classList.toggle("is-viewed", state.viewed);
      viewedBox.checked = state.viewed;
      element.classList.toggle("is-aged", state.shade !== null);
      if (state.shade === null) element.style.removeProperty("--age");
      else element.style.setProperty("--age", String(state.shade.level));
      header.title = state.shade?.tooltip ?? "";
      const { diff, range: current } = state;
      added.textContent = diff.kind === "text" ? `+${diff.diff.added}` : "";
      removed.textContent = diff.kind === "text" ? `−${diff.diff.removed}` : "";
      from.set(
        optionsFor(markedCommits(file, state.viewedAt)),
        current.fromExplicit ? current.from : BOARD_RANGE,
      );
      to.set(
        optionsFor(new Map()),
        current.toExplicit ? current.to : BOARD_RANGE,
      );
      renderBody(state);
      markLines(body, state.marks);
    },
  };
}
