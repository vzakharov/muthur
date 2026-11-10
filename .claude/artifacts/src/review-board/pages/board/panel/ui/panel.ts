import {
  renderDiff,
  type CommentTarget,
} from "#src/review-board/entities/file/index.ts";
import type { DiffResult } from "#src/review-board/shared/lib/diff.ts";
import { el } from "#src/review-board/shared/lib/dom.ts";

export interface PanelContent {
  path: string;
  diff: DiffResult;
  /** The range shown, as labels ("abc1234 subject"). */
  fromLabel: string;
  toLabel: string;
}

export interface PanelOptions {
  onClose(): void;
  onComment(target: CommentTarget, at: Element): void;
}

export interface Panel {
  element: HTMLElement;
  /** The path currently shown, or undefined while closed. */
  path(): string | undefined;
  /** Shows `content`, re-rendering the diff only when it differs from what is there. */
  show(content: PanelContent): void;
  close(): void;
}

/** The full diff of one file beside the board, scrolling on its own. */
export function createPanel(options: PanelOptions): Panel {
  const element = el("aside", "panel");
  element.hidden = true;

  const title = el("div", "panel-title");
  const counts = el("span", "counts");
  const range = el("div", "panel-range");
  const close = el("button", "panel-close", "Close");
  close.type = "button";
  close.addEventListener("click", () => {
    options.onClose();
  });
  const head = el("header", "panel-head");
  head.append(title, counts, close);
  const body = el("div", "panel-body");
  element.append(head, range, body);

  let shown: { path: string; diff: DiffResult } | undefined;

  return {
    element,
    path: () => shown?.path,
    show(content) {
      element.hidden = false;
      title.textContent = content.path;
      title.title = content.path;
      counts.textContent = `+${content.diff.added} −${content.diff.removed}`;
      range.textContent = `${content.fromLabel}  →  ${content.toLabel}`;
      if (shown?.path === content.path && shown.diff === content.diff) return;
      const sameFile = shown?.path === content.path;
      const scroll = sameFile ? body.scrollTop : 0;
      shown = { path: content.path, diff: content.diff };
      body.replaceChildren(
        renderDiff(content.diff, {
          path: content.path,
          onComment: (target, at) => {
            options.onComment(target, at);
          },
        }),
      );
      body.scrollTop = scroll;
    },
    close() {
      element.hidden = true;
      shown = undefined;
      body.replaceChildren();
    },
  };
}
