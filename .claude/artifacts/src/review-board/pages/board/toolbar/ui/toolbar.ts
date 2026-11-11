import type { StoreStatus } from "#src/review-board/entities/file/index.ts";
import { checkbox, el } from "#src/review-board/shared/lib/dom.ts";
import {
  createPicker,
  type PickerOption,
} from "#src/review-board/shared/lib/picker.ts";
import type { ReviewCommit } from "#src/review-board/shared/review-data/index.ts";

export interface ToolbarState {
  /** The board's range; null is the base / the head. */
  from: string | null;
  to: string | null;
  showWhitespace: boolean;
  showViewed: boolean;
  focusOnly: boolean;
  viewed: number;
  total: number;
  status: StoreStatus;
  focusUnviewed: number;
}

export interface ToolbarHandlers {
  /** Steps to the next unviewed focus item, or the next of all once each is viewed. */
  onFocus(): void;
  onFit(): void;
  onZoom(factor: number): void;
  onRange(end: "from" | "to", commit: string | null): void;
  onShowWhitespace(show: boolean): void;
  onShowViewed(show: boolean): void;
  /** Leaves on the board only the files the author marked for focus. */
  onFocusOnly(only: boolean): void;
  /** Leaves on the board only the files whose path contains the text; empty clears it. */
  onFilter(text: string): void;
}

export interface Toolbar {
  element: HTMLElement;
  update(state: ToolbarState): void;
}

const ZOOM_STEP = 1.25;
const DEFAULT_END = "";

const NOTES: Record<StoreStatus, string> = {
  connecting: "",
  loading: "Loading saved state…",
  slow: "Saved state can't be reached yet",
  ready: "",
  visit: "Marks and ranges last for this visit only",
};

function button(text: string, title: string, onClick: () => void) {
  const node = el("button", "tool-btn", text);
  node.type = "button";
  node.title = title;
  node.ariaLabel = title;
  node.addEventListener("click", onClick);
  return node;
}

/**
 * Fit / zoom, the step through the review's focus items (absent when it has
 * none), the board's commit range, the whitespace and viewed-file toggles and
 * the viewed tally.
 */
export function createToolbar(
  title: string,
  commits: readonly ReviewCommit[],
  baseSha: string,
  focusTotal: number,
  labelOf: (sha: string) => string,
  timeOf: (sha: string) => string,
  handlers: ToolbarHandlers,
): Toolbar {
  const element = el("div", "toolbar");
  const lastSha = commits[commits.length - 1]?.sha ?? baseSha;

  const heading = el("span", "toolbar-title", title);
  heading.title = title;

  const zoom = el("span", "tool-group");
  zoom.append(
    button("Fit", "Fit all files in view", () => {
      handlers.onFit();
    }),
    button("−", "Zoom out", () => {
      handlers.onZoom(1 / ZOOM_STEP);
    }),
    button("+", "Zoom in", () => {
      handlers.onZoom(ZOOM_STEP);
    }),
  );

  const from = createPicker("Board range from", (value) => {
    handlers.onRange("from", value === DEFAULT_END ? null : value);
  });
  const to = createPicker("Board range to", (value) => {
    handlers.onRange("to", value === DEFAULT_END ? null : value);
  });
  const range = el("span", "tool-group range");
  range.append(
    el("span", "tool-label", "Range"),
    from.element,
    "→",
    to.element,
  );
  const optionOf = (sha: string, value: string, prefix = ""): PickerOption => {
    const committed = timeOf(sha);
    return {
      value,
      label: `${prefix}${labelOf(sha)}`,
      lines: committed === "" ? [] : [`committed ${committed}`],
    };
  };

  const whitespace = checkbox("Show whitespace", (show) => {
    handlers.onShowWhitespace(show);
  });
  const showViewed = checkbox("Show viewed", (show) => {
    handlers.onShowViewed(show);
  });
  showViewed.label.title =
    "Show the files marked viewed and those with no textual change";

  const filter = el("input", "file-filter");
  filter.type = "search";
  filter.placeholder = "Filter files";
  filter.ariaLabel = "Filter files by path";
  filter.addEventListener("input", () => {
    handlers.onFilter(filter.value);
  });

  const focus = button(
    "",
    "Go to the next unviewed file the author marked for focus (unviewed / all)",
    () => {
      handlers.onFocus();
    },
  );
  focus.classList.add("focus-step");
  const focusOnly = checkbox("Focus only", (only) => {
    handlers.onFocusOnly(only);
  });
  focusOnly.label.title = "Show only the files the author marked for focus";
  const focusGroup = el("span", "tool-group");
  focusGroup.append(focus, focusOnly.label);
  focusGroup.hidden = focusTotal === 0;

  const tally = el("span", "tally");
  const note = el("span", "note");
  element.append(
    heading,
    zoom,
    focusGroup,
    range,
    // What decides which files show, and the tally, start a row of their own, whatever the width.
    el("span", "toolbar-break"),
    filter,
    whitespace.label,
    showViewed.label,
    tally,
    note,
  );

  return {
    element,
    update(state) {
      const fromIndex =
        state.from === null
          ? -1
          : commits.findIndex((commit) => commit.sha === state.from);
      from.set(
        [
          optionOf(baseSha, DEFAULT_END, "base · "),
          ...commits.map((commit) => optionOf(commit.sha, commit.sha)),
        ],
        state.from ?? DEFAULT_END,
      );
      const later = commits.slice(fromIndex + 1);
      to.set(
        later.map((commit) =>
          commit.sha === lastSha
            ? optionOf(commit.sha, DEFAULT_END, "head · ")
            : optionOf(commit.sha, commit.sha),
        ),
        state.to === null || state.to === lastSha ? DEFAULT_END : state.to,
      );
      whitespace.box.checked = state.showWhitespace;
      showViewed.box.checked = state.showViewed;
      focusOnly.box.checked = state.focusOnly;
      focus.textContent = `Focus ${state.focusUnviewed}/${focusTotal}`;
      tally.textContent = `${state.viewed} / ${state.total} viewed`;
      note.textContent = NOTES[state.status];
    },
  };
}
