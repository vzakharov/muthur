import { el } from "./dom.ts";

export interface PickerOption {
  value: string;
  label: string;
  /** Secondary lines under the label, such as a time. */
  lines?: readonly string[];
  /** Draws the row apart, for an option that carries something the viewer set. */
  marked?: boolean;
}

export interface Picker {
  element: HTMLElement;
  /** Replaces the options and the chosen value; the open list is left alone when nothing changed. */
  set(options: readonly PickerOption[], value: string): void;
}

const EDGE = 8;

/**
 * A drop-down in place of a `<select>`: a button showing the chosen option and
 * a list in the top layer (Popover API), so it escapes a transformed or
 * clipping ancestor. The list is placed from the button's screen rectangle,
 * below it or above when there is more room, and keeps its natural size
 * whatever the board's zoom.
 */
export function createPicker(
  label: string,
  onPick: (value: string) => void,
): Picker {
  const element = el("span", "picker");
  const button = el("button", "picker-btn");
  button.type = "button";
  button.ariaLabel = label;
  button.title = label;
  const text = el("span", "picker-text");
  button.append(text, el("span", "picker-caret", "▾"));
  const list = el("div", "picker-list");
  list.popover = "auto";
  element.append(button, list);
  // Linking the button as the list's invoker keeps a press on it from light-dismissing the list,
  // so a second click closes rather than reopens it; the click handler toggles instead, to place it.
  button.popoverTargetElement = list;

  button.addEventListener("click", (event) => {
    event.preventDefault();
    if (list.matches(":popover-open")) {
      list.hidePopover();
      return;
    }
    list.showPopover();
    place(button.getBoundingClientRect(), list);
  });

  let signature = "";
  let current = "";
  const mark = (): void => {
    for (const row of list.children)
      row.classList.toggle(
        "is-current",
        row instanceof HTMLElement && row.dataset["value"] === current,
      );
  };

  return {
    element,
    set(options, value) {
      current = value;
      text.textContent =
        options.find((option) => option.value === value)?.label ?? "";
      const next = JSON.stringify(options);
      if (next !== signature) {
        signature = next;
        list.replaceChildren(
          ...options.map((option) => {
            const row = el("button", "picker-row");
            row.type = "button";
            row.dataset["value"] = option.value;
            row.classList.toggle("is-marked", option.marked === true);
            row.append(el("span", "picker-label", option.label));
            for (const line of option.lines ?? [])
              row.append(el("span", "picker-line", line));
            row.addEventListener("click", () => {
              list.hidePopover();
              onPick(option.value);
            });
            return row;
          }),
        );
      }
      mark();
    },
  };
}

function place(anchor: DOMRect, list: HTMLElement): void {
  const below = window.innerHeight - anchor.bottom - EDGE;
  const above = anchor.top - EDGE;
  const down = below >= Math.min(list.scrollHeight, 240) || below >= above;
  list.style.maxHeight = `${Math.max(120, down ? below : above)}px`;
  const { width, height } = list.getBoundingClientRect();
  const left = Math.min(
    Math.max(EDGE, anchor.left),
    window.innerWidth - width - EDGE,
  );
  list.style.left = `${Math.max(EDGE, left)}px`;
  list.style.top = `${down ? anchor.bottom + 2 : Math.max(EDGE, anchor.top - height - 2)}px`;
}
