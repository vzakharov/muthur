export interface FileNode {
  kind: "file";
  name: string;
  path: string;
}
export interface FolderNode {
  kind: "folder";
  /** The folder's own name, or the joined names of a collapsed chain (`a/b/c`). */
  name: string;
  /** The full path from the repository root. */
  path: string;
  /** Folders first, then files, each group sorted by name. */
  children: TreeNode[];
}
export type TreeNode = FileNode | FolderNode;

interface Draft {
  folders: Map<string, Draft>;
  files: Set<string>;
}

const compare = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0);

const emptyDraft = (): Draft => ({ folders: new Map(), files: new Set() });

function insert(root: Draft, path: string): void {
  const parts = path.split("/").filter((part) => part !== "");
  const file = parts.pop();
  if (file === undefined) return;
  let at = root;
  for (const part of parts) {
    let next = at.folders.get(part);
    if (next === undefined) {
      next = emptyDraft();
      at.folders.set(part, next);
    }
    at = next;
  }
  at.files.add(file);
}

function childrenOf(draft: Draft, parentPath: string): TreeNode[] {
  const join = (name: string): string =>
    parentPath === "" ? name : `${parentPath}/${name}`;
  const folders = [...draft.folders]
    .sort(([a], [b]) => compare(a, b))
    .map(([name, first]) => {
      const names = [name];
      let at = first;
      while (at.files.size === 0 && at.folders.size === 1) {
        const only = at.folders.entries().next().value;
        if (only === undefined) break;
        names.push(only[0]);
        at = only[1];
      }
      const joined = names.join("/");
      const path = join(joined);
      return {
        kind: "folder" as const,
        name: joined,
        path,
        children: childrenOf(at, path),
      };
    });
  const files = [...draft.files].sort(compare).map((name) => ({
    kind: "file" as const,
    name,
    path: join(name),
  }));
  return [...folders, ...files];
}

/**
 * The folder tree of `paths` under an unnamed root. A chain of folders that
 * each hold only one folder collapses into one node; a folder holding a single
 * file stays a folder.
 */
export function buildTree(paths: readonly string[]): FolderNode {
  const draft = emptyDraft();
  for (const path of paths) insert(draft, path);
  return {
    kind: "folder",
    name: "",
    path: "",
    children: childrenOf(draft, ""),
  };
}
