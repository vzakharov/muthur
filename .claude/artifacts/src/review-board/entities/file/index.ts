export { fileKey } from "./model/keys.ts";
export { createFileStore } from "./model/store.ts";
export type { BoardPrefs, FileStore, StoreStatus } from "./model/store.ts";
export { fileDiff } from "./model/file-diff.ts";
export type { DiffSyntax, FileDiff } from "./model/file-diff.ts";
export type {
  BoardRange,
  EffectiveRange,
  RangeOverride,
  Shift,
} from "./model/range.ts";
export type { CommentTarget } from "./model/comment-target.ts";
export { viewFileUrl } from "./model/view-file-url.ts";
export { markLines, renderDiff } from "./ui/diff-view.ts";
export { renderMarkdown } from "./ui/markdown-view.ts";
export type { DiffViewOptions } from "./ui/diff-view.ts";
