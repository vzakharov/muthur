import { checkbox, el } from "#src/review-board/shared/lib/dom.ts";
import type { PackedFolder } from "#src/review-board/pages/board/layout/index.ts";

/** A folder's Viewed box: checked when every file it governs is viewed, mixed when some are; null when it governs none. */
export type FolderViewed = { checked: boolean; mixed: boolean } | null;

export interface FolderLayer {
  element: HTMLElement;
  /** Positions one rectangle per folder, creating them on first sight and hiding those no longer packed. */
  sync(
    folders: readonly PackedFolder[],
    viewedOf: (path: string) => FolderViewed,
  ): void;
}

interface FolderNode {
  node: HTMLElement;
  box: HTMLInputElement;
  check: HTMLElement;
}

/** The folder rectangles, behind the cards, each with a Viewed box in its header. */
export function createFolderLayer(
  onViewed: (path: string, viewed: boolean) => void,
): FolderLayer {
  const element = el("div", "folders");
  const nodes = new Map<string, FolderNode>();

  function create(folder: PackedFolder): FolderNode {
    const node = el("div", "folder");
    const head = el("div", "folder-head");
    head.dataset["path"] = folder.path;
    head.style.height = `${folder.header.height}px`;
    const { box, label: check } = checkbox(
      "Viewed",
      (viewed) => {
        onViewed(folder.path, viewed);
      },
      "folder-viewed",
    );
    check.title =
      "Mark every file here viewed, except those the author marked for focus";
    head.append(check, el("span", "folder-name", `${folder.name}/`));
    node.append(head);
    element.append(node);
    return { node, box, check };
  }

  return {
    element,
    sync(folders, viewedOf) {
      const packed = new Set<string>();
      for (const folder of folders) {
        packed.add(folder.path);
        let entry = nodes.get(folder.path);
        if (entry === undefined) {
          entry = create(folder);
          nodes.set(folder.path, entry);
        }
        const { node, box, check } = entry;
        node.hidden = false;
        node.style.left = `${folder.rect.x}px`;
        node.style.top = `${folder.rect.y}px`;
        node.style.width = `${folder.rect.width}px`;
        node.style.height = `${folder.rect.height}px`;
        const viewed = viewedOf(folder.path);
        check.hidden = viewed === null;
        box.checked = viewed?.checked ?? false;
        box.indeterminate = viewed?.mixed ?? false;
      }
      for (const [path, { node }] of nodes) node.hidden = !packed.has(path);
    },
  };
}
