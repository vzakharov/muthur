import type { StoreStatus } from "#src/review-board/entities/file/index.ts";
import { el, setOptions } from "#src/review-board/shared/lib/dom.ts";
import type { ReviewCommit } from "#src/review-board/shared/review-data/index.ts";

export interface ToolbarState {
  /** The board's range; null is the base / the head. */
  from: string | null;
  to: string | null;
  whitespace: boolean;
  hideViewed: boolean;
  focusOnly: boolean;
  viewed: number;
  total: number;
  status: StoreStatus;
  /** The focus item last stepped to, or null before the first step. */
  focusAt: number | null;
}

export interface ToolbarHandlers {
  /** Steps to the next of the review's focus items. */
  onFocus(): void;
  onFit(): void;
  onZoom(factor: number): void;
  onRange(end: "from" | "to", commit: string | null): void;
  onWhitespace(hide: boolean): void;
  onHideViewed(hide: boolean): void;
  /** Leaves on the board only the files the author marked for focus. */
  onFocusOnly(only: boolean): void;
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

function checkbox(text: string, onChange: (checked: boolean) => void) {
  const box = el("input", "");
  box.type = "checkbox";
  box.addEventListener("change", () => {
    onChange(box.checked);
  });
  const label = el("label", "tool-check");
  label.append(box, text);
  return { box, label };
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

  const from = el("select", "range-select");
  from.ariaLabel = "Board range from";
  from.addEventListener("change", () => {
    handlers.onRange("from", from.value === DEFAULT_END ? null : from.value);
  });
  const to = el("select", "range-select");
  to.ariaLabel = "Board range to";
  to.addEventListener("change", () => {
    handlers.onRange("to", to.value === DEFAULT_END ? null : to.value);
  });
  const range = el("span", "tool-group range");
  range.append(el("span", "tool-label", "Range"), from, "→", to);

  const whitespace = checkbox("Hide whitespace", (hide) => {
    handlers.onWhitespace(hide);
  });
  const hideViewed = checkbox("Hide viewed", (hide) => {
    handlers.onHideViewed(hide);
  });

  const focus = button(
    "",
    "Go to the next file the author marked for focus",
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
    whitespace.label,
    hideViewed.label,
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
      setOptions(
        from,
        [
          { value: DEFAULT_END, label: `base · ${labelOf(baseSha)}` },
          ...commits.map((commit) => ({
            value: commit.sha,
            label: labelOf(commit.sha),
          })),
        ],
        state.from ?? DEFAULT_END,
      );
      const later = commits.slice(fromIndex + 1);
      setOptions(
        to,
        later.map((commit) => ({
          value: commit.sha === lastSha ? DEFAULT_END : commit.sha,
          label:
            commit.sha === lastSha
              ? `head · ${labelOf(commit.sha)}`
              : labelOf(commit.sha),
        })),
        state.to === null || state.to === lastSha ? DEFAULT_END : state.to,
      );
      whitespace.box.checked = state.whitespace;
      hideViewed.box.checked = state.hideViewed;
      focusOnly.box.checked = state.focusOnly;
      focus.textContent =
        state.focusAt === null
          ? `Focus · ${focusTotal}`
          : `Focus ${state.focusAt + 1}/${focusTotal}`;
      tally.textContent = `${state.viewed} / ${state.total} viewed`;
      note.textContent = NOTES[state.status];
    },
  };
}
