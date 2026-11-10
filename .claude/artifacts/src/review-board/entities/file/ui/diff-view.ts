import type {
  DiffHunk,
  DiffLine,
  DiffResult,
} from "#src/review-board/shared/lib/diff.ts";
import { el } from "#src/review-board/shared/lib/dom.ts";
import type { LineSpan } from "#src/review-board/shared/review-data/index.ts";
import type { CommentTarget } from "../model/comment-target.ts";
import type { DiffSyntax } from "../model/file-diff.ts";

export interface DiffViewOptions {
  path: string;
  /** Null shows every line as plain text. */
  syntax: DiffSyntax | null;
  onComment(target: CommentTarget, at: Element): void;
}

const SIGNS = { context: " ", add: "+", del: "−" } as const;
const CLASSES = { context: "ctx", add: "add", del: "del" } as const;

function codeOf(
  text: string,
  side: "L" | "R",
  number: number | null,
  syntax: DiffSyntax | null,
  path: string,
): (string | HTMLElement)[] {
  if (syntax === null) return [text];
  const lines = side === "L" ? syntax.old : syntax.new;
  const tokens = number === null ? undefined : lines[number - 1];
  if (tokens === undefined)
    throw new Error(`no highlighted line ${number} for ${path}`);
  return tokens.map((token) =>
    token.scope === null ? token.text : el("span", token.scope, token.text),
  );
}

function renderRow(
  line: DiffLine,
  syntax: DiffSyntax | null,
  path: string,
): HTMLElement {
  const row = el("div", `row ${CLASSES[line.kind]}`);
  // A deleted line is addressed, and highlighted, on the old side; every other on the new one.
  const side = line.kind === "del" ? "L" : "R";
  const number = side === "L" ? line.oldLine : line.newLine;
  if (number !== null) {
    row.dataset["side"] = side;
    row.dataset["line"] = String(number);
  }
  row.append(
    el("span", "num", line.oldLine === null ? "" : String(line.oldLine)),
    el("span", "num", line.newLine === null ? "" : String(line.newLine)),
  );
  const plus = el("button", "plus", "+");
  plus.type = "button";
  plus.title = "Comment on this line";
  plus.ariaLabel = "Comment on this line";
  const code = el("span", "code");
  code.append(
    el("span", "sign", SIGNS[line.kind]),
    ...codeOf(line.text, side, number, syntax, path),
  );
  row.append(plus, code);
  return row;
}

/**
 * Marks the new-side rows under `root` whose line falls in one of `spans`
 * (first and last line inclusive) with `focus`, and clears the mark elsewhere.
 */
export function markLines(root: Element, spans: readonly LineSpan[]): void {
  for (const row of root.querySelectorAll<HTMLElement>('.row[data-side="R"]')) {
    const line = Number(row.dataset["line"]);
    const marked = spans.some(([first, last]) => line >= first && line <= last);
    row.classList.toggle("focus", marked);
  }
}

const hunkLabel = (hunk: DiffHunk): string =>
  `@@ -${hunk.oldStart},${hunk.oldCount} +${hunk.newStart},${hunk.newCount} @@`;

/**
 * A unified diff: old and new line-number gutters, a hunk separator before each
 * hunk, and a "+" per line that reports a `CommentTarget`. Every line row
 * carries `data-side` (`R` for added and context lines, `L` for deleted ones)
 * and `data-line`, the number on that side.
 */
export function renderDiff(
  diff: DiffResult,
  options: DiffViewOptions,
): HTMLElement {
  const root = el("div", "diff");
  if (diff.hunks.length === 0) {
    root.append(el("div", "empty", "No textual changes"));
    return root;
  }
  for (const hunk of diff.hunks) {
    root.append(el("div", "hunk", hunkLabel(hunk)));
    for (const line of hunk.lines)
      root.append(renderRow(line, options.syntax, options.path));
  }
  root.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const plus = target.closest(".plus");
    if (plus === null) return;
    const row = plus.closest<HTMLElement>(".row");
    if (row === null) return;
    const side = row.dataset["side"];
    const line = Number(row.dataset["line"]);
    if ((side !== "R" && side !== "L") || Number.isNaN(line)) return;
    options.onComment({ path: options.path, side, line }, row);
  });
  return root;
}
