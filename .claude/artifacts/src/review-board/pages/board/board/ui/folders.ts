import { el } from "#src/review-board/shared/lib/dom.ts";
import type { PackedFolder } from "#src/review-board/pages/board/layout/index.ts";

export interface FolderLayer {
  element: HTMLElement;
  /** Positions one rectangle per folder, creating them on first sight. */
  sync(folders: readonly PackedFolder[]): void;
}

/** The folder rectangles, behind the cards. */
export function createFolderLayer(): FolderLayer {
  const element = el("div", "folders");
  const nodes = new Map<string, HTMLElement>();
  return {
    element,
    sync(folders) {
      for (const folder of folders) {
        let node = nodes.get(folder.path);
        if (node === undefined) {
          node = el("div", "folder");
          const head = el("div", "folder-head", `${folder.name}/`);
          head.style.height = `${folder.header.height}px`;
          node.append(head);
          nodes.set(folder.path, node);
          element.append(node);
        }
        node.style.left = `${folder.rect.x}px`;
        node.style.top = `${folder.rect.y}px`;
        node.style.width = `${folder.rect.width}px`;
        node.style.height = `${folder.rect.height}px`;
      }
    },
  };
}
