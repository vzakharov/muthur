import type { ReviewFile } from "#src/review-board/shared/review-data/index.ts";

export interface Provenance {
  kind: "renamed" | "moved";
  from: string;
}

const split = (path: string): { dir: string; name: string } => {
  const cut = path.lastIndexOf("/");
  return { dir: path.slice(0, cut + 1), name: path.slice(cut + 1) };
};

/**
 * Where a renamed file came from: `renamed` from its old name when the
 * directory is unchanged, `moved` from its old full path otherwise. Null for a
 * file git did not report as renamed.
 */
export function provenance(
  file: Pick<ReviewFile, "path" | "oldPath">,
): Provenance | null {
  if (file.oldPath === null) return null;
  const before = split(file.oldPath);
  return before.dir === split(file.path).dir
    ? { kind: "renamed", from: before.name }
    : { kind: "moved", from: file.oldPath };
}
