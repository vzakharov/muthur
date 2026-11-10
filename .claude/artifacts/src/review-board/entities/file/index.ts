export { fileKey } from "./model/keys.ts";
export { createFileStore } from "./model/store.ts";
export type { BoardPrefs, FileStore, StoreStatus } from "./model/store.ts";
export { fileDiff } from "./model/file-diff.ts";
export type { FileDiff } from "./model/file-diff.ts";
export type {
  BoardRange,
  EffectiveRange,
  RangeOverride,
  Shift,
} from "./model/range.ts";
export type { CommentTarget } from "./model/comment-target.ts";
export { renderDiff } from "./ui/diff-view.ts";
export type { DiffViewOptions } from "./ui/diff-view.ts";
